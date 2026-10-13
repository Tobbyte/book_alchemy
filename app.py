"""BookAlchemy Flask App.

Limitations:
    - only one author per book
    - no validation for duplicate authors or title when adding manually
    - when authors automatically added via search, only name is filled.
      Requesting additional author info (birth date, death date) is out
      would need another api and is of scope for this project.
    - cover images only from search by api

    Dear reviewer: Since not explicitly requested, there's no error
    route handling and only basic validations.
    I will come back to this to clean up for my portfolio, but for
    this codio, I hope you can accept this as a working solution.
    (https://cdn-v2.meme.com/memes/aint-nobody-got-time/
    aint-nobody-got-time-dismissive-expression.webp)
"""

import os
from datetime import date
from typing import Any

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager
from werkzeug import Response

from config import (
    DB_PATH,
    ERR_NAME_REQUIRED,
    ERR_NO_AUTHOR_NAME,
    ERR_PUB_YEAR_MUST_BE_4_DIGITS,
    FLASH_BOOK_ADDED,
    FLASH_BOOK_DELETED,
    FLASH_ERR_BOOK_NOT_FOUND,
    FLASSH_ERR_NO_RESULT,
    ISBN_ALREADY_IN_DB,
    KEY_NOT_SET_ERR,
    PUBLICATION_YEAR_LENGTH,
)
from data_models import Author, Book, db
from google_books_api import GoogleBooksUnavailableError, search_book_google
from helpers import validate_date, validate_int, validate_isbn

load_dotenv()


class ValidationError(Exception):
    """Bundles all validation errors of a form."""

    def __init__(self, errors: list[str]) -> None:
        """Init base with custom errors."""
        super().__init__(errors)
        self.errors = errors


def raise_if_errors(errors: list[str | None]) -> None:
    """Raise a ValidationError if at least one error is present.

    The validate_* functions return None/"" for valid values, so empty
    entries are filtered out here.
    """
    real_errors = [err for err in errors if err]
    if real_errors:
        raise ValidationError(real_errors)


def as_clean_str(value: Any) -> str:  # noqa: ANN401
    """Convert a form/JSON value to a stripped string ("" for None)."""
    return "" if value is None else str(value).strip()


def flash_errors(errors: list[str]) -> None:
    """Flask flash all errors from list to display all at once."""
    for msg in errors:
        flash(msg, "error")


