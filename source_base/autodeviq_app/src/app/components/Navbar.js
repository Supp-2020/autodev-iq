"use client";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export const Navbar = () => {
  const router = useRouter();
  const [firstInitial, setFirstInitial] = useState("");

  useEffect(() => {
    // Get user info from localStorage
    const userJson = localStorage.getItem("user");
    if (userJson) {
      try {
        const user = JSON.parse(userJson);
        if (user?.firstName) {
          setFirstInitial(user.firstName.charAt(0).toUpperCase());
        }
      } catch (error) {
        console.error("Failed to parse user from localStorage", error);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("user");
    router.push("/login");
  };
  return (
    <header className="flex justify-between py-3 px-6 items-center">
      <div className="flex justify-between items-center navbar-container">
        <Link href="/" className="text-xl clickable">
          <Image src={"/assets/logo.png"} alt="logo" width={100} height={40} />
        </Link>
        <nav className="space-x-10">
          <Link href="/about" className="text-black clickable clickable-hover">
            About
          </Link>
          <Link href="#" className="text-black clickable clickable-hover">
            Team
          </Link>
          <Link href="#" className="text-black clickable clickable-hover">
            Tutorial
          </Link>
          {firstInitial && (
            <div className="group inline-flex items-center relative">
              <span className="text-white font-bold bg-blue-500 rounded-full w-8 h-8 flex items-center justify-center cursor-pointer">
                {firstInitial}
              </span>

              <button
                onClick={handleLogout}
                className="ml-2 text-blue-500 bg-gray-300 hover:bg-gray-200 px-3 py-1 rounded shadow-sm 
                         transition-all duration-200 opacity-0 group-hover:opacity-100"
              >
                Logout
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
};
