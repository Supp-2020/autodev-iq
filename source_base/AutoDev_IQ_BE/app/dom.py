import asyncio
import json
import argparse
import os
from pathlib import Path
from itertools import zip_longest
from urllib.parse import urlparse
from playwright.async_api import async_playwright
import cssutils
from bs4 import BeautifulSoup, Tag

cssutils.log.setLevel("CRITICAL")

TAGS_TO_IGNORE_IN_DOM_DIFF = ['style', 'script']

OUTPUT_DIR = os.path.join("app", "dom_diffs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_all_styles(soup: BeautifulSoup) -> dict:
  styles_map = {}
  for style_tag in soup.find_all('style'):
    try:
      sheet = cssutils.parseString(style_tag.string or '')
      for rule in sheet.cssRules.rulesOfType(cssutils.css.CSSRule.STYLE_RULE):
        selector = rule.selectorText
        properties = {p.name: p.value for p in rule.style}
        styles_map.setdefault(selector, {}).update(properties)
    except Exception:
      pass
  for element in soup.find_all(style=True):
    selector = generate_css_selector(element)
    try:
      style_declaration = cssutils.parseStyle(element['style'])
      properties = {p.name: p.value for p in style_declaration}
      styles_map.setdefault(selector, {}).update(properties)
    except Exception:
      pass
  return styles_map

def compare_css_rules(base_map: dict, test_map: dict) -> list:
  css_differences = []
  all_selectors = set(base_map.keys()) | set(test_map.keys())
  for selector in sorted(all_selectors):
    base_props = base_map.get(selector)
    test_props = test_map.get(selector)
    if not base_props:
      css_differences.append({"type": "css_rule_added", "selector": selector, "properties": test_props})
    elif not test_props:
      css_differences.append({"type": "css_rule_deleted", "selector": selector, "properties": base_props})
    elif base_props != test_props:
      prop_changes = {}
      for prop in set(base_props) | set(test_props):
        if base_props.get(prop) != test_props.get(prop):
          prop_changes[prop] = {"base_value": base_props.get(prop), "test_value": test_props.get(prop)}
      if prop_changes:
        css_differences.append({"type": "css_rule_modified", "selector": selector, "property_changes": prop_changes})
  return css_differences

def generate_css_selector(element: Tag) -> str:
  path = []
  current = element
  while current and isinstance(current, Tag) and current.name != 'html':
    selector = current.name
    if current.get('id'):
      path.insert(0, f'#{current["id"]}')
      break
    if current.get('class'):
      selector += '.' + '.'.join(current['class'])
    siblings = current.parent.find_all(current.name, recursive=False) if current.parent else []
    if len(siblings) > 1:
      index = siblings.index(current) + 1
      selector += f':nth-of-type({index})'
    path.insert(0, selector)
    current = current.parent
  return ' > '.join(path)

def compare_elements(elem1: Tag, elem2: Tag, differences: list):
  if elem1.name in TAGS_TO_IGNORE_IN_DOM_DIFF:
    return

  modifications = {}
  base_attrs = elem1.attrs.copy(); base_attrs.pop('style', None)
  test_attrs = elem2.attrs.copy(); test_attrs.pop('style', None)

  if base_attrs != test_attrs:
    modifications['attributes'] = {"base_value": base_attrs, "test_value": test_attrs}

  base_text = ''.join(s.strip() for s in elem1.find_all(string=True, recursive=False))
  test_text = ''.join(s.strip() for s in elem2.find_all(string=True, recursive=False))
  if base_text != test_text and (base_text or test_text):
    modifications['text_content'] = {"base_value": base_text, "test_value": test_text}

  if modifications:
    differences.append({"type": "dom_modification", "selector": generate_css_selector(elem1), "changes": modifications})

  base_children = [c for c in elem1.children if isinstance(c, Tag)]
  test_children = [c for c in elem2.children if isinstance(c, Tag)]

  for child1, child2 in zip_longest(base_children, test_children):
    if child1 and not child2:
      differences.append({"type": "dom_deletion", "selector": generate_css_selector(child1), "details": str(child1).strip()})
    elif not child1 and child2:
      differences.append({"type": "dom_addition", "selector": generate_css_selector(child2), "details": str(child2).strip()})
    elif child1.name != child2.name:
      differences.append({"type": "dom_deletion", "selector": generate_css_selector(child1), "details": str(child1).strip()})
      differences.append({"type": "dom_addition", "selector": generate_css_selector(child2), "details": str(child2).strip()})
    else:
      compare_elements(child1, child2, differences)

async def get_dom_and_css_diff(base_url: str, test_url: str) -> list:
  try:
    async with async_playwright() as p:
      browser = await p.chromium.launch()
      page = await browser.new_page()
      await page.goto(base_url, wait_until="domcontentloaded")
      base_html = await page.content()
      await page.goto(test_url, wait_until="domcontentloaded")
      test_html = await page.content()
      await browser.close()
  except Exception as e:
    print("Playwright error:", e)
    return []

  base_soup = BeautifulSoup(base_html, 'html.parser')
  test_soup = BeautifulSoup(test_html, 'html.parser')
  dom_diffs = []
  compare_elements(base_soup.html, test_soup.html, dom_diffs)
  css_diffs = compare_css_rules(
      extract_all_styles(base_soup),
      extract_all_styles(test_soup)
  )
  return dom_diffs + css_diffs

async def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("base_url", type=str)
  parser.add_argument("test_url", type=str)
  parser.add_argument("label", type=str)
  args = parser.parse_args()

  print(f"Running diff for label: {args.label}")
  diffs = await get_dom_and_css_diff(args.base_url, args.test_url)

  label_file = os.path.join(OUTPUT_DIR, f"{args.label}.json")
  with open(label_file, "w", encoding="utf-8") as f:
    json.dump(diffs, f, indent=2, ensure_ascii=False)
  print(f" Diff saved to {label_file}")

if __name__ == "__main__":
  asyncio.run(main())
