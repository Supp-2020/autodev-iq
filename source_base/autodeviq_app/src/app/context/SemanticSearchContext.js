"use client";
import { createContext, useContext, useState, useEffect } from "react";

const SemanticSearchContext = createContext();

export const useSemanticSearchContext = () => {
  const context = useContext(SemanticSearchContext);
  if (!context) {
    console.error(
      "useSemanticSearchContext must be used within AutoDevProvider"
    );
    throw new Error(
      "useSemanticSearchContext must be used within AutoDevProvider"
    );
  }
  return context;
};

export const SemanticSearchProvider = ({ children }) => {
  // Load saved state on first render
  const saved =
    typeof window !== "undefined"
      ? JSON.parse(sessionStorage.getItem("semantic_autoDev") || "{}")
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
      "semantic_autoDev",
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
    <SemanticSearchContext.Provider value={value}>
      {children}
    </SemanticSearchContext.Provider>
  );
};
