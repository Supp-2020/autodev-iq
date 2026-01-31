import { useEffect, useState } from "react";
import { RxCross2 } from "react-icons/rx";
import { useSemanticSearchContext } from "../context/SemanticSearchContext";
export const SuggestedQuestions = ({onQuestionClick}) => {
  const { projectId } = useSemanticSearchContext();
  const [questions, setQuestions] = useState([]);
  useEffect(() => {
    if (!projectId) return;

    const fetchQuestions = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/frequent-questions/${projectId}`);
        const data = await response.json();

        setQuestions(data?.frequent_questions?.slice(0, 3)); 
      } catch (error) {
        console.error("Failed to fetch suggested questions:", error);
      }
    };

    fetchQuestions();
  }, [projectId]);

  return (
    <div className="flex space-x-3 mt-2">
      {questions?.map((item, idx) => (
        <div
          key={idx}
          className="flex items-center justify-between p-2 rounded-lg border border-gray-200 shadow-sm cursor-pointer"
          onClick={() => onQuestionClick(item.question)}
        >
          <span className="text-gray-800 font-medium">{item.question}</span>
          <RxCross2 className="ml-1" />
        </div>
      ))}
    </div>
  );
};
