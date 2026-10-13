# ruff: noqa

import os
from datetime import date
from typing import Any

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug import Response

from data_models import Author, Book, db
from google_books_api import GoogleBooksUnavailableError, search_book_google
from helpers import validate_date, validate_int
from sqlalchemy import func, select
from sqlalchemy.orm import contains_eager

load_dotenv()


class ValidationError(Exception):
    """Bundles all validation errors of a form."""

    def __init__(self, errors: list[str]) -> None:
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


def as_clean_str(value: Any) -> str:
    """Convert a form/JSON value to a stripped string ("" for None)."""
    return "" if value is None else str(value).strip()


def flash_errors(errors: list[str]) -> None:
    for msg in errors:
        flash(msg, "error")


class BookAlchemyApp:
    """Asd.

    When searching for a book and the author is not in the database,
    the author will be added automatically to db (name only).

    Limitations:
    - only one author per book
    - no validation for duplicate authors or books (by title)
    - when authors automatically added via search, only name is populated.
      Requesting additional author info (birth date, death date) is out of
      scope for this project.
    - cover images only from search by api
    """

    def __init__(self, app: Flask):
        """Asd."""
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
        )

        super_secret_key = os.getenv(
            "SECRET_KEY"
        )  # needed for session (flash messages)
        if not super_secret_key:
            err_msg = "KEY_NOT_SET_ERROR"
            raise ValueError(err_msg)

        app.secret_key = super_secret_key

        db.init_app(app)

        self.app = app
        self.db = db
        self.register_routes()

    def create_tables(self) -> None:
        """Asd."""
        with self.app.app_context():
            self.db.create_all()

    def register_routes(self) -> None:
        """Asd."""
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

    def index(self) -> str:
        sort = request.args.get("sort", "title")

        if sort == "author":
            # title is tie-breaker
            order_by = (func.lower(Author.name), func.lower(Book.title))
        else:
            sort = "title"
            order_by = (func.lower(Book.title),)

        search_query = request.args.get("search_query", "").strip()
        if search_query:
            books = db.session.scalars(
                select(Book)
                .join(Book.author)
                .options(contains_eager(Book.author))
                .filter(func.lower(Book.title).contains(search_query.lower()))
                .order_by(*order_by)
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
            .options(contains_eager(Book.author))
            .order_by(*order_by)
        ).all()
        return render_template("home.html", books=books, sort=sort)

    def add_author(self) -> str | Response:
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
        if request.method == "POST":
            return self.handle_add_book_post()

        search_query = request.args.get("search_query", "").strip()
        if search_query:
            return self.handle_book_search(search_query)

        return self.render_add_book_form()

    def handle_book_search(self, search_query: str) -> str | Response:
        try:
            result = search_book_google(search_query)
        except GoogleBooksUnavailableError as err:
            flash(str(err), "error")
            return render_template(
                "add_book.html",
                authors=self.get_all_authors(),
                search_failed=True,
                search_query=search_query,
            )

        if result is None:
            flash("No books found matching that title.", "error")
            return redirect(url_for("add_book"))

        return render_template(
            "add_book.html",
            authors=self.get_all_authors(),
            search_results=[result],
            search_query=search_query,
        )

    def handle_add_book_post(self) -> str:
        """Add a book, either from a search result or from the manual form.

        Search results send the author as a name (author_name), the manual
        form sends the id of an existing author (author_id).
        """
        try:
            form_data = request.form.to_dict()
            author_name = form_data.get("author_name")
            if author_name:
                form_data["author_id"] = str(
                    self.get_or_create_author(author_name).id
                )
            new_book = self.add_book_to_db(form_data)
        except ValidationError as err:
            db.session.rollback()  # discard new author
            flash_errors(err.errors)
        else:
            flash(f"Book {new_book.title} was added.", "success")
        return self.render_add_book_form()

    def get_or_create_author(self, name: str | None) -> Author:
        name = as_clean_str(name)
        if not name:
            raise ValidationError(["Author name is missing."])

        author = db.session.scalars(
            select(Author).where(Author.name == name)
        ).first()
        if author is None:
            author = Author(name=name, birth_date=None, date_of_death=None)
            db.session.add(author)
            db.session.flush()  # assigns the id without committing yet
        return author

    def get_all_authors(self) -> list[Author]:
        return list(db.session.scalars(select(Author)).all())

    def render_add_book_form(self) -> str:
        return render_template("add_book.html", authors=self.get_all_authors())

    def add_book_to_db(self, form_data: Any) -> Book:
        title = as_clean_str(form_data.get("title"))
        author_id = as_clean_str(form_data.get("author_id"))
        isbn = as_clean_str(form_data.get("isbn"))
        publication_year = as_clean_str(form_data.get("publication_year"))
        cover_image_url = as_clean_str(form_data.get("cover_image_url"))

        if not cover_image_url.startswith(("http://", "https://")):
            cover_image_url = ""

        author = db.session.get(Author, author_id) if author_id else None

        # bundle possible errors to show all at once

        errors: list[str | None] = [
            None if title else "Title is required.",
            None if author else "Author does not exist.",
            "ISBN must be either 10 or 13 digits long."
            if isbn and len(isbn) not in (10, 13)
            else None,
            "Publication Year must be a 4-digit year."
            if publication_year and len(publication_year) != 4
            else None,
            validate_int(
                publication_year,
                "Publication Year",
                max_length=4,
                nullable=True,
            ),
            validate_int(isbn, "ISBN", max_length=13, nullable=True),
        ]
        raise_if_errors(errors)

        new_book = Book(
            title=title,
            isbn=isbn if isbn else None,
            publication_year=int(publication_year)
            if publication_year
            else None,
            cover_image_url=cover_image_url or None,
            author_id=author.id,  # save # pyright: ignore[reportOptionalMemberAccess]
        )

        self.db.session.add(new_book)
        self.db.session.commit()

        return new_book

    def add_author_to_db(self, form_data: Any) -> Author:
        name = as_clean_str(form_data.get("name"))
        birth_date = as_clean_str(form_data.get("birthdate"))
        date_of_death = as_clean_str(form_data.get("date_of_death"))

        # bundle possible errors to show all at once
        errors: list[str | None] = [
            None if name else "Name is required.",
            None if birth_date else "Birth date is required.",
            validate_date(birth_date, "Birth Date", nullable=True),
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
    # book_alchemy.reset_database()
    book_alchemy.create_tables()
    # book_alchemy.run(debug=True, host="0.0.0.0")  # noqa: S104
    book_alchemy.run(debug=True)  # noqa: S104