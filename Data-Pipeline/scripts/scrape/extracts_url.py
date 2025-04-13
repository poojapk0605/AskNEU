import os
import random
import time
import pandas as pd
from urllib.parse import urlparse, urljoin, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
START_URL = "https://www.recreation.northeastern.edu/"
ALLOWED_DOMAIN = "recreation.northeastern.edu"
OUTPUT_DIR = "scraped_urls"
EXCEL_FILE = os.path.join(OUTPUT_DIR, "all_urls.xlsx")
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


# Remove URL fragments
def remove_fragment(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


# Extract internal links
def extract_internal_links_html(page_source: str, base_url: str):
    soup = BeautifulSoup(page_source, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        full_url = urljoin(base_url, href)
        full_url = remove_fragment(full_url)
        parsed = urlparse(full_url)
        if parsed.netloc.endswith(ALLOWED_DOMAIN) and is_allowed(full_url):
            links.add(full_url)
    return links


# Crawl and collect URLs
def crawl_for_urls(start_url: str):
    if not is_allowed(start_url):
        print(f"Starting URL {start_url} is disallowed by robots.txt. Exiting.")
        return

    driver = start_webdriver()
    visited_urls = set()
    all_urls = set()
    stack = [start_url]

    try:
        while stack:
            url = stack.pop()
            if url in visited_urls:
                continue
            visited_urls.add(url)
            all_urls.add(url)

            print(f"Visiting: {url}")
            time.sleep(random.randint(MIN_DELAY, MAX_DELAY))

            try:
                driver.get(url)
                time.sleep(1)
                new_links = extract_internal_links_html(driver.page_source, driver.current_url)
                for link in new_links:
                    if link not in visited_urls:
                        stack.append(link)
            except (TimeoutException, WebDriverException) as e:
                print(f"Failed to load {url}: {e}")
                continue

        # Save to Excel
        df = pd.DataFrame(list(all_urls), columns=["URL"])
        df.to_excel(EXCEL_FILE, index=False)
        print(f"Saved {len(all_urls)} URLs to {EXCEL_FILE}")

    finally:
        driver.quit()


# Main execution
if __name__ == "__main__":
    crawl_for_urls(START_URL)