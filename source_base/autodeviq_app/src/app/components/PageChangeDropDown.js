"use client";
import { FormControl, MenuItem, Select, InputLabel } from "@mui/material";
import { useState } from "react";
import { useRouter } from "next/navigation";

export const PageChangeDropDown = ({ pathname = "" }) => {
  const router = useRouter();
  const useCases = [
    { label: "Semantic Search", path: "/semantic-search" },
    { label: "Test Generation", path: "/test-generation" },
    { label: "Visual Regression", path: "/visual-regression" },
  ];

  const [selectedPath, setSelectedPath] = useState(pathname);

  const filteredUseCases = useCases.filter((item) => item.path !== pathname);

  const handleChange = (event) => {
    const value = event.target.value;
    setSelectedPath(value);
    router.push(value); // navigate to selected path
  };
  return (
    <div className="flex flex-col">
      <FormControl fullWidth sx={{ width: 250 }}>
        <InputLabel id="project-select">Go to other Features</InputLabel>
        <Select
          labelId="project-select"
          id="project-select"
          label="Go to other Features"
          className="bg-white"
          sx={{ padding: "1px 6px" }}
          onChange={handleChange}
          value={selectedPath}
        >
          {/* Show the current page as selected and disabled */}
          <MenuItem value={pathname} disabled>
            {useCases.find((item) => item.path === pathname)?.label}
          </MenuItem>
          {filteredUseCases?.map((item) => (
            <MenuItem key={item.path} value={item.path}>
              {item.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </div>
  );
};
