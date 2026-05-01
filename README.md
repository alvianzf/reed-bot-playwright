# Reed.co.uk Automation Bot (a.k.a. The "I'm Too Lazy to Click" Engine)

Congratulations. You've found a way to automate the soul-crushing experience of applying for jobs on Reed.co.uk. Because why spend 5 minutes of your precious life clicking "Apply" when you can spend 5 hours building, debugging, and babysitting a Python script that does it for you?

## 🤡 What is this?
This is a Playwright-based automation engine that pretends to be a human named Alvian (or whoever you decide to be today) to navigate the labyrinthine React-infested waters of Reed.co.uk. 

It can:
- **Register** a new account (and gracefully handle Reed realizing you're from Indonesia).
- **Sign In** (assuming Cloudflare doesn't decide you're a threat to national security).
- **Apply to Jobs** (even the ones that ask annoying screening questions).

## 🛠 Setup (If you can handle a terminal)

1. **Clone this masterpiece:**
   ```bash
   git clone https://github.com/alvianzf/reed-scraper-playwright.git
   cd reed-bot
   ```

2. **Create a virtual environment (don't pollute your system):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Mac/Linux, because Windows is a different kind of pain
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Data Prep:**
   Open `reed_apply.json`, `reed_signin.json`, and `reed_signup.json`. Replace the `[EMAIL]` and `[PASSWORD]` placeholders with your actual credentials. Or keep them as is and wonder why it doesn't work. Your choice.
   Also, put your `cv.pdf` in the root folder. The bot isn't a magician; it needs something to upload.

## 🚀 How to Run (Hold my coffee)

### 1. The "I need an account" run:
```bash
./venv/bin/python form_automator.py --config reed_signup.json
```

### 2. The "I just want to sign in" run:
```bash
./venv/bin/python form_automator.py --config reed_signin.json
```

### 3. The "Get me a job" run:
```bash
# Apply to a specific job because you're picky
./venv/bin/python form_automator.py --config reed_apply.json --data job_url="https://www.reed.co.uk/jobs/some-cool-job/123456"
```

## 🧩 The JSON Logic (How to tell the bot what to do)

Each `.json` file is basically a script for the bot. If you mess up the syntax, it will cry (and by cry, I mean crash with a traceback that makes no sense).

### The Big Three:
1. **`settings`**: Where you tell it to run `headed` (so you can watch it fail) and `stop_on_error` (so it stops when it fails).
2. **`data`**: Your variables. Use `{{variable_name}}` in your steps to inject these. It's like Mail Merge, but for job hunting.
3. **`steps`**: The actual to-do list.

### Available Actions (The Bot's Vocabulary):
- `navigate`: Go to a URL. Simple. Even a bot can do this.
- `fill`: Type text into a box. Requires a `selector` (CSS magic) and a `value`.
- `click`: Smash a button. Supports `force: true` for when React is being difficult and `delay: 100` to pretend it's thinking.
- `optional_click`: Try to click something (like a cookie banner). If it's not there, the bot just shrugs and moves on.
- `wait`: Do absolutely nothing for `ms` milliseconds. Highly recommended.
- `wait_for_selector`: Wait for something to appear (or disappear, like Cloudflare challenges). 
- `assert_url_contains`: Panic if the URL doesn't have the right keywords after a step.

## ⚠️ Important Warnings (Read these, or don't)

- **Cloudflare is watching:** If you see a screen saying "Performing security verification," don't panic. The bot will wait. If it asks you to click a checkbox, do it. The bot is smart, but it's not "solve-a-captcha-in-0.1s" smart.
- **React Race Conditions:** This code is basically held together by `wait` steps. If the bot clicks too fast and Reed ignores it, increase the `ms` values in the JSON files. Welcome to modern web development.
- **Permission Denied:** If your terminal says `zsh: permission denied`, it's probably because I accidentally forgot to tell you to `chmod +x` something, or you're just having a bad day.

## 📂 Structure
- `form_automator.py`: The brains (if you can call it that).
- `reed_*.json`: The instructions.
- `wiki/`: Where I keep the logs of all the times this failed before it worked.

## 📜 License
Probably MIT. Honestly, if you can make this work better than I did, you deserve a medal. Or a job. Which is why you're here, right?

