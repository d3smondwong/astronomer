'use client';

import React, { forwardRef, useImperativeHandle, useRef, useEffect } from 'react';
import dayjs from 'dayjs';
import { Form, Input, DatePicker, TimePicker, Radio, Switch, Button, Tooltip } from 'antd';
import { Calendar, Clock, Info } from 'lucide-react';
import PlacesAutocompleteInput from '@/components/PlacesAutocompleteInput';
import { toast } from 'sonner';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';
import { useAuth } from '@/lib/authContext';
import { reportClientError } from '@/lib/errorReporter';

const TimePickerWithSolar = ({
  value,
  onChange,
  solarTimeLabel,
}: {
  value?: any;
  onChange?: (val: any) => void;
  solarTimeLabel?: string;
}) => (
  <div>
    <TimePicker
      value={value}
      onChange={onChange}
      className="w-full bazi-input h-10"
      format="HH:mm"
      showNow={false}
      suffixIcon={<Clock className="w-4 h-4 text-bronze-muted/40" />}
    />
    <div className="flex items-center gap-2 mt-2">
      <Form.Item name="solarCorrection" valuePropName="checked" noStyle initialValue={true}>
        <Switch size="small" />
      </Form.Item>
      <span className="text-[10px] text-bronze-muted">{solarTimeLabel ?? 'Solar Time'}</span>
      <Tooltip title="Calculates exact solar noon for precision.">
        <Info className="w-3 h-3 text-bronze-muted/40 cursor-help" />
      </Tooltip>
    </div>
  </div>
);

export interface BaziProfileFormRef {
  reset: () => void;
}

interface BaziProfileFormProps {
  /** Called with the new profileId after the chart is saved. */
  onSuccess: (profileId: string) => void;
  /** Show the demo profile button (landing page only). */
  showDemoButton?: boolean;
  /** Tailwind className for the submit button. Defaults to the landing-page gold style. */
  submitClassName?: string;
}

