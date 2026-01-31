"use client";
import { useState, useEffect } from "react";
import { FcFolder, FcOpenedFolder } from "react-icons/fc";
import { IoIosArrowDown, IoIosArrowForward } from "react-icons/io";
import { buildNestedTree } from "../utils/buildNestedTree";
import {
  extractUrlInfo,
  formatSizes,
  getFileAndFolderCountFromTree,
} from "../utils/reusableFunction";
import { LuLayers } from "react-icons/lu";
import { Box, CircularProgress } from "@mui/material";
import { FileIcon } from "./FileIcon";
import { MdArrowBackIos, MdArrowForwardIos } from "react-icons/md";

export const FolderStructure = ({
  selectedProject,
  selectedBranch,
  isPanelCollapsed,
  setIsPanelCollapsed,
}) => {
  const urlData = extractUrlInfo(selectedProject?.git_url);

  const [folderStructureData, setFolderStructureData] = useState([]);
  const [count, setCount] = useState({
    fileCount: 0,
    folderCount: 0,
  });
  const [folderLoader, setFolderLoader] = useState(false);

  useEffect(() => {
    const fetchTree = async () => {
      if (!urlData?.owner || !urlData?.repo) return;
      setFolderLoader(true);
      try {
        const res = await fetch(
          `https://api.github.com/repos/${urlData?.owner}/${urlData?.repo}/git/trees/${selectedBranch}?recursive=1`
        );
        const data = await res.json();
        const nestedData = buildNestedTree(data.tree);
        setFolderStructureData(nestedData);
        const { fileCount, folderCount } = getFileAndFolderCountFromTree(
          data.tree
        );
        setCount({
          fileCount: fileCount,
          folderCount: folderCount,
        });
      } catch (error) {
        console.error(error);
      } finally {
        setFolderLoader(false);
      }
    };

    fetchTree();
    // Token expires on Oct 2025, without token its 60 requests per hour per IP address
    // With token its 5000 requests per hour
    // To Generate a token, search PAT tokens for github
  }, [selectedProject, selectedBranch]);

  return (
    <section
      className={`${
        isPanelCollapsed ? "w-[50px]" : "w-[400px]"
      } flex flex-col shadow-md border border-gray-300 transition-all duration-400`}
    >
      <div className="bg-white/90 backdrop-blur-md border-r border-gray-200 flex flex-col flex-1 shadow-xl h-full">
        {/* Header */}
        <div
          className={`${
            isPanelCollapsed ? "pl-2 pr-0 py-4" : "p-4"
          } flex border-b border-gray-100 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex-shrink-0 justify-between items-center`}
        >
          {!isPanelCollapsed && (
            <div>
              <div className="flex gap-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
                  <LuLayers className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Project Explorer
                  </h2>
                  <p className="text-xs text-gray-600">
                    {`${count.fileCount} files • ${count.folderCount} folders`}
                  </p>
                </div>
              </div>
              {selectedBranch && (
                <div className="text-xs mt-2 px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 border border-indigo-200 inline-block max-w-[200px] truncate">
                  {selectedBranch}
                </div>
              )}
            </div>
          )}
          <span
            onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
            className="p-1 pl-2 cursor-pointer rounded-md hover:bg-gray-200 transition-color"
          >
            {isPanelCollapsed ? (
              <MdArrowForwardIos
                className="h-4 w-4"
                label="Close Project Explorer"
              />
            ) : (
              <MdArrowBackIos className="h-4 w-4" />
            )}
          </span>
        </div>

        {/* Scrollable content */}
        {!isPanelCollapsed && (
          <div
            className="p-4 flex-1 overflow-auto "
            style={{
              maxHeight: "640px",
              maxWidth: "380px",
              scrollBehavior: "smooth",
            }}
          >
            {folderLoader ? (
              <Box display="flex" justifyContent="center" py={2}>
                <CircularProgress sx={{ color: "#5c5c5cff" }} />
              </Box>
            ) : (
              folderStructureData?.map((node, idx) => (
                <FolderNode key={idx} node={node} />
              ))
            )}
          </div>
        )}

        {isPanelCollapsed && (
          <div className="p-2 flex flex-col items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center">
              <LuLayers className="h-5 w-5 text-white" />
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

const FolderNode = ({ node }) => {
  const [isOpen, setIsOpen] = useState(node.defaultOpen || false);

  // Folder rendering
  if (node.folder) {
    return (
      <div>
        <div
          className="flex items-center cursor-pointer select-none"
          onClick={() => setIsOpen(!isOpen)}
        >
          <span className="flex items-center">
            {isOpen ? (
              <IoIosArrowDown className="mr-1" />
            ) : (
              <IoIosArrowForward className="mr-1" />
            )}
            {isOpen ? (
              <FcOpenedFolder className="mr-1" />
            ) : (
              <FcFolder className="mr-1" />
            )}
            {node.folder}
          </span>
        </div>
        {isOpen && (
          <div className="ml-2 border-l border-gray-200 pl-2">
            {node.child?.map((childNode, idx) => (
              <FolderNode key={idx} node={childNode} />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File rendering
  if (node.file) {
    return (
      <div className="flex justify-between gap-4">
        <FileIcon filename={node.file} />
        <span className="text-xs text-gray-400">{formatSizes(node.size)}</span>
      </div>
    );
  }

  return null;
};
