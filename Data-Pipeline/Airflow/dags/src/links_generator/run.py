import os
import time
import threading
import pandas as pd
import requests
import re
import random
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from datetime import datetime

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
MAX_TIMEOUT = 30
MAX_THREADS = 5  # Number of parallel threads for crawling
VISITED_URLS = set()
BLOCKED_SITES = [
    "twitter.com", "facebook.com", "linkedin.com", "reddit.com",
    "instagram.com", "tiktok.com", "youtube.com", "medium.com"
]

# Location words to avoid
LOCATION_WORDS = [
    "Arlington", "Burlington", "Charlotte", "London", "Miami", 
    "Nahant", "Oakland", "Portland", "Seattle", "Silicon Valley", 
    "Toronto", "Vancouver","#main-content" ]

# Proxy configuration
# Add your proxies to this list - format: "ip:port" or "user:pass@ip:port"
PROXIES = [
    # Add your proxies here
    "154.16.214.14:3128"
    # Add more proxies as needed
]

# Flag to enable/disable proxy usage
USE_PROXIES = False

# Dictionary to store disallowed keywords for each subdomain
SUBDOMAIN_DISALLOWED = {}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ERROR_LOG_FILE = os.path.join(SCRIPT_DIR, "errors.log")
LOGGED_URLS_FILE = os.path.join(SCRIPT_DIR, "links_generator.txt")
EXCEL_OUTPUT_FILE = os.path.join(SCRIPT_DIR, "reachable_urls.xlsx")
PROXY_LOG_FILE = os.path.join(SCRIPT_DIR, "proxy_usage.log")

# Ensure log files are clean
open(ERROR_LOG_FILE, "w").close()
open(LOGGED_URLS_FILE, "w").close()
open(PROXY_LOG_FILE, "w").close()

# List to store reachable URLs for Excel export
reachable_urls_data = []
urls_lock = threading.Lock()  # Lock for thread-safe operations on the shared list
proxy_lock = threading.Lock()  # Lock for thread-safe proxy selection


def log_proxy_usage(proxy, url, success=True):
    """Logs proxy usage for monitoring purposes."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"
    with open(PROXY_LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {proxy} | {status} | {url}\n")


def get_random_proxy():
    """Returns a random proxy from the proxy list."""
    if not PROXIES or not USE_PROXIES:
        return None
    
    with proxy_lock:
        return random.choice(PROXIES)


def extract_disallowed_keywords(subdomain):
    """Fetches robots.txt from a given subdomain and extracts disallowed path keywords."""
    robots_url = f"https://{subdomain}/robots.txt"
    keywords = set()  # Use a set to avoid duplicates
    
    try:
        # Use a random proxy for the request
        proxy = get_random_proxy()
        proxies = {"http": f"http://{proxy}", "https": f"https://{proxy}"} if proxy else None
        
        response = requests.get(robots_url, timeout=10, proxies=proxies)
        if proxy:
            log_proxy_usage(proxy, robots_url, success=(response.status_code == 200))
            
        if response.status_code != 200:
            print(f"{Fore.YELLOW}Failed to fetch {robots_url} (Status Code: {response.status_code}){Style.RESET_ALL}")
            return []
        
        # Extract all lines containing "Disallow:"
        disallow_lines = re.findall(r"Disallow:\s+(/[\w\-/]*)", response.text)
        
        # Extract keywords by splitting at '/' and filtering out empty strings
        for line in disallow_lines:
            words = [word for word in line.split('/') if word]
            keywords.update(words)
        
        print(f"{Fore.CYAN}[ROBOTS] Found {len(keywords)} disallowed keywords for {subdomain}{Style.RESET_ALL}")
        return list(keywords)
    except requests.RequestException as e:
        if proxy:
            log_proxy_usage(proxy, robots_url, success=False)
        print(f"{Fore.YELLOW}Error fetching robots.txt for {subdomain}: {e}{Style.RESET_ALL}")
        return []


def configure_proxy_for_webdriver(options, proxy):
    """Configure Chrome options to use a proxy."""
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
        print(f"{Fore.CYAN}[PROXY] Using proxy: {proxy}{Style.RESET_ALL}")


def start_webdriver():
    """Starts a headless Selenium WebDriver with proxy support."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    # Set up a random proxy if enabled
    proxy = get_random_proxy()
    if proxy:
        configure_proxy_for_webdriver(options, proxy)
    
    # Add random user agent to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')
    
    ##Fix 
    from webdriver_manager.chrome import ChromeDriverManager
    driver_path = ChromeDriverManager(driver_version="135.0.7049.41").install()

    from selenium.webdriver.chrome.service import Service
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    # Add any options like headless here if needed
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    # Fix ends
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(MAX_TIMEOUT)
    return driver, proxy


