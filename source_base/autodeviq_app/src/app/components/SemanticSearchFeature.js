import { MdOutlineRemoveRedEye } from "react-icons/md";
import { BiSolidZap } from "react-icons/bi";
import { BsDiagram3 } from "react-icons/bs";
import { CiSearch } from "react-icons/ci";

export const SemanticSearchFeature = () => {
  const features = [
    {
      id: "chat",
      title: "Chat with Your Code",
      subtitle: "Ask anything about your project",
      description:
        "Natural conversations about your entire codebase with full context understanding",
      color: "blue",
      demo: "How does authentication work in this app?",
      appliedColor: {
        bg: "bg-blue-50",
        text: "text-blue-600",
        border: "border-blue-200",
      },
    },
    {
      id: "diagrams",
      title: "Visual Code Flow",
      subtitle: "See your code structure",
      description:
        "Auto-generated Mermaid diagrams showing how your code connects and flows",
      color: "purple",
      demo: "graph TD\nA[Login]  B[Validate]\nB  C[Dashboard]",
      appliedColor: {
        bg: "bg-purple-50",
        text: "text-purple-600",
        border: "border-purple-200",
      },
    },
    {
      id: "search",
      title: "Smart Code Search",
      subtitle: "Find code by meaning",
      description:
        "Semantic search that understands what you're looking for, not just keywords",
      color: "green",
      demo: "password validation logic",
      appliedColor: {
        bg: "bg-green-50",
        text: "text-green-600",
        border: "border-green-200",
      },
    },
  ];
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="bg-white pt-2">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-2">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Chat with Your Codebase
            </h2>
            <p className="text-lg text-gray-600">
              Chat naturally, see visual flows, and search semantically through
              your entire codebase
            </p>
          </div>
          <div className="flex items-center justify-center space-x-4 mb-6">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <MdOutlineRemoveRedEye className="w-4 h-4" />
              <span>Full repo context</span>
            </div>
            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <BiSolidZap className="w-4 h-4" />
              <span>Instant insights</span>
            </div>
            <div className="w-1 h-1 bg-gray-300 rounded-full"></div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <BsDiagram3 className="w-4 h-4" />
              <span>Visual diagrams</span>
            </div>
          </div>
          <div className="grid lg:grid-cols-3 gap-8">
            {features.map((feature) => {
              return (
                <div
                  key={feature.id}
                  className={`relative overflow-hidden border-2 rounded-xl bg-white shadow-lg ${feature.appliedColor.border}`}
                >
                  <div className="p-8">
                    {/* Content */}
                    <div className="space-y-3">
                      <h3
                        className={`text-xl font-semibold mb-1 ${feature.appliedColor.text}`}
                      >
                        {feature.title}
                      </h3>

                      <p className="text-gray-600 leading-relaxed">
                        {feature.description}
                      </p>

                      {/* Demo Preview */}
                      <div
                        className={`mt-6 p-4 rounded-lg  ${feature.appliedColor.bg}`}
                      >
                        {feature.id === "chat" && (
                          <div className="space-y-2">
                            <div className="text-xs text-gray-500 mb-2">
                              Try asking:
                            </div>
                            <div className="bg-white p-3 rounded-lg text-sm border">
                              "{feature.demo}"
                            </div>
                          </div>
                        )}

                        {feature.id === "diagrams" && (
                          <div className="space-y-2">
                            <div className="text-xs text-gray-500 mb-2">
                              Auto-generated:
                            </div>
                            <div className="bg-white p-3 rounded-lg text-xs font-mono border">
                              {feature.demo}
                            </div>
                          </div>
                        )}

                        {feature.id === "search" && (
                          <div className="space-y-2">
                            <div className="text-xs text-gray-500 mb-2">
                              Search example:
                            </div>
                            <div className="flex items-center space-x-2 ">
                              <CiSearch className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-700">
                                {feature.demo}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
