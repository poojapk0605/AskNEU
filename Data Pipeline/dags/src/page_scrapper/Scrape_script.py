import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import logging

# Configuration
BASE_DIR = "/opt/airflow/dags/src/page_scrapper"
SCRAPED_TEXT_DIR = os.path.join(BASE_DIR, "scraped_texts")
SCRAPED_PDF_DIR = os.path.join(BASE_DIR, "scraped_pdfs")
URL_EXCEL_PATH = os.path.join(BASE_DIR, "urls.xlsx")
LOG_DIR = os.path.join(BASE_DIR, "logs")
USE_PROXIES = False  # Toggle proxy usage
PROXIES = ["http://176.105.220.74:80"]  # Single proxy as in your code

remote_webdriver = "remote_chromedriver"  # Airflow connection name


# Ensure directories exist
os.makedirs(SCRAPED_TEXT_DIR, exist_ok=True)
os.makedirs(SCRAPED_PDF_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Logging setup (replacing colorama with standard logging for Airflow compatibility)
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


# Load URLs from Excel
def load_urls():
    try:
        df = pd.read_excel(URL_EXCEL_PATH)
        if 'URL' not in df.columns:
            raise ValueError("Excel file must contain a 'URL' column")
        return df['URL'].dropna().tolist()
    except Exception as e:
        log_error(f"Failed to load URLs from Excel: {e}")
        return []


# Setup Selenium WebDriver
def start_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1024,768")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    if USE_PROXIES and PROXIES:
        chrome_options.add_argument(f"--proxy-server={PROXIES[0]}")
    driver = webdriver.Remote(f"{remote_webdriver}:4444/wd/hub", options=chrome_options)
    driver.set_page_load_timeout(30)  # Added timeout for robustness
    return driver


def save_as_text(driver, url, filename):
    """Extracts text from a webpage and saves it as a .txt file."""
    try:
        txt_path = os.path.join(SCRAPED_TEXT_DIR, filename + ".txt")
        if os.path.exists(txt_path):
            log_skipped(f"Text file already exists: {txt_path}")
            return

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()

        # First pass: Collect unique container elements
        unique_containers = set()
        content = []
        processed_texts = set()

        # Find all list and paragraph containers
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

        # Save extracted text to a file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"URL (Source): {url}\n")
            f.write(f"Scraped on: {datetime.now()}\n\n")
            f.write("\n".join(content))

        log_success(f"Saved Text: {txt_path}")

    except Exception as e:
        log_error(f"Failed to save text for {url}: {e}")


def download_pdfs_from_page(driver, url, base_dir=SCRAPED_PDF_DIR):
    """Find and download all PDF links from a webpage."""
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

        downloaded_pdfs = []
        for pdf_url in pdf_links:
            try:
                parsed_url = urlparse(pdf_url)
                filename = os.path.basename(parsed_url.path)
                filename = "".join(x for x in filename if x.isalnum() or x in "._-").rstrip()[:255]
                pdf_path = os.path.join(base_dir, filename)

                if os.path.exists(pdf_path):
                    log_skipped(f"PDF already exists: {pdf_path}")
                    continue

                response = requests.get(pdf_url, stream=True, timeout=10)
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type:
                    log_skipped(f"Not a PDF: {pdf_url}")
                    continue

                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                log_success(f"Downloaded PDF: {pdf_path}")
                log_info(f"Source URL: {pdf_url}")
                downloaded_pdfs.append(pdf_path)

            except requests.exceptions.RequestException as e:
                log_error(f"Failed to download PDF: {pdf_url} - {e}")

        log_info(f"Downloaded {len(downloaded_pdfs)} PDFs from {url}")
        return downloaded_pdfs

    except Exception as e:
        log_error(f"Failed to process PDFs on {url}: {e}")
        return []


def scrape():
    urls = load_urls()
    if not urls:
        log_error("No URLs to scrape. Exiting.")
        return

    driver = start_driver()
    try:
        for url in urls:
            try:
                log_info(f"Scraping: {url}")
                driver.get(url)
                parsed_url = urlparse(url)
                filename = re.sub(r"[^\w\-]", "_", url.replace("https://", ""))
                save_as_text(driver, url, filename)
                download_pdfs_from_page(driver, url)
            except Exception as e:
                log_error(f"Failed to scrape {url}: {e}")
    finally:
        driver.quit()
        log_info("Scraping process completed.")


def main():
    scrape()


if __name__ == "__main__":
    main()