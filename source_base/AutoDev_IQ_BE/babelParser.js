// babel_parser.js
const fs = require("fs");
const parser = require("@babel/parser");

if (process.argv.length < 3) {
  console.error("Usage: node babel_parser.js <path-to-jsx-file>");
  process.exit(1);
}

const filePath = process.argv[2];
const code = fs.readFileSync(filePath, "utf8");

try {
  const ast = parser.parse(code, {
    sourceType: "module",
    plugins: [
      "jsx",
      "typescript",
      "classProperties",
      "decorators-legacy",
      "objectRestSpread",
      "optionalChaining"
    ]
  });

  function findJSXTags(node, found = []) {
    if (Array.isArray(node)) {
      node.forEach(n => findJSXTags(n, found));
    } else if (node && typeof node === "object") {
      if (node.type === "JSXElement" && node.openingElement?.name?.name) {
        found.push(node.openingElement.name.name);
      }
      Object.values(node).forEach(value => findJSXTags(value, found));
    }
    return found;
  }

  const jsxTags = [...new Set(findJSXTags(ast))];
  ast.__jsxTags = jsxTags;
  console.log(JSON.stringify(ast)); // full AST with __jsxTags

} catch (err) {
  console.error("Failed to parse file:", err.message);
  process.exit(1);
}
