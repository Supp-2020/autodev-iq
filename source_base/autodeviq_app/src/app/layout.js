import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AutoDevProvider } from "./context/AutoDevContext"; 

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "AutoDev IQ",
  description: "AutoDev IQ",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AutoDevProvider>
          <main>{children}</main>
        </AutoDevProvider>
      </body>
    </html>
  );
}
