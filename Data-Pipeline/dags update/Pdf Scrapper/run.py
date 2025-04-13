import fitz   # from PyMuPDF
import os

# Defininig Folder Paths

pdf_folder = r"C:\Users\nagku\Desktop\AskNEU\Data Scraping\Pdf Scrapper\Docs"
output_folder = r"C:\Users\nagku\Desktop\AskNEU\Data Scraping\Pdf Scrapper\scraped_texts"


def extract_text_from_pdfs(pdf_folder, output_folder):

    # Iterate over all PDF files in the folder
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):  # Process only PDFs
            pdf_path = os.path.join(pdf_folder, filename)
            output_txt_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")

            # Open the PDF and extract text
            doc = fitz.open(pdf_path)
            Source = filename.replace('.txt', '.pdf')
            text = f"URL (Source): {Source}" + "\n" + "Scraped on: 2025-04-03 00:38:36.836512" + "\n" + "\n"
            for page in doc:
                text += page.get_text("text") + "\n"

            # Save extracted text to a .txt file
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"Extracted text saved: {output_txt_path}")


# Run the extraction
extract_text_from_pdfs(pdf_folder, output_folder)