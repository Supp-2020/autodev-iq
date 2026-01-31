import { TestGenerationProvider } from "../context/TestGenerationContext";

export default function SemanticSearchLayout({ children }) {
  return <TestGenerationProvider>{children}</TestGenerationProvider>;
}