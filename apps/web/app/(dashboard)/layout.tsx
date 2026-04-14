'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import dayjs from 'dayjs';
import Link from 'next/link';
import Image from 'next/image';
import { Button, Divider, Layout, Popconfirm, Modal, Form, Input, DatePicker, TimePicker, Radio, Switch, Tooltip } from 'antd';
import { Plus, Users, MessageSquare, User, Trash2, Calendar, Clock, Info } from 'lucide-react';
import PlacesAutocompleteInput from '@/components/PlacesAutocompleteInput';
import { getProfiles, deleteProfile, saveProfile, calculateBazi, type BaziProfile } from '@/lib/baziOrchestrator';
import { toast } from 'sonner';
import { useLanguage } from '@/lib/languageContext';
import { translations } from '@/lib/translations';

const { Sider, Content } = Layout;

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
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
      <Form.Item name="solarCorrection" valuePropName="checked" noStyle initialValue={true}>
        <Switch size="small" />
      </Form.Item>
      <span style={{ fontSize: '10px', color: '#4d4635' }}>{solarTimeLabel ?? 'Solar Time'}</span>
      <Tooltip title="Calculates exact solar noon for precision.">
        <Info className="w-3 h-3 text-bronze-muted/40 cursor-help" />
      </Tooltip>
    </div>
  </div>
);

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [profiles, setProfiles] = useState<BaziProfile[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { language, setLanguage } = useLanguage();
  const tr = translations.sidebar;

  useEffect(() => {
    loadProfiles();
  }, [pathname]);

  useEffect(() => {
    // Set mounted flag and initial state
    setIsMounted(true);
    const handleResize = () => {
      setIsCollapsed(window.innerWidth < 1024);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadProfiles = () => {
    const loadedProfiles = getProfiles();
    setProfiles(loadedProfiles);
  };

  const onPlaceSelect = (lat: number, lng: number, address: string) => {
    form.setFieldsValue({ location: address, latitude: String(lat), longitude: String(lng) });
  };

  const handleAddProfile = () => {
    form.setFieldsValue({
      fullName: 'Desmond',
      dob: dayjs('1985-11-25'),
      time: dayjs('17:07', 'HH:mm'),
      location: 'Singapore',
      gender: 'male',
      latitude: '1.3253',
      longitude: '103.808053',
    });
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    form.resetFields();
  };

  const handleFormSubmit = async (values: any) => {
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
      toast.success(tr.successGenerated[language]);

      handleModalClose();
      loadProfiles();

      // Navigate to the new profile
      router.push(`/profile/${profileId}`);
    } catch (error) {
      console.error('Error generating Bazi chart:', error);
      toast.error(tr.errorGenerated[language]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProfile = (id: string) => {
    const remaining = profiles.filter((p) => p.id !== id);
    deleteProfile(id);
    setProfiles(remaining);
    toast.success(tr.successDeleted[language]);

    if (pathname.includes(id)) {
      if (remaining.length > 0) {
        const deletedIndex = profiles.findIndex((p) => p.id === id);
        const next = remaining[deletedIndex] ?? remaining[deletedIndex - 1];
        router.push(`/profile/${next.id}`);
      } else {
        handleAddProfile();
      }
    }
  };

  const isActive = (path: string) => {
    return pathname.includes(path);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Layout style={{ minHeight: '100vh' }}>
        {/* Left Sidebar */}
        <Sider className="dashboard-sider" width={isMounted && isCollapsed ? 85 : "12%"} style={{ background: 'linear-gradient(180deg, #f4f1e8 0%, #fbf9f4 100%)', borderRight: '1px solid rgba(115, 92, 0, 0.08)', boxShadow: '4px 0 20px rgba(115, 92, 0, 0.07)', position: 'fixed', height: '100vh', left: 0, top: 0, zIndex: 100, transition: 'width 0.3s ease' }}>
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* Logo */}
            <div style={{ padding: '12px 20px', borderBottom: '1px solid rgba(115, 92, 0, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Link href="/">
                {isMounted && isCollapsed ? (
                  <Image
                    src="/short_huat_life_logo.svg"
                    alt="Celestial Dawn"
                    width={40}
                    height={40}
                    style={{ width: 'auto', height: '40px' }}
                  />
                ) : (
                  <Image
                    src="/logo.png"
                    alt="Celestial Dawn"
                    width={180}
                    height={45}
                    style={{ width: 'auto', height: '56px' }}
                  />
                )}
              </Link>
            </div>

            {/* Nav Content */}
            <div className="sidebar-nav-content" style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
              {/* Profiles Section */}
              <div style={{ marginBottom: '8px' }}>
                {!(isMounted && isCollapsed) && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', padding: '0 4px' }}>
                    <h3 className="sidebar-section-label" style={{ fontSize: '11px', fontWeight: '600', color: 'rgba(115, 92, 0, 0.5)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'Noto Serif, serif' }}>
                      <span style={{ marginRight: '5px', fontSize: '14px', verticalAlign: 'middle', lineHeight: 1 }}>·</span>{tr.profiles[language]}
                    </h3>
                    <button
                      onClick={handleAddProfile}
                      style={{
                        width: '22px', height: '22px', padding: 0, borderRadius: '50%',
                        border: '1px solid rgba(115, 92, 0, 0.2)', background: 'transparent',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: 'pointer', color: '#735c00', transition: 'all 0.15s ease',
                        flexShrink: 0,
                      }}
                      onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(115, 92, 0, 0.08)'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(115, 92, 0, 0.4)'; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(115, 92, 0, 0.2)'; }}
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                )}

                <div>
                  {profiles.length === 0 ? (
                    <p style={{ fontSize: '13px', color: '#4d4635', padding: '8px 12px', opacity: 0.45, fontStyle: 'italic' }}>
                      {tr.noProfiles[language]}
                    </p>
                  ) : (
                    profiles.map((profile) => (
                      <div
                        key={profile.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          borderRadius: '6px',
                          marginBottom: '2px',
                          borderLeft: isActive(profile.id) ? '2px solid #735c00' : '2px solid transparent',
                          backgroundColor: isActive(profile.id) ? 'rgba(115, 92, 0, 0.07)' : 'transparent',
                          transition: 'all 0.15s ease',
                        }}
                        className="group"
                      >
                        <Link href={`/profile/${profile.id}`} style={{ flex: 1 }}>
                          <button
                            style={{
                              width: '100%', display: 'flex', alignItems: 'center', gap: isMounted && isCollapsed ? '4px' : '8px',
                              padding: '7px 10px', background: 'none', border: 'none', cursor: 'pointer',
                              fontSize: '14px', color: isActive(profile.id) ? '#735c00' : '#4d4635',
                              fontWeight: isActive(profile.id) ? '500' : '400',
                              textAlign: 'left', transition: 'color 0.15s ease', justifyContent: isMounted && isCollapsed ? 'center' : 'flex-start',
                            }}
                            title={profile.name}
                          >
                            <User className="w-3.5 h-3.5" style={{ flexShrink: 0, opacity: isActive(profile.id) ? 1 : 0.6 }} />
                            {!(isMounted && isCollapsed) && (
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{profile.name}</span>
                            )}
                            {isMounted && isCollapsed && (
                              <span style={{ fontSize: '12px', fontWeight: '500' }}>{profile.name.substring(0, 3)}</span>
                            )}
                          </button>
                        </Link>

                        <Popconfirm
                          title={tr.deleteProfile[language]}
                          description={`Are you sure you want to delete "${profile.name}"? This action cannot be undone.`}
                          onConfirm={() => handleDeleteProfile(profile.id)}
                          okText={tr.deleteOk[language]}
                          cancelText={tr.deleteCancel[language]}
                        >
                          <button
                            style={{
                              width: '28px', height: '28px', padding: 0, marginRight: '4px',
                              border: 'none', background: 'none', cursor: 'pointer',
                              color: '#c0392b', opacity: 0, borderRadius: '4px',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              transition: 'opacity 0.15s ease',
                            }}
                            className="group-hover:opacity-60 hover:!opacity-100"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </Popconfirm>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {!(isMounted && isCollapsed) && <Divider className="sidebar-divider" style={{ margin: '16px 0', borderColor: 'rgba(115, 92, 0, 0.08)' }} />}

              {/* Other Sections */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {!(isMounted && isCollapsed) && (
                  <div style={{ padding: '0 4px', marginBottom: '6px' }}>
                    <h3 className="sidebar-section-label" style={{ fontSize: '11px', fontWeight: '600', color: 'rgba(115, 92, 0, 0.5)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.12em', fontFamily: 'Noto Serif, serif' }}>
                      <span style={{ marginRight: '5px', fontSize: '14px', verticalAlign: 'middle', lineHeight: 1 }}>·</span>{tr.tools[language]}
                    </h3>
                  </div>
                )}

                <Link href="/compatibility" style={{ display: 'block' }}>
                  <div
                    className="sidebar-nav-item"
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: isMounted && isCollapsed ? 'center' : 'flex-start', gap: '9px',
                      padding: isMounted && isCollapsed ? '8px 0' : '8px 12px', borderRadius: '6px', cursor: 'pointer',
                      borderLeft: isActive('compatibility') ? '2px solid #735c00' : '2px solid transparent',
                      backgroundColor: isActive('compatibility') ? 'rgba(115, 92, 0, 0.07)' : 'transparent',
                      color: isActive('compatibility') ? '#735c00' : '#4d4635',
                      fontSize: '14px', fontWeight: isActive('compatibility') ? '500' : '400',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={e => { if (!isActive('compatibility')) (e.currentTarget as HTMLDivElement).style.background = 'rgba(115, 92, 0, 0.04)'; }}
                    onMouseLeave={e => { if (!isActive('compatibility')) (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
                    title="Compatibility"
                  >
                    <Users className="w-4 h-4" style={{ flexShrink: 0, opacity: isActive('compatibility') ? 1 : 0.55 }} />
                    {!(isMounted && isCollapsed) && <span className="sidebar-nav-label">{tr.compatibility[language]}</span>}
                  </div>
                </Link>

                <Link href="/ai_oracle_chat" style={{ display: 'block' }}>
                  <div
                    className="sidebar-nav-item"
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: isMounted && isCollapsed ? 'center' : 'flex-start', gap: '9px',
                      padding: isMounted && isCollapsed ? '8px 0' : '8px 12px', borderRadius: '6px', cursor: 'pointer',
                      borderLeft: isActive('ai_oracle_chat') ? '2px solid #735c00' : '2px solid transparent',
                      backgroundColor: isActive('ai_oracle_chat') ? 'rgba(115, 92, 0, 0.07)' : 'transparent',
                      color: isActive('ai_oracle_chat') ? '#735c00' : '#4d4635',
                      fontSize: '14px', fontWeight: isActive('ai_oracle_chat') ? '500' : '400',
                      transition: 'all 0.15s ease',
                    }}
                    onMouseEnter={e => { if (!isActive('ai_oracle_chat')) (e.currentTarget as HTMLDivElement).style.background = 'rgba(115, 92, 0, 0.04)'; }}
                    onMouseLeave={e => { if (!isActive('ai_oracle_chat')) (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
                    title="AI Oracle Chat"
                  >
                    <MessageSquare className="w-4 h-4" style={{ flexShrink: 0, opacity: isActive('ai_oracle_chat') ? 1 : 0.55 }} />
                    {!(isMounted && isCollapsed) && <span className="sidebar-nav-label">{tr.aiOracleChat[language]}</span>}
                  </div>
                </Link>
              </div>
            </div>

            {/* User Profile — bottom of sidebar */}
            <div className="sidebar-user-profile" style={{ padding: '12px', borderTop: '1px solid rgba(115, 92, 0, 0.08)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(115,92,0,0.22), rgba(115,92,0,0.07))',
                border: '1px solid rgba(115, 92, 0, 0.18)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
              }}>
                <User className="w-5 h-5" style={{ color: '#735c00' }} />
              </div>
              <p style={{ fontSize: '12px', fontWeight: '500', color: '#4d4635', margin: 0, fontFamily: 'Noto Serif, serif' }}>{tr.guest[language]}</p>
              <button className="sidebar-login-btn" style={{
                fontSize: '10px', color: '#735c00', background: 'transparent',
                border: '1px solid rgba(115, 92, 0, 0.3)', cursor: 'pointer',
                fontFamily: 'Noto Serif, serif', flexShrink: 0,
                borderRadius: '4px', padding: '4px 8px',
                transition: 'all 0.15s ease',
              }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(115, 92, 0, 0.08)'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(115, 92, 0, 0.5)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(115, 92, 0, 0.3)'; }}
              >
                {tr.login[language]}
              </button>
              {/* Language toggle */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  backgroundColor: '#3d3a5c',
                  borderRadius: '9999px',
                  padding: '3px',
                  flexShrink: 0,
                }}
              >
                {(['en', 'ch'] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setLanguage(lang)}
                    style={{
                      fontSize: '11px',
                      fontFamily: 'Noto Serif, serif',
                      fontWeight: 600,
                      letterSpacing: '0.05em',
                      padding: '3px 12px',
                      borderRadius: '9999px',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      backgroundColor: language === lang ? '#3d3a5c' : 'white',
                      color: language === lang ? 'white' : '#3d3a5c',
                      boxShadow: language === lang ? 'none' : '0 1px 3px rgba(0,0,0,0.1)',
                    }}
                  >
                    {lang === 'en' ? 'EN' : '中文'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Sider>

        {/* Main Content */}
        <Content className="dashboard-content" style={{ marginLeft: isMounted && isCollapsed ? '85px' : '12%', background: '#faf8f3', minHeight: '100vh', overflow: 'auto', transition: 'margin-left 0.3s ease' }}>
          {children}
        </Content>
      </Layout>

      {/* Add Profile Modal */}
      <Modal
        title={tr.modalTitle[language]}
        open={isModalOpen}
        onCancel={handleModalClose}
        footer={null}
        width={500}
      >
        <Form layout="vertical" form={form} onFinish={handleFormSubmit} className="space-y-6">
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
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
            <Radio.Group style={{ display: 'flex', gap: '24px' }}>
              <Radio value="female"><span style={{ fontSize: '12px' }}>{tr.labelFemale[language]}</span></Radio>
              <Radio value="male"><span style={{ fontSize: '12px' }}>{tr.labelMale[language]}</span></Radio>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Form.Item
              label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelLatitude[language]}</span>}
              name="latitude"
              rules={[
                { required: true, message: 'Required' },
                {
                  pattern: /^-?([0-8]?[0-9]|90)(\.[0-9]{1,6})?$/,
                  message: 'Valid latitude -90 to 90'
                }
              ]}
            >
              <Input
                placeholder="e.g., 1.3253"
                type="number"
                step="0.0001"
                className="bazi-input h-10"
              />
            </Form.Item>

            <Form.Item
              label={<span className="text-sm uppercase tracking-widest font-serif text-bronze-muted/60">{tr.labelLongitude[language]}</span>}
              name="longitude"
              rules={[
                { required: true, message: 'Required' },
                {
                  pattern: /^-?([0-9]{1,2}|1[0-7][0-9]|180)(\.[0-9]{1,6})?$/,
                  message: 'Valid longitude -180 to 180'
                }
              ]}
            >
              <Input
                placeholder="e.g., 103.8415"
                type="number"
                step="0.0001"
                className="bazi-input h-10"
              />
            </Form.Item>
          </div>

          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            style={{ backgroundColor: '#735c00', borderColor: '#735c00', height: '40px', marginTop: '24px' }}
          >
            {tr.btnGenerate[language]}
          </Button>
        </Form>
      </Modal>
    </div>
  );
}
