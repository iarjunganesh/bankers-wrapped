import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Banker's Wrapped",
  description: "Your financial year, told as a story.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    apple: "/favicon.svg",
  },
  openGraph: {
    title: "Banker's Wrapped",
    description: "Your financial year, told as a story.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