const BaziProfileForm = forwardRef<BaziProfileFormRef, BaziProfileFormProps>(
  ({ onSuccess, showDemoButton = false, submitClassName }, ref) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = React.useState(false);
    const { language } = useLanguage();
    const tr = translations.form;
    const { user, loading: authLoading, openAuthModal, refreshSession } = useAuth();

    // Stores form values when a guest is funneled to sign-up — auto-submitted once they upgrade.
    const pendingValuesRef = useRef<any>(null);
    const prevIsAnonRef = useRef<boolean | null>(null);

    useImperativeHandle(ref, () => ({
      reset: () => { form.resetFields(); setLoading(false); pendingValuesRef.current = null; },
    }));

    // When the guest (anonymous) upgrades to a permanent account, auto-submit any chart held
    // behind the sign-up prompt (it's now tied to the new account).
    useEffect(() => {
      const wasAnon = prevIsAnonRef.current;
      const nowAnon = user?.isAnonymous ?? null;
      prevIsAnonRef.current = nowAnon;
      if (wasAnon === true && nowAnon === false) {
        if (pendingValuesRef.current !== null) {
          const values = pendingValuesRef.current;
          pendingValuesRef.current = null;
          void submitChart(values, false);
        }
      }
    }, [user?.isAnonymous]); // eslint-disable-line react-hooks/exhaustive-deps

    const loadDemoProfile = () => {
      form.setFieldsValue({
        fullName: 'Desmond',
        dob: dayjs('1985-11-25'),
        time: dayjs('17:07', 'HH:mm'),
        location: 'Singapore',
        gender: 'male',
        latitude: '1.3253',
        longitude: '103.808053',
        solarCorrection: true,
      });
    };

    const onPlaceSelect = (lat: number, lng: number, address: string) => {
      form.setFieldsValue({ location: address, latitude: String(lat), longitude: String(lng) });
    };

    const submitChart = async (values: any, skipInsights: boolean) => {
      setLoading(true);
      // Minted here at the true origin so the same id spans browser → Next → FastAPI,
      // and ties a failure report to the server-side natal compute logs.
      const requestId = crypto.randomUUID();
      let status: number | undefined;
      try {
        const birthInput = {
          year: values.dob.year(),
          month: values.dob.month() + 1,
          day: values.dob.date(),
          hour: values.time.hour(),
          minute: values.time.minute(),
          gender: values.gender === 'male' ? 1 : 0,
          latitude: parseFloat(values.latitude),
          longitude: parseFloat(values.longitude),
          use_solar_time_correction: values.solarCorrection ?? true,
          profileName: values.fullName,
          birthLocation: values.location,
          skipInsights,
          requestId,
        };

        const idToken = user ? await user.getIdToken() : null;
        const response = await fetch('/api/chart', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(idToken && { Authorization: `Bearer ${idToken}` }),
          },
          body: JSON.stringify(birthInput),
        });
        status = response.status;

        if (response.status === 409) {
          // Guest's one free chart is already used (server-enforced) → require an account.
          // Hold the values so the chart auto-submits, tied to the new account, after sign-up.
          // pendingChart tells AuthModal to stand down from its own routing so this form owns
          // the post-auth navigation (avoids a competing redirect / dropped chart).
          pendingValuesRef.current = values;
          openAuthModal({ reason: 'pendingChart' });
          return;
        }

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const { profileId } = await response.json();
        form.resetFields();
        // Make sure the session cookie reflects the current (owner) identity before navigating —
        // otherwise the SSR ownership check would bounce us off the chart we just created (e.g.
        // right after an anonymous→permanent upgrade). If it can't be established even after
        // retries, don't walk into that redirect loop — the chart was saved; tell the user.
        if (!(await refreshSession())) {
          toast.error(translations.auth.sessionError[language]);
          return;
        }
        toast.success(tr.successGenerated[language]);
        onSuccess(profileId);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.error(`Error generating Bazi chart [req:${requestId}]:`, error);
        reportClientError({ context: 'chart_generation', requestId, uid: user?.uid, status, message });
        toast.error(tr.errorGenerated[language]);
      } finally {
        setLoading(false);
      }
    };

    const onFinish = async (values: any) => {
      // Auth signs in anonymously on load; in the brief window before that completes (or if it
      // failed), `user` is null and /api/chart would 401. Guard rather than show a generic error.
      if (!user) {
        toast.error(tr.notReady[language]);
        return;
      }
      // Guests (anonymous) get the chart only — skipInsights — and the server enforces the
      // one-free-chart limit, returning 409 which submitChart turns into a sign-up prompt.
      // Permanent users always generate, with insights.
      await submitChart(values, user.isAnonymous);
    };

    const labelClass = 'text-sm uppercase tracking-widest font-serif text-bronze-muted/60';

    return (
      <Form layout="vertical" form={form} onFinish={onFinish} className="space-y-6">
        <Form.Item
          label={<span className={labelClass}>{tr.labelProfileName[language]}</span>}
          name="fullName"
          rules={[
            { required: true, message: 'Please enter your profile name' },
            { min: 2, message: 'Profile name must be at least 2 characters' },
          ]}
        >
          <Input placeholder="Enter your profile name" className="bazi-input h-10" />
        </Form.Item>

        <div className="grid grid-cols-2 gap-4">
          <Form.Item
            label={<span className={labelClass}>{tr.labelDob[language]}</span>}
            name="dob"
            rules={[{ required: true, message: 'Please select your date of birth' }]}
          >
            <DatePicker
              className="w-full bazi-input h-10"
              suffixIcon={<Calendar className="w-4 h-4 text-bronze-muted/40" />}
            />
          </Form.Item>
          <Form.Item
            label={<span className={labelClass}>{tr.labelTimeOfBirth[language]}</span>}
            name="time"
            rules={[{ required: true, message: 'Please select your birth time' }]}
          >
            <TimePickerWithSolar solarTimeLabel={tr.solarTime[language]} />
          </Form.Item>
        </div>

        <Form.Item
          label={<span className={labelClass}>{tr.labelGender[language]}</span>}
          name="gender"
          rules={[{ required: true, message: 'Please select your gender' }]}
          style={{ marginTop: '-20px' }}
        >
          <Radio.Group className="flex gap-6">
            <Radio value="female"><span className="text-sm">{tr.labelFemale[language]}</span></Radio>
            <Radio value="male"><span className="text-sm">{tr.labelMale[language]}</span></Radio>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          label={<span className={labelClass}>{tr.labelBirthLocation[language]}</span>}
          name="location"
          rules={[{ required: true, message: 'Please enter your birth location' }]}
        >
          <PlacesAutocompleteInput
            placeholder="Hospital, Country"
            className="bazi-input h-10"
            onPlaceSelect={onPlaceSelect}
            onClear={() => form.setFieldsValue({ latitude: '', longitude: '' })}
          />
        </Form.Item>

        {/* Coordinates are populated by PlacesAutocompleteInput — never shown to the user */}
        <Form.Item name="latitude" hidden><Input /></Form.Item>
        <Form.Item name="longitude" hidden><Input /></Form.Item>

        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          disabled={authLoading}
          className={
            submitClassName ??
            'gold-gradient w-full h-12 text-white font-serif text-base tracking-wide border-none shadow-lg hover:opacity-90 transition-all active:scale-95'
          }
        >
          {tr.btnGenerate[language]}
        </Button>

        {showDemoButton && (
          <>
            <div className="flex items-center gap-3 pt-4">
              <div className="flex-1 h-px bg-gold-deep/10" />
              <span className="text-xs text-bronze-muted/50 uppercase tracking-wider">
                {tr.newLabel[language]}
              </span>
              <div className="flex-1 h-px bg-gold-deep/10" />
            </div>
            <Button
              onClick={loadDemoProfile}
              className="w-full h-10 border border-gold-deep/30 text-gold-deep hover:bg-gold-deep/5 font-serif tracking-wide text-sm"
            >
              {tr.btnDemo[language]}
            </Button>
          </>
        )}
      </Form>
    );
  }
);

BaziProfileForm.displayName = 'BaziProfileForm';

export default BaziProfileForm;
