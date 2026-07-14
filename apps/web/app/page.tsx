"use client";

import { useEffect, useRef } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

import {
  Stars,
  Trees
} from 'lucide-react';
import { motion } from 'motion/react';
import TempleBuddhistIcon from '@mui/icons-material/TempleBuddhist';
import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
import BaziProfileForm from '@/components/BaziProfileForm';
import { useLanguage } from '@/lib/languageContext';
import { useAuth } from '@/lib/authContext';
import { translations } from '@/lib/translations';


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
        <Image src="/temple_icon.svg" alt="Temple" width={56} height={56} className="w-10 h-10 md:w-12 md:h-12 lg:w-14 lg:h-14" />
        <div className="w-12 h-[1px] bg-outline-variant"></div>
      </div>
      <blockquote className="text-xl md:text-2xl font-serif italic text-bronze-muted/80 leading-relaxed text-center">
        &ldquo;The winds of destiny are never neutral; they carry the whispers of your ancestors and the blueprint of your future.&rdquo;
      </blockquote>
    </motion.div>
  </div>
  );
};

const BaziForm = () => {
  const router = useRouter();
  const { language } = useLanguage();
  const { spotlightCreateForm, setSpotlightCreateForm } = useAuth();
  const tr = translations.landing;

  // Base card shadow (≈ shadow-xl). When spotlit, add a huge spread ring that darkens the
  // whole page except this form. Always control box-shadow inline so it transitions both ways.
  const baseShadow = '0 8px 40px rgba(0,0,0,0.18)';
  const spotlightShadow = `${baseShadow}, 0 0 0 9999px rgba(0,0,0,0.5)`;

  return (
    <>
      {/* Transparent catcher over the darkened page — click anywhere outside the form to dismiss. */}
      {spotlightCreateForm && (
        <div
          onClick={() => setSpotlightCreateForm(false)}
          className="fixed inset-0 z-[55]"
          aria-hidden
        />
      )}

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="bg-surface-lowest p-8 md:p-10 rounded-lg relative overflow-hidden"
        style={{
          boxShadow: spotlightCreateForm ? spotlightShadow : baseShadow,
          transition: 'box-shadow 0.4s ease',
          ...(spotlightCreateForm && { zIndex: 60 }),
        }}
      >
        <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full border border-gold-deep/10"></div>

        <div className="relative z-10">
          <div className="mb-8 text-center">
            <Stars className="text-gold-deep w-8 h-8 mx-auto mb-3" />
            <h2 className="text-2xl font-serif text-bronze-muted mb-2">{tr.formHeading[language]}</h2>
            <p className="text-xs text-bronze-muted/60">{tr.formSubHeading[language]}</p>
          </div>

          <BaziProfileForm
            showDemoButton
            onSuccess={(profileId) => {
              setSpotlightCreateForm(false);
              router.push(`/profile/${profileId}`);
            }}
          />
        </div>
      </motion.div>
    </>
  );
};

const FeatureCard = ({ icon: Icon, title, description, label, iconSrc }: any) => (
  <div className="feature-card bg-surface-low p-10 rounded-lg shadow-sm border border-gold-deep/5 flex flex-col items-center text-center space-y-6 relative group">
    <div className="w-16 h-16 rounded-full bg-gold-deep/5 flex items-center justify-center border border-gold-deep/20">
      {iconSrc ? (
        <Image src={iconSrc} alt={title} width={32} height={32} className="w-auto h-8" />
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
  const { openAuthModal, user, loading } = useAuth();
  const router = useRouter();
  const tr = translations.landing;

  // Arriving with ?login=1 (e.g. redirected here from a profile the visitor can't access):
  // pop the auth modal for guests, then strip the param. Wait for auth to resolve so a
  // permanent user who already signed in isn't prompted needlessly.
  const loginPromptHandledRef = useRef(false);
  useEffect(() => {
    if (loginPromptHandledRef.current || loading) return;
    if (new URLSearchParams(window.location.search).get('login') !== '1') return;
    loginPromptHandledRef.current = true;
    router.replace('/');
    if (!user || user.isAnonymous) openAuthModal();
  }, [loading, user, router, openAuthModal]);

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