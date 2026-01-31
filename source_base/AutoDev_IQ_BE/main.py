import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import shutil
import os, json
import time
import bcrypt
import stat
import pathlib
from typing import Optional, List
from git import Repo, GitCommandError
from starlette.responses import StreamingResponse

from config import config
from app.processor import process_project, process_project_diff, get_file_diff
from app.utils import get_cache_statistics, clear_project_cache, clear_embedding_cache, clear_all_cache
from app.qa import answer_question_stream
from app.qa import generate_unit_tests_from_feature
from app.background_qa_generator import start_background_qa_generation
from app.reactRunner import run_react_in_docker, stop_docker_container
from app.unit_test import UnitTest
from app.vrt_runner import run_visual_regression_test

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Directories

PROJECTS_DIR = config.CHROMA_DIR
os.makedirs(PROJECTS_DIR, exist_ok=True)

BASE_DIR = pathlib.Path(__file__).parent.resolve()
USERS_FILE = BASE_DIR / "users.txt"

# Classes or Models

class UploadRequest(BaseModel):
  git_url: str

class QuestionRequest(BaseModel):
  project_id: str
  question: str
  max_docs: int = 5
  prompt_type: str = "code_prompt"

class FeatureUploadRequest(BaseModel):
  project_id: str
  feature_branch: str

class FeatureTestRequest(BaseModel):
  project_id: str
  file_name: str# e.g., "product-service__feature_price-update"

class ReactRunnerRequest(BaseModel):
  project_id: str

