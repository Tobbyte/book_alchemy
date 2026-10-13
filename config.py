"""Configuration for the Books Alchemy app."""

from pathlib import Path

PUBLICATION_YEAR_LENGTH = 4
PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = f"sqlite:///{PROJECT_ROOT / 'data/library.sqlite'}"
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
