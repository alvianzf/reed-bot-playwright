# Sluzby Zamestnanosti Job Scraper (Async Edition)

A high-performance, concurrent Playwright-based automation tool for the Slovakian "Služby zamestnanosti" (gov.sk) job portal.

## 🚀 Features

*   **Concurrent Scraping**: Process multiple job pages simultaneously using `asyncio` (configurable concurrency).
*   **Intelligent Deduplication**: Automatically stops when it hits 2 consecutive jobs already in your CSV.
*   **Deep Data Extraction**: Extracts every available field, including **email addresses** via regex scanning.
*   **Session Persistence**: Logs in once and shares the authentication state across all concurrent workers.
*   **Incremental Updates**: Prepends new jobs to `jobs.csv` to keep your dataset up-to-date and chronological.

## 🛠 Setup

1. **Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install playwright
   playwright install chromium
   ```

2. **Configuration:**
   Edit [sluzby_config.json](file:///Users/azfaturrahman/Projects/devshore/reed-bot/sluzby_config.json) to set your credentials and search parameters.

   **Sample `sluzby_config.json`:**
   ```json
   {
     "settings": {
       "headed": true,
       "concurrency": 5,
       "timeout": 60000
     },
     "credentials": {
       "username": "YourUsername",
       "password": "YourPassword"
     },
     "search": {
       "profession": "Zvárač kovov",
       "filters": {
         "location": "Slovensko",
         "suitable_for_foreigners": true
       }
     }
   }
   ```

## 🚀 How to Run

```bash
source venv/bin/activate
python sluzby_scraper.py
```

**Output:** `jobs.csv` (Email column prioritized).

## 📂 Project Structure

*   `sluzby_scraper.py`: The async automation engine.
*   `sluzby_config.json`: Centralized settings and credentials.
*   `jobs.csv`: Your master job dataset.
*   `wiki/`: Technical deep-dives and documentation.

## 📜 License
MIT
