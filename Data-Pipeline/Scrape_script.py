import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import re
import time
import random
import logging
import threading
from datetime import datetime

# Configuration
BASE_DIR = "/opt/airflow/data"  # Adjust based on Airflow environment
SCRAPED_TEXT_DIR = os.path.join(BASE_DIR, "scraped_texts")
SCRAPED_PDF_DIR = os.path.join(BASE_DIR, "scraped_pdfs")
URL_EXCEL_PATH = os.path.join(BASE_DIR, "config/urls.xlsx")
LOG_DIR = os.path.join(BASE_DIR, "logs")
MAX_THREADS = min(4, os.cpu_count() or 1)
MAX_RETRIES = 3
MIN_DELAY, MAX_DELAY = 1, 3
USE_PROXIES = False  # Toggle proxy usage
PROXIES = [
    "http://176.105.220.74:80",
    "http://45.32.123.156:80",
    # Add more proxies as needed
]
PDF_EXTENSIONS = ('.pdf',)
SKIP_EXTENSIONS = ('.jpg', '.png', '.gif', '.jpeg', '.css', '.js')

# Ensure directories exist
os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
os.makedirs(SCRAPED_PDF_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_info(msg): logger.info(msg)
def log_error(msg): logger.error(msg)
def log_success(msg): logger.info(msg)
def log_skipped(msg): logger.info(msg)

# Thread-local storage for WebDriver
thread_local = threading.local()
visited_urls = set()
visited_urls_lock = threading.Lock()

# Helper Functions
def start_webdriver(proxy=None):
    """Initialize a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0")
    if proxy and USE_PROXIES:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def url_to_filename(url):
    """Convert a URL to a safe filename."""
    parsed = urlparse(url)
    netloc = parsed.netloc.replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = 'index'
    return f"{netloc}_{path}"

def download_single_pdf(url, base_dir=SCRAPED_PDF_DIR):
    """Download a single PDF from a URL."""
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        filename = "".join(x for x in filename if x.isalnum() or x in "._-").rstrip()
        filename = filename[:255]
        pdf_path = os.path.join(base_dir, filename)
        if os.path.exists(pdf_path):
            log_skipped(f"PDF already exists: {pdf_path}")
            return
        response = requests.get(url, stream=True, timeout=10)
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type:
            log_skipped(f"Not a PDF: {url}")
            return
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log_success(f"Downloaded PDF: {pdf_path}")
        log_info(f"Original URL: {url}")
    except Exception as e:
        log_error(f"Failed to download PDF: {url} - {e}")

def save_as_text(driver, url, filename):
    """Extract text from a webpage and save as a .txt file."""
    try:
        txt_path = os.path.join(SCRAPED_TEXT_DIR, filename + ".txt")
        if os.path.exists(txt_path):
            log_skipped(f"Text file already exists: {txt_path}")
            return
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
        unique_containers = set()
        content = []
        processed_texts = set()
        containers = soup.find_all(["ul", "ol", "div", "section"])
        for container in containers:
            container_hash = hash(container.get_text(strip=True, separator=' '))
            if container_hash in unique_containers:
                continue
            unique_containers.add(container_hash)
            for elem in container.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
                text = elem.get_text(strip=True)
                if not text or text in processed_texts:
                    continue
                processed_texts.add(text)
                if elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    content.append(f"\n[{text}]\n")
                elif elem.name == "li":
                    content.append(f"- {text}")
                else:
                    content.append(text)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"URL (Source): {url}\n")
            f.write(f"Scraped on: {datetime.now()}\n\n")
            f.write("\n".join(content))
        log_success(f"Saved Text: {txt_path}")
    except Exception as e:
        log_error(f"Failed to save text for {url}: {e}")

def download_pdfs_from_page(driver, url, base_dir=SCRAPED_PDF_DIR):
    """Download all PDFs linked from a webpage."""
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.lower().endswith('.pdf'):
                full_pdf_url = urljoin(url, href)
                pdf_links.append(full_pdf_url)
        pdf_links = list(set(pdf_links))
        log_info(f"Found {len(pdf_links)} unique PDF links on {url}")
        for pdf_url in pdf_links:
            download_single_pdf(pdf_url, base_dir)
    except Exception as e:
        log_error(f"Failed to process PDFs on {url}: {e}")

def extract_internal_links_html(html_content, base_url, allowed_domain):
    """Extract internal links from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href.split('#')[0])
        parsed = urlparse(absolute_url)
        domain = parsed.netloc.lower()
        if (domain == allowed_domain or domain.endswith(f".{allowed_domain}")) and not parsed.path.lower().endswith(SKIP_EXTENSIONS):
            links.add(absolute_url)
    return links

