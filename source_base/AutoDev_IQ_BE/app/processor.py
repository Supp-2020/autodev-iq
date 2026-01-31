import os
import json
from difflib import unified_diff
from typing import Dict

from git import Repo
from app.utils import detect_project_type
from app.react_processor import ReactProjectProcessor
from app.java_processor import JavaProjectProcessor


from git import Repo

def process_project(project_path: str, git_url: str, project_id: str):
    print(f"\n🔍 Detecting project type in: {project_path}")
    project_type = detect_project_type(project_path)
    print(f"📦 Detected project type: {project_type}")

    if project_type == "java":
        java_files = [
            os.path.join(dp, f)
            for dp, _, fs in os.walk(project_path)
            if ".git" not in dp
            for f in fs if f.endswith(".java")
        ]
        if not java_files:
            raise Exception(f"❌ No Java files found in: {project_path}")

        print(f"🧠 Java files found: {len(java_files)}")
        processor = JavaProjectProcessor(project_id=project_id)
        processor.process(java_files)
        print("✅ Java project processed.")

    elif project_type == "react":
        babel_script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "babelParser.js")
        )
        if not os.path.exists(babel_script_path):
            raise FileNotFoundError(f"❌ babelParser.js not found at: {babel_script_path}")

        processor = ReactProjectProcessor(
            project_id=project_id,
            babel_script_path=babel_script_path
        )
        processor.process(react_project_path=project_path)
        print("✅ React project processed.")

    else:
        raise Exception(f"❌ Unsupported project type in: {project_path}")

    # 🔍 Detect remote default branch from origin/HEAD
    try:
        repo = Repo(project_path)
        default_ref = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
        main_branch = default_ref.split("/")[-1]  # e.g., 'main' or 'master'
    except Exception as e:
        print(f"⚠️ Could not detect remote default branch: {e}")
        main_branch = "main"

    # 📝 Store metadata including main branch
    write_project_metadata(project_path, git_url, project_type, main_branch)



def get_file_diff(repo: Repo, file_path: str) -> str:
    try:
        full_path = os.path.abspath(file_path)
        rel_path = os.path.relpath(full_path, repo.working_tree_dir).replace("\\", "/")
        print(f"⚠️ Changed File: {rel_path}")

        try:
            old = repo.git.show(f"main:{rel_path}").splitlines(keepends=True)
        except Exception:
            print(f"⚠️ File {rel_path} not in 'main' branch. Treating as new file.")
            old = []

        with open(full_path, encoding="utf-8") as f:
            new = f.read().splitlines(keepends=True)

        diff = list(unified_diff(old, new, fromfile=f"main/{rel_path}", tofile=f"feature/{rel_path}"))
        return "".join(diff)

    except Exception as e:
        print(f"❌ Failed to generate diff for {file_path}: {e}")
        return ""


def process_project_diff(file_content_map: Dict[str, str], project_id: str):
    java_files = {f: c for f, c in file_content_map.items() if f.endswith(".java")}
    react_files = {f: c for f, c in file_content_map.items() if f.endswith((".js", ".jsx", ".ts", ".tsx"))}

    if java_files:
        print(f"🔍 Java files changed: {len(java_files)}")
        processor = JavaProjectProcessor(project_id=project_id)
        for file_path, content in java_files.items():
            print(f"📄 Embedding Java: {file_path}")
            processor.process_full_file(file_path, content)

    if react_files:
        print(f"🔍 React files changed: {len(react_files)}")
        babel_script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "babelParser.js")
        )
        if not os.path.exists(babel_script_path):
            raise FileNotFoundError(f"babelParser.js not found at {babel_script_path}")

        processor = ReactProjectProcessor(project_id=project_id, babel_script_path=babel_script_path)
        for file_path, content in react_files.items():
            print(f"📄 Embedding React: {file_path}")
            processor.process_full_file(file_path, content)


def write_project_metadata(project_path: str, git_url: str, project_type: str, main_branch: str):
    metadata = {
        "git_url": git_url,
        "project_type": project_type,
        "main_branch": main_branch
    }
    with open(os.path.join(project_path, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

