"""
Main script for processing text documents and uploading to Pinecone vector database.
Enhanced with detailed statistics tracking.
"""

import os
import time
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from colorama import Fore, Style, init
from config import *
from datetime import datetime
from urllib.parse import urlparse

# Initialize colorama
init(autoreset=True)

os.environ['PINECONE_API_KEY'] = PINECONE_API_KEY

def initialize_components():
    """Initialize embeddings, Pinecone client, and vector store"""
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
    
    # Initialize Pinecone
    pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
    
    # Check if the index exists, if not, create it
    if PINECONE_INDEX_NAME not in [index_info["name"] for index_info in pc.list_indexes()]:
        print(f"{Fore.CYAN}Creating new index: {Fore.WHITE}{PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric=PINECONE_METRIC,
            spec=ServerlessSpec(cloud=PINECONE_ENVIRONMENT, region=PINECONE_REGION),
        )
    else:
        print(f"{Fore.CYAN}Using existing index: {Fore.WHITE}{PINECONE_INDEX_NAME}")
    
    # Connect to the Pinecone index
    vector_store = PineconeVectorStore(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
    
    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    return text_splitter, vector_store

def process_file(filename, text_splitter, vector_store):
    """
    Process an individual text file and upsert chunks to Pinecone
    
    Returns:
        tuple: (filename, chunk_count, success_flag)
    """
    try:
        full_path = os.path.join(DIRECTORY_PATH, filename)
        
        with open(full_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Check if the file has more than Minimum lines
        if len(lines) <= MIN_DOC_SIZE:
            print(f"{Fore.YELLOW}Skipping {filename}: less than {MIN_DOC_SIZE} lines")
            return filename, 0, False
        
        # Extract URL and date from the first two lines
        try:
            source = lines[0].split("URL (Source): ")[1].strip()
            date = lines[1].split("Scraped on: ")[1].strip()
        except IndexError:
            print(f"{Fore.RED}Skipping {filename}: Unable to extract source and date")
            return filename, 0, False
        
        # Get all text including headers
        remaining_text = "".join(lines[0:])
        
        # Split the text into chunks
        chunks = text_splitter.split_text(remaining_text)
        
        # More Metadata
        unix_date = datetime.fromisoformat(date).timestamp()
        filename_stem = os.path.splitext(filename)[0]
        extract_subdomain_func = lambda url: (urlparse(url).hostname.split('.')[0] if len(urlparse(url).hostname.split('.')) > 2 else "Northeastern")
        extract_subdomain = extract_subdomain_func(source)
        # Prepare metadata and IDs for each chunk
        metadatas = [{"source": source, "date": date, "unix_time": unix_date, "Subdomain": extract_subdomain} for _ in chunks]
        ids = [f"{filename_stem}_{i}" for i in range(len(chunks))]
        
        # Add chunks to Pinecone with embeddings and metadata
        vector_store.add_texts(
            texts=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"{Fore.GREEN}Processed {Fore.WHITE}{Style.BRIGHT}{filename}{Style.RESET_ALL}{Fore.GREEN}: {len(chunks)} chunks upserted to Pinecone")
        
        return filename, len(chunks), True
        
    except Exception as e:
        print(f"{Fore.RED}Error processing {filename}: {str(e)}")
        return filename, 0, False

def main():
    """Main function to process all documents in the directory"""
    # Start timer for the entire process
    overall_start_time = time.time()
    
    print(f"{Fore.BLUE}{'=' * 80}")
    print(f"{Fore.BLUE}{Style.BRIGHT}DOCUMENT PROCESSING AND PINECONE UPLOAD")
    print(f"{Fore.BLUE}{'=' * 80}")
    
    text_splitter, vector_store = initialize_components()
    
    # Count total files to process
    txt_files = [f for f in os.listdir(DIRECTORY_PATH) if f.endswith('.txt')]
    total_files = len(txt_files)
    processed_files = 0
    successful_files = 0
    total_chunks = 0
    
    print(f"{Fore.CYAN}Found {Fore.WHITE}{Style.BRIGHT}{total_files}{Style.RESET_ALL}{Fore.CYAN} text files to process")
    print(f"{Fore.BLUE}{'-' * 80}")
    
    # Process each file in the directory
    for filename in txt_files:
        # Track individual file stats
        start_file_time = time.time()
        result = process_file(filename, text_splitter, vector_store)
        
        # If process_file returned chunks count (update)
        if isinstance(result, tuple) and len(result) == 3:
            _, chunks, success = result
            total_chunks += chunks
            if success:
                successful_files += 1
        else:
            # For compatibility with original process_file function
            successful_files += 1
        
        processed_files += 1
        progress_percentage = (processed_files / total_files) * 100
        print(f"{Fore.BLUE}Progress: {Fore.WHITE}{Style.BRIGHT}{processed_files}/{total_files}{Style.RESET_ALL}{Fore.BLUE} files ({progress_percentage:.1f}%)")
        
        if processed_files < total_files:
            print(f"{Fore.BLUE}{'-' * 80}")
    
    # Calculate time statistics
    total_time = time.time() - overall_start_time
    avg_time_per_file = total_time / processed_files if processed_files > 0 else 0
    
    # Print summary statistics
    print(f"{Fore.BLUE}{'=' * 80}")
    print(f"{Fore.GREEN}{Style.BRIGHT}PROCESSING COMPLETE")
    print(f"{Fore.GREEN}Processed: {processed_files}/{total_files} files ({successful_files} successful)")
    print(f"{Fore.GREEN}Total chunks: {total_chunks}")
    print(f"{Fore.GREEN}Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"{Fore.GREEN}Average time per file: {avg_time_per_file:.2f} seconds")
    print(f"{Fore.BLUE}{'=' * 80}")

if __name__ == "__main__":
    main()