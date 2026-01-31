from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
import os
import time
import glob
import argparse
from typing import Dict, List, Optional
import subprocess
import json

class FastCodeQA:
    def __init__(self, project_name: str = "default", default_model: str = "llama3"):
        """Initialize with project-specific vector store"""
        self.project_name = project_name
        persist_dir = f"./chroma-{project_name}"
        
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(f"Vector store not found: {persist_dir}")
        
        self.vectordb = Chroma(
            persist_directory=persist_dir,
            embedding_function=OllamaEmbeddings(model="codellama")
        )
        
        self.current_model = default_model
        self.available_models = self._get_available_models()
        self.model_configs = {
            "llama3": {"temperature": 0.3, "num_ctx": 2048, "num_predict": 512},
            "codellama": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 1024},
            "deepseek-coder": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 1024},
            "qwen2.5-coder": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 1024},
            "codegemma": {"temperature": 0.1, "num_ctx": 2048, "num_predict": 512}
        }
        
        self.llm = self._create_llm(self.current_model)
        self.memory = ConversationBufferWindowMemory(k=3, return_messages=True)
        self.qa_chains = {}  # Cache chains per model
        self.cached_responses = {}  # Model-specific caching

    def _get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                return models
        except Exception as e:
            print(f"⚠️ Could not fetch models: {e}")
        
        # Fallback to common models
        return ["llama3", "codellama", "deepseek-coder", "qwen2.5-coder"]

    def _create_llm(self, model_name: str) -> OllamaLLM:
        """Create LLM with model-specific configuration"""
        config = self.model_configs.get(model_name, self.model_configs["llama3"])
        return OllamaLLM(model=model_name, **config)

    def _get_model_prompt(self, model_name: str) -> PromptTemplate:
        """Get model-specific prompt template"""
        if "coder" in model_name.lower() or model_name == "codellama":
            template = """As an expert code analyst, provide detailed technical answers about this codebase.

Context:
{context}

Question: {question}

Provide a comprehensive answer covering:
1. Technical implementation details
2. Code structure and patterns
3. Dependencies and relationships
4. Potential improvements or issues

Be thorough but concise."""
        else:
            template = """You're a senior Java developer. Answer concisely based on this codebase.

Context:
{context}

Question: {question}

Provide a direct, technical answer focusing on:
1. What the code does
2. Key methods/classes involved
3. Main flow if applicable

Keep response under 200 words."""
        
        return PromptTemplate(template=template, input_variables=["context", "question"])

    def _create_qa_chain(self, model_name: Optional[str] = None):
        """Create QA chain for specific model"""
        if model_name is None:
            model_name = self.current_model
            
        if model_name in self.qa_chains:
            return self.qa_chains[model_name]
        
        llm = self._create_llm(model_name)
        prompt = self._get_model_prompt(model_name)
        
        # Model-specific retrieval settings
        if "coder" in model_name.lower() or model_name == "codellama":
          search_kwargs = {"k": 12}  # More context for coding models
        else:
          search_kwargs = {"k": 8}    # Less for general models
        
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectordb.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        self.qa_chains[model_name] = chain
        return chain

    def switch_model(self, model_name: str) -> bool:
        """Switch to different model"""
        if model_name not in self.available_models:
            print(f"❌ Model '{model_name}' not available.")
            print(f"Available models: {', '.join(self.available_models)}")
            return False
        
        self.current_model = model_name
        print(f"✅ Switched to model: {model_name}")
        return True

    def list_models(self) -> List[str]:
        """List available models with current indicator"""
        models_info = []
        for model in self.available_models:
            indicator = " (current)" if model == self.current_model else ""
            models_info.append(f"{model}{indicator}")
        return models_info

    def _get_cache_key(self, question: str, model: str) -> str:
        """Cache key with model name"""
        return f"{model}:{question.lower().strip()[:50]}"

    def ask_fast(self, question: str, model: Optional[str] = None) -> Dict:
        """Fast question answering with model selection"""
        target_model = model or self.current_model
        cache_key = self._get_cache_key(question, target_model)
        
        # Check cache first
        if cache_key in self.cached_responses:
            cached = self.cached_responses[cache_key]
            cached['from_cache'] = True
            cached['model_used'] = target_model
            return cached
        
        start_time = time.time()
        
        try:
            # Switch model if needed
            if model and model != self.current_model:
                if not self.switch_model(model):
                    target_model = self.current_model
            
            qa_chain = self._create_qa_chain(target_model)
            result = qa_chain.invoke({"query": question})
            
            # Extract file references
            sources = set()
            for doc in result.get('source_documents', []):
                sources.add(doc.metadata.get('source', 'Unknown'))
            
            response = {
                'answer': result['result'],
                'sources': list(sources)[:5],
                'response_time': time.time() - start_time,
                'model_used': target_model,
                'from_cache': False
            }
            
            # Cache the response
            self.cached_responses[cache_key] = response
            
            return response
            
        except Exception as e:
            return {
                'answer': f"Error: {str(e)}",
                'sources': [],
                'response_time': time.time() - start_time,
                'model_used': target_model,
                'from_cache': False
            }

    def search_methods(self, query: str, limit: int = 10) -> List[Dict]:
        """Direct method search without LLM"""
        docs = self.vectordb.similarity_search(query, k=limit)
        
        methods = []
        for doc in docs:
            methods.append({
                'file': doc.metadata.get('source', 'Unknown'),
                'method': doc.metadata.get('method', 'Unknown'),
                'signature': doc.metadata.get('signature', 'Unknown'),
                'preview': doc.page_content[:150] + "..."
            })
        
        return methods

    def get_project_overview(self) -> Dict:
        """Quick project overview"""
        # Sample the vector store
        all_docs = self.vectordb.get()
        
        files = set()
        methods_count = 0
        
        if 'metadatas' in all_docs:
            for metadata in all_docs['metadatas']:
                if isinstance(metadata, dict):
                    files.add(metadata.get('source', 'Unknown'))
                    methods_count += 1
        
        return {
            'total_files': len(files),
            'total_methods': methods_count,
            'sample_files': list(files)[:10]
        }

