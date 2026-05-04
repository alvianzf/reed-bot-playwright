import csv
import asyncio
import re
import json
from pathlib import Path
from playwright.async_api import async_playwright

def load_config():
    config_path = Path("sluzby_config.json")
    if not config_path.exists():
        raise FileNotFoundError("sluzby_config.json not found")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

async def scrape_job_detail(browser, url, storage_state_path, settings, index, total):
    print(f"[{index}/{total}] Scraping {url}")
    # Create a new context for each job to avoid session pollution and for isolation
    context = await browser.new_context(storage_state=storage_state_path)
    page = await context.new_page()
    
    job_data = {}
    try:
        await page.goto(url, timeout=settings.get("timeout", 60000))
        await page.wait_for_selector("h1.govuk-heading-xl", timeout=settings.get("detail_timeout", 20000))
        
        name = await page.inner_text("h1.govuk-heading-xl")
        company = await page.evaluate("""() => {
            const h1 = document.querySelector('h1.govuk-heading-xl');
            const p = h1 ? h1.nextElementSibling : null;
            return p && p.classList.contains('govuk-body') ? p.innerText.trim() : '';
        }""")

        # Extract emails
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', await page.inner_text("body")))
        email_str = "; ".join(emails)

        job_data = {
            "Name": name.strip(), 
            "URL": url, 
            "Email": email_str,
            "Company Name": company.strip()
        }
        
        summary_data = await page.evaluate("""() => {
            const data = {};
            const rows = document.querySelectorAll('.govuk-summary-list__row');
            rows.forEach(row => {
                const key = row.querySelector('.govuk-summary-list__key');
                const val = row.querySelector('.govuk-summary-list__value');
                if (key && val) data[key.innerText.trim()] = val.innerText.trim().replace(/\\n/g, ' ');
            });
            return data;
        }""")
        job_data.update(summary_data)
        
        if "Miesto výkonu práce" in job_data:
            loc = job_data["Miesto výkonu práce"].replace("place", "").replace("Google maps", "").strip()
            job_data["Miesto výkonu práce"] = re.sub(r'\\s+', ' ', loc)
        
        print(f"  ✓ Scraped: {name.strip()[:30]}")
    except Exception as e:
        print(f"  ✗ Error {url}: {e}")
    
    await context.close()
    return job_data

async def scrape_sluzby():
    config = load_config()
    settings = config.get("settings", {})
    creds = config.get("credentials", {})
    search = config.get("search", {})
    filters = search.get("filters", {})
    concurrency = settings.get("concurrency", 5)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not settings.get("headed", True))
        
        # Initial login context
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to homepage...")
        await page.goto("https://www.sluzbyzamestnanosti.gov.sk")
        
        # Accept cookies
        try:
            await page.click("button:has-text('Súhlasím')", timeout=5000)
        except:
            pass

        # Login
        print(f"Logging in as {creds.get('username')}...")
        await page.click("#loginBtn1")
        await page.wait_for_selector("#username", timeout=30000)
        await page.fill("#username", creds.get("username", ""))
        await page.fill("#password", creds.get("password", ""))
        await page.click("#kc-login")
        
        await page.wait_for_selector("text=Vitajte, Ján", timeout=30000)
        print("Logged in successfully.")

        # Save storage state
        storage_state_path = "storage_state.json"
        await context.storage_state(path=storage_state_path)

        # Search
        profession = search.get("profession", "Zvárač kovov")
        print(f"Searching for '{profession}'...")
        await page.fill("#nazovProfesie", profession)
        try:
            await page.wait_for_selector("ul#nazovProfesie__listbox li", timeout=5000)
            await page.click("ul#nazovProfesie__listbox li:first-child")
        except:
            pass
        await page.click("button.idsk-search-component__button")

        # Filters
        print("Applying filters...")
        await page.wait_for_selector("#paging-data", timeout=30000)
        if filters.get("location"):
            try: await page.check("#lokalita0")
            except: pass
        
        if filters.get("suitable_for_foreigners"):
            try:
                expander = page.locator("button:has-text('Miesto vhodné pre')")
                if await expander.count() > 0 and await expander.get_attribute("aria-expanded") == "false":
                    await expander.click()
                await page.locator("label:has-text('vhodné pre cudzinca')").click()
            except: pass
        
        await asyncio.sleep(3)
        await page.wait_for_selector("#paging-data", timeout=30000)
        
        # Load existing for deduplication
        existing_urls = []
        if Path("jobs.csv").exists():
            try:
                with open("jobs.csv", "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_urls = [row["URL"] for row in reader if "URL" in row]
            except: pass

        # Collect links
        print("Finding job links across all pages...")
        job_urls = []
        page_num = 1
        consecutive_seen_count = 0
        stop_pagination = False
        
        while not stop_pagination:
            print(f"  - Reading page {page_num}...")
            await page.wait_for_selector("#paging-data", timeout=30000)
            await asyncio.sleep(2)
            
            links = await page.query_selector_all("a.govuk-link.govuk-\\!-font-size-24.govuk-\\!-font-weight-bold")
            if not links: links = await page.query_selector_all("a.govuk-link[href*='/pracovna-ponuka/']")
            
            new_on_page = 0
            for link in links:
                url = await link.get_attribute("href")
                if not url: continue
                if not url.startswith("http"): url = "https://www.sluzbyzamestnanosti.gov.sk" + url
                
                if url in existing_urls:
                    consecutive_seen_count += 1
                    if consecutive_seen_count >= 2:
                        stop_pagination = True
                        break
                else:
                    consecutive_seen_count = 0
                    if url not in job_urls:
                        job_urls.append(url)
                        new_on_page += 1
            
            if stop_pagination: break
            print(f"    Added {new_on_page} new links.")
            
            next_button = page.locator("#next-page")
            if await next_button.count() > 0 and await next_button.is_visible():
                await next_button.scroll_into_view_if_needed()
                await next_button.click()
                page_num += 1
                await asyncio.sleep(3)
            else: break
            
        print(f"Found {len(job_urls)} new jobs. Starting concurrent scraping (max {concurrency})...")
        await context.close() # Close initial context, will use storage state for workers

        # Concurrent scraping
        semaphore = asyncio.Semaphore(concurrency)
        async def sem_scrape(url, idx, total):
            async with semaphore:
                res = await scrape_job_detail(browser, url, storage_state_path, settings, idx, total)
                await asyncio.sleep(settings.get("wait_between_jobs", 500) / 1000)
                return res

        tasks = [sem_scrape(url, i+1, len(job_urls)) for i, url in enumerate(job_urls)]
        jobs_data = await asyncio.gather(*tasks)
        jobs_data = [j for j in jobs_data if j] # Filter out failures

        # Merge and Write
        if jobs_data:
            existing_data = []
            if Path("jobs.csv").exists():
                try:
                    with open("jobs.csv", "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        existing_data = list(reader)
                except: pass
            
            final_data = jobs_data + existing_data
            all_keys = set()
            for job in final_data: all_keys.update(job.keys())
            priority = ["Name", "URL", "Email", "Company Name"]
            fieldnames = priority + sorted([k for k in all_keys if k not in priority])

            with open("jobs.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(final_data)
            print(f"Saved {len(jobs_data)} new jobs (Total: {len(final_data)}) to jobs.csv")
        else:
            print("No new jobs found.")

        await browser.close()
        if Path(storage_state_path).exists(): Path(storage_state_path).unlink()

if __name__ == "__main__":
    asyncio.run(scrape_sluzby())
