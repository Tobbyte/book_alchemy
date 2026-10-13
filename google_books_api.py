import os

import requests
from dotenv import load_dotenv

load_dotenv()
google_books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY")


def search_book_google(title):
    # Google Books endpoint (doesn't require a key for basic title searches)
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": title,
        "key": google_books_api_key,
    }

    for attempt in range(5):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt == 4:
                print(f"Google Books API Request failed: {e}")
                return None

    data = response.json()

    if "items" not in data:
        print("No books found matching that title.")
        return None

    print(
        f"got {len(data['items'])} results from Google Books API for title '{title}'.",
    )
    # Extract data from the first match
    volume_info = data["items"][0]["volumeInfo"]

    # 1. Title & Authors
    book_title = volume_info.get("title", "Unknown Title")
    author = volume_info.get("authors", ["Unknown Author"])[0]
    published_date = volume_info.get("publishedDate").split("-")[
        0
    ]  # Get only the year part

    # 2. Extract ISBN (Looking for ISBN_13 first, then ISBN_10)
    isbn = "N/A"
    identifiers = volume_info.get("industryIdentifiers", [])
    for id_type in identifiers:
        if id_type.get("type") in ["ISBN_13", "ISBN_10"]:
            isbn = id_type.get("identifier")
            if id_type.get("type") == "ISBN_13":  # Prefer ISBN_13
                break

    # 3. Extract Cover Image Link
    image_links = volume_info.get("imageLinks", {})
    # Google provides 'thumbnail' or 'smallThumbnail'
    cover_url = image_links.get(
        "thumbnail",
        image_links.get("smallThumbnail", ""),
    )

    return {
        "title": book_title,
        "author": author,
        "publication_year": published_date,
        "isbn": isbn,
        "cover_image_url": cover_url,
    }


# --- Example Usage ---
if __name__ == "__main__":
    search_term = "Dune"
    print(f"Searching Google Books for: '{search_term}'...\n")

    book_info = search_book_google(search_term)

    if book_info:
        print(f"Title:       {book_info['title']}")
        print(f"Author:      {book_info['author']}")
        print(f"ISBN:        {book_info['isbn']}")
        print(f"Cover URL:   {book_info['cover_image_url']}")
