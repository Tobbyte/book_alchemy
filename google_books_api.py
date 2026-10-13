import os

import requests
from dotenv import load_dotenv

load_dotenv()


def search_book_google(title):
    url = "https://www.googleapis.com/books/v1/volumes"
    google_books_api_key = os.getenv(
        "GOOGLE_BOOKS_API_KEY",
    )  # optional, stored in .env
    params = {
        "q": title,
        "key": google_books_api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
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
        published_date = volume_info.get("publishedDate")
        publication_year = (
            published_date.split("-")[0] if published_date else None
        )

        # 2. Extract ISBN could be 10 or 13
        isbn = None
        identifiers = volume_info.get("industryIdentifiers", [])
        for id_type in identifiers:
            if id_type.get("type") in ["ISBN_13", "ISBN_10"]:
                isbn = id_type.get("identifier")
                if id_type.get("type") == "ISBN_13":  # Prefer 13
                    break

        # 3. Extract Cover Image Link
        image_links = volume_info.get("imageLinks", {})
        cover_url = image_links.get(
            "thumbnail",
            image_links.get("smallThumbnail", ""),
        )

    except (requests.exceptions.RequestException, ValueError) as e:
        # TODO: retry on 503 Server Error
        print(f"Google Books API Request failed: {e}")
        return None

    return {
        "title": book_title,
        "author": author,
        "publication_year": publication_year,
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
