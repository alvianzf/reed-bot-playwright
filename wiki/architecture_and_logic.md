# Architecture & Logic

[← Back to Main Wiki](./project_wiki.md)

## 🏗 High-Level Architecture

The Reed.co.uk Registration Bot is designed around a **Data-Driven Automation Architecture**. Instead of hardcoding Playwright commands directly into a monolithic Python script, the logic is split into two distinct layers:

1.  **The Automation Engine (`form_automator.py`)**: A generalized Python interpreter that drives the Playwright browser.
2.  **The Configuration Sequence (`reed_signup.json`)**: A human-readable JSON file that dictates the exact state, data, and steps the engine should execute.

This separation of concerns allows developers (or non-developers) to tweak selectors, adjust waits, or change form data without ever touching the underlying Python code.

### 🚀 CLI Overrides
The engine now supports dynamic data overrides via the command line:
`./venv/bin/python form_automator.py --config reed_apply.json --data job_url="https://..."`
Any values passed via `--data key=value` will override the defaults in the JSON `data` block.

---

## ⚙️ The Core Logic (`form_automator.py`)

The Python engine is responsible for three primary tasks:

### 1. The Execution Loop (`run_automation`)

When the script runs, it loads the JSON file and initializes a synchronous Playwright browser context. It then enters a loop, iterating over the `steps` array defined in the JSON. For each step, it hands control to the `run_step()` function. If a step fails (and `stop_on_error` is false), the script catches the exception, logs the error, and gracefully continues to the next step, making it highly resilient to transient UI failures (like missing optional cookie banners).

### 2. Action Handlers (`run_step`)

The engine translates abstract JSON commands into concrete Playwright API calls. Supported actions include:

- `navigate`: Calls `pw.page.goto(url)`.
- `fill`: Resolves the template value and calls `pw.page.fill(selector, value)`.
- `click`: Calls `pw.page.click(selector, force=force, delay=delay)`. Supports optional `force: true` and `delay: ms` from JSON.
- `optional_click`: Wraps the click in a `try/except` block with an adjustable timeout and an optional `force: true` parameter.
- `select`: Calls `pw.page.select_option(selector, value)`.
- `upload`: Uses Playwright's native file-handling via `pw.page.set_input_files(selector, value)`.
- `wait`: Explicitly pauses execution via `pw.page.wait_for_timeout(ms)`.

### 3. The Recursive Templating Engine (`resolve` & `_transform`)

To bypass strict anti-automation blocks (like "Email already registered"), the engine cannot use static data.
Before any `fill` or `select` action occurs, the engine passes the JSON value through the `resolve()` function.

- **Variable Injection**: It uses regular expressions to find tags like `{{password}}` and swaps them with the corresponding value from the JSON `data` block.
- **Recursion**: If a resolved variable contains another template tag (e.g., `{{email}}` resolves to `{{fn:random_email}}`), the function recursively calls itself until it returns a raw string.
- **Custom Functions**: The `_transform()` function handles dynamic generation logic:
  - `{{fn:random_email}}`: Generates a unique 10-character alphanumeric string and appends a domain.
  - `{{fn:random_name}}`: Randomly selects from a predefined list of first and last names.
  - `{{fn:split_name:0}}` / `{{fn:split_name:-1}}`: Takes the currently generated full name and safely splits it into First or Last name components for specific form fields.

---

## 📄 The Configuration State (`reed_signup.json`)

The JSON file acts as the "script" for the automation engine.

- **`settings`**: Configures global browser behavior (e.g., `headed: true` for visual debugging).
- **`data`**: The centralized payload of user data. This is where the templating engine pulls its values from. Changing a value here automatically cascades to every step that references it.
- **`steps`**: An ordered array of objects. Each object represents a single DOM interaction. Steps are intentionally granular. For example, explicitly defining a `Wait for form validation` step between a `fill` and a `click` ensures that React SPA (Single Page Application) state changes have time to propagate before the automation interacts with the UI.
