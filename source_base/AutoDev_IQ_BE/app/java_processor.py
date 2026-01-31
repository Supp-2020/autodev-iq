import os
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import javalang
import networkx as nx
import matplotlib.pyplot as plt

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from config import config


class JavaProjectProcessor:
    def __init__(self, project_id: str, persist_base_dir: str = config.CHROMA_DIR):
        self.project_id = project_id
        self.persist_dir = os.path.join(persist_base_dir, project_id, "chroma")
        self.graph_image_path = os.path.join(persist_base_dir, project_id, "call_graph.png")
        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=OllamaEmbeddings(model=config.MODEL_NAME, base_url=config.OLLAMA_BASE_URL)
        )
        self.existing_hashes = self._load_existing_hashes()

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_existing_hashes(self) -> set:
        try:
            return {meta["hash"] for meta in self.vectorstore.get()["metadatas"] if "hash" in meta}
        except Exception:
            return set()

    def parse_java_methods(self, file_path: str, file_content: str) -> List[Dict]:
        try:
            tree = javalang.parse.parse(file_content)
            lines = file_content.splitlines()
            methods = []

            for _, node in tree.filter(javalang.tree.MethodDeclaration):
                if not node.position:
                    continue

                method_name = node.name
                return_type = node.return_type.name if node.return_type else "void"
                params = "(" + ", ".join([f"{param.type.name} {param.name}" for param in node.parameters]) + ")"
                start_line = node.position.line

                end_line = start_line
                for _, child in node:
                    if hasattr(child, "position") and child.position:
                        end_line = max(end_line, child.position.line)

                calls = set()
                for _, method_invocation in node.filter(javalang.tree.MethodInvocation):
                    call_name = method_invocation.member
                    if method_invocation.qualifier:
                        call_name = f"{method_invocation.qualifier}.{call_name}"
                    calls.add(call_name)

                body_text = "\n".join(lines[start_line - 1:end_line])
                method_hash = self._hash_text(body_text)

                methods.append({
                    "file": file_path,
                    "name": method_name,
                    "signature": f"{return_type} {method_name}{params}",
                    "start_line": start_line,
                    "end_line": end_line,
                    "body": body_text,
                    "calls": list(calls),
                    "hash": method_hash
                })

            return methods
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return []

    def build_call_graph(self, enhanced_docs: List[Dict]) -> nx.DiGraph:
        call_graph = nx.DiGraph()
        method_index = {}

        for doc in enhanced_docs:
            for method in doc["methods"]:
                full_name = f"{os.path.basename(doc['file'])}::{method['signature']}"
                method_index[full_name] = method
                call_graph.add_node(full_name)

        for doc in enhanced_docs:
            for method in doc["methods"]:
                caller = f"{os.path.basename(doc['file'])}::{method['signature']}"
                for callee_name in method["calls"]:
                    for method_id in method_index:
                        if callee_name in method_id:
                            call_graph.add_edge(caller, method_id)

        return call_graph

    def save_call_graph_image(self, graph: nx.DiGraph):
        plt.figure(figsize=(14, 12))
        pos = nx.spring_layout(graph, k=0.5)
        nx.draw(
            graph,
            pos,
            with_labels=True,
            node_color="lightblue",
            edge_color="gray",
            node_size=800,
            font_size=8,
            arrows=True
        )
        plt.title("Java Method Call Graph")
        plt.axis("off")
        os.makedirs(os.path.dirname(self.graph_image_path), exist_ok=True)
        plt.savefig(self.graph_image_path, bbox_inches="tight", dpi=300)
        plt.close()
        print(f"📷 Saved call graph image to {self.graph_image_path}")

    def prepare_documents(self, enhanced_docs: List[Dict]) -> List[Document]:
        documents = []
        for doc in enhanced_docs:
            file_name = os.path.basename(doc["file"])
            for method in doc["methods"]:
                if method["hash"] in self.existing_hashes:
                    continue  # 🚫 Skip duplicate
                calls_str = "; ".join(method['calls']) if method['calls'] else "None"
                documents.append(Document(
                    page_content=(
                        f"Method: {method['signature']}\n"
                        f"File: {file_name}\n"
                        f"Calls: {calls_str}\n"
                        f"Code:\n{method['body']}"
                    ),
                    metadata={
                        "source": file_name,
                        "method": method['name'],
                        "signature": method['signature'],
                        "num_calls": len(method['calls']),
                        "hash": method["hash"]
                    }
                ))
        return documents

    def process(self, java_file_paths: List[str]):
        print("🧠 Parsing Java files in parallel...")
        enhanced_docs = []

        def parse_worker(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"file": file_path, "methods": self.parse_java_methods(file_path, content)}

        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
            futures = [executor.submit(parse_worker, f) for f in java_file_paths]
            for future in as_completed(futures):
                result = future.result()
                if result["methods"]:
                    enhanced_docs.append(result)

        call_graph = self.build_call_graph(enhanced_docs)
        print(f"✅ Built call graph with {len(call_graph.nodes)} methods")
        self.save_call_graph_image(call_graph)

        documents = self.prepare_documents(enhanced_docs)
        if not documents:
            print("✅ No new methods to embed.")
            return

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(documents)

        self.vectorstore.add_documents(chunks)
        print(f"🚀 Embedded {len(chunks)} new code chunks into Chroma DB")

    def process_full_file(self, file_path: str, content: str):
        print(f"\n📥 Processing full file: {file_path}")
        file_name = os.path.basename(file_path)
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

        self.vectorstore.add_documents(chunks)
        print(f"🚀 Embedded and stored: {file_path}")
