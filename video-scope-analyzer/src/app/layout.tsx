import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Team Builders Video Scope Analyzer",
  description: "Transform job site videos into structured scope summaries with AI-powered transcription and parsing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen antialiased`} suppressHydrationWarning={true}>
        {children}
      </body>
    </html>
  );
}
