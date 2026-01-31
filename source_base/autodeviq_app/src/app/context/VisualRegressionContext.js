"use client";
import { createContext, useContext, useState, useEffect } from "react";

const VisualRegressionContext = createContext();

export const useVisualRegressionContext = () => {
  const context = useContext(VisualRegressionContext);
  if (!context) {
    console.error(
      "useVisualRegressionContext must be used within AutoDevProvider"
    );
    throw new Error(
      "useVisualRegressionContext must be used within AutoDevProvider"
    );
  }
  return context;
};

export const VisualRegressionProvider = ({ children }) => {
  // Load saved state on first render
  const saved =
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("visual_regression_autoDev") || "{}")
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
      "visual_regression_autoDev",
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
    <VisualRegressionContext.Provider value={value}>
      {children}
    </VisualRegressionContext.Provider>
  );
};
