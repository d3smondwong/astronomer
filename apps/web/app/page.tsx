"use client";

import React from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import dayjs from 'dayjs';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import {
  Form,
  Input,
  DatePicker,
  TimePicker,
  Radio,
  Switch,
  Button,
  Tooltip,
} from 'antd';
import {
  Stars,
  Calendar,
  Clock,
  Info,
  Trees
} from 'lucide-react';
import { motion } from 'motion/react';
import TempleBuddhistIcon from '@mui/icons-material/TempleBuddhist';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import { saveProfile, calculateBazi, type BaziProfile } from '@/lib/baziOrchestrator';
import { toast } from 'sonner';
import PlacesAutocompleteInput from '@/components/PlacesAutocompleteInput';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

// Wrapper so Ant Design can pass value/onChange to TimePicker while
// rendering the Solar Time row inside the same Form.Item — error appears below both.
const TimePickerWithSolar = ({ value, onChange, solarTimeLabel }: { value?: any; onChange?: (val: any) => void; solarTimeLabel?: string }) => (
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

const Hero = () => {
  const { language } = useLanguage();
  const tr = translations.landing;
  return (
  <div className="space-y-10 md:pt-12">
    <div className="space-y-4">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="font-serif text-gold-deep tracking-tight leading-tight text-4xl md:text-5xl font-normal text-center"
      >
        {tr.heroLine1[language]}<br />
        <span className="mt-4 block">{tr.heroLine2[language]}</span>
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="text-2xl md:text-3xl font-serif italic text-bronze-muted leading-snug text-center"
      >
        {tr.tagline[language]}
      </motion.p>
    </div>

    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1, delay: 0.4 }}
      className="pt-4 space-y-6"
    >
      <div className="flex items-center gap-4 justify-center">
        <div className="w-12 h-[1px] bg-outline-variant"></div>
        <img src="/temple_icon.svg" alt="Temple" className="w-10 h-10 md:w-12 md:h-12 lg:w-14 lg:h-14" />
        <div className="w-12 h-[1px] bg-outline-variant"></div>
      </div>
      <blockquote className="text-xl md:text-2xl font-serif italic text-bronze-muted/80 leading-relaxed text-center">
        "The winds of destiny are never neutral; they carry the whispers of your ancestors and the blueprint of your future."
      </blockquote>
    </motion.div>
  </div>
  );
};

const BaziForm = () => {
  const router = useRouter();
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);
  const { language } = useLanguage();
  const tr = translations.landing;

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
    form.setFieldsValue({
      location: address,
      latitude: String(lat),
      longitude: String(lng),
    });
  };

  const onFinish = async (values: any) => {
    setLoading(true);
    try {
      const profileId = `profile_${Date.now()}`;

      const profile: BaziProfile = {
        id: profileId,
        name: values.fullName,
        birthDate: values.dob.toDate(),
        birthTime: values.time.format('HH:mm'),
        birthLocation: values.location,
        gender: values.gender,
        latitude: parseFloat(values.latitude),
        longitude: parseFloat(values.longitude),
      };

      // Calculate Bazi chart (async)
      const baziChart = await calculateBazi({
        name: profile.name,
        birthDate: profile.birthDate,
        birthTime: profile.birthTime,
        birthLocation: profile.birthLocation,
        gender: profile.gender,
        latitude: profile.latitude,
        longitude: profile.longitude,
      });

      // Save profile with Bazi chart
      const profileWithChart: BaziProfile = {
        ...profile,
        baziChart,
      };

      saveProfile(profileWithChart);

      toast.success('Bazi chart generated successfully!');

      // Navigate to the profile dashboard
      router.push(`/profile/${profileId}`);
    } catch (error) {
      console.error('Error generating Bazi chart:', error);
      toast.error('Failed to generate Bazi chart. Please try again.');
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
      className="bg-surface-lowest p-8 md:p-10 rounded-lg shadow-xl relative overflow-hidden"
    >
      <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full border border-gold-deep/10"></div>

      <div className="relative z-10">
        <div className="mb-8 text-center">
          <Stars className="text-gold-deep w-8 h-8 mx-auto mb-3" />
          <h2 className="text-2xl font-serif text-bronze-muted mb-2">{tr.formHeading[language]}</h2>
          <p className="text-xs text-bronze-muted/60">{tr.formSubHeading[language]}</p>
        </div>

        <Form layout="vertical" form={form} onFinish={onFinish} className="space-y-6">
          <Form.Item
            label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelProfileName[language]}</span>}
            name="fullName"
            rules={[
              { required: true, message: 'Please enter your profile name' },
              { min: 2, message: 'Profile name must be at least 2 characters' }
            ]}
          >
            <Input placeholder="Enter your profile name" className="bazi-input h-10" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelDob[language]}</span>}
              name="dob"
              rules={[{ required: true, message: 'Please select your date of birth' }]}
            >
              <DatePicker className="w-full bazi-input h-10" suffixIcon={<Calendar className="w-4 h-4 text-bronze-muted/40" />} />
            </Form.Item>
            <Form.Item
              label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelTimeOfBirth[language]}</span>}
              name="time"
              rules={[{ required: true, message: 'Please select your birth time' }]}
            >
              <TimePickerWithSolar solarTimeLabel={tr.solarTime[language]} />
            </Form.Item>
          </div>

          <Form.Item
            label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelGender[language]}</span>}
            name="gender"
            rules={[{ required: true, message: 'Please select your gender' }]}
            style={{ marginTop: '-12px' }}
          >
            <Radio.Group className="flex gap-6">
              <Radio value="female"><span className="text-xs">{tr.labelFemale[language]}</span></Radio>
              <Radio value="male"><span className="text-xs">{tr.labelMale[language]}</span></Radio>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelBirthLocation[language]}</span>}
            name="location"
            rules={[{ required: true, message: 'Please enter your birth location' }]}
          >
            <PlacesAutocompleteInput
              placeholder="Hospital, Country"
              className="bazi-input h-10"
              onPlaceSelect={onPlaceSelect}
              onClear={() => {
                form.setFieldsValue({ latitude: '', longitude: '' });
              }}
            />
          </Form.Item>

          <Form.Item name="latitude" hidden><Input /></Form.Item>
          <Form.Item name="longitude" hidden><Input /></Form.Item>

          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            className="gold-gradient w-full h-12 text-white font-serif text-base tracking-wide border-none shadow-lg hover:opacity-90 transition-all active:scale-95"
          >
            {tr.btnGenerate[language]}
          </Button>

          <div className="flex items-center gap-3 pt-4">
            <div className="flex-1 h-px bg-gold-deep/10"></div>
            <span className="text-xs text-bronze-muted/50 uppercase tracking-wider">{tr.newLabel[language]}</span>
            <div className="flex-1 h-px bg-gold-deep/10"></div>
          </div>

          <Button
            onClick={loadDemoProfile}
            className="w-full h-10 border border-gold-deep/30 text-gold-deep hover:bg-gold-deep/5 font-serif tracking-wide text-sm"
          >
            {tr.btnDemo[language]}
          </Button>
        </Form>
      </div>
    </motion.div>
  );
};

