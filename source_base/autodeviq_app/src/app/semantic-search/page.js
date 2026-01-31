"use client";
import { PageChangeDropDown } from "../components/PageChangeDropDown";
import { MainBody } from "../components/Body";
import { FolderStructure } from "../components/FolderStructure";
import { Navbar } from "../components/Navbar";
import Footer from "../components/Footer";
import { UploadCode } from "../components/UploadCode";
import { Heading } from "../components/Heading";
import { usePathname } from "next/navigation";
import { useSemanticSearchContext } from "../context/SemanticSearchContext";
import { SemanticSearchFeature } from "../components/SemanticSearchFeature";

export default function SemanticSearch() {
  const {
    selectedProject,
    projectId,
    isPanelCollapsed,
    selectedBranch,
    setIsPanelCollapsed,
    setProjectId,
    setSelectedProject,
    setSelectedBranch,
  } = useSemanticSearchContext();
  const pathname = usePathname();

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex justify-between mb-6 pt-6 px-6 gap-2 flex-shrink-0">
          <Heading
            heading="Semantic Search"
            content="AI-powered code analysis"
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
            <MainBody
              projectId={projectId}
              isPanelCollapsed={isPanelCollapsed}
            />
          </div>
        ) : <SemanticSearchFeature />}
      </div>
      <Footer />
    </div>
  );
}
