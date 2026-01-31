import Image from "next/image";
import { FaRegCheckCircle } from "react-icons/fa";

export const TestGenerationFeature = () => {
  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="bg-gray-50 pt-4 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">How AI Test Generation Works</h2>
            <p className="text-lg text-gray-600">
              Our intelligent system understands your code and creates meaningful tests
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                  1
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Detect Code Change</h3>
                  <p className="text-gray-600">
                    AI automatically identifies new or modified files in your repository.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                  2
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">
                    Code Analysis & Pattern Recognition
                  </h3>
                  <p className="text-gray-600">
                   AI analyzes your code's logic, functions, and potential edge cases.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                  3
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">
                    Test Generation
                  </h3>
                  <p className="text-gray-600">
                    Creates comprehensive unit, integration, and end-to-end
                    tests with assertions
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                  4
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">
                    Automated Commit
                  </h3>
                  <p className="text-gray-600">
                    The generated test files are seamlessly committed to your repository.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-lg">
              <Image
                src={"/assets/test-generation.png"}
                alt="ai-logo"
                width={600}
                height={600}
              />
              <div className="mt-4 flex justify-center">
                <div className="flex items-center space-x-2 bg-white/80 rounded-full px-3 py-1 border border-green-200 bg-green-300 text-green-600">
                  <FaRegCheckCircle className="w-4 h-4 mr-1" />
                  <span className="text-sm text-green-600 font-medium">
                    AI Generated
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