const FeatureCard = ({ icon: Icon, title, description, label, iconSrc }: any) => (
  <div className="feature-card bg-surface-low p-10 rounded-lg shadow-sm border border-gold-deep/5 flex flex-col items-center text-center space-y-6 relative group">
    <div className="w-16 h-16 rounded-full bg-gold-deep/5 flex items-center justify-center border border-gold-deep/20">
      {iconSrc ? (
        <Image src={iconSrc} alt={title} width={32} height={32} style={{ width: 'auto', height: '32px' }} />
      ) : (
        <Icon className="text-gold-deep w-8 h-8" />
      )}
    </div>
    <div className="space-y-3">
      <h3 className="text-2xl font-serif text-gold-deep tracking-tight">{title}</h3>
      <p className="text-sm leading-relaxed text-bronze-muted/80 italic">
        {description}
      </p>
    </div>
    <div className="pt-4 border-t border-gold-deep/10 w-full">
      <span className="text-[10px] uppercase tracking-[0.2em] text-bronze-muted/60">{label}</span>
    </div>
  </div>
);


export default function Home() {
  const { language } = useLanguage();
  const tr = translations.landing;

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-grow pt-32 pb-20">
        <section className="max-w-7xl mx-auto px-8 grid md:grid-cols-2 gap-16 items-start">
          <Hero />
          <BaziForm />
        </section>

        <div className="max-w-7xl mx-auto px-8 flex justify-center py-10">
          <div className="w-px h-20 bg-gradient-to-b from-gold-deep/30 to-transparent"></div>
        </div>

        <section className="max-w-7xl mx-auto px-8 grid grid-cols-1 md:grid-cols-3 gap-8">
          <FeatureCard
            icon={TempleBuddhistIcon}
            title={tr.featureAncientTitle[language]}
            description={tr.featureAncientDesc[language]}
            label={tr.featureAncientLabel[language]}
          />
          <FeatureCard
            icon={Trees}
            title={tr.featureFiveTitle[language]}
            description={tr.featureFiveDesc[language]}
            label={tr.featureFiveLabel[language]}
          />
          <FeatureCard
            icon={TimelineOutlinedIcon}
            title={tr.featureLuckTitle[language]}
            description={tr.featureLuckDesc[language]}
            label={tr.featureLuckLabel[language]}
          />
        </section>
      </main>

      <Footer />
    </div>
  );
}