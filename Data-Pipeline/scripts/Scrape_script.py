import os
import sys
import time
import random
import requests
import re
from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options

# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

###############################################################################
#                               CONFIGURATION                                 #
###############################################################################
init(autoreset=True)  # For colored logs

START_URL = "https://www.recreation.northeastern.edu/"  # We'll parse as HTML
ALLOWED_DOMAIN = "recreation.northeastern.edu"

SCRAPED_TEXT_DIR = "/opt/airflow/data/scraped_texts"
SCRAPING_SCRIPT_PATH = "/opt/airflow/scripts/Scrape_script.py"
UNITTEST_SCRIPT_PATH = "/opt/airflow/tests/test_scraper.py"
SCRAPED_PDF_DIR = "/opt/airflow/data/scraped_pdfs"
ERROR_LOG_FILE = "/opt/airflow/logs/errors.log"
SKIPPED_LOG_FILE = "/opt/airflow/logs/skipped_pages.log"

# os.mkdir(SCRAPED_TEXT_DIR, exist_ok=True)
# os.mkdir(SCRAPED_PDF_DIR, exist_ok=True)
os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
os.makedirs(SCRAPED_PDF_DIR, exist_ok=True)

MAX_TIMEOUT = 30  # page load timeout
MAX_RETRIES = 4  # total attempts per URL
MIN_DELAY, MAX_DELAY = 3, 7  # random delay (seconds)
PROXY_ROTATE_THRESHOLD = 4  # rotate proxy after 4 failures

# Proxies for rotation
PROXIES = [
    "http://203.30.191.189:80",
    "http://117.102.119.150:8080",
    "http://190.61.88.147:8080",
    "http://200.54.194.13:53281",
]

# User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
]

# File types to skip
SKIP_EXTENSIONS = (".zip", ".mp4", ".avi", ".gz", ".tar", ".7z", ".iso")
# PDF or DOCX to save
PDF_EXTENSIONS = (".pdf", ".docx")

# Social or external sites to block
BLOCKED_SITES = [
    "twitter.com",
    "facebook.com",
    "linkedin.com",
    "reddit.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "medium.com",
]

###############################################################################
#                           SETUP & LOGGING                                   #
###############################################################################
os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
os.makedirs(SCRAPED_PDF_DIR, exist_ok=True)
open(ERROR_LOG_FILE, "w").close()
open(SKIPPED_LOG_FILE, "w").close()


def log_error(message):
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def log_skipped(message):
    with open(SKIPPED_LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def log_success(message):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def log_info(message):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")


###############################################################################
#                         SELENIUM DRIVER & PROXY LOGIC                       #
###############################################################################
driver = None
current_proxy = None
remote_webdriver = "remote_chromedriver"  # Airflow connection name


def start_webdriver(proxy=None):
    """Creates a new Selenium WebDriver with optional proxy and random user-agent.
    Disables images for faster page loads."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1024,768")

    # Disable images
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    # Rotate user-agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f"--user-agent={user_agent}")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    # driver_ = webdriver.Chrome(
    #     service=Service(ChromeDriverManager().install()), options=options
    # )

    driver_ = webdriver.Remote(f"{remote_webdriver}:4444/wd/hub", options=options)

    driver_.set_page_load_timeout(MAX_TIMEOUT)
    return driver_


def rotate_proxy():
    """Rotate to a random proxy (no validation)."""
    global driver, current_proxy
    if driver:
        driver.quit()
    new_proxy = random.choice(PROXIES)
    log_info(f"[INFO] Rotating Proxy to: {new_proxy}")
    driver = start_webdriver(new_proxy)
    current_proxy = new_proxy


def close_and_new_driver():
    """Close current driver and open a new one with the same proxy."""
    global driver, current_proxy
    if driver:
        driver.quit()
    driver = start_webdriver(current_proxy)


###############################################################################
#                            FILE SAVING FUNCTIONS                            #
###############################################################################
def save_pdf_or_doc(url: str):
    """Download PDF or DOCX to 'scraped_pdfs' folder."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    save_path = os.path.join(SCRAPED_PDF_DIR, filename)
    if os.path.exists(save_path):
        log_skipped(f"[SKIPPED] Already Scraped: {url}")
        return
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            log_success(f"[SUCCESS] Downloaded: {url}")
        else:
            log_error(f"[ERROR] Failed to download {url} (status={resp.status_code})")
    except Exception as e:
        log_error(f"[ERROR] Could not download {url}: {e}")


def save_text_file(url: str, page_source: str):
    """Saves text content with [HEADINGS] and [PARAGRAPHS], removing headers/footers."""
    import re
    from bs4 import BeautifulSoup

    filename = re.sub(r"[^\w\-]", "_", url.replace("https://", "")) + ".txt"
    txt_path = os.path.join(SCRAPED_TEXT_DIR, filename)

    if os.path.exists(txt_path):
        log_skipped(f"[SKIPPED] Already Scraped: {url}")
        return

    soup = BeautifulSoup(page_source, "html.parser")
    for element in soup(["script", "style", "header", "footer", "nav"]):
        element.decompose()

    headings = [
        h.get_text(strip=True)
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if h.get_text(strip=True)
    ]
    paragraphs = [
        p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)
    ]

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(
            f"URL: {url}\n\n[HEADINGS]\n"
            + "\n".join(headings)
            + "\n\n[PARAGRAPHS]\n"
            + "\n\n".join(paragraphs)
        )

    log_success(f"[SUCCESS] Scraped: {url}")


