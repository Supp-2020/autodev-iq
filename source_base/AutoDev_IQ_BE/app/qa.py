import os
import re
import concurrent.futures
from functools import lru_cache
from typing import List
import time

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from config import config

PROMPT_DIR = "./prompts"

def clean_mermaid_response(response: str) -> str:
    """Remove markdown code block formatting from mermaid responses using regex."""
    response = response.strip()
    
    # Remove markdown code blocks using regex patterns
    # Pattern 1: Remove ```
    response = re.sub(r'^```mermaid\s*\n?', '', response, flags=re.MULTILINE)
    
    # Pattern 2: Remove generic ```
    response = re.sub(r'^```\s*\n?', '', response, flags=re.MULTILINE)
    
    # Pattern 3: Remove ```
    response = re.sub(r'\n?```\s*$', '', response, flags=re.MULTILINE)
    
    # Pattern 4: Remove any remaining standalone ```
    response = re.sub(r'^\s*```\s*$', '', response, flags=re.MULTILINE)
    
    # Clean up any extra whitespace and empty lines
    response = response.strip()
    
    # Ensure proper flowchart format - extract flowchart content if wrapped
    if not response.startswith("flowchart"):
        flowchart_match = re.search(r'(flowchart\s+TD.*?)(?:\n\s*$|\Z)', response, re.DOTALL)
        if flowchart_match:
            response = flowchart_match.group(1).strip()
    
    return response

