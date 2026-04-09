import type { Metadata } from 'next';
import { Inter, Geist } from 'next/font/google';
import '@/styles/index.css';
import '@/styles/fonts.css';
import '@/styles/theme.css';
import { Toaster } from '@/components/ui/sonner';
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Bazi Fortune Telling',
  description: 'Discover your destiny through the ancient art of Four Pillars of Destiny',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={cn("font-sans", geist.variable)}>
      <body className={inter.className}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
