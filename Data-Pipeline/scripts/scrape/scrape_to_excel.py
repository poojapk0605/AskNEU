import os
import random
import time
import pandas as pd
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
INPUT_EXCEL = "scraped_urls/all_urls.xlsx"
OUTPUT_DIR = "scraped_text_excels"
MAX_TIMEOUT = 30
MIN_DELAY, MAX_DELAY = 3, 7
BOT_USER_AGENT = "MyEthicalScraperBot/1.0"  # Custom user-agent for your bot

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# User-Agents for rotation (for browser emulation, not robots.txt)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
]


# Check if URL is allowed by robots.txt
def is_allowed(url, user_agent=BOT_USER_AGENT):
    robots_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()  # Fetches and parses robots.txt
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            print(f"Disallowed by robots.txt: {url}")
        return allowed
    except Exception as e:
        print(f"Error fetching robots.txt for {url}: {e}")
        return True  # Default to allow if robots.txt is inaccessible


# Setup Selenium WebDriver
def start_webdriver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1024,768")
    prefs = {"profile.managed_default_content_settings.images": 2}  # Disable images
    options.add_experimental_option("prefs", prefs)
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"--user-agent={user_agent}")
    driver_ = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver_.set_page_load_timeout(MAX_TIMEOUT)
    return driver_


# Scrape text from a URL
def scrape_text(url: str, driver):
    if not is_allowed(url):
        return {"headings": [], "paragraphs": []}  # Skip if disallowed

    try:
        print(f"Scraping: {url}")
        driver.get(url)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()

        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]) if
                    h.get_text(strip=True)]
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]

        return {"headings": headings, "paragraphs": paragraphs}
    except (TimeoutException, WebDriverException) as e:
        print(f"Failed to scrape {url}: {e}")
        return {"headings": [], "paragraphs": []}


# Process URLs and save to Excel
def process_urls():
    driver = start_webdriver()
    try:
        # Read URLs from Excel
        df = pd.read_excel(INPUT_EXCEL)
        urls = df["URL"].tolist()

        # Dictionary to group content by main URL (path-based)
        url_content = {}

        for url in urls:
            time.sleep(random.randint(MIN_DELAY, MAX_DELAY))
            content = scrape_text(url, driver)

            # Use the path as the key for grouping (e.g., /about/ or /fitness/)
            parsed = urlparse(url)
            path_key = parsed.path.split('/')[1] if parsed.path else "root"  # e.g., "about" or "root" for homepage
            if path_key not in url_content:
                url_content[path_key] = []
            url_content[path_key].append({"URL": url, "Headings": "; ".join(content["headings"]),
                                          "Paragraphs": "; ".join(content["paragraphs"])})

        # Save each main URL group to a separate Excel file
        for path_key, contents in url_content.items():
            output_file = os.path.join(OUTPUT_DIR, f"{path_key or 'homepage'}_content.xlsx")
            df_content = pd.DataFrame(contents)
            df_content.to_excel(output_file, index=False)
            print(f"Saved content for {path_key or 'homepage'} to {output_file}")

    finally:
        driver.quit()


# Main execution
if __name__ == "__main__":
    process_urls()