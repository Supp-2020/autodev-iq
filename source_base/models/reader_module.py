import os
import time
import javalang
import subprocess
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
import hashlib
import pickle
import sys
import argparse

class OptimizedCodeReader:
    def __init__(self, cache_dir: str = "./cache", project_name: str = "default"):
        self.project_name = project_name
        self.cache_dir = os.path.join(cache_dir, project_name)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_file_hash(self, filepath: str) -> str:
        """Get file hash for caching"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _load_cache(self, cache_key: str):
        """Load from cache if exists"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def _save_cache(self, cache_key: str, data):
        """Save to cache"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

    def clone_repository(self, git_url: str, target_dir: str = None) -> str:
        """Clone Git repository to temporary directory"""
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="code_reader_")
        
        try:
            print(f"🔄 Cloning repository: {git_url}")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', git_url, target_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            print(f"✅ Repository cloned to: {target_dir}")
            return target_dir
            
        except subprocess.TimeoutExpired:
            raise Exception("Git clone timed out (5 minutes)")
        except FileNotFoundError:
            raise Exception("Git not found. Please install Git first.")
        except Exception as e:
            if target_dir and os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            raise e

    def parse_java_file(self, file_path: str, content: str) -> List[Dict]:
        """Optimized Java parsing - extract only essential info"""
        file_hash = hashlib.md5(content.encode()).hexdigest()
        cached = self._load_cache(f"java_{file_hash}")
        if cached:
            return cached
            
        try:
            tree = javalang.parse.parse(content)
            methods = []
            lines = content.split('\n')
            
            for _, node in tree.filter(javalang.tree.MethodDeclaration):
                # Get method signature only
                method_name = node.name
                return_type = node.return_type.name if node.return_type else "void"
                params = [param.type.name for param in node.parameters]
                
                # Extract minimal method body (first 5 lines)
                start_line = max(0, (node.position.line - 1) if node.position else 0)
                body_lines = lines[start_line:start_line + 5]
                
                # Simple call extraction
                calls = []
                for _, call in node.filter(javalang.tree.MethodInvocation):
                    calls.append(call.member)
                
                methods.append({
                    "name": method_name,
                    "signature": f"{return_type} {method_name}({', '.join(params)})",
                    "body": '\n'.join(body_lines),
                    "calls": calls[:5],  # Limit calls
                    "file": os.path.basename(file_path)
                })
            
            self._save_cache(f"java_{file_hash}", methods)
            return methods
        except Exception as e:
            print(f"Parse error {file_path}: {str(e)[:50]}")
            return []

    def load_files_parallel(self, directory: str, max_workers: int = 4) -> List[Tuple[str, str]]:
        """Load files in parallel"""
        java_files = []
        for root, _, files in os.walk(directory):
            # Skip common build/dependency directories
            skip_dirs = ['target', 'node_modules', '.git', 'build', 'dist', '.gradle']
            if any(skip_dir in root for skip_dir in skip_dirs):
                continue
            for file in files:
                if file.endswith('.java'):
                    java_files.append(os.path.join(root, file))
        
        print(f"Found {len(java_files)} Java files")
        
        def load_file(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return filepath, f.read()
            except:
                return filepath, ""
        
        files_content = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(load_file, f): f for f in java_files}
            for future in as_completed(future_to_file):
                filepath, content = future.result()
                if content:
                    files_content.append((filepath, content))
        
        return files_content

    def process_files_parallel(self, files_content: List[Tuple[str, str]], max_workers: int = 4) -> List[Dict]:
        """Process files in parallel"""
        def process_file(file_data):
            filepath, content = file_data
            methods = self.parse_java_file(filepath, content)
            return {"file": filepath, "methods": methods} if methods else None
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_file, fd) for fd in files_content]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)
        
        return results

    def create_optimized_documents(self, processed_files: List[Dict]) -> List[Document]:
        """Create lean documents for embedding"""
        documents = []
        for file_data in processed_files:
            for method in file_data["methods"]:
                # Compact representation
                content = (
                    f"File: {method['file']}\n"
                    f"Method: {method['signature']}\n"
                    f"Calls: {', '.join(method['calls'][:3])}\n"  # Limit calls
                    f"Code:\n{method['body'][:300]}"  # Limit body
                )
                
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "source": method['file'],
                        "method": method['name'],
                        "signature": method['signature']
                    }
                ))
        
        return documents
    
def delete_folder(path):
    """Alternative folder deletion that handles Windows quirks"""
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            try:
                os.chmod(filename, stat.S_IWRITE)
                os.unlink(filename)
            except Exception as e:
                print(f"Could not delete {filename}: {e}")
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)


def main():
    parser = argparse.ArgumentParser(description='Java Code Reader with Git support')
    parser.add_argument('source', help='Local directory path or git URL')
    parser.add_argument('--project', '-p', default='default', help='Project name for organization')
    parser.add_argument('--workers', '-w', type=int, default=4, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    start_time = time.time()
    source_dir = None
    temp_dir = None
    
    try:
        reader = OptimizedCodeReader(project_name=args.project)
        
        # Determine if source is Git URL or local directory
        if args.source.startswith(('http://', 'https://', 'git@')):
            print("🌐 Git repository detected")
            temp_dir = reader.clone_repository(args.source)
            source_dir = temp_dir
        else:
            if not os.path.exists(args.source):
                print(f"❌ Directory not found: {args.source}")
                return
            source_dir = args.source
            print(f"📁 Local directory: {source_dir}")
        
        print("🔄 Loading files...")
        files_content = reader.load_files_parallel(source_dir, args.workers)
        print(f"✅ Loaded {len(files_content)} files in {time.time() - start_time:.2f}s")
        
        if not files_content:
            print("❌ No Java files found!")
            return
        
        print("🔄 Processing files...")
        processed_files = reader.process_files_parallel(files_content, args.workers)
        total_methods = sum(len(f["methods"]) for f in processed_files)
        print(f"✅ Processed {total_methods} methods in {time.time() - start_time:.2f}s")
        
        print("🔄 Creating embeddings...")
        documents = reader.create_optimized_documents(processed_files)
        
        # Optimized chunking
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks
            chunk_overlap=50,
            separators=["\n\n", "\n", " "]
        )
        chunks = splitter.split_documents(documents)
        
        # Create project-specific vector store
        persist_dir = f"./chroma-{args.project}"
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=OllamaEmbeddings(model="codellama"),
            persist_directory=persist_dir
        )
        
        print(f"🎉 Completed in {time.time() - start_time:.2f}s")
        print(f"📊 {len(chunks)} chunks stored in {persist_dir}")
        print(f"🚀 Ready for QA! Use: python qa.py --project {args.project}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Cleanup temporary directory
        # if temp_dir and os.path.exists(temp_dir):
        #     shutil.rmtree(temp_dir)
        #     print(f"🧹 Cleaned up temporary directory")
        delete_folder(temp_dir)

if __name__ == "__main__":
    main()