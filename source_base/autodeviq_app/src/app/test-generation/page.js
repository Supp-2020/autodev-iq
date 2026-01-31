"use client";
import Footer from "../components/Footer";
import { Navbar } from "../components/Navbar";
import { usePathname } from "next/navigation";
import { useTestGenerationContext } from "../context/TestGenerationContext";
import { Heading } from "../components/Heading";
import { UploadCode } from "../components/UploadCode";
import { PageChangeDropDown } from "../components/PageChangeDropDown";
import { FolderStructure } from "../components/FolderStructure";
import { TestGenerationBody } from "../components/TestGenerationBody";
import { TestGenerationFeature } from "../components/TestGenerationFeature";

export default function TestGeneration() {
  const {
    selectedProject,
    projectId,
    isPanelCollapsed,
    selectedBranch,
    setIsPanelCollapsed,
    setProjectId,
    setSelectedProject,
    setSelectedBranch,
  } = useTestGenerationContext();
  const pathname = usePathname();
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex justify-between mb-6 pt-6 px-6 gap-2 flex-shrink-0">
          <Heading
            heading="Test Generation"
            content="Generate test for new added code"
          />
          <UploadCode
            setProjectId={setProjectId}
            selectedProject={selectedProject}
            setSelectedProject={setSelectedProject}
            setSelectedBranch={setSelectedBranch}
            setIsPanelCollapsed={setIsPanelCollapsed}
          />
          <PageChangeDropDown pathname={pathname} />
        </div>

        {Object.keys(selectedProject)?.length > 0 ? (
          <div className="flex gap-6 flex-1 min-h-0">
            <FolderStructure
              selectedProject={selectedProject}
              selectedBranch={selectedBranch}
              isPanelCollapsed={isPanelCollapsed}
              setIsPanelCollapsed={setIsPanelCollapsed}
            />
            <TestGenerationBody
              projectId={projectId}
              isPanelCollapsed={isPanelCollapsed}
              selectedProject={selectedProject}
              setSelectedBranch={setSelectedBranch}
            />
          </div>
        ) : <TestGenerationFeature />}
      </div>
      <Footer />
    </div>
  );
}
