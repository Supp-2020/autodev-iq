"use client";

import { usePathname } from "next/navigation";
import { Navbar } from "./components/Navbar";
import Footer from "./components/Footer";

export default function LayoutWrapper({ children }) {
  const pathname = usePathname();

  const isAuthRoute = pathname.startsWith("/login") || pathname.startsWith("/register");

  return (
    <>
      {!isAuthRoute && <Navbar />}
      <main className="flex-grow">{children}</main>
      {!isAuthRoute && <Footer />}
    </>
  );
}
