import {
  VscJson,
  VscMarkdown,
  VscFileBinary,
  VscFileZip,
  VscTerminalCmd,
} from "react-icons/vsc";
import { AiFillHtml5 } from "react-icons/ai";
import { DiCss3 } from "react-icons/di";
import {
  SiJavascript,
  SiTypescript,
  SiReact,
  SiApachemaven,
  SiGradle,
} from "react-icons/si";
import { MdOutlinePermMedia } from "react-icons/md";
import { FiFileText } from "react-icons/fi";
import { RiFileSettingsLine } from "react-icons/ri";
import { TbFileTypeSql, TbFileTypeXml } from "react-icons/tb";
import { FaJava } from "react-icons/fa";
import { PiDotOutlineFill } from "react-icons/pi";

const extensionToIconMap = {
  js: <SiJavascript className="text-yellow-400" />,
  ts: <SiTypescript className="text-blue-400" />,
  jsx: <SiReact className="text-sky-400" />,
  tsx: <SiReact className="text-blue-300" />,
  html: <AiFillHtml5 className="text-orange-600" />,
  css: <DiCss3 className="text-blue-600" />,
  json: <VscJson className="text-yellow-500" />,
  md: <VscMarkdown className="text-gray-500" />,
  png: <MdOutlinePermMedia className="text-blue-500" />,
  jpg: <MdOutlinePermMedia className="text-blue-500" />,
  jpeg: <MdOutlinePermMedia className="text-blue-500" />,
  txt: <FiFileText className="text-gray-500" />,
  java: <FaJava className="text-red-600" />,
  class: <VscFileBinary className="text-gray-600" />,
  jar: <VscFileZip className="text-purple-600" />,
  sql: <TbFileTypeSql className="text-yellow-400" />,
  gradle: <SiGradle className="text-green-700" />,
  pom: <SiApachemaven className="text-red-700" />,
  xml: <TbFileTypeXml className="text-orange-500" />,
  properties: <RiFileSettingsLine className="text-blue-500" />,
  cmd: <VscTerminalCmd className="text-brown-700" />,
  bat: <VscTerminalCmd className="text-brown-700" />,
};

export const FileIcon = ({ filename }) => {
  const ext = filename?.split(".")?.pop()?.toLowerCase();
  const icon = extensionToIconMap[ext];

  return (
    <div className="flex items-center gap-2 text-gray-800 text-sm">
      {icon || <PiDotOutlineFill className="text-gray-500" />}
      <span>{filename}</span>
    </div>
  );
};
