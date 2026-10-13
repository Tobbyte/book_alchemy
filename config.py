"""Configuration for the Books Alchemy app."""

from pathlib import Path

PUBLICATION_YEAR_LENGTH = 4
PROJECT_ROOT = Path(__file__).parent.resolve()
DB_PATH = f"sqlite:///{PROJECT_ROOT / 'data/library.sqlite'}"
FLASK_APP_SECRET_KEY_KEY = "SECRET_KEY"  # noqa: S105
KEY_NOT_SET_ERR = "Key not set"
FLASH_ERR_BOOK_NOT_FOUND = "Book not found."
FLASH_BOOK_ADDED = 'Book "{book_title}" was added.'
FLASH_BOOK_DELETED = 'Book "{book_title}" was deleted.'
FLASSH_ERR_NO_RESULT = "No books found matching that title."
ERR_NO_AUTHOR_NAME = "No author name."
ERR_PUB_YEAR_MUST_BE_4_DIGITS = "Publication Year must be a 4 digits."
ERR_NAME_REQUIRED = "Name is required."
