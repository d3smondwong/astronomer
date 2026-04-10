import Image from 'next/image';

export default function Footer() {
  return (
    <footer className="w-full py-3 border-t border-gold-deep/10 glass-panel">
      <div className="flex flex-col items-center gap-1 w-full max-w-7xl mx-auto px-4">
        <Image
          src="/logo.png"
          alt="Huat Life"
          width={220}
          height={55}
          style={{ width: 'auto', height: '56px' }}
        />
        <div className="flex flex-wrap gap-4 md:gap-12 justify-center font-serif text-xs md:text-sm tracking-wide md:tracking-widest uppercase text-gold-deep">
          <a href="#" className="hover:text-gold-light transition-all duration-300">Privacy</a>
          <a href="#" className="hover:text-gold-light transition-all duration-300">Terms of Destiny</a>
          <a href="#" className="hover:text-gold-light transition-all duration-300">Contact</a>
        </div>
        <p className="font-serif text-xs md:text-sm tracking-wide md:tracking-widest uppercase text-gold-deep/70 px-4 text-center">
          © 2026 HUAT.LIFE
        </p>
      </div>
    </footer>
  );
}
