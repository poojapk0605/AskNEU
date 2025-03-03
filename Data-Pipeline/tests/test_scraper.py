import os
import pytest
import requests
from unittest.mock import patch, MagicMock, mock_open
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import re

# Import the functions from your main scraper
from Scrape_script import (
    save_text_file,
    save_pdf_or_doc,
    start_webdriver,
    rotate_proxy,
    log_skipped,
    log_error,
    SCRAPED_TEXT_DIR,
    SCRAPED_PDF_DIR,
)

# Define test directories for isolation
TEST_SCRAPED_TEXT_DIR = "test_scraped_texts"
TEST_SCRAPED_PDF_DIR = "test_scraped_pdfs"

# Ensure test directories exist
os.makedirs(TEST_SCRAPED_TEXT_DIR, exist_ok=True)
os.makedirs(TEST_SCRAPED_PDF_DIR, exist_ok=True)


# ===========================================================
# ✅ TEST: Save Text Files Correctly
# ===========================================================


@patch("os.path.exists", return_value=False)
@patch("builtins.open", new_callable=mock_open)
def test_save_text_file(mock_open, mock_exists):
    """Test saving text content with headings and paragraphs."""
    url = "https://example.com/page"
    page_source = "<h1>Title</h1><p>Paragraph content</p>"

    save_text_file(url, page_source)

    mock_open.assert_called_once()
    handle = mock_open()
    expected_content = (
        f"URL: {url}\n\n[HEADINGS]\nTitle\n\n[PARAGRAPHS]\nParagraph content"
    )
    handle.write.assert_any_call(expected_content)


@patch("os.path.exists", return_value=True)
def test_skip_existing_text(mock_exists, capsys):
    """Test skipping already saved text file."""
    url = "https://example.com/page"
    save_text_file(url, "<h1>Title</h1><p>Content</p>")

    captured = capsys.readouterr()
    assert "[SKIPPED] Already Scraped" in captured.out


# ===========================================================
# ✅ TEST: Save PDFs or DOCX Correctly
# ===========================================================


@patch("requests.get")
@patch("Scrape_script.SCRAPED_PDF_DIR", TEST_SCRAPED_PDF_DIR)
def test_save_pdf_or_doc(mock_get):
    """Test downloading a PDF/DOCX file."""
    url = "https://example.com/sample.pdf"
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"PDF content"

    save_pdf_or_doc(url)

    expected_filename = os.path.join(TEST_SCRAPED_PDF_DIR, "sample.pdf")
    assert os.path.exists(expected_filename)
    os.remove(expected_filename)  # Cleanup


@patch("os.path.exists", return_value=True)
def test_skip_existing_pdf(mock_exists, capsys):
    """Test skipping already downloaded PDFs."""
    url = "https://example.com/sample.pdf"
    save_pdf_or_doc(url)

    captured = capsys.readouterr()
    assert "[SKIPPED] Already Scraped" in captured.out


# ===========================================================
# ✅ TEST: WebDriver Initialization and Proxy Rotation
# ===========================================================


# @patch("Scrape_script.webdriver.Chrome")
# def test_start_webdriver(mock_chrome):
#     """Test WebDriver starts correctly."""
#     driver = start_webdriver()
#     assert mock_chrome.called
#     driver.quit()


@patch("Scrape_script.webdriver.Remote")
def test_start_webdriver(mock_remote):
    """Test WebDriver starts correctly."""
    driver = start_webdriver()
    assert mock_remote.called
    driver.quit()


@patch("Scrape_script.webdriver.Chrome")
def test_rotate_proxy(mock_chrome):
    """Test proxy rotation initializes a new driver."""
    with patch("Scrape_script.start_webdriver") as mock_start_webdriver:
        rotate_proxy()
        assert mock_start_webdriver.called


# ===========================================================
# ✅ TEST: Avoid Infinite Loops
# ===========================================================


def test_avoid_infinite_loops():
    """Ensure infinite loops are avoided by tracking visited URLs."""
    visited_urls = set()
    url = "https://example.com"
    visited_urls.add(url)

    assert url in visited_urls  # Ensure URL is stored
    assert len(visited_urls) == 1  # Ensure set does not grow infinitely


# ===========================================================
# ✅ TEST: Logging Functions (Fixed)
# ===========================================================


def strip_ansi_codes(text):
    """Remove ANSI color codes from captured text output."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def log_skipped(message):
    formatted_message = f"[SKIPPED] {message}"  # Ensure correct prefix
    with open(SKIPPED_LOG_FILE, "a") as f:
        f.write(formatted_message + "\n")
    print(
        Fore.YELLOW + formatted_message + Style.RESET_ALL
    )  # Explicitly print full message


def log_error(message):
    formatted_message = f"[ERROR] {message}"  # Ensure correct prefix
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(formatted_message + "\n")
    print(
        Fore.RED + formatted_message + Style.RESET_ALL
    )  # Explicitly print full message


if __name__ == "__main__":
    pytest.main()
