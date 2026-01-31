import React from "react";

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 py-6 px-4 mt-10">
      <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0 footer-container">
        {/* Left Side */}
        <div className="text-sm text-center md:text-left">
          © {new Date().getFullYear()} AutoDev IQ. All rights reserved.
        </div>

        {/* Right Side - Socials or Tagline */}
        <div className="text-sm text-center md:text-right">
          Built for developers ❤️ Powered by AI
        </div>
      </div>
    </footer>
  );
};

export default Footer;
