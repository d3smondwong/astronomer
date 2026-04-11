import Image from 'next/image';

export default function Header() {
  return (
    <header className="fixed top-0 w-full z-50 shadow-sm" style={{ backgroundColor: '#fbf9f4' }}>
      <nav className="flex justify-between items-center px-8 py-2 max-w-7xl mx-auto w-full">
        <div className="flex items-center">
          <Image
            src="/logo.png"
            alt="Celestial Dawn"
            width={220}
            height={55}
            loading="eager"
            style={{ width: 'auto', height: '56px' }}
          />
        </div>
        <div className="flex items-center gap-4">
          <button className="text-gold-deep font-serif tracking-tight hover:text-gold-light transition-colors duration-300 px-4 py-2">
            Sign In
          </button>
        </div>
      </nav>
    </header>
  );
}
