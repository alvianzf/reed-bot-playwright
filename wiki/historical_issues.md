# Historical Issues & Challenges

[← Back to Main Wiki](./project_wiki.md)

## Detailed Debugging History

Building a resilient bot for a modern SPA (Single Page Application) like Reed.co.uk required bypassing multiple anti-automation and UX hurdles. Below is an exhaustive log of the challenges faced, what approaches failed, where the code changes happened, and whether the final approach was successful.

---

### 1. The "Email Already Registered" Blocker
*   **What we tried:** Reusing the same static email address (`alvian@emailemail.com`) across multiple test iterations.
*   **Status:** ❌ Failed initially
*   **The Issue:** Reed's backend caught the duplicate email and threw an inline validation error. Because the bot didn't know how to handle the error, it sat on the login page waiting for the CV upload screen to appear, eventually timing out and crashing.
*   **Where the change happened:** `form_automator.py` and `reed_signup.json`
*   **The Fix:** Built a dynamic Python templating engine in `form_automator.py` and implemented a `{{fn:random_email}}` function. This generates a completely unique 10-character string (e.g., `user_a1b2c3@example.com`) every run.
*   **Final Outcome:** ✅ Successful. (Note: Once the system was stabilized, we transitioned back to a static, final user email for the actual registration flow).

### 2. The Recursive Templating Bug
*   **What we tried:** Setting the JSON parameter to `"email": "{{fn:random_email}}"`.
*   **Status:** ❌ Failed initially
*   **The Issue:** The engine evaluated `{{email}}`, found the string `{{fn:random_email}}`, but injected that literal string directly into the browser. The form immediately rejected it with the error: *"Please include an '@' in the email address."*
*   **Where the change happened:** `form_automator.py` (specifically the `resolve()` function)
*   **The Fix:** Rewrote the `resolve` function to be fully recursive. If a resolved template yields another template tag (containing `{{`), the engine will recursively process it until it returns the final generated string.
*   **Final Outcome:** ✅ Successful

### 3. The "Next" Button Race Condition (React State Delay)
*   **What we tried:** 
    1. Instructing Playwright to click `#signup_button` immediately after filling out the password field. (Failed)
    2. Adding a 1000ms wait. (Partially successful, but still failed sometimes).
*   **Status:** ✅ Successful after further tuning.
*   **The Issue:** The terminal logged `✓ Clicked`, but the browser did not advance. Playwright was typing and clicking *too fast*—before Reed's React DOM had time to process the `onChange` event and validate the password strength.
*   **Where the change happened:** `form_automator.py` (added `force` and `delay` support) and `reed_signup.json` (increased wait to 3000ms).
*   **The Fix:** 
    - Injected a longer `wait` step of 3000ms to ensure React state is fully settled.
    - Updated `form_automator.py` to support `force: true` and `delay: 100` in the JSON config.
    - Applied these parameters to the `Click Next / Signup` step in `reed_signup.json` to simulate a more realistic human click and bypass strict actionability checks.
*   **Final Outcome:** ✅ Successful end-to-end run verified.

### 4. Geo-IP Field Hiding (The Missing Inputs)
*   **What we tried:** Running the bot without interacting with the "Country" dropdown on the Profile page.
*   **Status:** ❌ Failed initially
*   **The Issue:** Because the host machine's IP was outside the UK (Indonesia), Reed's JavaScript defaulted the country dropdown to Indonesia. As a result, it dynamically hid all UK-specific fields from the DOM (Postcode, Right-to-Work, etc.), causing the bot to crash when looking for them.
*   **Where the change happened:** `reed_signup.json`
*   **The Fix:** Added an explicit Playwright `select` action to aggressively set the `select[name="country"]` field to `United Kingdom`. This forces the DOM to render all necessary UK fields regardless of the host's geographic location.
*   **Final Outcome:** ✅ Successful

### 5. Strict Phone Formatting Validation
*   **What we tried:** Filling an authentic Slovakian phone number `+421 905 440 035` into the contact field.
*   **Status:** ❌ Failed initially
*   **The Issue:** Because the country was forced to the UK, the phone UI defaulted to the British flag (`+44`). When Playwright typed `+421...` into a field expecting a UK format, Reed's strict frontend validation threw an "Invalid phone number" error.
*   **Where the change happened:** `reed_signup.json`
*   **The Fix:** Swapped the JSON configuration to utilize a standard UK dummy phone number (`07700900077`).
*   **Final Outcome:** ✅ Successful

### 6. The Cookie Banner Overlay Interception
*   **What we tried (Attempt 1):** Clicking the banner using the generic Playwright text selector `text="Reject All"`.
    *   **Status:** ❌ Failed (Strict Mode violations / Timeouts).
*   **What we tried (Attempt 2):** Launching an autonomous AI Browser Subagent to visually crawl the page and figure out the exact DOM structure.
    *   **Status:** ❌ Failed (The subagent got confused by the layout and mistakenly clicked "Manage Preferences" instead of "Reject All").
*   **Where the change happened:** `temp_find_cookie.py` (Investigation) and `reed_signup.json`
*   **The Fix:** Wrote a lightweight DOM-scraper script to crawl the raw HTML and iframes. Discovered Reed uses OneTrust, with the exact selector `#onetrust-reject-all-handler`. Added this with a `force: true` parameter to bypass CSS animation delays.
*   **Final Outcome:** ✅ Successful

