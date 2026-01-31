import os
import json
import pickle
import numpy as np
from typing import Optional, Dict
from collections import OrderedDict
from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from config import config

_cache_manager = None

def detect_project_type(path: str) -> str:
    """Detect project type based on file extensions."""
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith(".java"):
                return "java"
            if f.endswith((".js", ".jsx", ".ts", ".tsx")):
                return "react"
    return "unknown"

class PersistentProjectCacheManager:
    def __init__(self, max_cache_size_per_project: int = 300, max_total_embeddings: int = 3000):
        self.cache_dir = Path("./qa_cache_storage")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.qa_cache_dir = self.cache_dir / "qa_responses"
        self.embedding_cache_dir = self.cache_dir / "embeddings"
        self.stats_file = self.cache_dir / "cache_stats.json"
        
        self.qa_cache_dir.mkdir(exist_ok=True)
        self.embedding_cache_dir.mkdir(exist_ok=True)
        
        self.project_caches = {}
        self.embedding_cache = OrderedDict()
        self.question_frequency = {}
        self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        
        self.max_cache_size_per_project = max_cache_size_per_project
        self.max_total_embeddings = max_total_embeddings
        self.similarity_threshold = 0.85
        self.max_similarity_checks = 20
        
        # Load embeddings lazily only when needed
        self._embeddings = None
        self._loaded_from_disk = False
        self._load_cache_from_disk()
        
        print(f"🔧 Cache initialized - Projects: {len(self.project_caches)}, Embeddings: {len(self.embedding_cache)}")
    
    @property
    def embeddings(self):
        """Lazy load embeddings only when needed."""
        if self._embeddings is None:
            from app.qa import get_embeddings
            self._embeddings = get_embeddings()
        return self._embeddings
    
    def _get_project_cache_file(self, project_id: str) -> Path:
        return self.qa_cache_dir / f"{project_id}.pkl"
    
    def _get_project_frequency_file(self, project_id: str) -> Path:
        return self.qa_cache_dir / f"{project_id}_freq.json"
    
    def _get_embedding_cache_file(self) -> Path:
        return self.embedding_cache_dir / "embeddings.pkl"
    
    def _load_cache_from_disk(self):
        if self._loaded_from_disk:
            return
            
        try:
            pkl_files = list(self.qa_cache_dir.glob("*.pkl"))
            if not pkl_files:
                self._loaded_from_disk = True
                return
                
            for cache_file in pkl_files:
                if "_freq" in cache_file.name:
                    continue
                    
                project_id = cache_file.stem
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                        self.project_caches[project_id] = OrderedDict(cache_data)
                    
                    freq_file = self._get_project_frequency_file(project_id)
                    if freq_file.exists():
                        with open(freq_file, 'r') as f:
                            self.question_frequency[project_id] = json.load(f)
                    else:
                        self.question_frequency[project_id] = {}
                        
                except Exception as e:
                    print(f"⚠️ Failed to load cache for {project_id}: {e}")
            
            embedding_file = self._get_embedding_cache_file()
            if embedding_file.exists() and embedding_file.stat().st_size > 0:
                try:
                    with open(embedding_file, 'rb') as f:
                        embedding_data = pickle.load(f)
                        self.embedding_cache = OrderedDict(embedding_data)
                except Exception as e:
                    print(f"⚠️ Failed to load embeddings: {e}")
            
            if self.stats_file.exists():
                try:
                    with open(self.stats_file, 'r') as f:
                        self.cache_stats = json.load(f)
                except Exception:
                    pass
                    
            self._loaded_from_disk = True
                    
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
    
    def _save_project_cache(self, project_id: str):
        try:
            cache_file = self._get_project_cache_file(project_id)
            with open(cache_file, 'wb') as f:
                pickle.dump(dict(self.project_caches.get(project_id, {})), f, protocol=pickle.HIGHEST_PROTOCOL)
            
            freq_data = self.question_frequency.get(project_id, {})
            if freq_data:
                freq_file = self._get_project_frequency_file(project_id)
                with open(freq_file, 'w') as f:
                    json.dump(freq_data, f)
                
        except Exception as e:
            print(f"⚠️ Failed to save cache for {project_id}: {e}")
    
    def _save_embedding_cache(self):
        try:
            embedding_file = self._get_embedding_cache_file()
            with open(embedding_file, 'wb') as f:
                pickle.dump(dict(self.embedding_cache), f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"⚠️ Failed to save embeddings: {e}")
    
    def _save_cache_stats(self):
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.cache_stats, f)
        except Exception as e:
            print(f"⚠️ Failed to save stats: {e}")
    
    def _get_embedding_cached(self, text: str) -> np.ndarray:
        if text in self.embedding_cache:
            self.embedding_cache.move_to_end(text)
            return self.embedding_cache[text]
        
        try:
            emb = self.embeddings.embed_query(text)
            if isinstance(emb, list) and len(emb) > 0:
                emb = emb[0] if isinstance(emb[0], list) else emb
            emb_array = np.array(emb)
            
            self.embedding_cache[text] = emb_array
            
            if len(self.embedding_cache) > self.max_total_embeddings:
                eviction_count = len(self.embedding_cache) - self.max_total_embeddings + 50
                for _ in range(eviction_count):
                    if len(self.embedding_cache) > 0:
                        oldest_key = next(iter(self.embedding_cache))
                        del self.embedding_cache[oldest_key]
                        self.cache_stats["evictions"] += 1
                
                if eviction_count > 0 and len(self.embedding_cache) % 50 == 0:
                    self._save_embedding_cache()
            
            if len(self.embedding_cache) % 20 == 0:
                self._save_embedding_cache()
            
            return emb_array
            
        except Exception as e:
            print(f"❌ Error embedding text: {e}")
            return np.zeros(384)
    
    def _calculate_similarity_fast(self, q1: str, q2: str) -> float:
        try:
            emb1 = self._get_embedding_cached(q1)
            emb2 = self._get_embedding_cached(q2)
            dot_product = np.dot(emb1, emb2)
            norms = np.linalg.norm(emb1) * np.linalg.norm(emb2)
            return dot_product / norms if norms > 0 else 0.0
        except Exception:
            return 0.0
    
    def _normalize_question(self, question: str) -> str:
        return question.lower().strip()
    
    def _get_project_cache(self, project_id: str) -> OrderedDict:
        if project_id not in self.project_caches:
            self.project_caches[project_id] = OrderedDict()
            self.question_frequency[project_id] = {}
        return self.project_caches[project_id]
    
    def _evict_project_cache(self, project_id: str):
        project_cache = self.project_caches[project_id]
        
        if len(project_cache) > self.max_cache_size_per_project:
            eviction_count = len(project_cache) - self.max_cache_size_per_project + 10
            for _ in range(eviction_count):
                if len(project_cache) > 0:
                    oldest_question = next(iter(project_cache))
                    del project_cache[oldest_question]
                    
                    if oldest_question in self.question_frequency[project_id]:
                        del self.question_frequency[project_id][oldest_question]
                    
                    self.cache_stats["evictions"] += 1
    
    def check_cache(self, project_id: str, question: str) -> Optional[str]:
        normalized_q = self._normalize_question(question)
        project_cache = self._get_project_cache(project_id)
        
        if normalized_q in project_cache:
            response = project_cache[normalized_q]
            project_cache.move_to_end(normalized_q)
            self.question_frequency[project_id][normalized_q] = self.question_frequency[project_id].get(normalized_q, 0) + 1
            self.cache_stats["hits"] += 1
            print(f"⚡ EXACT MATCH - {project_id}")
            return response
        
        if len(project_cache) < 5:
            self.cache_stats["misses"] += 1
            print(f"❌ CACHE MISS - {project_id}")
            return None
        
        cache_items = list(project_cache.items())
        check_limit = min(len(cache_items), self.max_similarity_checks)
        
        if project_id in self.question_frequency and self.question_frequency[project_id]:
            freq_data = self.question_frequency[project_id]
            cache_items.sort(key=lambda x: freq_data.get(x[0], 0), reverse=True)
        
        for cached_q, response in cache_items[:check_limit]:
            similarity = self._calculate_similarity_fast(normalized_q, cached_q)
            if similarity >= self.similarity_threshold:
                project_cache.move_to_end(cached_q)
                self.question_frequency[project_id][cached_q] = self.question_frequency[project_id].get(cached_q, 0) + 1
                self.cache_stats["hits"] += 1
                print(f"⚡ SEMANTIC MATCH - {project_id} (similarity: {similarity:.2f})")
                return response
        
        self.cache_stats["misses"] += 1
        print(f"❌ CACHE MISS - {project_id}")
        return None
    
    def store_response(self, project_id: str, question: str, response: str):
        normalized_q = self._normalize_question(question)
        project_cache = self._get_project_cache(project_id)
        
        project_cache[normalized_q] = response
        self.question_frequency[project_id][normalized_q] = self.question_frequency[project_id].get(normalized_q, 0) + 1
        
        self._evict_project_cache(project_id)
        self._save_project_cache(project_id)
        self._save_cache_stats()
        
        print(f"💾 STORED - {project_id}")
    
    def clear_project_cache(self, project_id: str) -> bool:
        try:
            if project_id in self.project_caches:
                del self.project_caches[project_id]
            if project_id in self.question_frequency:
                del self.question_frequency[project_id]
            
            cache_file = self._get_project_cache_file(project_id)
            if cache_file.exists():
                cache_file.unlink()
                
            freq_file = self._get_project_frequency_file(project_id)
            if freq_file.exists():
                freq_file.unlink()
            
            print(f"🗑️ Cleared cache for: {project_id}")
            return True
        except Exception as e:
            print(f"❌ Error clearing cache for {project_id}: {e}")
            return False
    
    def clear_embedding_cache(self) -> bool:
        try:
            self.embedding_cache.clear()
            embedding_file = self._get_embedding_cache_file()
            if embedding_file.exists():
                embedding_file.unlink()
            print("🗑️ Cleared embedding cache")
            return True
        except Exception as e:
            print(f"❌ Error clearing embedding cache: {e}")
            return False
    
    def clear_all_cache(self) -> bool:
        try:
            self.project_caches.clear()
            self.embedding_cache.clear()
            self.question_frequency.clear()
            self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
            
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    file_path.unlink()
            
            print("🗑️ Cleared all caches")
            return True
        except Exception as e:
            print(f"❌ Error clearing all caches: {e}")
            return False
    
    def get_cache_stats(self, project_id: str = None) -> Dict:
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_ratio = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        if project_id:
            if project_id in self.project_caches:
                cache_size = len(self.project_caches[project_id])
                freq_stats = self.question_frequency.get(project_id, {})
                most_frequent = sorted(freq_stats.items(), key=lambda x: x[1], reverse=True)[:5]
                return {
                    "project_id": project_id,
                    "cached_questions": cache_size,
                    "cache_utilization": f"{(cache_size/self.max_cache_size_per_project)*100:.1f}%",
                    "most_frequent_questions": most_frequent,
                    "hit_ratio": f"{hit_ratio:.1f}%"
                }
            return {"project_id": project_id, "cached_questions": 0}
        
        return {
            "total_projects": len(self.project_caches),
            "total_cached_questions": sum(len(cache) for cache in self.project_caches.values()),
            "embedding_cache_size": len(self.embedding_cache),
            "hit_ratio": f"{hit_ratio:.1f}%",
            "cache_stats": self.cache_stats,
            "projects": list(self.project_caches.keys())
        }

# Global cache manager functions
def get_cache_manager():
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = PersistentProjectCacheManager(
            max_cache_size_per_project=300,
            max_total_embeddings=3000
        )
    return _cache_manager

def get_cache_statistics(project_id: str = None):
    return get_cache_manager().get_cache_stats(project_id)

def clear_project_cache(project_id: str) -> bool:
    return get_cache_manager().clear_project_cache(project_id)

def clear_embedding_cache() -> bool:
    return get_cache_manager().clear_embedding_cache()

def clear_all_cache() -> bool:
    return get_cache_manager().clear_all_cache()

def check_cache(project_id: str, question: str) -> Optional[str]:
    return get_cache_manager().check_cache(project_id, question)

def store_cache_response(project_id: str, question: str, response: str):
    get_cache_manager().store_response(project_id, question, response)
