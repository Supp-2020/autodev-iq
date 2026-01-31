import subprocess
import os
import json
import sys
import time
import base64

from fastapi import HTTPException


def encode_image_to_base64(path):
  if not path or not os.path.exists(path):
    return None
  with open(path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode("utf-8")


async def run_visual_regression_test(base_url, test_url, label=None):
  timestamp = str(int(time.time()))
  label = label or f"vrt_{timestamp}"
  temp_dir = f"temp_output_{timestamp}"
  os.makedirs(temp_dir, exist_ok=True)

  # 🧪 Backstop.js configuration with no-sandbox fix
  backstop_config = {
    "id": f"vrt_test_{timestamp}",
    "viewports": [{"label": "desktop", "width": 1366, "height": 768}],
    "scenarios": [{
      "label": "Visual Test",
      "url": test_url,
      "referenceUrl": base_url,
      "misMatchThreshold": 0.1,
      "requireSameDimensions": True,
      "engine": "puppeteer",
      "engineOptions": {
        "args": ["--no-sandbox", "--disable-setuid-sandbox"]
      }
    }],
    "paths": {
      "bitmaps_reference": f"{temp_dir}/backstop_data/bitmaps_reference",
      "bitmaps_test": f"{temp_dir}/backstop_data/bitmaps_test",
      "engine_scripts": f"{temp_dir}/backstop_data/engine_scripts",
      "html_report": f"{temp_dir}/html_report",
      "ci_report": f"{temp_dir}/backstop_data/ci_report"
    },
    "report": ["browser"],
    "engine": "puppeteer",
    "engineOptions": {
      "args": ["--no-sandbox", "--disable-setuid-sandbox"]
    }
  }

  config_path = os.path.join(temp_dir, "backstop.json")
  with open(config_path, "w") as f:
    json.dump(backstop_config, f, indent=2)

  # Run Backstop reference creation
  subprocess.run(f"npx backstop reference --configPath={config_path}", shell=True, check=True)
  result = subprocess.run(f"npx backstop test --configPath={config_path} --no-open", shell=True, capture_output=True, text=True)

  # 🎯 Extract screenshots
  ref_dir = backstop_config["paths"]["bitmaps_reference"]
  test_dir = backstop_config["paths"]["bitmaps_test"]
  base_img = test_img = diff_img = None

  for root, _, files in os.walk(test_dir):
    for fname in files:
      if fname.endswith(".png"):
        if fname.startswith("failed_diff_"):
          diff_img = os.path.join(root, fname)
        elif "document_0_desktop.png" in fname:
          test_img = os.path.join(root, fname)

  for fname in os.listdir(ref_dir):
    if fname.endswith(".png"):
      base_img = os.path.join(ref_dir, fname)

  # 🚀 Run DOM diff and capture JSON
  try:
    dom_script = os.path.join("app", "dom.py")
    subprocess.run(
        ["python", dom_script, base_url, test_url, label],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True
    )
    print("DOM script executed successfully.")

    output_path = os.path.join("app", "dom_diffs", f"{label}.json")
    if not os.path.exists(output_path):
      raise FileNotFoundError(f"Diff output file not found: {output_path}")

    with open(output_path, "r", encoding="utf-8") as f:
      dom_json_output = json.load(f)

  except subprocess.CalledProcessError as e:
    print(" DOM script failed:")
    print("STDOUT:\n", e.stdout)
    print("STDERR:\n", e.stderr)
    raise RuntimeError(f"DOM diff script failed:\n{e.stderr}") from e

  # 🧠 Pass DOM diff to LLaMA enrichment
  try:
    result = subprocess.run(
        ["python", "VisualLama.py", label],
        capture_output=True,
        text=True,
        cwd="app",  # adjust if your script is inside the `app/` folder
        check=True
    )
    enriched_json = json.loads(result.stdout)  # ✅ map result to enriched_json

  except subprocess.CalledProcessError as e:
    print("❌ Subprocess failed.")
    print("STDERR:", e.stderr)
    print("STDOUT:", e.stdout)
    return {
      "label": label,
      "error": "Subprocess failed while calling AI analysis.",
      "stderr": e.stderr,
      "stdout": e.stdout
    }

  except json.JSONDecodeError as e:
    print("❌ Failed to parse JSON output.")
    print("Raw output:", result.stdout)
    return {
      "label": label,
      "error": "Invalid JSON returned from subprocess.",
      "raw_output": result.stdout
    }

  # ✅ Final return block with enriched_json now mapped
  return {
    "label": label,
    "message": "VRT and AI completed." if result.returncode == 0 else "VRT done with visual mismatches.",
    "html_report": f"{temp_dir}/html_report/index.html",
    "base_image": encode_image_to_base64(base_img),
    "test_image": encode_image_to_base64(test_img),
    "diff_image": encode_image_to_base64(diff_img),
    "llama_output": enriched_json  # ✅ mapped correctly
  }