### 7. Extraneous Steps on CV Upload
*   **What we tried:** Instructing the bot to look for a "Next" or "Continue" button immediately after uploading `cv.pdf`.
*   **Status:** ❌ Failed initially
*   **The Issue:** The action timed out trying to find the button.
*   **Where the change happened:** `reed_signup.json`
*   **The Fix:** Realized that upon successful file upload, Reed's interface actually auto-redirects the user to the Profile form. We removed the unnecessary button click entirely and replaced it with a simple `wait` for the Profile DOM to load.
*   **Final Outcome:** ✅ Successful

### 8. Opt-Out Checkbox Brittle Selectors
*   **What we tried:** Attempting to target the hidden `<input type="checkbox">` for marketing communications.
*   **Status:** ⚠️ Partially Successful (but brittle)
*   **The Issue:** Modern websites style checkboxes by hiding the native input. Directly targeting the hidden input is brittle and often fails Playwright's actionability checks.
*   **Where the change happened:** `reed_signup.json`
*   **The Fix:** Utilized Playwright's ability to click text nodes. By instructing the bot to click the literal text `"I'd prefer not to receive these emails"`, it clicks the associated `<label>`, which natively and safely toggles the hidden checkbox state.
*   **Final Outcome:** ✅ Successful
### 9. Browser Closed Prematurely / Target Page Lost
*   **What we tried:** Running the full registration flow manually via terminal.
*   **Status:** ❌ Failed in latest run (Step 19)
*   **The Issue:** The bot logged `✗ Step failed: Page.click: Target page, context or browser has been closed`. This typically occurs if the browser window is closed manually by the user during the headed run, or if a sudden navigation/redirection causes Playwright to lose track of the active page context.
*   **Where the change happened:** N/A (Operational issue)
*   **The Fix:** Ensure the browser window is not interacted with or closed during the automated run. If the issue persists due to site redirections, we may need to implement a more robust "wait for navigation" handler.
*   **Final Outcome:** Pending re-run.

### 10. CLI Argument Bug (Unrecognized --config)
*   **What we tried:** Running the bot with `--config` and the new `--data` flag.
*   **Status:** ❌ Failed initially
*   **The Issue:** The command returned `error: unrecognized arguments: --config`. During the implementation of the `--data` override feature, the code that defined the `--config` argument was accidentally overwritten instead of appended to.
*   **Where the change happened:** `form_automator.py` (`main` function)
*   **The Fix:** Restored the `parser.add_argument("--config", ...)` line so that the engine correctly recognizes both the mandatory config file and the optional data overrides.
*   **The Fix:** Restored the `parser.add_argument("--config", ...)` line so that the engine correctly recognizes both the mandatory config file and the optional data overrides.
*   **Final Outcome:** ✅ Successful. (CLI now correctly parses both arguments).

### 11. The "Invisible" Apply Click (OneTrust Overlay Interception)
*   **What we tried:** Using `button:has-text("Apply now")` with `force: true`.
*   **Status:** ❌ Failed (Timeout / Interception)
*   **The Issue:** Even with `force: true`, the click was being intercepted by a nearly invisible OneTrust dark filter (`.onetrust-banner-sdk-dark-filter`). This overlay appears about 2 seconds after the job page loads, physically blocking the browser from interacting with the underlying "Apply" button. Because Playwright saw an intercepting element, it sat waiting for it to disappear, eventually timing out.
*   **Where the change happened:** `reed_apply.json`
*   **The Fix:** 
    - Added a second `optional_click` step specifically for the `#onetrust-reject-all-handler` immediately after navigating to the job URL.
    - Added an explicit **2-second wait** after cookie rejection to allow the dark filter to fully animate away before attempting to click the underlying page.
    - Added an additional **2-second wait** after the "Apply now" click to ensure the React drawer modal is fully rendered before searching for the "Submit" button.
*   **Final Outcome:** ✅ Resolved and verified.

### 12. The Cloudflare Security Wall
*   **What we tried:** Navigating directly to the login or job page.
*   **Status:** ❌ Failed initially (Blocked by "Managed Challenge")
*   **The Issue:** Reed occasionally triggers a Cloudflare "Performing security verification" page. If the bot tries to interact with the page while this challenge is active, it will fail to find any elements and crash.
*   **Where the change happened:** `form_automator.py` (added `wait_for_selector` with `hidden` state) and `reed_apply.json`.
*   **The Fix:** 
    - Implemented a `Bypass Cloudflare` step using `wait_for_selector` on the "security verification" text with `state: "hidden"`.
    - This allows the bot to wait for the challenge to complete naturally (which it often does in `headed` mode) before proceeding.
*   **Final Outcome:** ✅ Successful (Bot now waits for the challenge to clear before acting).

### 13. Complex Screening Questions (Modal)
*   **What we tried:** 
    1. Clicking "Continue" immediately on the application modal. (Failed)
    2. Using simple `label:has-text("Yes/No")`. (Brittle when multiple questions are present).
*   **Status:** ✅ Successful.
*   **The Issue:** Some jobs require answering multiple screening questions (e.g., "Right to Work" and "Years of Experience"). If multiple questions appear on the same modal screen, simple text-based selectors can click the wrong option or miss the second question entirely.
*   **Where the change happened:** `reed_apply.json`.
*   **The Fix:** 
    - Implemented **context-aware selectors** using the `:has-text()` operator.
    - Example: `.screening-questions_question__7lK2j:has-text("experience") label:has-text("Yes")` specifically targets the "Yes" label within the "Experience" question block.
    - Added separate optional steps for both "Experience" (Yes) and "Right to Work" (No) to cover various job requirements.
*   **Final Outcome:** ✅ Robust handling for multi-question modals verified.
