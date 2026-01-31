🧠 AutoDev IQ — Setup Guide

This project powers AI-based analysis of Java and React codebases using FastAPI, Ollama, LangChain, and ChromaDB.

📦 Install Dependencies

pip install -r requirements.txt

⚙️ Babel Setup (for React/JS Code Parsing)

To analyze and parse JavaScript or React projects, this backend uses Babel via Node.js to generate ASTs and extract method/component-level information.

🟢 Install Node.js

Make sure Node.js is installed.

Check version:
node -v
npm -v

📦 Install Babel CLI and Parser Dependencies

npm install @babel/core @babel/parser @babel/traverse

▶️ Start the FastAPI Server

Cd \source_base\AutoDev_IQ_BE

Run Command: 
python -m uvicorn main:app --reload  

Server Will be hosted on: http://127.0.0.1:8000 

