import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


# ── Playwright wrapper ─────────────────────────────────────────────────────────

class PW:
    def __init__(self, headed=True):
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=not headed)
        self.page = self.browser.new_page()

    def navigate(self, url: str):
        self.page.goto(url)

    def fill(self, selector: str, text: str):
        self.page.fill(selector, text)

    def click(self, selector: str, force: bool = False, delay: int = 0):
        self.page.click(selector, force=force, delay=delay)

    def select(self, selector: str, value: str):
        self.page.select_option(selector, value)

    def text(self) -> str:
        return self.page.inner_text("body")

    def current_url(self) -> str:
        return self.page.url

    def wait(self, ms: int):
        self.page.wait_for_timeout(ms)

    def upload(self, selector: str, filepath: str):
        self.page.set_input_files(selector, filepath)

    def close(self):
        self.browser.close()
        self.pw.stop()


# ── Value resolver (unchanged, your good work) ────────────────────────────────

def resolve(value: Any, data: dict) -> str:
    if not isinstance(value, str):
        return str(value)

    def lookup(expr: str) -> str:
        expr = expr.strip()
        if expr.startswith("fn:"):
            _, fn, *args = expr.split(":")
            return _transform(fn, args, data)

        keys = expr.split(".")
        node = data
        for k in keys:
            if isinstance(node, dict):
                node = node.get(k, "")
            elif isinstance(node, list):
                try:
                    node = node[int(k)]
                except:
                    node = ""
            else:
                node = ""

        return str(node) if node is not None else ""

    result = re.sub(r"\{\{\s*(.*?)\s*\}\}", lambda m: lookup(m.group(1)), value)
    if "{{" in result and result != value:
        return resolve(result, data)
    return result


def _transform(fn: str, args: list, data: dict) -> str:
    import random
    if fn == "split_name":
        full = data.get("name", "")
        parts = full.split()
        idx = int(args[0]) if args else 0
        if idx == -1:
            return parts[-1] if parts else ""
        return parts[idx] if idx < len(parts) else ""
    elif fn == "random":
        return str(random.randint(10000, 99999))
    elif fn == "random_email":
        import string
        chars = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = args[0] if args else "example.com"
        return f"user_{chars}@{domain}"
    elif fn == "random_name":
        firsts = ["Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley"]
        lasts = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        return f"{random.choice(firsts)} {random.choice(lasts)}"
    return ""


# ── Step runner ───────────────────────────────────────────────────────────────

def run_step(pw: PW, step: dict, data: dict):
    action = step.get("action")

    if action == "navigate":
        url = resolve(step["url"], data)
        print(f"  → {url}")
        pw.navigate(url)

    elif action == "wait":
        ms = int(resolve(str(step.get("ms", 1000)), data))
        pw.wait(ms)

    elif action == "fill":
        selector = step["selector"]
        value = resolve(step["value"], data)
        pw.fill(selector, value)
        print(f"  ✓ Filled '{value[:20]}{'…' if len(value) > 20 else ''}'")

    elif action == "click":
        selector = step["selector"]
        force = step.get("force", False)
        delay = step.get("delay", 0)
        pw.click(selector, force=force, delay=delay)
        print("  ✓ Clicked")

    elif action == "optional_click":
        try:
            force_click = step.get("force", False)
            pw.page.click(step["selector"], timeout=5000, force=force_click)
            print("  ✓ Clicked (optional)")
        except Exception as e:
            print(f"  - Element not clicked (skipped). Reason: {str(e).splitlines()[0]}")

    elif action == "select":
        value = resolve(step["value"], data)
        pw.select(step["selector"], value)
        print(f"  ✓ Selected '{value}'")

    elif action == "upload":
        value = resolve(step["value"], data)
        pw.upload(step["selector"], value)
        print(f"  ✓ Uploaded '{value}'")

    elif action == "assert_url_contains":
        time.sleep(2)
        url = pw.current_url()
        keywords = [resolve(k, data) for k in step.get("keywords", [])]

        print(f"  URL: {url}")

        if any(kw.lower() in url.lower() for kw in keywords):
            print("  ✅ Success — URL matched")
        else:
            print("  ⚠ URL mismatch")

    elif action == "wait_for_selector":
        selector = step["selector"]
        state = step.get("state", "visible")
        timeout = int(step.get("timeout", 30000))
        pw.page.wait_for_selector(selector, state=state, timeout=timeout)
        print(f"  ✓ Selector '{selector}' is {state}")

    elif action == "check":
        selector = step["selector"]
        pw.page.check(selector)
        print(f"  ✓ Checked '{selector}'")

    elif action == "keep_open":
        ms = int(resolve(str(step.get("ms", 15000)), data))
        print(f"  ⏳ Keeping browser open {ms//1000}s")
        pw.wait(ms)

    else:
        print(f"  ⚠ Unknown action '{action}'")


# ── Engine ────────────────────────────────────────────────────────────────────

def run_automation(config: dict):
    settings = config.get("settings", {})
    data = config.get("data", {})
    steps = config.get("steps", [])

    print(f"\n🚀 {settings.get('name', 'Automation')} starting...\n")

    pw = PW(headed=settings.get("headed", True))

    try:
        for i, step in enumerate(steps, 1):
            label = step.get("label", step.get("action", f"step-{i}"))
            print(f"[{i}/{len(steps)}] {label}")

            try:
                run_step(pw, step, data)
            except Exception as e:
                print(f"  ✗ Step failed: {e}")
                try:
                    print(f"    Current URL: {pw.current_url()}")
                except:
                    pass
                if settings.get("stop_on_error", False):
                    break

    finally:
        if not settings.get("keep_browser_open", False):
            pw.close()

    print("\n🏁 Automation complete.\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        sys.exit(f"Config file not found: {path}")
    with p.open() as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Playwright form automator")
    parser.add_argument("--config", required=True)
    parser.add_argument("--data", action="append", help="Override data values: key=value")
    args = parser.parse_args()

    config = load_config(args.config)
    
    if args.data:
        for item in args.data:
            if "=" in item:
                k, v = item.split("=", 1)
                config.setdefault("data", {})[k] = v
                
    run_automation(config)


if __name__ == "__main__":
    main()