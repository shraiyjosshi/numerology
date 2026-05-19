import type { Metadata, Viewport } from "next";
import { Source_Serif_4, Inter } from "next/font/google";
import PageMandala from "@/components/PageMandala";
import StudioShell from "@/components/StudioShell";
import "./globals.css";

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-serif-display",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL
  ?? (process.env.VERCEL_PROJECT_PRODUCTION_URL && `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`)
  ?? (process.env.VERCEL_URL && `https://${process.env.VERCEL_URL}`)
  ?? "http://localhost:3000";

const title = "Numerology — Vedic numerology tools";
const description = "Vedic numerology tools: name and phone numbers.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title,
  description,
  openGraph: {
    type: "website",
    siteName: "Numerology",
    title,
    description,
    url: "/",
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
  themeColor: "#FDF8F1",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sourceSerif.variable} ${inter.variable}`}>
      <body className="antialiased">
        <div className="page-mandala-bg" aria-hidden="true">
          <PageMandala />
        </div>
        <StudioShell>{children}</StudioShell>
      </body>
    </html>
  );
}