def log_error(message):
    """Logs errors to a file."""
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def log_reachable_url(url, title=""):
    """Logs reachable URLs to a file and adds to Excel data list."""
    # Log to text file
    with open(LOGGED_URLS_FILE, "a") as f:
        f.write(url + "\n")
    print(f"{Fore.GREEN}[LOGGED] Reachable URL: {url}{Style.RESET_ALL}")
    
    # Add to Excel data with thread safety
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with urls_lock:
        reachable_urls_data.append({
            "URL": url,
            "Title": title,
            "Timestamp": timestamp
        })


def normalize_url(url):
    """Removes fragments from URLs to ensure URLs differing only by fragments are treated as the same."""
    parsed = urlparse(url)
    # Reconstruct the URL without the fragment
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{('?' + parsed.query) if parsed.query else ''}"


def is_pdf_link(url):
    """Checks if the URL points to a PDF file."""
    return url.lower().endswith('.pdf')


def contains_location_word(url):
    """Checks if the URL contains any of the location words to avoid."""
    url_lower = url.lower()
    for word in LOCATION_WORDS:
        if word.lower() in url_lower:
            return True
    return False


def contains_disallowed_keyword(url, subdomain):
    """Checks if the URL contains any disallowed keywords for the subdomain."""
    # If we haven't processed this subdomain yet, do it now
    if subdomain not in SUBDOMAIN_DISALLOWED:
        SUBDOMAIN_DISALLOWED[subdomain] = extract_disallowed_keywords(subdomain)
    
    # Check if any disallowed keyword is in the URL
    for keyword in SUBDOMAIN_DISALLOWED[subdomain]:
        if keyword.lower() in url.lower():
            return True
    return False


def is_url_visited(url):
    """Checks if the normalized URL (without fragments) has been visited."""
    normalized = normalize_url(url)
    return normalized in VISITED_URLS


def mark_url_visited(url):
    """Marks a normalized URL (without fragments) as visited."""
    normalized = normalize_url(url)
    VISITED_URLS.add(normalized)


def should_skip_url(url, subdomain):
    """Determines if a URL should be skipped based on various criteria."""
    # Check if it's a PDF
    if is_pdf_link(url):
        return True
    
    # Check if it contains location words
    if contains_location_word(url):
        print(f"{Fore.YELLOW}[SKIP] URL contains location word: {url}{Style.RESET_ALL}")
        return True
    
    # Check if it contains disallowed keywords
    if contains_disallowed_keyword(url, subdomain):
        print(f"{Fore.YELLOW}[SKIP] URL contains disallowed keyword: {url}{Style.RESET_ALL}")
        return True
    
    return False