class UserRegistration(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class CacheClearRequest(BaseModel):
    project_id: Optional[str] = None
    clear_embeddings: bool = False
    clear_all: bool = False

class UnitTestRequest(BaseModel):
    project_id: str
    test_file_name: str
    unit_test: str
    branch_name: str

class UnitTestResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None

class URLPayload(BaseModel):
  base_url: str
  test_url: str

class CloneFeatureBranchRequest(BaseModel):
  git_url: str
  branch: str

# Functions

def load_users() -> list:
    try:
        if not USERS_FILE.exists():
            return []
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users(users: list):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        # Handle cases where the hashed_password is invalid
        return False

def on_rm_error(func, path, exc_info):
  os.chmod(path, stat.S_IWRITE)
  func(path)

def remove_directory(path: str, max_retries: int = 3, delay: float = 1.0):
  for _ in range(max_retries):
    try:
      if os.path.exists(path):
        shutil.rmtree(path, onerror=on_rm_error)
        if os.path.exists(path):
          temp_name = f"{path}_delete_{time.time()}"
          try:
            os.rename(path, temp_name)
            shutil.rmtree(temp_name, onerror=on_rm_error)
          except:
            pass
        return
      time.sleep(delay)
    except Exception:
      time.sleep(delay)

  if os.path.exists(path):
    raise RuntimeError(f"Failed to remove directory {path} after {max_retries} attempts")

# API's

@app.post("/upload")
async def upload_code(req: UploadRequest):
  try:
    project_id = os.path.basename(req.git_url.rstrip("/")).replace(".git", "")
    project_path = os.path.join(PROJECTS_DIR, project_id)

    print(f"🚀 Starting upload for: {req.git_url}")
    print(f"📁 Target project path: {project_path}")

    # Clone repo only if not already present
    if not os.path.exists(project_path):
      print("🔄 Cloning Git repository...")
      Repo.clone_from(req.git_url, project_path)
      print("✅ Clone successful.")
    else:
      print("📦 Repo already exists — skipping clone.")

    # Start processing (excluding .git)
    print("🧠 Processing project files (excluding .git)...")
    process_project(project_path, req.git_url, project_id)

    #start_background_qa_generation(project_id, project_path)

    print("🎉 Project upload and processing complete.")
    return {"status": "success", "project_id": project_id}

  except Exception as e:
    print(f"❌ Upload failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-feature")
async def upload_feature(req: FeatureUploadRequest):
  try:
    project_path = os.path.join(PROJECTS_DIR, req.project_id)
    if not os.path.exists(project_path):
      raise HTTPException(status_code=404, detail="Main project not uploaded yet.")

    repo = Repo(project_path)
    repo.remotes.origin.fetch()

    # Checkout the feature branch
    if req.feature_branch not in repo.heads:
      repo.git.checkout("-b", req.feature_branch, f"origin/{req.feature_branch}")
    else:
      repo.git.checkout(req.feature_branch)

    # Get list of changed files (JavaScript/Java)
    changed_files_output = repo.git.diff("main...HEAD", name_only=True).splitlines()
    changed_files = [
      os.path.join(project_path, f.strip())
      for f in changed_files_output
      if f.endswith((".java", ".js", ".jsx", ".ts", ".tsx"))
    ]

    if not changed_files:
      raise HTTPException(status_code=400, detail="No code files changed in feature branch.")

    # Read full content of changed files
    file_content_map = {}
    filenames_only = []
    for file_path in changed_files:
      try:
        with open(file_path, "r", encoding="utf-8") as f:
          file_content_map[file_path] = f.read()
          filenames_only.append(os.path.basename(file_path))
      except Exception as e:
        print(f"⚠️ Skipped unreadable file: {file_path}, error: {e}")

    if not file_content_map:
      raise HTTPException(status_code=400, detail="No readable changed files.")

    # Construct feature_id and pass to processor
    feature_id = f"{req.project_id}__{req.feature_branch.replace('/', '_')}"
    process_project_diff(file_content_map, feature_id)

    return {
      "status": "success",
      "files_changed": len(file_content_map),
      "feature_id": feature_id,
      "file_names": filenames_only,
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/clone-feature-branch")
async def clone_feature_branch_and_run(req: CloneFeatureBranchRequest):
  try:
    import pathlib

    project_name = os.path.basename(req.git_url.rstrip("/")).replace(".git", "")
    branch_safe = req.branch.replace("/", "-")
    project_id = f"{project_name}-{branch_safe}"
    target_path = os.path.join(PROJECTS_DIR, project_id)

    if os.path.exists(target_path):
      remove_directory(target_path)

    print(f"🔄 Cloning {req.git_url} (branch: {req.branch}) into {target_path}")
    Repo.clone_from(req.git_url, target_path, branch=req.branch, single_branch=True)

    return {
      "status": "success",
      "project_id": project_id,
      "project_path": target_path,
    }

  except GitCommandError as e:
    raise HTTPException(status_code=500, detail=f"Git error: {str(e)}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/askStream")
async def ask_question_with_stream(req: QuestionRequest):
  
  def response_generator():
    try:
      # Get the token stream from your QA function
      token_stream = answer_question_stream(
          req.project_id,
          req.question,
          req.max_docs,
          req.prompt_type
      )
      
      # Stream each token as it arrives
      for token in token_stream:
        if token:  # Only send non-empty tokens
          # Format as Server-Sent Events (SSE)
          data = {
              "type": "token",
              "content": str(token),
              "timestamp": time.time()
          }
          yield f"data: {json.dumps(data)}\n\n"
      
      # Send completion signal
      completion_data = {
          "type": "complete",
          "content": "",
          "timestamp": time.time()
      }
      yield f"data: {json.dumps(completion_data)}\n\n"
      
    except Exception as e:
      # Send error in stream format
      error_data = {
          "type": "error",
          "content": str(e),
          "timestamp": time.time()
      }
      yield f"data: {json.dumps(error_data)}\n\n"
  
  try:
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
  
@app.post("/ask")
async def ask_question_stream(req: QuestionRequest):
  try:
    token_generator = answer_question_stream(
        req.project_id,
        req.question,
        req.max_docs,
        req.prompt_type
    )
    return StreamingResponse(token_generator, media_type="application/json")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-feature-branches", response_model=List[str])
async def list_feature_branches(project_id: str):
  try:
    project_path = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.exists(project_path):
      raise HTTPException(status_code=404, detail=f"Project not found at: {project_path}")

    repo = Repo(project_path)
    repo.remotes.origin.fetch()

    branches = [
      ref.name.replace("origin/", "")
      for ref in repo.remotes.origin.refs
      if ref.name.startswith("origin/")
         and not ref.name.endswith(("HEAD"))
    ]

    return sorted(branches)

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.get("/projects")
def list_all_projects():
  base_dir = config.CHROMA_DIR
  projects = []

  if not os.path.exists(base_dir):
    raise HTTPException(status_code=404, detail="No project directory found.")

  for project_id in os.listdir(base_dir):
    project_dir = os.path.join(base_dir, project_id)
    metadata_file = os.path.join(project_dir, "metadata.json")

    if os.path.isfile(metadata_file):
      try:
        with open(metadata_file, "r", encoding="utf-8") as f:
          metadata = json.load(f)
          projects.append({
            "project_id": project_id,
            "git_url": metadata.get("git_url", "unknown"),
            "project_type": metadata.get("project_type", "unknown"),
            "main_branch": metadata.get("main_branch", "main")
          })
      except Exception as e:
        continue  # Skip broken metadata files

  return {"projects": projects}

@app.post("/generate-unit-test")
async def generate_unit_test(req: FeatureTestRequest):
  try:
    tests = generate_unit_tests_from_feature(req.project_id, req.file_name)
    return {"status": "success", "tests": tests}
  except FileNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  
@app.post("/register")
async def register_user(user: UserRegistration):
    users = load_users()
    
    if any(u["email"].lower() == user.email.lower() for u in users):
        raise HTTPException(status_code=400, detail="Email already exists !")
    
    hashed_pw = hash_password(user.password)
    
    new_user = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        "email": user.email,
        "password": hashed_pw
    }
    
    users.append(new_user)
    save_users(users)
    
    return {"message": "Registration successful"}

@app.post("/login")
async def login_user(user: UserLogin):
    users = load_users()
    user_data = next((u for u in users if u["email"].lower() == user.email.lower()), None)
    
    if not user_data or not verify_password(user.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials !")
    
    user_data.pop("password", None)
    return {"message": "Login successful", "user": user_data}

@app.get("/cache/stats")
async def get_cache_stats(project_id: Optional[str] = None):
    try:
        stats = get_cache_statistics(project_id)
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/clear")
async def clear_cache(req: CacheClearRequest):
    try:
        if req.clear_all:
            success = clear_all_cache()
            message = "All caches cleared successfully" if success else "Failed to clear all caches"
            
        elif req.clear_embeddings:
            success = clear_embedding_cache()
            message = "Embedding cache cleared successfully" if success else "Failed to clear embedding cache"
            
        elif req.project_id:
            success = clear_project_cache(req.project_id)
            message = f"Cache cleared for project {req.project_id}" if success else f"Failed to clear cache for {req.project_id}"
            
        else:
            raise HTTPException(status_code=400, detail="Must specify project_id, clear_embeddings=true, or clear_all=true")
        
        return {"status": "success" if success else "error", "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/projects")
async def list_cached_projects():
    try:
        stats = get_cache_statistics()
        return {
            "status": "success", 
            "projects": stats.get("projects", []),
            "total_projects": stats.get("total_projects", 0),
            "total_questions": stats.get("total_cached_questions", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/frequent-questions/{project_id}")
async def get_frequent_questions(project_id: str):
    try:
        freq_file = os.path.join(
            "qa_cache_storage", 
            "qa_responses", 
            f"{project_id}_freq.json"
        )
        
        if not os.path.exists(freq_file):
            raise HTTPException(
                status_code=404, 
                detail=f"No question data found for project {project_id}"
            )
        
        with open(freq_file, 'r') as f:
            freq_data = json.load(f)
        
        questions = [
            {"question": q[0].upper() + q[1:] if q else q, "count": c} 
            for q, c in list(freq_data.items())[:3]
        ]

        return {
            "project_id": project_id,
            "frequent_questions": questions
        }
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail="Invalid question frequency data format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing request: {str(e)}"
        )

@app.post("/create-unit-test", response_model=UnitTestResponse)
async def create_unit_test(request: UnitTestRequest):

    # Endpoint to create unit test files and perform Git operations
    try:
        # Initialize the service
        unit_test_service = UnitTest()

        # Process the request
        result = await unit_test_service.create_unit_test(
            project_id=request.project_id,
            test_file_name=request.test_file_name,
            unit_test_content=request.unit_test,
            branch_name=request.branch_name
        )

        return UnitTestResponse(
            success=True,
            message="Unit test file created and pushed successfully",
            data=result
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Project not found: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except GitCommandError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Git operation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/run-react")
async def run_react_app(req: ReactRunnerRequest):
  try:
    project_path = os.path.join(PROJECTS_DIR, req.project_id)
    if not os.path.exists(project_path):
      raise HTTPException(status_code=404, detail="Main project not uploaded yet.")
    url = run_react_in_docker(project_path, req.project_id)
    return {"status": "success", "url": url}
  except FileNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except subprocess.CalledProcessError as e:
    raise HTTPException(status_code=500, detail=f"Docker error: {e}")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-container")
def stop_container(container_name: str):
  try:
    stop_docker_container(container_name)
    return {"status": "success", "message": f"Container '{container_name}' stopped and removed."}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-vrt")
async def run_vrt(payload: URLPayload, open_browser: bool = False):
  try:
    return await run_visual_regression_test(payload.base_url, payload.test_url, open_browser)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
