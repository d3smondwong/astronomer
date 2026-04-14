import 'antd/dist/reset.css';
import type { Metadata } from "next";
import "@/styles/globals.css";
import "react-day-picker/dist/style.css";
import { ConfigProvider } from 'antd';
import { LanguageProvider } from '@/lib/languageContext';

const antdTheme = {
  token: {
    colorPrimary: '#735c00',
    fontFamily: 'Noto Serif, serif',
    borderRadius: 4,
    colorBgContainer: '#ffffff',
    colorText: '#4d4635',
    colorBorder: 'rgba(127, 118, 99, 0.15)',
  },
  components: {
    Button: {
      colorPrimary: '#735c00',
      colorPrimaryHover: '#d4af37',
      borderRadius: 4,
    },
    Input: {
      activeBorderColor: '#735c00',
      hoverBorderColor: '#d4af37',
    },
    Radio: {
      colorPrimary: '#735c00',
      colorBorder: '#8b7f73',
    },
  },
};

export const metadata: Metadata = {
  title: "Celestial Dawn",
  description: "An ethereal Bazi reading application rooted in ancient wisdom and driven by AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ConfigProvider theme={antdTheme}>
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </ConfigProvider>
      </body>
    </html>
  );
}