def crawl_dfs_stack(start_url: str, allowed_domain: str):
    """Crawl a website starting from start_url using DFS."""
    stack = [(start_url, 0, PROXIES[:])]
    thread_local.driver = start_webdriver(PROXIES[0] if PROXIES and USE_PROXIES else None)
    try:
        while stack:
            url, fail_count, proxies = stack.pop()
            with visited_urls_lock:
                if url in visited_urls:
                    continue
                visited_urls.add(url)
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if not (domain == allowed_domain or domain.endswith(f".{allowed_domain}")):
                log_skipped(f"External domain: {url} (allowed: {allowed_domain})")
                continue
            path_lower = parsed.path.lower()
            if path_lower.endswith(PDF_EXTENSIONS):
                download_single_pdf(url)
                continue
            if path_lower.endswith(SKIP_EXTENSIONS):
                log_skipped(f"Ignored extension: {url}")
                continue
            attempt_proxy = proxies[0] if proxies else None
            try:
                log_info(f"Visiting: {url} (fail_count={fail_count}, proxy={attempt_proxy})")
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                thread_local.driver.get(url)
                content_lower = thread_local.driver.page_source.lower()
                if "verify you are human" in content_lower or "access denied" in content_lower:
                    raise Exception("Blocked/AccessDenied")
                filename = url_to_filename(url)
                save_as_text(thread_local.driver, url, filename)
                download_pdfs_from_page(thread_local.driver, url)
                new_links = extract_internal_links_html(thread_local.driver.page_source, url, allowed_domain)
                with visited_urls_lock:
                    for link in new_links:
                        if link not in visited_urls:
                            stack.append((link, 0, proxies[:]))
            except (TimeoutException, WebDriverException, Exception) as e:
                log_error(f"Failed: {url} - {e} (fail_count={fail_count}, proxy={attempt_proxy})")
                if fail_count + 1 < MAX_RETRIES and proxies:
                    remaining_proxies = proxies[1:] if len(proxies) > 1 else []
                    new_proxy = remaining_proxies[0] if remaining_proxies else None
                    log_info(f"Rotating to proxy: {new_proxy or 'None'}")
                    thread_local.driver.quit()
                    thread_local.driver = start_webdriver(new_proxy)
                    stack.append((url, fail_count + 1, remaining_proxies))
                else:
                    log_error(f"Skipping {url} after {MAX_RETRIES} attempts.")
            finally:
                thread_local.driver.quit()
                thread_local.driver = start_webdriver(attempt_proxy if proxies else None)
    finally:
        thread_local.driver.quit()

def worker(start_urls_chunk):
    """Process a chunk of starting URLs in a thread."""
    for start_url in start_urls_chunk:
        try:
            parsed = urlparse(start_url)
            allowed_domain = parsed.netloc.lower()
            log_info(f"Starting crawl for: {start_url} (Domain: {allowed_domain})")
            crawl_dfs_stack(start_url, allowed_domain)
        except Exception as e:
            log_error(f"Worker failed for {start_url}: {e}")

def main():
    """Main function to orchestrate the scraping process."""
    try:
        df = pd.read_excel(URL_EXCEL_PATH)
        if 'URL' not in df.columns:
            raise ValueError("Excel file must contain a 'URL' column")
        start_urls = df['URL'].dropna().tolist()
        if not start_urls:
            log_error("No URLs found in Excel file.")
            return
        chunk_size = max(1, len(start_urls) // MAX_THREADS)
        url_chunks = [start_urls[i:i + chunk_size] for i in range(0, len(start_urls), chunk_size)]
        threads = []
        for chunk in url_chunks:
            t = threading.Thread(target=worker, args=(chunk,))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        log_info("Scraping completed successfully.")
    except KeyboardInterrupt:
        log_info("Scraping interrupted by user.")
    except Exception as e:
        log_error(f"Scraping failed: {e}")

if __name__ == "__main__":
    main()