export function buildNestedTree(flatTree = []) {
  const result = [];

  flatTree.forEach((item) => {
    const parts = item.path.split("/");
    let currentLevel = result;

    parts.forEach((part, index) => {
      const isLast = index === parts.length - 1;
      const isFile = item.type === "blob" && isLast;

      if (isFile) {
        // Add file node
        if (!currentLevel.some((node) => node.file === part)) {
          currentLevel.push({
            file: part,
            size: item.size, // Add the file size here
          });
        }
      } else {
        // Look for existing folder node
        let folderNode = currentLevel.find((node) => node.folder === part);
        if (!folderNode) {
          folderNode = {
            folder: part,
            child: [],
            // optional: add defaultOpen flag if you want
            // defaultOpen: part === 'src' ? true : undefined
          };
          currentLevel.push(folderNode);
        }
        currentLevel = folderNode.child;
      }
    });
  });

  return result;
}