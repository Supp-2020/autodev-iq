import argparse
import json
import os
import sys
import requests
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import config

OLLAMA_ENDPOINT = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
MODEL = config.MODEL_NAME
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOM_DIFFS_DIR = os.path.join(BASE_DIR, "dom_diffs")


def log(message: str, level="INFO"):
  print(f"[{level}] {message}", file=sys.stderr)


def format_change_for_display(change: dict) -> str:
  change_type_str = change.get("type", "Unknown Change").replace('_', ' ').title()
  selector = change.get("selector", "N/A")
  ai_fix = change.get("ai_fix_suggestion", "No suggestion provided.")

  details_list = []

  if change['type'] == 'dom_modification':
    changes = change.get('changes', {})
    if 'attributes' in changes:
      base_val = json.dumps(changes['attributes']['base_value'])
      test_val = json.dumps(changes['attributes']['test_value'])
      details_list.append(f"- Attributes changed from {base_val} to {test_val}.")
    if 'text_content' in changes:
      base_val = f"\"{changes['text_content']['base_value']}\""
      test_val = f"\"{changes['text_content']['test_value']}\""
      details_list.append(f"- Text content changed from {base_val} to {test_val}.")
  elif change['type'] == 'css_rule_modified':
    prop_changes = change.get('property_changes', {})
    for prop, vals in prop_changes.items():
      base_val = vals.get('base_value', 'N/A')
      test_val = vals.get('test_value', 'N/A')
      details_list.append(f"- CSS property '{prop}' changed from '{base_val}' to '{test_val}'.")
  elif change['type'] in ('dom_addition', 'dom_deletion'):
    details_list.append(f"- Element HTML: {change.get('details', 'N/A')}")
  elif change['type'] in ('css_rule_added', 'css_rule_deleted'):
    properties = json.dumps(change.get('properties', {}))
    details_list.append(f"- Rule properties: {properties}")

  details_str = "\n".join(details_list) if details_list else "No specific details."

  return f"""----------------------------------------
TYPE: {change_type_str}
SELECTOR: {selector}
DETAILS:
{details_str}
SUGGESTED FIX:
  {ai_fix}
""".strip()


def generate_text_report_string(analyzed_changes: list) -> str:
  report_parts = [
    "========================================",
    "    VRT (Visual Regression) Report    ",
    "========================================"
  ]

  if not analyzed_changes:
    report_parts.append("\nNo changes were detected or analyzed.")
  else:
    for change in analyzed_changes:
      formatted_string = format_change_for_display(change)
      report_parts.append(f"\n{formatted_string}")

  report_parts.append("\n\n--- End of Report ---")
  return "\n".join(report_parts)


def load_diff_file(label: str) -> list:
  path = os.path.join(DOM_DIFFS_DIR, f"{label}.json")
  if not os.path.exists(path):
    raise FileNotFoundError(f"Diff file not found at '{path}'")
  with open(path, "r", encoding="utf-8") as f:
    return json.load(f)


def build_prompt(change: dict) -> str:
  selector = change.get("selector", "N/A")
  change_type = change.get("type", "unknown")
  base_instruction = (
    "You are an expert Visual Regression Testing (VRT) analysis bot. "
    "Based on the following change, provide a concise, one-line code snippet or action "
    "to revert the change to its original state. Output ONLY the fix, with no explanation."
  )
  prompt_details = ""
  if change_type == "dom_modification":
    changes = change.get("changes", {})
    attr_change = changes.get("attributes")
    text_change = changes.get("text_content")
    prompt_details = f"A DOM modification occurred on element `{selector}`.\n"
    if attr_change:
      prompt_details += f"- Attributes changed from {json.dumps(attr_change['base_value'])} to {json.dumps(attr_change['test_value'])}.\n"
    if text_change:
      prompt_details += f"- Text content changed from \"{text_change['base_value']}\" to \"{text_change['test_value']}\".\n"
  elif change_type in ("dom_addition", "dom_deletion"):
    action = "added" if change_type == "dom_addition" else "deleted"
    prompt_details = f"A DOM element was {action} at selector `{selector}`.\n- The element's HTML is: `{change.get('details', '')}`."
  elif change_type == "css_rule_modified":
    prop_changes = change.get("property_changes", {})
    changes_str = ", ".join(
        f"'{prop}' changed from '{vals.get('base_value', 'N/A')}' to '{vals.get('test_value', 'N/A')}'"
        for prop, vals in prop_changes.items()
    )
    prompt_details = f"A CSS rule was modified for selector `{selector}`.\n- Changes: {changes_str}."
  elif change_type in ("css_rule_added", "css_rule_deleted"):
    action = "added" if change_type == "css_rule_added" else "deleted"
    prompt_details = f"A CSS rule was {action} for selector `{selector}`.\n- The rule's properties are: {json.dumps(change.get('properties', {}))}."
  else:
    prompt_details = f"An unknown change was detected: {json.dumps(change)}"
  return f"{base_instruction}\n\nCHANGE DETAILS:\n{prompt_details}"


def query_llama(prompt: str) -> str:
  log(" Querying Llama 3 for a direct fix...")
  try:
    response = requests.post(
        OLLAMA_ENDPOINT,
        json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.0}},
        timeout=60
    )
    response.raise_for_status()
    return response.json()["response"].strip()
  except requests.RequestException as e:
    log(f"Network error during LLaMA call: {e}", level="ERROR")
    return "Error: LLaMA network issue"
  except Exception as e:
    log(f"Unexpected error: {traceback.format_exc()}", level="ERROR")
    return "Error: Unexpected processing error"


def main(label: str):
  try:
    diff_data = load_diff_file(label)
  except FileNotFoundError as e:
    log(str(e), level="ERROR")
    sys.exit(1)

  analyzed_differences = []
  log(f" Found {len(diff_data)} VRT changes to analyze for label '{label}'.")

  for i, change in enumerate(diff_data):
    log(f"--- Analyzing change {i + 1}/{len(diff_data)} ---")
    prompt = build_prompt(change)
    fix_suggestion = query_llama(prompt)
    change["ai_fix_suggestion"] = fix_suggestion
    analyzed_differences.append(change)

  # Prepare output
  text_report_string = generate_text_report_string(analyzed_differences)

  final_output_object = {
    "label": label,
    "ai_analysis": text_report_string,
    "changes": analyzed_differences,
    "status": "success"
  }

  # Optional save to file
  try:
    output_path = os.path.join(DOM_DIFFS_DIR, f"{label}_analyzed.json")
    with open(output_path, "w", encoding="utf-8") as f:
      json.dump(final_output_object, f, indent=2, ensure_ascii=False)
    log(f" Saved enriched file to {output_path}")
  except Exception as e:
    log(f"Could not save enriched file: {e}", level="ERROR")

  # Output to subprocess
  sys.stdout.write(json.dumps(final_output_object, ensure_ascii=False))
  sys.stdout.flush()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Analyze a VRT diff file and return enriched data.")
  parser.add_argument('label', type=str, help='The label of the diff report to analyze (e.g., "homepage").')
  args = parser.parse_args()
  main(args.label)