def extract_internal_links(driver, allowed_subdomain):
    """Extracts internal links from the current page, restricting to the same subdomain."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()
    base_url = driver.current_url

    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag["href"].strip())  # Get absolute URL
        parsed_url = urlparse(href)

        # Skip URLs that should be skipped
        if should_skip_url(href, allowed_subdomain):
            continue

        # Only allow URLs within the same subdomain
        if parsed_url.netloc == allowed_subdomain and not any(blocked in href for blocked in BLOCKED_SITES):
            links.add(href)

    return links


def get_page_title(driver):
    """Extracts the page title from the current page."""
    try:
        return driver.title
    except:
        return ""


def crawl_website(url, driver, allowed_subdomain, current_proxy):
    """Recursively crawls a website, ensuring it stays within the given subdomain."""
    if is_url_visited(url):
        return
    
    # Skip URLs that should be skipped
    if should_skip_url(url, allowed_subdomain):
        return
    
    mark_url_visited(url)

    try:
        driver.get(url)
        if current_proxy:
            log_proxy_usage(current_proxy, url, success=True)
            
        time.sleep(random.uniform(2, 5))  # Randomized delay to avoid detection
        final_url = driver.current_url.lower()

        # Ensure we're still within the allowed subdomain
        if urlparse(final_url).netloc != allowed_subdomain:
            return

        # Get page title for Excel logging
        page_title = get_page_title(driver)
        log_reachable_url(final_url, page_title)

        for new_link in extract_internal_links(driver, allowed_subdomain):
            crawl_website(new_link, driver, allowed_subdomain, current_proxy)

    except Exception as e:
        if current_proxy:
            log_proxy_usage(current_proxy, url, success=False)
        log_error(f"[ERROR] Failed to process {url}: {e}")
        
        # If using proxies and we get an error, try to restart with a new proxy
        if USE_PROXIES and PROXIES:
            print(f"{Fore.YELLOW}[PROXY] Attempting to switch proxy after error...{Style.RESET_ALL}")
            try:
                driver.quit()
                driver, new_proxy = start_webdriver()  # Start a new driver with a new proxy
                # Try again with the new proxy (but don't recurse on error to avoid infinite loops)
                mark_url_visited(url)  # Prevent double-marking
                driver.get(url)
                time.sleep(random.uniform(2, 5))
                final_url = driver.current_url.lower()
                
                if urlparse(final_url).netloc == allowed_subdomain:
                    page_title = get_page_title(driver)
                    log_reachable_url(final_url, page_title)
                    
                    for new_link in extract_internal_links(driver, allowed_subdomain):
                        crawl_website(new_link, driver, allowed_subdomain, new_proxy)
            except Exception as e2:
                log_error(f"[ERROR] Second attempt with new proxy also failed for {url}: {e2}")


def worker(start_urls):
    """Thread worker function to crawl multiple start URLs in parallel."""
    driver, current_proxy = start_webdriver()

    for url in start_urls:
        parsed_url = urlparse(url.strip())

        if not parsed_url.scheme or not parsed_url.netloc:
            log_error(f"[ERROR] Invalid URL: {url}")
            continue

        # Extract and store the allowed subdomain
        allowed_subdomain = parsed_url.netloc  # Example: military.northeastern.edu
        
        # Pre-fetch robots.txt for this subdomain
        if allowed_subdomain not in SUBDOMAIN_DISALLOWED:
            SUBDOMAIN_DISALLOWED[allowed_subdomain] = extract_disallowed_keywords(allowed_subdomain)

        crawl_website(url, driver, allowed_subdomain, current_proxy)
        
        # Occasionally rotate proxy between URLs to avoid detection
        if USE_PROXIES and PROXIES and random.random() < 0.3:  # 30% chance to rotate proxy
            driver.quit()
            print(f"{Fore.CYAN}[PROXY] Rotating proxy between URLs{Style.RESET_ALL}")
            driver, current_proxy = start_webdriver()

    driver.quit()


def save_to_excel():
    """Saves the collected URLs to an Excel file."""
    try:
        df = pd.DataFrame(reachable_urls_data)
        df.to_excel(EXCEL_OUTPUT_FILE, index=False)
        print(f"{Fore.GREEN}[INFO] Successfully saved {len(reachable_urls_data)} URLs to {EXCEL_OUTPUT_FILE}{Style.RESET_ALL}")
    except Exception as e:
        log_error(f"[ERROR] Failed to save Excel file: {e}")


def read_urls_from_csv():
    """Reads URLs from the CSV file and returns a list of URLs."""
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
    csv_path = os.path.join(current_dir, "urls.xlsx")

    try:
        df = pd.read_excel(csv_path)  # Using absolute path
        if "url" not in df.columns:
            print(f"Error: 'url' column not found in {csv_path}")
            return []
        return df["url"].tolist()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []


def main():
    """Main function to read URLs from CSV and start crawling in parallel."""
    # Check if proxy list is populated
    if USE_PROXIES and not PROXIES:
        print(f"{Fore.YELLOW}[WARNING] Proxy usage is enabled but no proxies are defined. Please add proxies to the PROXIES list.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[WARNING] Proceeding without proxy usage.{Style.RESET_ALL}")
    
    urls = read_urls_from_csv()
    chunk_size = max(1, len(urls) // MAX_THREADS)
    url_chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    threads = []
    for chunk in url_chunks:
        thread = threading.Thread(target=worker, args=(chunk,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        
    # After all threads are done, save data to Excel
    save_to_excel()

    print(f"{Fore.GREEN}[INFO] Crawling complete. Check '{LOGGED_URLS_FILE}' for text results and '{EXCEL_OUTPUT_FILE}' for Excel data.{Style.RESET_ALL}")


if __name__ == "__main__":
    main()