###############################################################################
#                             DFS CRAWL LOGIC                                 #
###############################################################################
visited_urls = set()


def remove_fragment(url: str) -> str:
    """Removes #fragment from a URL."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def extract_internal_links_html(page_source: str, base_url: str):
    """Extract valid internal links from HTML content."""
    soup = BeautifulSoup(page_source, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        full_url = urljoin(base_url, href)
        full_url = remove_fragment(full_url)
        # skip mailto or blocked
        if full_url.startswith("mailto:") or any(b in full_url for b in BLOCKED_SITES):
            continue
        parsed = urlparse(full_url)
        if parsed.netloc.endswith(ALLOWED_DOMAIN):
            links.add(full_url)
    return links


def crawl_dfs_stack(start_url: str):
    """Stack-based DFS ignoring robots.txt, treating everything as HTML.
    - 4 attempts per URL. If fail_count+1 == 4 => rotate proxy & re-try that URL
    - Skips external domain or certain file types
    - Saves PDF/doc or text
    - Closes driver after each page
    """
    global driver
    stack = [(start_url, 0)]  # (url, fail_count)
    while stack:
        url, fail_count = stack.pop()
        if url in visited_urls:
            continue
        visited_urls.add(url)

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Skip external domain
        if not (domain.endswith(f".{ALLOWED_DOMAIN}") or domain == ALLOWED_DOMAIN):
            log_skipped(f"[SKIPPED] External domain: {url}")
            continue

        path_lower = parsed.path.lower()
        # If PDF or doc => download
        if path_lower.endswith(PDF_EXTENSIONS):
            save_pdf_or_doc(url)
            continue
        # If skip extension => skip
        if path_lower.endswith(SKIP_EXTENSIONS):
            log_skipped(f"[SKIPPED] Ignored extension: {url}")
            continue

        try:
            log_info(f"[INFO] Visiting: {url} (fail_count={fail_count})")
            time.sleep(random.randint(MIN_DELAY, MAX_DELAY))

            driver.get(url)
            time.sleep(1)

            content_lower = driver.page_source.lower()
            # If blocked by captcha or "access denied"
            if (
                "verify you are human" in content_lower
                or "access denied" in content_lower
            ):
                raise Exception("Blocked/AccessDenied")

            # Parse as HTML
            save_text_file(url, driver.page_source)
            new_links = extract_internal_links_html(
                driver.page_source, driver.current_url
            )
            for link in new_links:
                if link not in visited_urls:
                    stack.append((link, 0))

        except (TimeoutException, WebDriverException, Exception) as e:
            log_error(f"[FAILED] {url} - {e} (fail_count={fail_count})")
            # If we haven't tried 4 times yet => re-try
            if fail_count + 1 < MAX_RETRIES:
                # If about to do the 4th attempt => rotate proxy
                if fail_count + 1 >= PROXY_ROTATE_THRESHOLD:
                    rotate_proxy()
                stack.append((url, fail_count + 1))
            else:
                # Hard skip
                log_error(f"[ERROR] Skipping {url} after {MAX_RETRIES} attempts.")

        # close & re-open driver => new session each page
        close_and_new_driver()


###############################################################################
#                               MAIN                                          #
###############################################################################
driver = None
current_proxy = None


def main():
    global driver
    try:
        # Start with no proxy
        driver = start_webdriver(proxy=None)
        crawl_dfs_stack(START_URL)
    except Exception as e:
        log_error(f"[FATAL ERROR] {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
        log_info("[INFO] Scraping Complete!")
        sys.exit(0)


if __name__ == "__main__":
    main()
