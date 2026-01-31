"use client";
import { createContext, useContext, useState, useEffect } from "react";

const TestGenerationContext = createContext();

export const useTestGenerationContext = () => {
  const context = useContext(TestGenerationContext);
  if (!context) {
    console.error(
      "useTestGenerationContext must be used within AutoDevProvider"
    );
    throw new Error(
      "useTestGenerationContext must be used within AutoDevProvider"
    );
  }
  return context;
};

export const TestGenerationProvider = ({ children }) => {
  // Load saved state on first render
  const saved =
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("test_autoDev") || "{}")
      : {};

  const [projectId, setProjectId] = useState(saved.projectId || "");
  const [selectedProject, setSelectedProject] = useState(
    saved.selectedProject || {}
  );
  const [selectedBranch, setSelectedBranch] = useState(
    saved.selectedBranch || ""
  );
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(
    saved.isPanelCollapsed || false
  );

  // Sync to sessionStorage whenever any of these states change
  useEffect(() => {
    sessionStorage.setItem(
      "test_autoDev",
      JSON.stringify({
        projectId,
        selectedProject,
        selectedBranch,
        isPanelCollapsed,
      })
    );
  }, [projectId, selectedProject, selectedBranch, isPanelCollapsed]);

  const value = {
    projectId,
    setProjectId,
    selectedProject,
    setSelectedProject,
    selectedBranch,
    setSelectedBranch,
    isPanelCollapsed,
    setIsPanelCollapsed,
  };

  return (
    <TestGenerationContext.Provider value={value}>
      {children}
    </TestGenerationContext.Provider>
  );
};
