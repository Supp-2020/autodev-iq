'use client';

import { useRouter } from 'next/navigation';
import { FaBrain, FaSearch, FaVial, FaCodeBranch } from 'react-icons/fa';

export default function AboutPage() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-white text-white px-6 py-12 flex items-center justify-center">
      <div className="max-w-3xl w-full bg-blue-500 rounded-2xl shadow-xl p-8 border bg-blue-700">
        <h1 className="text-3xl font-bold mb-6 text-center">🚀 About AutoDev</h1>
        
        <p className="mb-4 text-lg leading-relaxed">
          <strong>AutoDev</strong> is your intelligent companion for code understanding, testing, and visual validation.
          It’s designed to simplify a developer’s life, all while keeping your data <span className="text-green-400 font-semibold">secure</span> and local.
        </p>

        <div className="space-y-4 mb-6">
          <div className="flex items-start space-x-3">
            <FaSearch className="mt-1 text-blue-400" />
            <p><strong>Semantic Search:</strong> Paste your codebase link and ask questions. You’ll get insightful answers <em>and</em> mermaid diagrams!</p>
          </div>
          <div className="flex items-start space-x-3">
            <FaCodeBranch className="mt-1 text-pink-400" />
            <p><strong>Test Case Generation:</strong> Auto-generate test cases using the power of AI to save time and ensure coverage.</p>
          </div>
          <div className="flex items-start space-x-3">
            <FaVial className="mt-1 text-yellow-400" />
            <p><strong>Visual Regression:</strong> Detect unexpected UI changes with built-in visual regression testing.</p>
          </div>
        </div>

        <p className="text-center text-green-400 font-bold">
          🧠 One tool, multiple solutions – built for developers, by developers.
        </p>
        <div className="flex justify-center">
          <button
            onClick={() => router.push('/')}
            className="bg-white text-black font-semibold px-6 py-2 rounded-lg shadow hover:bg-gray-200 transition duration-200 mt-4"
          >
            Go to Home
          </button>
        </div>
      </div>
    </div>
  );
}
