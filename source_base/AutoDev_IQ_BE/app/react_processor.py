import os
import subprocess
import json
import time
import hashlib
import shutil
import networkx as nx
import matplotlib.pyplot as plt
from shutil import which
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from config import config

class ReactProjectProcessor:
    def __init__(self, project_id: str, babel_script_path: str, persist_base_dir: str = config.CHROMA_DIR):
        self.project_id = project_id
        self.babel_script_path = babel_script_path
        self.persist_dir = os.path.join(persist_base_dir, project_id, "chroma")
        self.graph_image_path = os.path.join(persist_base_dir, project_id, "component_graph.png")
        self.node_path = which("node") or "C:\\nvm4w\\nodejs\\node.exe"

    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def parse_with_babel(self, file_path):
        result = subprocess.run([
            self.node_path, self.babel_script_path, file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"❌ Babel error in {file_path}:\n{result.stderr.strip()}")
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"❌ JSON parse error in {file_path}")
            return None

    def extract_components(self, ast, file_content):
        results = []
        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "FunctionDeclaration" and node.get("id"):
                    name = node["id"]["name"]
                    body = file_content[node["start"]:node["end"]]
                    results.append({"name": name, "type": "function", "body": body})
                elif node.get("type") == "VariableDeclaration":
                    for decl in node.get("declarations", []):
                        init = decl.get("init", {})
                        if init.get("type") == "ArrowFunctionExpression":
                            name = decl["id"]["name"]
                            body = file_content[decl["start"]:decl["end"]]
                            results.append({"name": name, "type": "arrow_function", "body": body})
                elif node.get("type") == "ClassDeclaration" and node.get("id"):
                    name = node["id"]["name"]
                    body = file_content[node["start"]:node["end"]]
                    results.append({"name": name, "type": "class_component", "body": body})
                for child in node.values():
                    walk(child)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(ast)
        return results

    def parallel_embed_documents(self, docs):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

        def embed_chunks(doc):
            return splitter.split_documents([doc])

        chunks = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = [executor.submit(embed_chunks, doc) for doc in docs]
            for future in as_completed(futures):
                chunks.extend(future.result())

        if not chunks:
            self.log("⚠️ No chunks to embed.")
            return

        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model=config.MODEL_NAME, base_url=config.OLLAMA_BASE_URL),
            persist_directory=self.persist_dir,
            collection_metadata={"source_type": "react"}
        )
        vectordb.persist()
        self.log("🎉 Parallel embedding complete and persisted to disk")

    def parallel_parse_files(self, file_paths):
        results = {}
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = {executor.submit(self._parse_file, path): path for path in file_paths}
            for future in as_completed(futures):
                path = futures[future]
                try:
                    results[path] = future.result()
                except Exception as e:
                    self.log(f"❌ Error parsing {path}: {e}")
        return results

    def _parse_file(self, path):
        with open(path, "r", encoding="utf8") as fp:
            code = fp.read()
        ast = self.parse_with_babel(path)
        return {"code": code, "ast": ast}

    def build_documents(self, react_files):
        docs = []
        component_defs = {}
        jsx_usages = {}
        existing_hashes = set()
        try:
            db = Chroma(persist_directory=self.persist_dir, embedding_function=OllamaEmbeddings(model=config.MODEL_NAME))
            all_docs = db.get()
            existing_hashes = {m.get("hash") for m in all_docs["metadatas"] if "hash" in m}
        except Exception:
            self.log("⚠️ Could not load existing DB or metadata; starting fresh")

        parsed_files = self.parallel_parse_files(react_files)
        for path, parsed in parsed_files.items():
            code = parsed["code"]
            ast = parsed["ast"]
            if not ast:
                self.log(f"⚠️ Skipping {path} due to parse failure")
                continue
            jsx_usages[path] = ast.get("__jsxTags", [])
            components = self.extract_components(ast, code)
            self.log(f"📄 {os.path.basename(path)}: {len(components)} component(s) extracted")
            for comp in components:
                comp_name = comp["name"]
                component_defs[comp_name] = path
                body_hash = hashlib.md5(comp["body"].encode("utf-8")).hexdigest()
                if body_hash in existing_hashes:
                    self.log(f"⏩ Skipping unchanged component: {comp_name}")
                    continue
                doc = Document(
                    page_content=f"Component: {comp_name}\nFile: {os.path.basename(path)}\nCode:\n{comp['body']}",
                    metadata={
                        "source": path,
                        "component": comp_name,
                        "type": comp["type"],
                        "hash": body_hash
                    }
                )
                docs.append(doc)
        return docs, component_defs, jsx_usages

    def build_component_call_graph(self, component_defs, jsx_usages):
        graph = nx.DiGraph()
        for caller_file, used_tags in jsx_usages.items():
            caller_name = os.path.basename(caller_file)
            for tag in used_tags:
                callee_file = component_defs.get(tag)
                if callee_file:
                    callee_name = os.path.basename(callee_file)
                    graph.add_edge(caller_name, callee_name)
        return graph

    def save_component_graph_image(self, graph):
        if graph.number_of_nodes() == 0:
            self.log("⚠️ No components in graph to visualize.")
            return
        plt.figure(figsize=(14, 10))
        pos = nx.spring_layout(graph, k=0.5)
        nx.draw(
            graph, pos, with_labels=True, node_color="lightgreen",
            edge_color="gray", node_size=1000, font_size=9
        )
        plt.title("React Component Call Graph (via JSX tags)")
        plt.axis("off")
        os.makedirs(os.path.dirname(self.graph_image_path), exist_ok=True)
        plt.savefig(self.graph_image_path, bbox_inches="tight", dpi=300)
        self.log(f"📈 Component graph saved to {self.graph_image_path}")

    def process(self, react_project_path: str):
        self.log("📂 Loading React source files (.js/.jsx/.ts/.tsx)...")
        react_files = [
            os.path.join(dp, f)
            for dp, _, fs in os.walk(react_project_path)
            for f in fs if f.endswith((".js", ".jsx", ".ts", ".tsx"))
        ]
        self.log(f"🔍 Found {len(react_files)} files")
        self.log("🧠 Parsing & extracting components and JSX tags...")
        docs, component_defs, jsx_usages = self.build_documents(react_files)
        self.log(f"✅ Extracted {len(docs)} components")
        self.log("📊 Building JSX-based component graph...")
        graph = self.build_component_call_graph(component_defs, jsx_usages)
        self.save_component_graph_image(graph)
        self.log(f"📦 Embedding {len(docs)} components into vector store...")
        self.parallel_embed_documents(docs)

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_existing_hashes(self) -> set:
        try:
            db = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=OllamaEmbeddings(model=config.MODEL_NAME, base_url=config.OLLAMA_BASE_URL)
            )
            return {meta.get("hash") for meta in db.get()["metadatas"] if "hash" in meta}
        except Exception:
            return set()

    def process_full_file(self, file_path: str, content: str):
        print(f"\n📥 Processing full file: {file_path}")
        file_name = os.path.basename(file_path)

        # Ensure existing_hashes is loaded
        if not hasattr(self, "existing_hashes"):
            self.existing_hashes = self._load_existing_hashes()

        file_hash = self._hash_text(content)

        if file_hash in self.existing_hashes:
            print(f"⏭️ Skipping {file_name}, already embedded.")
            return

        document = Document(
            page_content=content,
            metadata={"source": file_name, "hash": file_hash}
        )

        splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=10)
        chunks = splitter.split_documents([document])
        print(f"🪓 Split into {len(chunks)} chunk(s)")

        vectordb = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=OllamaEmbeddings(model=config.MODEL_NAME, base_url=config.OLLAMA_BASE_URL)
        )
        vectordb.add_documents(chunks)
        print(f"🚀 Embedded and stored: {file_path}")

