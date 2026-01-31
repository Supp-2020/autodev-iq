"use client";
import { createContext, useContext, useState } from "react";

const AutoDevContext = createContext();

export const useAutoDevContext = () => {
  const context = useContext(AutoDevContext);
  if (!context) {
    console.error("useAutoDevContext must be used within AutoDevProvider");
    throw new Error("useAutoDevContext must be used within AutoDevProvider");
  }
  return context;
};

/* Add states which you want to serve globally across the application */
export const AutoDevProvider = ({ children }) => {

  const value = {};

  return (
    <AutoDevContext.Provider value={value}>{children}</AutoDevContext.Provider>
  );
};