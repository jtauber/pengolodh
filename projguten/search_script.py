import typer
import zipfile
import os
import requests
from lxml import html


def search_gutenberg(query: str, limit: int = 10) -> tuple:
    search_url = f"https://www.gutenberg.org/ebooks/search/?query={query}"
    response = requests.get(search_url)
    tree = html.fromstring(response.content)
    books = tree.xpath('//li[@class="booklink"]')

    book_info = []

    for book in books[:limit]:
        title_element = book.xpath('.//span[@class="title"]')
        link_element = book.xpath('.//a[@class="link"]')
        if title_element and link_element:
            title = title_element[0].text
            href = link_element[0].get('href')
            book_id = href.split('/')[-1] if href else None
            
            if book_id:
                book_info.append((title, book_id))

    return book_info, books

def get_book_details(book_id: str):
    """Get details about a specific book"""
    book_url = f"https://www.gutenberg.org/ebooks/{book_id}"
    response = requests.get(book_url)
    tree = html.fromstring(response.content)
    
    # Try to find author
    author_element = tree.xpath('//a[contains(@href, "/ebooks/author/")]/text()')
    author = author_element[0] if author_element else "Unknown Author"
    
    # Try to find language
    language_element = tree.xpath('//tr[th[contains(text(), "Language")]]/td/text()')
    language = language_element[0] if language_element else "Unknown Language"
    
    # Try to find release date
    release_element = tree.xpath('//tr[th[contains(text(), "Release Date")]]/td/text()')
    release_date = release_element[0] if release_element else "Unknown Date"

    formats = {}
    all_links = tree.xpath('//a')

    for link in all_links:
        href = link.get('href', '')
        link_text = link.text_content().strip()
        
        # Check if this is one of our download file patterns
        if (('.epub3.' in href or '.epub.' in href or '.txt.' in href or 
            '.kf8.' in href or '.kindle.' in href) and 
            'send/' not in href and link_text):
            
            formats[link_text] = f"https://www.gutenberg.org{href}"

    return {
        'author': author,
        'language': language, 
        'release_date': release_date,
        'formats': formats
    }

def download_book(url: str, filename: str) -> bool:
    """Download a book file from the list"""
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)

        print(f"Successfully downloaded {filename}!")
        return True
    
    except Exception as e:
        print(f"Download failed: {e}.")
        return False
    
def extract_epub(epub_filename: str):
    """Extract an EPUB file to a folder with the same name"""
    try:
        # Create the folder name (remove .epub extension)
        folder_name = epub_filename.replace('.epub', '')
        
        # Create the directory if it doesn't exist
        os.makedirs(folder_name, exist_ok=True)
        
        print(f"Extracting {epub_filename} to {folder_name}/")
        
        # Extract the EPUB (which is a ZIP file)
        with zipfile.ZipFile(epub_filename, 'r') as zip_ref:
            zip_ref.extractall(folder_name)
        
        print(f"Successfully extracted to {folder_name}/")
        return True
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        return False

def main(query: str = typer.Argument(..., help="Search Project Gutenberg terms such as 'shakespeare', 'old english', 'jane austen', or 'beowulf'. Use quotes for multi-word arguments.")):
    """Search Project Gutenberg and show first 10 results"""
    book_info, all_books = search_gutenberg(query)

    if book_info:
        print(f"Showing first {len(book_info)} of {len(all_books)} results for {query}:")
        for i, (title, book_id) in enumerate(book_info, 1):
            print(f"{i}. {title}")

        if len(all_books) > len(book_info):
            difference = len(all_books) - len(book_info)
            answer = input(f"There are {difference} more results. Show more? (y/n): ")
            if answer.lower() in ["yes", "y"]:
                book_info, _ = search_gutenberg(query, 50)
                for i, (title, book_id) in enumerate(book_info[10:], 11):  
                    print(f"{i}. {title}")
            else:
                pass

        selection = True
        while selection:
            choice = input(f"\nEnter a number (1-{len(book_info)}) to see details, or press Enter to skip: ")
            
            if choice.strip():
                try:
                    book_index = int(choice) - 1
                    if 0 <= book_index < len(book_info):
                        selected_title, selected_id = book_info[book_index]
                        print(f"\nYou selected: {selected_title}")
                        print(f"Book ID: {selected_id}")
                        print("Getting details...")
                        details = get_book_details(selected_id)
                        print(f"Author: {details['author']}")
                        print(f"Language: {details['language']}")
                        print(f"Release Date: {details['release_date']}")
                        print("\nAvailable formats:")
                        format_list = list(details['formats'].items())
                        for i, (format_name, url) in enumerate(format_list, 1):
                            print(f"  {i}. {format_name}")
                        if format_list:
                            download_choice = input(f"\nDownload a format? Enter number (1-{len(format_list)}) or press Enter to skip: ")
                            
                            if download_choice.strip():
                                try:
                                    format_index = int(download_choice) - 1
                                    if 0 <= format_index < len(format_list):
                                        format_name, url = format_list[format_index]
                                        
                                        # Create a safe filename
                                        safe_title = "".join(c for c in selected_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                                        safe_title = safe_title[:50]  # Limit length
                                        
                                        # Figure out file extension
                                        if '.epub3.' in url:
                                            extension = '.epub'
                                        elif '.epub.' in url:
                                            extension = '.epub'
                                        elif '.txt.' in url:
                                            extension = '.txt'
                                        elif '.kf8.' in url or '.kindle.' in url:
                                            extension = '.mobi'
                                        else:
                                            extension = '.download'
                                        
                                        filename = f"{safe_title}{extension}"
                                        download_book(url, filename)
                                        download_success = download_book(url, filename)
                                        # If it's an EPUB and download was successful, extract it
                                        if download_success and extension == '.epub':
                                            extract_choice = input("Extract EPUB contents? (y/n): ")
                                            if extract_choice.lower() in ['y', 'yes']:
                                                extract_epub(filename)
                                    else: 
                                        print("Invalid selection!")
                                except ValueError:
                                    print("Please enter a valid number!")
                        else: 
                            print("No download formats found.")
                    else:
                        print("Invalid selection!")
                except ValueError:
                    print("Please enter a valid number!")
            else:
                break

    else:
        print(f"No results found for {query}")

if __name__ == "__main__":
    typer.run(main)