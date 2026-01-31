import os
import subprocess
import socket
import time
import tempfile
import shutil

def in_docker():
  """Detect if running inside a Docker container."""
  return os.path.exists("/.dockerenv")

def find_free_port():
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('', 0))
    return s.getsockname()[1]

def write_dockerfile(temp_dir):
  dockerfile_content = '''
    FROM node:18
    WORKDIR /app
    COPY package*.json ./
    RUN npm install
    COPY . .
    EXPOSE 3000
    CMD ["npm", "start"]
    '''
  with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
    f.write(dockerfile_content)

def stop_docker_container(container_name):
  print(f"🛑 Stopping and removing Docker container: {container_name}")
  subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_react_in_docker(project_path, name: str):
  if not os.path.exists(project_path):
    raise FileNotFoundError(f"Project path does not exist: {project_path}")

  temp_build_dir = tempfile.mkdtemp()
  shutil.copytree(project_path, os.path.join(temp_build_dir, "app"), dirs_exist_ok=True)
  dockerfile_dir = os.path.join(temp_build_dir, "app")

  write_dockerfile(dockerfile_dir)

  image_name = f"{name}"
  container_name = f"{name}"
  host_port = find_free_port()

  try:
    print(f"🐳 Building Docker image: {image_name}...")
    subprocess.run(["docker", "build", "-t", image_name, dockerfile_dir], check=True)

    print(f"🚀 Starting Docker container '{container_name}' on host port {host_port}...")
    subprocess.run([
      "docker", "run", "--name", container_name,
      "-p", f"{host_port}:3000",
      "-d", image_name
    ], check=True)

    print("⏳ Waiting for app to start...")

    success_patterns = ["compiled successfully", "listening on", "started server", "compiled with warnings", "built in"]
    failure_patterns = ["error", "failed", "exception", "exit"]

    max_wait_time = 180  # 3 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
      logs = subprocess.check_output(["docker", "logs", container_name], text=True, stderr=subprocess.DEVNULL)
      lower_logs = logs.lower()

      for success in success_patterns:
        if success in lower_logs:
          # ✅ Use host.docker.internal if running inside Docker
          base_host = "host.docker.internal" if in_docker() else "localhost"
          url = f"http://{base_host}:{host_port}"
          print(f"✅ React app is running at: {url}")
          return url, container_name, host_port

      for failure in failure_patterns:
        if failure in lower_logs:
          print("❌ React app failed to start. Detected error in logs.")
          print("📋 Container logs:\n", logs)
          return None, container_name, None

      time.sleep(3)

    print("⏳ Timeout reached without detecting success or error.")
    print("📋 Container logs:\n", logs)
    return None, container_name, None

  except subprocess.CalledProcessError as e:
    print(f"🚨 Docker command failed: {e}")
    return None, container_name, None
