"use client";
import { CardComponent } from "./components/Card";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "./components/Navbar";
import Footer from "./components/Footer";

export default function Home() {
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const isLoggedIn = localStorage.getItem("isLoggedIn");
    if (isLoggedIn === "true") {
      setAuthorized(true);
    } else {
      router.push("/login");
    }
    setIsReady(true);
  }, [router]);

  if (!isReady) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent border-solid rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!authorized) {
    return null;
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="flex-1">
        <div className="relative w-full h-[250px]">
          <Image
            src="/assets/banner.png"
            alt="banner"
            fill
            className="object-cover"
          />
        </div>
        <CardComponent />
      </div>
      <Footer />
    </div>
  );
}
