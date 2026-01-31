# config.py
import os

class Config:
    def __init__(self):
        self.MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:latest")
        self.CHROMA_DIR = os.getenv("CHROMA_DIR", "./indexed_projects")

        # Make Ollama host dynamic for Docker/local
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.TEMPERATURE = float(os.getenv("TEMPERATURE", 0.5))
        self.MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))

config = Config()
