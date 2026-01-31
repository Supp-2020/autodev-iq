import os
import logging
from typing import Optional, Dict, Any
from git import Repo, GitCommandError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectType:
    JAVA = "java"
    REACT = "react"

class UnitTest:
    
    def __init__(self, base_path: str = "indexed_projects"):
        self.base_path = base_path
    
    def detect_project_type(self, project_path: str) -> str:
        java_indicators = ["pom.xml", "build.gradle", "src/main/java"]
        react_indicators = ["package.json", "src", "node_modules"]
        
        for indicator in java_indicators:
            if os.path.exists(os.path.join(project_path, indicator)):
                return ProjectType.JAVA
        
        for indicator in react_indicators:
            if os.path.exists(os.path.join(project_path, indicator)):
                return ProjectType.REACT
        
        raise ValueError("Could not detect project type (Java or React)")
    
    def find_file_in_project(self, project_path: str, filename: str) -> Optional[str]:
        
        # Recursively search for a file in the project directory
        
        for root, dirs, files in os.walk(project_path):
            # Skip common directories to avoid unnecessary searches
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'target', 'build', '.idea', '__pycache__']]
            
            for file in files:
                if file == filename or file.startswith(filename.split('.')[0]):
                    return os.path.join(root, file)
        
        return None
    
    def find_main_java_package_structure(self, project_path: str) -> str:
        main_java_path = os.path.join(project_path, "src", "main", "java")
        
        if not os.path.exists(main_java_path):
            logger.warning(f"src/main/java not found in {project_path}")
            return ""
        
        # Dictionary to store package paths with their scores
        package_scores = {}
        
        # Walk through src/main/java directory
        for root, dirs, files in os.walk(main_java_path):
            # Skip hidden directories and common non-package directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['META-INF', 'resources']]
            
            # Count .java files in this directory
            java_files = [f for f in files if f.endswith('.java')]
            
            if java_files:
                # Get relative path from src/main/java
                relative_path = os.path.relpath(root, main_java_path)
                if relative_path == '.':
                    relative_path = ""
                
                depth = len(relative_path.split(os.sep)) if relative_path else 0
                file_count = len(java_files)
                
                # Get the directory with most files and rename the last folder /tests
                score = depth * 10 + file_count
                package_scores[relative_path] = {
                    'score': score,
                    'depth': depth,
                    'files': file_count
                }
                
                logger.debug(f"Package: '{relative_path}' - Depth: {depth}, Files: {file_count}, Score: {score}")
        
        if not package_scores:
            logger.warning("No Java files found in src/main/java")
            return ""
        
        # Find the package with the highest score (deepest structure + file count)
        best_package = max(package_scores.items(), key=lambda x: x[1]['score'])
        package_path = best_package[0]
        package_info = best_package[1]
        
        logger.info(f"Selected package: '{package_path}' - Depth: {package_info['depth']}, Files: {package_info['files']}, Score: {package_info['score']}")
        
        return package_path

    def create_java_test_file(self, project_path: str, test_file_name: str, unit_test_content: str, project_id: str) -> str:
        # Find the most common package structure in src/main/java
        package_path = self.find_main_java_package_structure(project_path)
        
        # Construct the test directory path
        if package_path:
            # Split the package path and replace last segment with 'tests'
            path_parts = package_path.split(os.sep)
            if len(path_parts) > 0:
                path_parts[-1] = 'service'
                test_package_path = os.sep.join(path_parts)
                logger.info(f"Transformed package structure from {package_path} to {test_package_path}")
            else:
                test_package_path = package_path
                
            test_dir = os.path.join(project_path, "src", "test", "java", test_package_path)
            logger.info(f"Using package structure: {test_package_path}")
        else:
            # Fallback to basic test directory
            test_dir = os.path.join(project_path, "src", "test", "java")
            logger.info("Using default test directory (no package structure found)")
        
        # Create test directory if it doesn't exist
        os.makedirs(test_dir, exist_ok=True)
        
        # Create the test file
        test_file_path = os.path.join(test_dir, f"{test_file_name}Test.java")
        
        # If we found a package structure, we might want to add package declaration
        final_content = unit_test_content
        if package_path and "package " not in unit_test_content:
            # Convert file path to package name (replace / or \ with .)
            package_name = test_package_path.replace(os.sep, '.')
            package_declaration = f"package {package_name};\n\n"
            final_content = package_declaration + unit_test_content
            logger.info(f"Added package declaration: package {package_name};")
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        path_parts = test_file_path.split(os.sep)
        try:
            # Find the index of project_id in the path
            project_index = path_parts.index(project_id)
            # Get all parts after project_id
            trimmed_parts = path_parts[project_index+1:]
            # Join them back together
            trimmed_path = os.sep.join(trimmed_parts)
        except ValueError:
            # If project_id not found, fall back to trimming from 'src'
            try:
                src_index = path_parts.index('src')
                trimmed_path = os.sep.join(path_parts[src_index:])
            except ValueError:
                # If neither project_id nor 'src' found, return full path
                trimmed_path = test_file_path
        
        logger.info(f"Created Java test file: {trimmed_path}")
        return trimmed_path
    
    def create_react_test_file(self, project_path: str, test_file_name: str, unit_test_content: str, project_id: str) -> str:
        
        # Create a React test file at the same level as the original file
        
        # Find the original file
        original_file = self.find_file_in_project(project_path, test_file_name)
        
        if not original_file:
            raise FileNotFoundError(f"Could not find file '{test_file_name}' in project")
        
        # Get the directory of the original file
        file_dir = os.path.dirname(original_file)
        
        # Create test file name (handle different extensions)
        base_name = test_file_name.split('.')[0]
        test_file_path = os.path.join(file_dir, f"{base_name}.test.js")
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(unit_test_content)
        
        logger.info(f"Created React test file: {test_file_path}")
        
        path_parts = test_file_path.split(os.sep)
        try:
            # Find the index of project_id in the path
            project_index = path_parts.index(project_id)
            # Get all parts after project_id
            trimmed_parts = path_parts[project_index+1:]
            # Join them back together
            trimmed_path = os.sep.join(trimmed_parts)
        except ValueError:
            # If project_id not found, fall back to trimming from 'src'
            try:
                src_index = path_parts.index('src')
                trimmed_path = os.sep.join(path_parts[src_index:])
            except ValueError:
                # If neither project_id nor 'src' found, return full path
                trimmed_path = test_file_path
        
        logger.info(f"Created React test file: {trimmed_path}")
        return trimmed_path
    
    async def perform_git_operations(self, project_path: str, test_file_path: str, 
                                   test_file_name: str, branch_name: str) -> str:
        
        # Perform Git operations: checkout branch, add, commit, and push (Commented out right now)
        try:
            # Initialize Git repo
            repo = Repo(project_path)
            
            # Ensure we have a clean working directory
            if repo.is_dirty():
                logger.warning("Working directory is dirty, but proceeding...")
            
            # Checkout or create the branch
            logger.info(f"Checking out branch: {branch_name}")
            try:
                # Try to checkout existing branch
                repo.git.checkout(branch_name)
            except GitCommandError:
                # Branch doesn't exist, create it
                logger.info(f"Branch {branch_name} doesn't exist, creating it")
                repo.git.checkout('-b', branch_name)
            
            # Add the test file
            logger.info(f"Adding file to Git: {test_file_path}")
            repo.index.add([test_file_path])
            
            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
                logger.warning("No changes to commit")
                return "No changes to commit"
            
            # Commit the changes
            commit_message = f"Added unit tests for the file {test_file_name}"
            logger.info(f"Committing with message: {commit_message}")
            repo.index.commit(commit_message)
            
            # Push to origin
            logger.info(f"Pushing to origin/{branch_name}")
            origin = repo.remote(name='origin')
            origin.push(branch_name)
            
            return "Git operations completed successfully"
            
        except GitCommandError as e:
            logger.error(f"Git operation failed: {e}")
            raise GitCommandError(f"Git operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Git error: {e}")
            raise Exception(f"Git operation failed: {str(e)}")
    
    async def create_unit_test(self, project_id: str, test_file_name: str, 
                             unit_test_content: str, branch_name: str) -> Dict[str, Any]:
        
        # Main method to create unit test files and perform Git operations
        
        # Validate inputs
        if not all([project_id.strip(), test_file_name.strip(), 
                   unit_test_content.strip(), branch_name.strip()]):
            raise ValueError("All fields must be non-empty")
        
        # Construct project path
        project_path = os.path.join(self.base_path, project_id)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project with ID '{project_id}' not found")
        
        # Check if it's a Git repository
        if not os.path.exists(os.path.join(project_path, '.git')):
            raise ValueError("Project is not a Git repository")
        
        logger.info(f"Processing unit test creation for project: {project_id}")
        
        # Detect project type
        project_type = self.detect_project_type(project_path)
        logger.info(f"Detected project type: {project_type}")
        
        # Create test file based on project type
        if project_type == ProjectType.JAVA:
            test_file_path = self.create_java_test_file(project_path, test_file_name, unit_test_content,project_id)
        elif project_type == ProjectType.REACT:
            test_file_path = self.create_react_test_file(project_path, test_file_name, unit_test_content,project_id)
        else:
            raise ValueError(f"Unsupported project type: {project_type}")
        
        # Perform Git operations
        git_result = await self.perform_git_operations(
            project_path, test_file_path, test_file_name, branch_name
        )
        
        return {
            "project_id": project_id,
            "project_type": project_type,
            "test_file_path": os.path.relpath(test_file_path, project_path),
            "branch_name": branch_name,
            "git_result": git_result
        }