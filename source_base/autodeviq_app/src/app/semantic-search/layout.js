import { SemanticSearchProvider } from "../context/SemanticSearchContext";

export default function SemanticSearchLayout({ children }) {
  return <SemanticSearchProvider>{children}</SemanticSearchProvider>;
}