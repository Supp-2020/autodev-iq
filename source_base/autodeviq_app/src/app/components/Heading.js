
export const Heading = ({ heading = "", content = "" }) => {
  return (
    <div>
      <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-500 to-blue-800 bg-clip-text text-transparent mb-1">
        {heading}
      </h1>
      <div className="flex items-center gap-2">
        <p className="text-gray-600 text-sm">{content}</p>
      </div>
    </div>
  );
};
