"""Configuration for the Books Alchemy app."""

from pathlib import Path

PUBLICATION_YEAR_LENGTH = 4
PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = PROJECT_ROOT / "data" / "library.sqlite"
DB_PATH.parent.mkdir(exist_ok=True)
KEY_NOT_SET_ERR = "Key not set"
FLASH_ERR_BOOK_NOT_FOUND = "Book not found."
FLASH_BOOK_ADDED = 'Book "{book_title}" was added.'
FLASH_BOOK_DELETED = 'Book "{book_title}" was deleted.'
FLASSH_ERR_NO_RESULT = "No books found matching that title."
ERR_NO_AUTHOR_NAME = "No author name."
ERR_PUB_YEAR_MUST_BE_4_DIGITS = "Publication Year must be a 4 digits."
ERR_NAME_REQUIRED = "Name is required."

FILED_NAME_REQUIRED_ERR = "{filed_name} is required."
FIELD_NAME_MUST_BE_INT_ERR = "{filed_name} must be a whole number."
FIELD_NAME_MUST_BE_MAX_LENGTH_ERR = (
    "{filed_name} must be max {max_length} digits long."
)
ISBN_INVALID = "{isbn} must be 10 or 13 digits long (ISBN-10 may end with X)."
FILED_NAME_MUST_BE_VALID_DATE = (
    "{field_name} must be valid date in format YYYY-MM-DD."
)
ISBN_ALREADY_IN_DB = "ISBN already in db."

MAX_RETRIES = 5
RETRY_DELAY = 0.5
GOOGLE_BOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_API_STATUS_503 = 503
GOOGLE_API_MAX_RESULTS = 10
ERR_MSG_GOOGLE_RETUREND_503 = (
    "Google Books API returned 503 (attempt {attempt})."
)
ERR_NO_BOOKS_FOUND_FOR_TITLE = "No books found matching that title."
GOOGLE_API_REQUEST_FAILD = "Google Books API Request failed: {e}"
GOOGLE_API_UNAVAIULABLE = (
    "Google Books is temporarily unavailable (tried {attempts}x)."
)
