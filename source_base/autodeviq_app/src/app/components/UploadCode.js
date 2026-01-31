"use client";
import { useState, useRef } from "react";
import {
  Button,
  Popper,
  ClickAwayListener,
  Paper,
  Box,
  Chip,
  CircularProgress,
} from "@mui/material";
import { FaChevronDown, FaUserCircle } from "react-icons/fa";
import { extractUrlInfo, isValidGitHubUrl } from "../utils/reusableFunction";
import TopAlert from "../reuseables/TopAlert";
import { IoIosGitBranch } from "react-icons/io";

export const UploadCode = ({
  setProjectId,
  selectedProject,
  setSelectedProject,
  setSelectedBranch,
  setIsPanelCollapsed,
  showExtraInfo = false,
}) => {

  const [gitUrl, setGitUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [isSavedProjectData, setIsSavedProjectData] = useState(false);

  const [savedProjectData, setSavedProjectData] = useState([]);
  const [isDropDownOpen, setIsDropDownOpen] = useState(false);
  const inputWrapperRef = useRef(null);
  const [alert, setAlert] = useState({
    open: false,
    typeOfPopup: "",
    message: "",
  });

  const handleAnalyze = async () => {
    if (!gitUrl || !isValidGitHubUrl(gitUrl)) {
      setAlert({
        open: true,
        typeOfPopup: "error",
        message:
          "Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo).",
      });
      return;
    }
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ git_url: gitUrl }),
      });

      const data = await response.json();

      if (data.project_id) {
        setAlert({
          open: true,
          typeOfPopup: "success",
          message: "Project is indexed successfully",
        });
        // Refetch projects, then select the one that matches the new project_id
        const listResponse = await fetch("http://127.0.0.1:8000/projects", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        const listData = await listResponse.json();

        setSavedProjectData(listData);

        // Find and select the newly indexed project
        const foundProject = listData.projects?.find(
          (item) => item.project_id === data.project_id
        );

        if (foundProject) {
          setSelectedProject(foundProject);
          setProjectId(foundProject.project_id);
          setSelectedBranch(foundProject.main_branch);
          setGitUrl("");
        }
      } else {
        setAlert({
          open: true,
          typeOfPopup: "error",
          message: "Project ID Error, Upload Again",
        });
      }
    } catch (err) {
      setAlert({
        open: true,
        typeOfPopup: "error",
        message: "Project did not indexed successfully",
      });
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleProjectList = async () => {
    if (!isDropDownOpen) {
      setIsDropDownOpen(true);
      setGitUrl("");
      if (savedProjectData.length === 0) {
        setIsSavedProjectData(true);
        fetch("http://127.0.0.1:8000/projects", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        })
          .then((res) => res.json())
          .then((data) => setSavedProjectData(data))
          .catch((err) => console.error(err))
          .finally(() => setIsSavedProjectData(false));
      }
    } else {
      setIsDropDownOpen(false);
    }
  };

  return (
    <div>
      <TopAlert
        open={alert.open}
        typeOfPopup={alert.typeOfPopup}
        message={alert.message}
        onClose={() => setAlert({ open: false, typeOfPopup: "", message: "" })}
      />
      <div className="flex justify-center gap-2">
        <div>
          <div
            ref={inputWrapperRef}
            className="relative"
            style={{ width: 700 }}
          >
            {/* Input Field */}
            <input
              type="text"
              placeholder="https://github.com/user/repo"
              value={
                selectedProject && selectedProject.project_id
                  ? selectedProject.project_id
                  : gitUrl
              }
              onChange={(e) => setGitUrl(e.target.value)}
              className={`w-full bg-white border border-gray-300 rounded-sm px-4 py-4 pr-12 ${
                selectedProject && selectedProject.project_id
                  ? "pointer-events-none text-transparent caret-transparent"
                  : ""
              }`}
            />

            {/* Selected Chip Item from dropdown */}
            {Object.keys(selectedProject)?.length > 0 ? (
              <div className="absolute top-1/2 left-4 -translate-y-1/2 pointer-events-auto">
                <Chip
                  label={selectedProject.project_id}
                  onDelete={() => {
                    setSelectedProject({});
                    setProjectId("");
                    setSelectedBranch("");
                    setIsPanelCollapsed(false);
                  }}
                  sx={{
                    backgroundColor: "#E0E7FF",
                    fontWeight: "bold",
                    fontSize: "14px",
                    height: 32,
                  }}
                />
              </div>
            ) : null}

            {/* Dropdown icon in input field */}
            <div className="absolute top-1/2 right-4 -translate-y-1/2 flex items-center">
              <div className="h-5 border-l border-gray-300 mr-4" />
              <button
                onClick={handleProjectList}
                className="text-black-600 clickable focus:outline-none transition-transform duration-700 ease-in-out"
              >
                <div
                  className={`transition-transform duration-300 ease-in-out ${
                    isDropDownOpen ? "rotate-180" : "rotate-0"
                  }`}
                >
                  <FaChevronDown size={20} />
                </div>
              </button>
            </div>

            {/* Dropdown Popper */}
            <Popper
              open={isDropDownOpen}
              anchorEl={inputWrapperRef.current}
              placement="bottom-start"
              style={{
                zIndex: 10,
                width: inputWrapperRef.current?.offsetWidth || 850,
              }}
            >
              <ClickAwayListener onClickAway={() => setIsDropDownOpen(false)}>
                <Paper
                  elevation={3}
                  sx={{
                    maxHeight: 300,
                    overflowY: "auto",
                    borderRadius: 1,
                    padding: 2,
                  }}
                >
                  {isSavedProjectData ? (
                    <Box display="flex" justifyContent="center" py={2}>
                      <CircularProgress sx={{ color: "#5c5c5cff" }} />
                    </Box>
                  ) : (
                    savedProjectData?.projects?.map((item, idx) => (
                      <Box
                        key={idx}
                        onClick={() => {
                          setSelectedProject(item);
                          setProjectId(item.project_id);
                          setSelectedBranch(item.main_branch);
                          setIsDropDownOpen(false);
                        }}
                        className="flex justify-between w-full py-2 hover:bg-gray-100 border-b border-gray-200 transition clickable"
                      >
                        <div className="text-sm text-gray-800 py-1 min-w-0">
                          <div className="font-semibold truncate overflow-hidden text-ellipsis whitespace-nowrap">
                            {item.project_id}
                            <span
                              className={`ml-4 px-2 py-1 rounded  font-medium ${
                                item.project_type === "java"
                                  ? "bg-red-500 text-white text-xs"
                                  : item.project_type === "react"
                                  ? "bg-blue-500 text-white text-xs"
                                  : ""
                              }`}
                            >
                              {item.project_type}
                            </span>
                          </div>
                          <div className="italic text-gray-500 truncate overflow-hidden text-ellipsis whitespace-nowrap">
                            {item.git_url}
                          </div>
                        </div>
                        <div className="text-sm text-gray-800 py-1 flex items-center gap-1">
                          <FaUserCircle size={20} />
                          <span>{extractUrlInfo(item.git_url).owner}</span>
                        </div>
                      </Box>
                    ))
                  )}
                </Paper>
              </ClickAwayListener>
            </Popper>
          </div>
          <h3 className="mt-2 flex items-center gap-1 text-gray-700 text-sm">
            <IoIosGitBranch /> Upload Repository URL
          </h3>
        </div>
        <div>
          <Button
            variant="contained"
            onClick={handleAnalyze}
            disabled={
              loading || (selectedProject && selectedProject.project_id)
            }
            loading={loading}
            loadingPosition="start"
            sx={{
              backgroundColor: "#4F46E2",
              padding: "16px 20px",
              width: "160px",
            }}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </Button>
        </div>
      </div>
      {!selectedProject?.git_url && showExtraInfo &&(
        <div className="flex flex-col items-center justify-center mt-10 px-4">
          <img
            src="/assets/VR.png"
            alt="Visual Regression Illustration"
            className="w-[300px] h-[300px] mb-6 shadow-lg rounded-lg"
          />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            What is Visual Regression Testing?
          </h2>
          <p className="text-center text-gray-600 max-w-2xl">
            Visual Regression Testing helps detect unintended changes in the UI by comparing new screen 
            captures with a previously approved baseline. This allows teams to catch visual bugs early, ensure design consistency, and maintain high-quality user experiences.
          </p>
        </div>
      )}
    </div>
  );
};
