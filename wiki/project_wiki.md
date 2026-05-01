# Reed.co.uk Registration Bot - Project Wiki

## 🎯 Project Goal
To build a robust, completely automated Python/Playwright script that reads a JSON configuration file (`reed_signup.json`) and autonomously completes the entire Reed.co.uk jobseeker registration process. The bot is designed to handle dynamic test data generation, file uploads, and transient UI overlays (like cookie banners) without requiring any manual user intervention.

---

## ✅ System Capabilities

*   **Automation Engine (`form_automator.py`)**: The core engine successfully parses the JSON sequence and seamlessly drives the browser using Playwright.
*   **Dynamic Data Templating**: We built a recursive template resolver supporting variables (e.g., `{{password}}`) and custom functions. 
    *   **Final Identity**: The system has transitioned from random test data to a static user identity (`alvian@devshorepartners.com`) for the final registration process.
    *   **Generation Capabilities**: The underlying engine still supports `{{fn:random_email}}`, `{{fn:random_name}}`, and `{{fn:split_name}}` for any future testing or regression runs.
*   **Form Navigation & Standard Inputs**: The bot successfully navigates to the login page, fills the email/password, and clicks the initial signup button.
*   **File Uploads**: Playwright successfully handles the CV file upload (`cv.pdf`) using the `input[data-qa="drop-input"]` selector.
*   **Dynamic UK Form Logic**: 
    *   We successfully forced the "Country" dropdown to `United Kingdom`. This is critical because Reed hides UK-specific fields (like Postcode and Right to Work) if the IP is detected as overseas (e.g., Indonesia).
    *   UK-specific test phone numbers (`07700900077`) are now correctly formatted and bypass the "Invalid phone number" validation.
*   **Profile Completion**: The bot successfully locates and fills the Current Job Title, Desired Job Title, Salary, Postcode, and selects "Remote" for the desired work location.
*   **Checkbox Interactions**: The bot accurately clicks complex radio/checkbox fields, including the "Right to Work" status and the marketing "Opt-out" checkbox.
*   **Sign-In Logic**: A dedicated `reed_signin.json` has been created to handle the authentication flow for existing users, reusing the same robust click and wait patterns developed for registration.
*   **Job Application Logic**: A new `reed_apply.json` has been introduced. It handles complex screening questions (context-aware), Cloudflare bypasses, and multi-step modal interactions.
*   **CLI Data Overrides**: The engine supports `--data` flag to inject dynamic parameters (like `job_url`) at runtime.

---

## 📂 Project Structure

- **`form_automator.py`**: The core execution engine (Playwright interpreter).
- **`reed_apply.json`**: Configuration for automated job applications.
- **`reed_signin.json`**: Configuration for user authentication.
- **`reed_signup.json`**: Configuration for new user registration.
- **`cv.pdf`**: The resume used for registration and applications.
- **`wiki/`**: Comprehensive project documentation and historical logs.

---

## 📖 Related Documents

*   👉 **[Historical Issues & Challenges](./historical_issues.md)** - A detailed technical log of the 8 major blockers faced during development (like the React Race Condition and the Cookie Banner Interception), what we tried, exactly where the code changed, and the final working solutions.
*   ⚙️ **[Architecture & Logic](./architecture_and_logic.md)** - A deep dive into the system's design, how `form_automator.py` interprets the JSON, and how the recursive templating engine manages dynamic data generation.