def smart_document_retrieval(question: str, max_docs: int) -> int:
    """Optimize document count based on question complexity."""
    question_lower = question.lower()
    
    simple_words = ('what is', 'list', 'show me', 'which')
    complex_words = ('explain', 'how does', 'why', 'architecture', 'workflow')
    medium_words = ('describe', 'tell me about', 'summarize')
    
    if any(word in question_lower for word in simple_words):
        return min(max_docs, max(15, max_docs // 3))
    
    if any(word in question_lower for word in complex_words):
        return max_docs
    
    if any(word in question_lower for word in medium_words):
        return min(max_docs, max(20, int(max_docs * 0.7)))
    
    question_words = len(question.split())
    if question_words <= 5:
        return min(max_docs, max(12, max_docs // 4))
    
    if question_words >= 15:
        return max_docs
    
    return min(max_docs, max(18, int(max_docs * 0.6)))

def optimize_context_for_question(question: str, retrieved_docs: List, max_context_docs: int = None) -> List:
    """Filter and rank retrieved documents for better accuracy."""
    if not retrieved_docs or len(retrieved_docs) <= 10:
        return retrieved_docs
    
    question_keywords = {word.lower() for word in question.split() if len(word) > 3}
    question_lower = question.lower()
    
    scored_docs = []
    code_terms = {'function', 'class', 'method', 'import', 'def ', 'return'}
    question_code_terms = {'function', 'method', 'code', 'implement'}
    
    for doc in retrieved_docs:
        content_lower = doc.page_content.lower()
        content_words = {word for word in content_lower.split() if len(word) > 3}
        
        keyword_matches = len(question_keywords & content_words)
        
        phrase_bonus = sum(2 for phrase in question.split() 
                          if len(phrase) > 4 and phrase.lower() in content_lower)
        
        code_bonus = (1 if any(term in content_lower for term in code_terms) and 
                     any(term in question_lower for term in question_code_terms) else 0)
        
        total_score = keyword_matches + phrase_bonus + code_bonus
        scored_docs.append((doc, total_score))
    
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    if max_context_docs:
        return [doc for doc, score in scored_docs[:max_context_docs]]
    
    if scored_docs:
        max_score = scored_docs[0][1]
        min_useful_score = max(1, max_score * 0.3)
        return [doc for doc, score in scored_docs if score >= min_useful_score][:25]
    
    return [doc for doc, score in scored_docs]

def prepare_components_parallel(project_id: str, prompt_type: str, question: str, max_docs: int):
    """Prepare components in parallel for faster processing."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        prompt_future = executor.submit(load_prompt_template, prompt_type)
        db_future = executor.submit(get_chroma_db, project_id)
        
        prompt = prompt_future.result()
        db = db_future.result()
    
    optimal_docs = smart_document_retrieval(question, max_docs)
    retriever = db.as_retriever(search_kwargs={"k": optimal_docs})
    llm = get_llm(streaming=True)
    
    return prompt, retriever, llm, optimal_docs

@lru_cache(maxsize=10)
def load_prompt_template(prompt_type: str) -> PromptTemplate:
    prompt_path = os.path.join(PROMPT_DIR, f"{prompt_type}.txt")
    if not os.path.exists(prompt_path):
        raise ValueError(f"Prompt template not found: {prompt_path}")
    with open(prompt_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    return PromptTemplate.from_template(template_str)

@lru_cache(maxsize=1)
def get_embeddings():
    return OllamaEmbeddings(model=config.MODEL_NAME)

@lru_cache(maxsize=20)
def get_chroma_db(project_id: str):
    return Chroma(
        persist_directory=f"{config.CHROMA_DIR}/{project_id}/chroma",
        embedding_function=get_embeddings()
    )

@lru_cache(maxsize=2)
def get_llm(streaming: bool = False):
    if streaming:
        return OllamaLLM(
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
    return OllamaLLM(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE
    )

def answer_question_stream(project_id, question, max_docs, prompt_type):
    """Core Q&A function with caching integration."""
    start_time = time.time()
    
    from app.utils import check_cache, store_cache_response
    
    cached_response = check_cache(project_id, question)
    if cached_response:
        print(f"📋 Response time: {time.time() - start_time:.3f}s (cached)")
        yield from stream_cached_response(cached_response)
        return

    prompt, retriever, llm, optimal_docs = prepare_components_parallel(
        project_id, prompt_type, question, max_docs
    )

    retrieved_docs = retriever.get_relevant_documents(question)
    optimized_docs = optimize_context_for_question(question, retrieved_docs)

    context = optimized_docs
    formatted_prompt = prompt.format(context=context, question=question)

    if prompt_type == "flowchart_prompt":
        # Get complete response
        response = llm(formatted_prompt)
        
        # ✅ Clean mermaid response using regex
        response = clean_mermaid_response(response)
        
        # Cache the clean flowchart response
        store_cache_response(project_id, question, response)
        print(f"📋 Response time: {time.time() - start_time:.3f}s (generated - flowchart)")
        
        yield response
        return

    # For streaming prompts - collect response while streaming
    full_response = []
    for chunk in llm.stream(formatted_prompt):
        full_response.append(chunk)
        yield chunk
    
    # Cache the complete streamed response
    final_response = "".join(full_response)
    store_cache_response(project_id, question, final_response)
    print(f"📋 Response time: {time.time() - start_time:.3f}s (generated - streamed)")

def generate_unit_tests_from_feature(feature_id: str, target_filename: str) -> List[dict]:
    # Generate unit tests from feature comparison for a specific file (optimized)."""
    
    start_time = time.time()
    
    from app.utils import check_cache, store_cache_response

    cached_response = check_cache(feature_id, target_filename)
    if cached_response:
        print(f"📋 Unit test response time: {time.time() - start_time:.3f}s (cached)")
        return [{"file": target_filename, "unit_test": cached_response}]
    
    base_id = feature_id.split("__", 1)[0]
    feature_vs = get_chroma_db(feature_id)
    base_vs = get_chroma_db(base_id)

    # Get only relevant metadata from Chroma (faster than retrieving everything)
    feature_docs = feature_vs.similarity_search(target_filename, k=100)
    if not feature_docs:
        raise FileNotFoundError(f"No embedded feature chunks found for: {target_filename}")

    # Gather all chunk content
    feature_doc = "\n".join([doc.page_content for doc in feature_docs])
    base_docs = base_vs.similarity_search(target_filename, k=10)
    if not base_docs:
        print(f"⚠️ No base chunks found for {target_filename}")
        return []

    base_doc = "\n".join([doc.page_content for doc in base_docs])

    # Prepare LLM input
    if target_filename.endswith(".java"):
        prompt_template = load_prompt_template("unit_test_java_prompt")
    elif target_filename.endswith(".jsx") or target_filename.endswith(".tsx"):
        prompt_template = load_prompt_template("unit_test_react_prompt")
    else:
        prompt_template = load_prompt_template("unit_test_prompt")  # default / fallback
    
    prompt = prompt_template.format(feature_code=feature_doc, base_code=base_doc)

    llm = get_llm()

    try:
        response = llm.invoke(prompt)
        generated_test = response.strip()
        
        # Cache the generated unit test
        store_cache_response(feature_id, target_filename, generated_test)
        print(f"📋 Unit test response time: {time.time() - start_time:.3f}s (generated)")
        
        return [{"file": target_filename, "unit_test": generated_test}]
    except Exception as e:
        print(f"❌ Error generating test for {target_filename}: {e}")
        return []


# Increase or decrease the chunk_size or delay for streaming purpose
def stream_cached_response(cached_response, chunk_size=20, delay=0.3):
    import time

    for i in range(0, len(cached_response), chunk_size):
        chunk = cached_response[i:i + chunk_size]
        yield chunk
        time.sleep(delay)
