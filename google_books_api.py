"""Module to search for books using the Google Books API."""

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 5
RETRY_DELAY = 0.5
GOOGLE_BOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_API_STATUS_503 = 503
ERR_MSG_GOOGLE_RETUREND_503 = (
    "Google Books API returned 503 (attempt {attempt})."
)
ERR_NO_BOOKS_FOUND_FOR_TITLE = "No books found matching that title."
GOOGLE_API_REQUEST_FAILD = "Google Books API Request failed: {e}"
GOOGLE_API_UNAVAIULABLE = (
    "Google Books is temporarily unavailable (tried {attempts}x)."
)


class GoogleBooksUnavailableError(Exception):
    """The Google Books API could not be reached or kept failing."""


def search_book_google(title: str) -> dict[str, Any] | None:  # pylint: disable=too-many-locals
    """Search for a book by title using the Google Books API."""
    url = GOOGLE_BOKS_API_URL
    google_books_api_key = os.getenv(
        "GOOGLE_BOOKS_API_KEY",
    )  # optional, stored in .env
    params = {"q": title, "key": google_books_api_key}

    attempts = 0
    try:
        # The API often answers with a temporary 503, so retry those.
        for attempt in range(MAX_RETRIES + 1):
            attempts = attempt + 1
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != GOOGLE_API_STATUS_503:
                break
            print(
                ERR_MSG_GOOGLE_RETUREND_503.format(
                    attempt=attempts / MAX_RETRIES + 1,
                ),
            )
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            print(ERR_NO_BOOKS_FOUND_FOR_TITLE)
            return None

        # use first match
        volume_info = data["items"][0]["volumeInfo"]

        book_title = volume_info.get("title", "Unknown Title")
        author = volume_info.get("authors", ["Unknown Author"])[0]
        published_date = volume_info.get("publishedDate")
        publication_year = (
            # comes as YYYY-MM-DD from api, split for year only
            published_date.split("-")[0] if published_date else None
        )

        isbn = None
        identifiers = volume_info.get("industryIdentifiers", [])
        for id_type in identifiers:
            if id_type.get("type") in ["ISBN_13", "ISBN_10"]:
                isbn = id_type.get("identifier")
                if id_type.get("type") == "ISBN_13":
                    break

        image_links = volume_info.get("imageLinks", {})
        cover_url = image_links.get(
            "thumbnail",
            image_links.get("smallThumbnail", ""),
        )

    except (requests.exceptions.RequestException, ValueError) as e:
        # ValueError: response body was not valid JSON
        print(GOOGLE_API_REQUEST_FAILD.format(e=e))
        raise GoogleBooksUnavailableError(
            GOOGLE_API_UNAVAIULABLE.format(attempts=attempts),
        ) from None  # hide e, the request would include API key!

    return {
        "title": book_title,
        "author": author,
        "publication_year": publication_year,
        "isbn": isbn,
        "cover_image_url": cover_url,
    }


# DEBUG
if __name__ == "__main__":
    search_term = "Dune"
    print(f"Searching Google Books for: '{search_term}'...\n")

    try:
        book_info = search_book_google(search_term)
    except GoogleBooksUnavailableError as err:
        print(err)
        book_info = None

    if book_info:
        print(f"Title:       {book_info['title']}")
        print(f"Author:      {book_info['author']}")
        print(f"ISBN:        {book_info['isbn']}")
        print(f"Cover URL:   {book_info['cover_image_url']}")
