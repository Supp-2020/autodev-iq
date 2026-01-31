"use client"
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

export default function MermaidWrapper({ chart }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!chart || !containerRef.current) return;

    const renderChart = async () => {
      try {
        // Initialize mermaid
        mermaid.initialize({ 
          startOnLoad: false,
          theme: 'default'
        });

        // Clear previous content
        containerRef.current.innerHTML = '';

        // Create a unique ID for this diagram
        const id = `mermaid-${Date.now()}`;
        
        // Render the diagram
        const { svg } = await mermaid.render(id, chart);
        containerRef.current.innerHTML = svg;
      } catch (error) {
        console.error('Mermaid rendering error:', error);
        containerRef.current.innerHTML = `<pre>${chart}</pre>`;
      }
    };

    renderChart();
  }, [chart]);

  return <div ref={containerRef} />;
}