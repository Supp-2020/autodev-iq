import { VisualRegressionProvider } from "../context/VisualRegressionContext";

export default function VisualRegressionLayout({ children }) {
  return <VisualRegressionProvider>{children}</VisualRegressionProvider>;
}