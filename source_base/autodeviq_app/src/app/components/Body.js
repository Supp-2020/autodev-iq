"use client";
import { useState } from "react";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { Button, TextField } from "@mui/material";
import MermaidWrapper from "./MermaidWrapper";
import Image from "next/image";
import { FaUserCircle } from "react-icons/fa";
import TopAlert from "../reuseables/TopAlert";
import { parseMarkdownWithCodeBlocks } from "../utils/reusableFunction";
import { IoSparklesSharp } from "react-icons/io5";
import { Stop } from "@mui/icons-material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";

export const MainBody = ({ projectId, isPanelCollapsed }) => {
  const [chatMessages, setChatMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [alert, setAlert] = useState({
    open: false,
    typeOfPopup: "",
    message: "",
  });
  let didAbort = false;
  const [abortController, setAbortController] = useState(null);

  const handleGenerate = async (prePrompt) => {
    const finalPrompt = prePrompt?.trim() || inputValue.trim();
    if (!finalPrompt) {
      setError("Please type a question.");
      return;
    }
    if (!projectId) {
      setError("Please upload a project first!");
      return;
    }

    setError("");
    setLoading(true);

    const lowerQuestion = finalPrompt.toLowerCase();
    let promptType = "code_prompt";

    if (
      lowerQuestion.includes("visualize") ||
      lowerQuestion.includes("visualise") ||
      lowerQuestion.includes("flowchart") ||
      lowerQuestion.includes("mermaid")
    ) {
      promptType = "flowchart_prompt";
    }

    const newMessage = {
      question: finalPrompt,
      answer: "",
      promptType,
      flowchart: "",
    };

    setChatMessages((prev) => [...prev, newMessage]);
    setInputValue("");

    const controller = new AbortController();
    setAbortController(controller);

    try {
      const response = await fetch("http://127.0.0.1:8000/askStream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          project_id: projectId,
          question: newMessage.question,
          max_docs: 2,
          prompt_type: promptType,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let partial = "";
      let done = false;

      // For flowchart_prompt, accumulate all tokens before updating UI
      let flowchartBuffer = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;

        if (value) {
          partial += decoder.decode(value, { stream: true });

          const events = partial.split("\n\n");
          partial = events.pop() || "";

          for (const event of events) {
            if (event.startsWith("data: ")) {
              const jsonStr = event.slice(6);
              const parsed = JSON.parse(jsonStr);

              if (parsed.type === "token") {
                const token = parsed.content || "";

                if (promptType === "flowchart_prompt") {
                  // For flowchart: just accumulate in buffer, no UI update
                  flowchartBuffer += token;
                } else {
                  // For code_prompt: stream tokens to UI in real-time
                  setChatMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    updated[updated.length - 1] = {
                      ...last,
                      answer: last.answer + token,
                      hasStartedStreaming: true,
                    };
                    return updated;
                  });
                }
              }

              if (parsed.type === "complete") {
                setChatMessages((prev) => {
                  const updated = [...prev];
                  const lastMessage = updated[updated.length - 1];

                  if (lastMessage.promptType === "flowchart_prompt") {
                    // For flowchart: update UI with complete content
                    updated[updated.length - 1] = {
                      ...lastMessage,
                      flowchart: flowchartBuffer,
                      isComplete: true,
                    };
                  } else {
                    // For code_prompt: just mark as complete
                    updated[updated.length - 1] = {
                      ...lastMessage,
                      isComplete: true,
                    };
                  }

                  return updated;
                });

                done = true;
              }
            }
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        didAbort = true;
      }
      console.error(err);
      if (!didAbort) {
        setAlert({
          open: true,
          typeOfPopup: "error",
          message: "Failed to get response. Please try again!!",
        });
      }
    } finally {
      setLoading(false);
      setAbortController(null);
    }
  };

  return (
    <section className="flex-1 mr-6 flex flex-col min-h-0">
      <TopAlert
        open={alert.open}
        typeOfPopup={alert.typeOfPopup}
        message={alert.message}
        onClose={() => setAlert({ open: false, typeOfPopup: "", message: "" })}
      />
      <div className="shadow-xl border border-gray-300 flex flex-col flex-1 min-h-0 max-h-full">
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex-shrink-0">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
              <Image
                src={"/assets/Ai-Logo.png"}
                alt="ai-logo"
                width={33}
                height={33}
              />
            </div>
            <div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                AutoDev IQ Code Assistant
              </h2>
              <p className="text-sm text-gray-600">
                Intelligent code analysis & insights
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 bg-white/80 rounded-full px-3 py-1 border border-green-200">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600 font-medium">
                AI Online
              </span>
            </div>
          </div>
        </div>
        <div
          className="p-4 flex flex-col flex-1 overflow-y-auto overflow-x-hidden min-h-0"
          style={{
            maxHeight: "500px",
            scrollBehavior: "smooth",
          }}
        >
          {chatMessages?.length ? (
            chatMessages.map((msg, idx) => {
              const isLastAndLoading =
                idx === chatMessages.length - 1 && loading;

              let answerStr = "";
              if (msg.promptType !== "flowchart_prompt") {
                try {
                  const parsed =
                    typeof msg.answer === "string"
                      ? JSON.parse(msg.answer)
                      : msg.answer;

                  const rawAnswer = parsed?.result || String(msg.answer);
                  answerStr = parseMarkdownWithCodeBlocks(rawAnswer);
                } catch {
                  answerStr = parseMarkdownWithCodeBlocks(String(msg.answer));
                }
              }

              return (
                <div key={idx} className="bg-white flex flex-col items-end">
                  <div className="flex items-start space-x-2 max-w-2xl ml-auto mb-4">
                    <div className="bg-gradient-to-r from-blue-500 to-indigo-500 rounded-tr-sm rounded-2xl p-4 text-white shadow-lg">
                      <p className="text-sm leading-relaxed">{msg.question}</p>
                    </div>
                    <div className="w-8 h-8 rounded-full ring-2 ring-blue-200 bg-blue-500 flex items-center justify-center">
                      <FaUserCircle className="text-white w-4 h-4" />
                    </div>
                  </div>
                  <div
                    className={`${
                      isPanelCollapsed ? "max-w-7xl" : "max-w-3xl"
                    } flex items-start space-x-2 mr-auto`}
                  >
                    <div className=" w-8 h-8 flex-shrink-0 rounded-full ring-2 ring-blue-200 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
                      <Image
                        src={"/assets/Ai-Logo.png"}
                        alt="ai-logo"
                        width={20}
                        height={20}
                      />
                    </div>

                    {msg.promptType === "flowchart_prompt" ? (
                      <div className="p-4 mb-4">
                        {msg.isComplete ? (
                          <MermaidWrapper chart={msg.flowchart} />
                        ) : (
                          <div className="bg-white rounded-2xl rounded-tl-sm p-4 border border-gray-300">
                            {isLastAndLoading
                              ? "Generating flowchart..."
                              : "Flowchart ready"}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div
                        className="bg-white rounded-2xl rounded-tl-sm p-4 border border-gray-300 mb-4"
                        dangerouslySetInnerHTML={{
                          __html:
                            !msg.hasStartedStreaming && isLastAndLoading
                              ? "Thinking..."
                              : answerStr,
                        }}
                      ></div>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="text-center mx-auto">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <IoSparklesSharp className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Welcome to AI Code Analysis
              </h3>
              <p className="text-gray-600 max-w-md mx-auto">
                I can help you understand your code, find issues, suggest
                improvements, and answer any questions about your project.
              </p>
            </div>
          )}
        </div>

        <div className="bg-white p-4 rounded-3xl rounded-bl-none rounded-br-none shadow-md flex flex-col border border-gray-300 flex-shrink-0">
          <div className="flex gap-2">
            <TextField
              fullWidth
              label="Ask a question"
              name="ask-inputField"
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) {
                  e.preventDefault();
                  handleGenerate();
                }
              }}
            />
            <Button
              onClick={
                loading
                  ? () => abortController?.abort()
                  : () => handleGenerate()
              }
              loadingPosition="start"
              variant="contained"
              sx={{
                padding: "14px 18px",
                width: 54,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#000",
              }}
              color={loading ? "error" : "success"}
            >
              {loading ? <Stop /> : <ArrowUpwardIcon />}
            </Button>
          </div>
          {error && <p className="text-red-500">{error}</p>}
          <div className="flex justify-between">
            <SuggestedQuestions
              onQuestionClick={(question) => {
                setInputValue(question);
                handleGenerate(question);
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
};
