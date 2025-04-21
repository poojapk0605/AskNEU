import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import re
from datetime import datetime
from Scrape_script import load_urls, save_as_text, download_pdfs_from_page, SCRAPED_TEXT_DIR, SCRAPED_PDF_DIR

class TestScraper(unittest.TestCase):

    @patch('Scrape_script.pd')
    def test_load_urls(self, mock_pd):
        """Test load_urls function with various Excel scenarios."""
        # Mock DataFrame
        mock_df = MagicMock()
        mock_df.__getitem__.return_value.dropna.return_value.tolist.return_value = [
            'https://vpn.northeastern.edu',
            'https://canvas.northeastern.edu'
        ]
        mock_pd.read_excel.return_value = mock_df

        # Test with valid DataFrame
        urls = load_urls()
        self.assertEqual(urls, ['https://vpn.northeastern.edu', 'https://canvas.northeastern.edu'])

        # Test with missing 'URL' column
        mock_df.__getitem__.side_effect = KeyError('URL')
        with self.assertRaises(ValueError):
            load_urls()

        # Test with exception
        mock_pd.read_excel.side_effect = Exception("File not found")
        urls = load_urls()
        self.assertEqual(urls, [])

    @patch('Scrape_script.datetime')
    @patch('Scrape_script.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_as_text(self, mock_open, mock_exists, mock_datetime):
        """Test save_as_text function with HTML content extraction."""
        mock_driver = MagicMock()
        mock_driver.page_source = """
        <html>
            <body>
                <div>
                    <h1>Main Title</h1>
                    <p>Intro paragraph.</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 1</li>  <!-- Duplicate -->
                    </ul>
                </div>
                <section>
                    <h2>Subtitle</h2>
                    <p>Another paragraph.</p>
                </section>
                <script>script content</script>
                <header>header content</header>
            </body>
        </html>
        """
        url = "https://vpn.northeastern.edu"
        # Match filename generation from Scrape_script.py
        filename = re.sub(r"[^\w\-]", "_", url.replace("https://", ""))
        mock_exists.return_value = False
        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

        save_as_text(mock_driver, url, filename)

        # Verify file write
        mock_open.assert_called_once_with(os.path.join(SCRAPED_TEXT_DIR, f"{filename}.txt"), "w", encoding="utf-8")
        handle = mock_open()
        written = ''.join(call.args[0] for call in handle.write.call_args_list)
        expected_content = (
            "URL (Source): https://vpn.northeastern.edu\n"
            "Scraped on: 2023-01-01 12:00:00\n\n"
            "[Main Title]\n"
            "Intro paragraph.\n"
            "- Item 1\n"
            "[Subtitle]\n"
            "Another paragraph.\n"
        )
        self.assertEqual(written, expected_content)

    @patch('Scrape_script.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_as_text_existing_file(self, mock_open, mock_exists):
        """Test save_as_text skips if file exists."""
        mock_driver = MagicMock()
        url = "https://vpn.northeastern.edu"
        filename = re.sub(r"[^\w\-]", "_", url.replace("https://", ""))
        mock_exists.return_value = True
        save_as_text(mock_driver, url, filename)
        mock_open.assert_not_called()

    @patch('Scrape_script.requests.get')
    @patch('Scrape_script.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_pdfs_from_page(self, mock_open, mock_exists, mock_get):
        """Test download_pdfs_from_page with PDF links."""
        mock_driver = MagicMock()
        mock_driver.page_source = """
        <html>
            <body>
                <a href="https://vpn.northeastern.edu/file1.pdf">PDF 1</a>
                <a href="/file2.pdf">PDF 2</a>
            </body>
        </html>
        """
        url = "https://vpn.northeastern.edu"
        mock_exists.return_value = False
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_response.iter_content = lambda chunk_size: [b'pdf content']
        mock_get.return_value = mock_response

        downloaded = download_pdfs_from_page(mock_driver, url)

        self.assertEqual(len(downloaded), 2)
        self.assertIn(os.path.join(SCRAPED_PDF_DIR, "file1.pdf"), downloaded)
        self.assertIn(os.path.join(SCRAPED_PDF_DIR, "file2.pdf"), downloaded)
        mock_open.assert_any_call(os.path.join(SCRAPED_PDF_DIR, "file1.pdf"), 'wb')
        mock_open.assert_any_call(os.path.join(SCRAPED_PDF_DIR, "file2.pdf"), 'wb')
        mock_get.assert_any_call("https://vpn.northeastern.edu/file1.pdf", stream=True, timeout=10)
        mock_get.assert_any_call("https://vpn.northeastern.edu/file2.pdf", stream=True, timeout=10)

    @patch('Scrape_script.requests.get')
    @patch('Scrape_script.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_pdfs_from_page_invalid_content(self, mock_open, mock_exists, mock_get):
        """Test download_pdfs_from_page skips non-PDF content."""
        mock_driver = MagicMock()
        mock_driver.page_source = """
        <html><body><a href="https://vpn.northeastern.edu/file.pdf">File</a></body></html>
        """
        url = "https://vpn.northeastern.edu"
        mock_exists.return_value = False
        mock_response = MagicMock()
        mock_response.headers = {'content-type': 'text/plain'}
        mock_get.return_value = mock_response

        downloaded = download_pdfs_from_page(mock_driver, url)
        self.assertEqual(downloaded, [])
        mock_open.assert_not_called()

if __name__ == '__main__':
    unittest.main()