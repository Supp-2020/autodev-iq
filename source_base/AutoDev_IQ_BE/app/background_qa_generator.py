import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.qa import answer_question_stream
from app.utils import detect_project_type

def load_prompts_from_file(file_path: str) -> list:
    # Load prompts from text file
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            prompts = []
            for line in f.readlines():
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Remove numbering if present (e.g., "1.Show me..." -> "Show me...")
                    if line[0].isdigit() and '.' in line:
                        line = line.split('.', 1)[1].strip()
                    prompts.append(line)
        
        print(f"📝 Loaded {len(prompts)} prompts from {file_path}")
        return prompts
    
    except Exception as e:
        print(f"❌ Error loading prompts: {e}")
        return []

def generate_and_cache_answer(project_id: str, question: str, question_num: int):
    # Generate answer for a single question and cache it
    try:
        print(f"🤖 Generating answer {question_num}: {question[:50]}...")
        
        # Collect the streamed response
        full_response = ""
        for token in answer_question_stream(project_id, question, max_docs=5, prompt_type="code_prompt"):
            full_response += str(token)
        
        print(f"✅ Completed answer {question_num}: {question[:30]}...")
        return {"success": True, "question": question, "response_length": len(full_response)}
        
    except Exception as e:
        print(f"❌ Failed answer {question_num}: {str(e)}")
        return {"success": False, "question": question, "error": str(e)}

def generate_background_qa(project_id: str, project_path: str):
    # Generate Q&A pairs in background after upload completes
    try:
        print(f"🔍 Starting background QA generation for project: {project_id}")
        
        # Detect project type
        project_type = detect_project_type(project_path)
        print(f"📂 Detected project type: {project_type}")
        
        if project_type == "unknown":
            print("⚠️ Unknown project type, skipping QA generation")
            return
        
        # Load appropriate prompts
        if project_type == "java":
            prompts = load_prompts_from_file("prompts/sample_prompts_java.txt")
        elif project_type == "react":
            prompts = load_prompts_from_file("prompts/sample_prompts_react.txt")
        else:
            print(f"❌ Unsupported project type: {project_type}")
            return
        
        if not prompts:
            print("❌ No prompts loaded, skipping QA generation")
            return
        
        print(f"🚀 Starting parallel QA generation for {len(prompts)} questions...")
        
        # Generate answers in parallel (limit to 2 concurrent to avoid overwhelming)
        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(generate_and_cache_answer, project_id, prompt, i+1)
                for i, prompt in enumerate(prompts)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Print summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"📊 QA Generation Complete for {project_id}:")
        print(f"   ✅ Successful: {successful}/{len(prompts)}")
        print(f"   ❌ Failed: {failed}/{len(prompts)}")
        print(f"   💾 All answers cached automatically")
        
    except Exception as e:
        print(f"❌ Error in background QA generation: {e}")

def start_background_qa_generation(project_id: str, project_path: str):
    # Start QA generation in a background thread
    def background_task():
        # Wait a bit to ensure indexing is fully complete
        time.sleep(3)
        generate_background_qa(project_id, project_path)
    
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    print(f"🔄 Started background QA generation for {project_id}")

# Create sample prompt files if they don't exist
def ensure_prompt_files_exist():
    # Create sample prompt files if they don't exist
    os.makedirs("prompts", exist_ok=True)
    
    # Java prompts
    java_file = "prompts/sample_prompts_java.txt"
    if not os.path.exists(java_file):
        with open(java_file, 'w', encoding='utf-8') as f:
            f.write("1.Show me all REST API endpoints\n")
            f.write("2.List all service classes and their methods\n")
            f.write("3.What is the overview of the backend system\n")
            f.write("4.How are exceptions handled in this application\n")
        print(f"📝 Created {java_file}")
    
    # React prompts
    react_file = "prompts/sample_prompts_react.txt"
    if not os.path.exists(react_file):
        with open(react_file, 'w', encoding='utf-8') as f:
            f.write("1.List all React components in this project\n")
            f.write("2.How is routing configured between different pages\n")
            f.write("3.Show me all API calls to backend\n")
            f.write("4.What state management is used here\n")
            f.write("5.Find all form validation logic\n")
        print(f"📝 Created {react_file}")

# Initialize on import
ensure_prompt_files_exist()