class BookAlchemyApp:
    """BookAlchemy Flask App.

    Add books manually or search for them via Google Books API.
    If the author is not in the database, it will be added
    automatically.
    """

    def __init__(self, app: Flask) -> None:  # pylint: disable=redefined-outer-name
        """Init main app with db and routes."""
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
        super_secret_key = os.getenv(
            "SECRET_KEY",
        )  # needed for session (flash messages)

        if not super_secret_key:
            raise ValueError(KEY_NOT_SET_ERR)

        app.secret_key = super_secret_key

        db.init_app(app)

        self.app = app
        self.db = db
        self.register_routes()

    def create_tables(self) -> None:
        """Create all tables for db."""
        with self.app.app_context():
            self.db.create_all()

    def register_routes(self) -> None:
        """Register routes."""
        self.app.add_url_rule(
            "/",
            view_func=self.index,
            methods=["GET"],
        )

        self.app.add_url_rule(
            "/add_author",
            view_func=self.add_author,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/add_book",
            view_func=self.add_book,
            methods=["GET", "POST"],
        )

        self.app.add_url_rule(
            "/book/<int:book_id>/delete",
            view_func=self.delete_book,
            methods=["POST"],
        )

    def index(self) -> str:
        """Render the home page with a list of books."""
        sort = request.args.get("sort", "title")

        if sort == "author":
            order_by = (func.lower(Author.name), func.lower(Book.title))
        else:
            sort = "title"
            order_by = (func.lower(Book.title),)

        # user searched on homepage
        search_query = request.args.get("search_query", "").strip()

        if search_query:
            books = db.session.scalars(
                select(Book)
                .join(Book.author)
                .options(contains_eager(Book.author))
                .filter(func.lower(Book.title).contains(search_query.lower()))
                .order_by(*order_by),
            ).all()

            return render_template(
                "home.html",
                books=books,
                sort=sort,
                search_query=search_query,
            )

        books = db.session.scalars(
            select(Book)
            .join(Book.author)
            # note to self: eager load with existing join to avoid lazy
            # load query per book
            .options(contains_eager(Book.author))
            .order_by(*order_by),
        ).all()
        return render_template("home.html", books=books, sort=sort)

    def add_author(self) -> str | Response:
        """Add an author to the database."""
        if request.method == "POST":
            try:
                new_author = self.add_author_to_db(request.form)
            except ValidationError as err:
                flash_errors(err.errors)
            else:
                flash(f"Author {new_author.name} was added.", "success")
            return redirect(url_for("add_author"))

        return render_template("add_author.html")

    def add_book(self) -> str | Response:
        """Add a book to the database."""
        if request.method == "POST":
            return self.handle_add_book_post()

        search_query = request.args.get("search_query", "").strip()
        if search_query:
            return self.handle_book_search(search_query)

        return self.render_add_book()

    def delete_book(self, book_id: int) -> Response:
        """Delete a book from the database.

        If the author has no other books, delete the author as well.
        """
        book = db.session.get(Book, book_id)
        if book is None:
            flash(FLASH_ERR_BOOK_NOT_FOUND, "error")
            return redirect(url_for("index"))

        book_title = book.title
        author = book.author
        has_other_books = (
            db.session.scalar(
                select(Book.id)
                .where(Book.author_id == book.author_id, Book.id != book.id)
                .limit(1),
            )
            is not None
        )

        db.session.delete(book)

        if not has_other_books:
            db.session.delete(author)

        db.session.commit()

        flash(FLASH_BOOK_DELETED.format(book_title=book_title), "success")
        return redirect(url_for("index"))

    def handle_book_search(self, search_query: str) -> str | Response:
        """Handle search via api in add_book route."""
        try:
            result = search_book_google(search_query)

        except GoogleBooksUnavailableError as err:
            # google books api often throws 503.
            flash(str(err), "error")
            return render_template(
                "add_book.html",
                authors=self.get_all_authors(),
                search_failed=True,
                search_query=search_query,
            )

        if result is None:
            flash(FLASSH_ERR_NO_RESULT, "error")
            return redirect(url_for("add_book"))

        return render_template(
            "add_book.html",
            authors=self.get_all_authors(),
            search_results=result,
            search_query=search_query,
        )

    def handle_add_book_post(self) -> str:
        """Add a book, either from a search result or from manually.

        Search results send the author as a name (author_name),
        the manual form sends the id of an existing author (author_id).
        """
        try:
            form_data = request.form.to_dict()
            author_name = form_data.get("author_name")
            if author_name:
                # from api
                form_data["author_id"] = str(
                    self.get_or_create_author(author_name).id,
                )

            new_book = self.add_book_to_db(form_data)

        except ValidationError as err:
            db.session.rollback()  # discard new author
            flash_errors(err.errors)

        else:
            flash(
                FLASH_BOOK_ADDED.format(book_title=new_book.title),
                "success",
            )

        return self.render_add_book()

    def get_or_create_author(self, name: str | None) -> Author:
        """Get an existing author by name or create a new one."""
        name = as_clean_str(name)
        if not name:
            raise ValidationError([ERR_NO_AUTHOR_NAME])

        author = db.session.scalars(
            select(Author).where(Author.name == name),
        ).first()

        if author is None:
            author = Author(name=name, birth_date=None, date_of_death=None)
            db.session.add(author)
            db.session.flush()  # assigns the id without committing yet
            # to rollback in add book if adding book fails.
        return author

    def get_all_authors(self) -> list[Author]:
        """Get all authors from the database."""
        return list(db.session.scalars(select(Author)).all())

    def render_add_book(self) -> str:
        """Render add_book route."""
        return render_template("add_book.html", authors=self.get_all_authors())

    def add_book_to_db(self, form_data: Any) -> Book:  # noqa: ANN401
        """Add a book to the database."""
        title = as_clean_str(form_data.get("title"))
        author_id = as_clean_str(form_data.get("author_id"))
        isbn = as_clean_str(form_data.get("isbn")).replace("-", "")
        publication_year = as_clean_str(form_data.get("publication_year"))
        cover_image_url = as_clean_str(form_data.get("cover_image_url"))

        if not cover_image_url.startswith(("http://", "https://")):
            cover_image_url = ""

        author = db.session.get(Author, author_id) if author_id else None

        # bundle possible errors to show all at once
        errors: list[str | None] = [
            None if title else "Title is required.",
            None if author else "Author does not exist.",
            ERR_PUB_YEAR_MUST_BE_4_DIGITS
            if publication_year
            and len(publication_year) != PUBLICATION_YEAR_LENGTH
            else None,
            validate_int(
                publication_year,
                "Publication Year",
                max_length=4,
                nullable=True,
            ),
            validate_isbn(isbn, "ISBN", nullable=True),
        ]
        raise_if_errors(errors)

        new_book = Book(
            title=title,
            isbn=isbn or None,
            publication_year=int(publication_year)
            if publication_year
            else None,
            cover_image_url=cover_image_url or None,
            author_id=author.id,  # pyright: ignore[reportOptionalMemberAccess]
        )

        self.db.session.add(new_book)
        try:
            self.db.session.commit()
        except IntegrityError as e:
            self.db.session.rollback()
            if "UNIQUE constraint failed: book.isbn" in str(e):
                raise ValidationError([ISBN_ALREADY_IN_DB]) from None
            raise

        return new_book

    def add_author_to_db(self, form_data: Any) -> Author:  # noqa: ANN401
        """Add an author to the database."""
        name = as_clean_str(form_data.get("name"))
        birth_date = as_clean_str(form_data.get("birthdate"))
        date_of_death = as_clean_str(form_data.get("date_of_death"))

        # bundle possible errors to show all at once
        errors: list[str | None] = [
            None if name else ERR_NAME_REQUIRED,
            validate_date(birth_date, "Birth Date"),
            validate_date(date_of_death, "Date of Death", nullable=True),
        ]

        raise_if_errors(errors)

        new_author = Author(
            name=name,
            birth_date=date.fromisoformat(birth_date),
            date_of_death=(
                date.fromisoformat(date_of_death) if date_of_death else None
            ),
        )
        self.db.session.add(new_author)
        self.db.session.commit()
        return new_author

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)

    def reset_database(self) -> None:
        """Reset the database by dropping and recreating all tables."""
        with self.app.app_context():
            self.db.drop_all()
            self.db.create_all()


app = Flask(__name__)

if __name__ == "__main__":
    book_alchemy = BookAlchemyApp(app)
    # book_alchemy.reset_database()  # noqa: ERA001
    book_alchemy.create_tables()
    # book_alchemy.run(debug=True)  # noqa: ERA001
    # codio needs host binding.
    book_alchemy.run(debug=True, host="0.0.0.0")  # noqa: S104
