# Sluzby Zamestnanosti Scraper - Wiki

## 🎯 Project Goal
To provide a reliable, high-speed way to monitor and extract job listings from the Slovakian government job portal ([sluzbyzamestnanosti.gov.sk](https://www.sluzbyzamestnanosti.gov.sk)).

## ✅ Capabilities

### ⚡ Performance & Concurrency
*   **Async Engine**: Built with `asyncio` and `async_playwright`.
*   **Parallel Processing**: Scales scraping speed by opening multiple isolated browser contexts (workers).
*   **Semaphore Management**: Uses `asyncio.Semaphore` to throttle requests and prevent server blocking.
*   **Sample Concurrency Logic**:
    ```python
    semaphore = asyncio.Semaphore(concurrency)
    async def sem_scrape(url):
        async with semaphore:
            return await scrape_job_detail(browser, url, storage_state)
    ```

### 🧠 Intelligent Automation
*   **Deduplication**: Automatically halts collection if 2 consecutive URLs match existing entries in `jobs.csv`.
*   **Storage State**: Shares a single authentication session across all workers using `context.storage_state()`.
*   **Data Extraction**:
    *   **Email Scraper**: `re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text)`
    *   **Summary List Parser**: Dynamically maps all GOV.UK style summary rows into CSV columns.

### 📊 Data Integrity
*   **Incremental Merging**: Prepends new findings to historical data.
*   **Unique Headers**: Automatically updates the CSV header if new data fields are discovered on the portal.

## ⚙️ Technical Details

*   **Runtime**: Python 3.9+
*   **Key Libraries**: `playwright`, `asyncio`, `csv`, `re`, `json`.
*   **Target Selectors**:
    *   Search Links: `a.govuk-link[href*='/pracovna-ponuka/']`
    *   Next Page: `#next-page` (Ajax loader)

## 📂 Project Structure
*   `sluzby_scraper.py`: Core logic with async task scheduling.
*   `sluzby_config.json`: Externalized settings and credentials.
*   `jobs.csv`: Master dataset (UTF-8 encoded).

## 🚀 Future Improvements
*   Automatic CV application logic using PDF upload.
*   Real-time notifications via Telegram API.
*   Dockerization for cloud deployment.