def list_available_projects() -> List[str]:
    """List all available projects"""
    chroma_dirs = glob.glob("./chroma-*")
    projects = []
    for dir_path in chroma_dirs:
        project_name = os.path.basename(dir_path).replace("chroma-", "")
        projects.append(project_name)
    return projects

class InteractiveQA:
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.qa = FastCodeQA(project_name)
        self.session_history = []

    def run(self):
        """Run interactive session"""
        # Show project overview
        overview = self.qa.get_project_overview()
        print(f"\n📊 Project '{self.project_name}' Overview:")
        print(f"   Files: {overview['total_files']}")
        print(f"   Methods: {overview['total_methods']}")
        
        print(f"\n💬 You QA interface is Ready! Current model: {self.qa.current_model}")
        print("Commands:")
        print("- 'What does UserService do?'")
        print("- 'Show payment processing flow'")
        print("- 'models' - list available models")
        print("- 'use codellama' - switch model")
        print("- 'ask with deepseek-coder: How does auth work?' - one-time model use")
        print("- 'overview' - show project stats")
        print("- 'search <query>' - direct method search")
        print("- 'exit' to quit\n")
        
        while True:
            try:
                question = input("❓ Ask: ").strip()
                
                if question.lower() in ['exit', 'quit']:
                    break
                
                if question.lower() == 'models':
                    models = self.qa.list_models()
                    print(f"\n🤖 Available models:")
                    for model in models:
                        print(f"   {model}")
                    continue
                
                if question.lower().startswith('use '):
                    model_name = question[4:].strip()
                    self.qa.switch_model(model_name)
                    continue
                
                if question.lower() == 'overview':
                    overview = self.qa.get_project_overview()
                    print(f"📊 Files: {overview['total_files']}, Methods: {overview['total_methods']}")
                    continue
                
                if question.lower().startswith('search '):
                    query = question[7:]
                    methods = self.qa.search_methods(query)
                    print(f"\n🔍 Found {len(methods)} methods:")
                    for m in methods[:5]:
                        print(f"   📄 {m['file']} :: {m['method']}")
                    continue
                
                # Handle "ask with model: question" syntax
                target_model = None
                if question.lower().startswith('ask with '):
                    parts = question[9:].split(':', 1)
                    if len(parts) == 2:
                        target_model = parts[0].strip()
                        question = parts[1].strip()
                
                if not question:
                    continue
                
                print("🤔 Thinking...")
                result = self.qa.ask_fast(question, target_model)
                
                cache_indicator = " (cached)" if result['from_cache'] else ""
                model_indicator = f" using {result['model_used']}" if target_model else ""
                print(f"\n🤖 Answer ({result['response_time']:.1f}s{cache_indicator}{model_indicator}):")
                print(f"{result['answer']}\n")
                
                if result['sources']:
                    print(f"📁 Sources: {', '.join(result['sources'])}\n")
                
                self.session_history.append((question, result))
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"⚠️ Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Interactive Code QA')
    parser.add_argument('--project', '-p', help='Project name to query')
    parser.add_argument('--list', '-l', action='store_true', help='List available projects')
    
    args = parser.parse_args()
    
    if args.list:
        projects = list_available_projects()
        if projects:
            print("📋 Available projects:")
            for project in projects:
                print(f"   - {project}")
        else:
            print("❌ No projects found. Run reader.py first.")
        return
    
    if not args.project:
        projects = list_available_projects()
        if not projects:
            print("❌ No projects found. Run reader.py first.")
            return
        elif len(projects) == 1:
            args.project = projects[0]
            print(f"🎯 Using project: {args.project}")
        else:
            print("📋 Available projects:")
            for i, project in enumerate(projects, 1):
                print(f"   {i}. {project}")
            
            try:
                choice = input("\nSelect project (number or name): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        args.project = projects[idx]
                    else:
                        print("❌ Invalid selection")
                        return
                else:
                    if choice in projects:
                        args.project = choice
                    else:
                        print("❌ Project not found")
                        return
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return
    
    try:
        qa_session = InteractiveQA(args.project)
        qa_session.run()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Run reader.py first to create the vector store")

if __name__ == "__main__":
    main()