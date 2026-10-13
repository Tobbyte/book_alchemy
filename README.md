# Book Alchemy

A small Flask app for building and browsing a personal book shelf.

## Features

- View, search, and sort books by title or author
- Add books manually or choose from Google Books API search.
- Add author details
- Delete books and remove authors who no longer have any books
- Store data locally in SQLite
- Click a book to see it's details

## Setup

### Requirements

- Python 3.11 or newer

### Install

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=replace-with-a-random-secret
GOOGLE_BOOKS_API_KEY=your-google-books-api-key (optional, works without!)
```

`SECRET_KEY` is required for Flask session and flash-message support. The Google
Books API key is optional; manual book entry works without it.

## Run

```bash
python app.py
```

Open <http://127.0.0.1:5000> in a browser.

The application creates the SQLite tables on startup. The database is stored at
`data/library.sqlite` and is not recreated between runs.

## How to use

1. Open **Add Author** to add an author and optional date-of-death information.
2. Open **Add Book** to enter a book manually, or search for a title and choose a result to add to your shelf.
3. Use the home page to search, sort, inspect, or delete books.

## Project structure

```text
app.py                 Flask application and routes
config.py              Application and validation messages
data_models.py         SQLAlchemy Author and Book models
google_books_api.py    Google Books API integration
helpers.py             Form validation helpers
templates/             Jinja HTML templates
static/                CSS
data/library.sqlite    Local application database
```

## Notes

- Each book supports only one author.
- Google Books searches display up to 10 matching results.
- Google Books doesn't provide author details except name.
- The built-in Flask server is intended for local development, not production
  deployment.


## Acknowledgement

- Made with ❤️ and without ai (except this readme and html styling).