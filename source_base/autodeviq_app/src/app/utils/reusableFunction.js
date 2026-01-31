export const extractUrlInfo = (url) => {
  if (!url) return null;

  const normalizedUrl = url
    // Convert SSH form `git@github.com:user/repo.git` to HTTPS
    .replace(/^git@([^:]+):/, "https://$1/")
    // Convert `ssh://git@github.com/user/repo.git` to HTTPS
    .replace(/^ssh:\/\/git@([^/]+)\//, "https://$1/")
    // Remove `.git` at the end if present
    .replace(/\.git$/, "")
    // Remove trailing slash if any
    .replace(/\/+$/, "");

  const match = normalizedUrl.match(
    /^https:\/\/github\.com\/([^/]+)\/([^/]+)$/
  );

  if (match) {
    return {
      owner: match[1],
      repo: match[2],
    };
  }

  return null;
};

export const isValidGitHubUrl = (url) => {
  const regex = /^https:\/\/(www\.)?github\.com\/[\w.-]+\/[\w.-]+\/?$/;
  return regex.test(url.trim());
};

export const getFileAndFolderCountFromTree = (tree = []) => {
  const fileCount = tree.filter((item) => item.type === "blob").length;
  const folderCount = tree.filter((item) => item.type === "tree").length;
  return { fileCount, folderCount };
};

export function formatSizes(bytes, decimals = 2) {
  if (!bytes || bytes === 0) return "0 KB"; // Avoid showing "Bytes"

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["KB", "MB", "GB"];

  // Force minimum index to be 0 (KB)
  const i = Math.max(0, Math.floor(Math.log(bytes) / Math.log(k)) - 1);
  const value = parseFloat((bytes / Math.pow(k, i + 1)).toFixed(dm));

  return `${value} ${sizes[i]}`;
}

export function parseMarkdownWithCodeBlocks(text) {
  const lines = text.replace(/\\n/g, "\n").split("\n");
  let inCodeBlock = false;
  let html = "";

  for (let line of lines) {
    if (line.trim().startsWith("```")) {
      if (!inCodeBlock) {
        html += "<pre><code>";
        inCodeBlock = true;
      } else {
        html += "</code></pre>";
        inCodeBlock = false;
      }
    } else {
      if (inCodeBlock) {
        // Escape HTML characters inside code blocks
        const escapedLine = line
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;");
        html += escapedLine + "\n";
      } else {
        let formattedLine = line
          // Bold: **text**
          .replace(
            /\*\*(.*?)\*\*/g,
            `<h2 class="font-bold text-xl text-gray-800 ">$1</h2>`
          )
          // Inline code: `text`
          .replace(
            /`([^`]+)`/g,
            `<span class="font-mono bg-gray-100 text-gray-800 px-1 py-0.5 rounded border border-gray-300">$1</span>`
          );

        html += formattedLine + "<br/>";
      }
    }
  }

  if (inCodeBlock) {
    html += "</code></pre>";
  }

  return html;
}

export function extractCodeBlocks(markdown) {
  if (!markdown) return "";

  // Match ```language(optional)\n ...code... \n```
  const regex = /```[a-zA-Z]*\n([\s\S]*?)```/g;
  let mergedCode = "";
  let match;

  while ((match = regex.exec(markdown)) !== null) {
    mergedCode += match[1].trim() + "\n\n"; // separate with double newlines
  }

  return mergedCode.trim(); // remove trailing spaces/newlines
}
