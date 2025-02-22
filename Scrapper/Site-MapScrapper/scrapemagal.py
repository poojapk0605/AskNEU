from collections import defaultdict

import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os
import json
from urllib.parse import urlparse, urljoin
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
SITEMAP_URL = "https://www.northeastern.edu/sitemap_index.xml"
ALLOWED_DOMAIN = "northeastern.edu"
SCRAPED_TEXT_DIR = "scraped_texts"
ERROR_LOG_FILE = "errors.log"
SKIPPED_LOG_FILE = "skipped_pages.log"
MAX_TIMEOUT = 30  # Reduce timeout to prevent long hangs
MAX_RETRIES = 1  # Retry once before skipping

# Block social media and external sites
BLOCKED_SITES = [
    "twitter.com", "facebook.com", "linkedin.com", "reddit.com",
    "instagram.com", "tiktok.com", "youtube.com", "medium.com"
]

# Create directories if they don't exist
os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)

# Create or clear logs
open(ERROR_LOG_FILE, "w").close()
open(SKIPPED_LOG_FILE, "w").close()

# Function to start Selenium WebDriver
def start_webdriver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(MAX_TIMEOUT)  # Set max timeout
    return driver

# Start WebDriver
driver = start_webdriver()
visited_urls = set()

def log_error(message):
    """Logs errors to a separate file."""
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def log_skipped(message):
    """Logs skipped pages to a separate file."""
    with open(SKIPPED_LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def crawl_urls(url, retry=False):
    """Scrapes a webpage, saves its text as a .txt file, and follows internal links."""
    global driver

    main_sites = 2
    main_sites_counter = 0

    if url in visited_urls:
        return
    visited_urls.add(url)

    try:
        print(f"{Fore.CYAN}[INFO] Visiting: {url}{Style.RESET_ALL}")
        driver.get(url)
        time.sleep(3)

        final_url = driver.current_url.lower()
        print(f"{Fore.CYAN}[INFO] Final URL after redirection: {final_url}{Style.RESET_ALL}")

        if not urlparse(final_url).netloc.endswith(ALLOWED_DOMAIN):
            log_skipped(f"[SKIPPED] External Redirect: {final_url}")
            return

        nested_links = extract_internal_links()
        print(f"{Fore.BLUE}[INFO] Found {len(nested_links)} internal links on {url}{Style.RESET_ALL}")

        urls_under_main_site = defaultdict(set)

        for nested_link in nested_links:
            print(f"{Fore.YELLOW}[INFO] Scraping subpage: {nested_link}{Style.RESET_ALL}")
            driver.get(nested_link)
            time.sleep(3)
            urls_under_main_site[nested_link] = extract_internal_links()

        for scrape_url in list(urls_under_main_site.values()):
            for url_scrape in list(scrape_url):
                print(f"{Fore.YELLOW}[INFO] Extracting content from: {url_scrape}{Style.RESET_ALL}")
                driver.get(url_scrape)
                time.sleep(3)
                filename = url_scrape.replace("https://", "").replace("/", "_").replace("?", "_").replace("=", "_")
                save_as_text(url_scrape, filename)

    except Exception as e:
        error_message = str(e).lower()

        # Handle 'Invalid Session ID' Error by Restarting WebDriver
        if "invalid session id" in error_message:
            log_error(f"[ERROR] WebDriver session lost! Restarting Chrome...")
            driver.quit()
            driver = start_webdriver()

            if not retry:
                log_error(f"[RETRYING] Retrying: {url}")
                # crawl(url, retry=True)
            else:
                log_error(f"[FAILED] Could not recover session for: {url}")

        # Handle Timeout Errors & Move On
        elif "read timed out" in error_message or "timeout" in error_message:
            log_error(f"[TIMEOUT] Skipping {url} due to timeout.")

        else:
            log_error(f"[ERROR] Unable to process {url}: {e}")

def extract_internal_links():
    """Extracts all valid internal links from a webpage."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()
    base_url = driver.current_url

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        href = urljoin(base_url, href)

        parsed_url = urlparse(href)
        domain = parsed_url.netloc.lower()

        if domain.endswith(ALLOWED_DOMAIN) and domain.count(".") >= 2:
            if any(blocked in href for blocked in BLOCKED_SITES):
                continue
            links.add(href)

    print(f"{Fore.GREEN}[INFO] Extracted {len(links)} links from {driver.current_url}{Style.RESET_ALL}")
    return links

def save_as_text(url, filename):
    """Extracts text from a webpage and saves it as a .txt file."""
    try:
        txt_path = os.path.join(SCRAPED_TEXT_DIR, filename + ".txt")

        if os.path.exists(txt_path):
            log_skipped(f"[SKIPPED] Text file already exists: {txt_path}")
            return

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style"]):
            element.decompose()

        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())  # Remove empty lines

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n{text}")

        print(f"{Fore.GREEN}[SUCCESS] Saved Text: {txt_path}{Style.RESET_ALL}")

    except Exception as e:
        log_error(f"[ERROR] Failed to save text for {url}: {e}")

try:
    sitemap_links = [
        # "https://www.northeastern.edu/3-typical-co-op-schedules/",  # Test link
        "https://www.northeastern.edu/sitemap.xml",
        "https://studenthealthplan.northeastern.edu/sitemap.xml",
        "https://uhcs.northeastern.edu/sitemap_index.xml",
        "https://graduate.northeastern.edu/sitemap_index.xml",
        "https://international.northeastern.edu/sitemap_index.xml",
        "https://studentfinance.northeastern.edu/sitemap_index.xml",
        "https://recreation.northeastern.edu/wp-sitemap.xml",
        "https://studentemployment.northeastern.edu/wp-sitemap.xml",
        "https://housing.northeastern.edu/sitemap_index.xml",
        "https://news.northeastern.edu/sitemap_index.xml",
        "https://coe.northeastern.edu/sitemap_index.xml",
        "https://www.khoury.northeastern.edu/sitemap_index.xml",
        "https://cps.northeastern.edu/sitemap_index.xml",
        "https://ece.northeastern.edu/sitemap_index.xml",
        "https://mie.northeastern.edu/sitemap_index.xml",
        "https://its.northeastern.edu/wp-sitemap.xml",
        "https://alumni.northeastern.edu/sitemap_index.xml",
        "https://core.northeastern.edu/wp-sitemap.xml",
        "https://geo.northeastern.edu/sitemap_index.xml",
        "https://cssh.northeastern.edu/sitemap_index.xml"
    ]

    print(f"{Fore.CYAN}[INFO] Found {len(sitemap_links)} real pages to scrape.{Style.RESET_ALL}")

    for url in sitemap_links:
        crawl_urls(url)

except Exception as e:
    log_error(f"[FATAL ERROR] {e}")

finally:
    driver.quit()

print(f"{Fore.GREEN}[INFO] Scraping complete. Check the 'scraped_texts' directory.{Style.RESET_ALL}")
