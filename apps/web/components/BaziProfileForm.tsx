'use client';

import React, { forwardRef, useImperativeHandle } from 'react';
import dayjs from 'dayjs';
import { Form, Input, DatePicker, TimePicker, Radio, Switch, Button, Tooltip } from 'antd';
import { Calendar, Clock, Info } from 'lucide-react';
import PlacesAutocompleteInput from '@/components/PlacesAutocompleteInput';
import { toast } from 'sonner';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

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

    useImperativeHandle(ref, () => ({
      reset: () => { form.resetFields(); setLoading(false); },
    }));

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

    const onFinish = async (values: any) => {
      setLoading(true);
      try {
        // Build birth input for FastAPI
        const birthInput = {
          year: values.dob.year(),
          month: values.dob.month() + 1, // dayjs months are 0-indexed
          day: values.dob.date(),
          hour: values.time.hour(),
          minute: values.time.minute(),
          gender: values.gender === 'male' ? 1 : 0,
          latitude: parseFloat(values.latitude),
          longitude: parseFloat(values.longitude),
          use_solar_time_correction: values.solarCorrection ?? true,
          profileName: values.fullName,
          birthLocation: values.location,
        };

        // POST to /api/chart (Next.js Route Handler)
        const response = await fetch('/api/chart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(birthInput),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `HTTP ${response.status}`);
        }

        const { profileId } = await response.json();
        toast.success(tr.successGenerated[language]);
        form.resetFields();
        setLoading(false);
        onSuccess(profileId);
      } catch (error) {
        console.error('Error generating Bazi chart:', error);
        toast.error(tr.errorGenerated[language]);
        setLoading(false);
      }
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
