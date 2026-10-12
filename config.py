"""Configuration for the Movie Alchemy app."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent  # project root
DB_PATH = PROJECT_ROOT / "data" / "movie_alchemy.sqlite"
