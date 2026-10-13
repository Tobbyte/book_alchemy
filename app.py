# ruff: noqa
"""Asd."""
from datetime import date
import os
from typing import Any
import json
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

from data_models import Author, Book, db
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug import Response
from dotenv import load_dotenv
from helpers import (
    validate_int,
    validate_date,
)
from google_books_api import search_book_google

load_dotenv()

class BookAlchemyApp:
    """Asd.

    When searching for a book and the author is not in the database,
    the author will be added automatically to db.

    Limitations:
    - only one author per book
    - no validation for duplicate authors or books (by title)
    - when authors automatically added via search, only name is populated.
      Requesting additional author info (birth date, death date) is out of
      scope for this project.
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

    def create_tables(self):
        """Asd."""
        with self.app.app_context():
            self.db.create_all()

    def register_routes(self):
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
        return render_template(
            "home.html",
            books=db.session.scalars(
                select(Book).options(joinedload(Book.author))
                # note to self: the option joinedload is used to eager load the author relationship,
                # so that we don't have to make a separate query for each book's author when rendering the template.
            ).all(),
        )

    def add_author(self) -> str | Response:
        # Logic to add an author to the database
        if request.method == "POST":
            try:
                new_author = self.add_author_to_db(request.form)
            except Exception as e:
                # if fields have errors, err messages are returned
                for msg in e.args[0]:
                    flash(msg, "error")
                return redirect(url_for("add_author"))

            flash(f"Autor {new_author.name} wurde hinzugefügt.", "success")  # pyright: ignore[reportOptionalMemberAccess]
            return redirect(url_for("add_author"))

        return render_template("add_author.html")

    def add_author_to_db(self, form_data: dict[str, Any]) -> None | Author:
        """Add an author to the database."""
        name = form_data.get("name", "").strip()
        birth_date = form_data.get("birthdate", "").strip()
        date_of_death = form_data.get("date_of_death", "").strip()

        if not name or not birth_date:
            # Handle missing required fields
            err_msg = "Name and birth date are required."
            raise ValueError(err_msg)

        # bundle possible errors to show all at once
        errors = [
            err
            for err in [
                validate_date(birth_date, "Birth Date", nullable=True),
                validate_date(date_of_death, "Date of Death", nullable=True),
            ]
        ]
        if any(errors):
            raise ValueError(errors)

        new_author = Author(
            name=name,
            birth_date=date.fromisoformat(birth_date),
            date_of_death=date_of_death or None,
        )

        self.db.session.add(new_author)
        self.db.session.commit()

        return new_author

    def add_book(self) -> str | Response:
        # Logic to add a book to the database
        all_authors = list(db.session.scalars(select(Author)).all())
        search_query = request.args.get("search_query", "").strip()

        if search_query:
            search_result = search_book_google(search_query)
            search_results = [search_result] if search_result else None

            if search_results is None:
                flash("No books found matching that title.", "error")
                return redirect(url_for("add_book"))
            return render_template(
                "add_book.html",
                authors=all_authors,
                search_results=search_results,
                search_query=search_query,
            )

        if request.method == "POST":
            request_data = request.form
            book_data = request_data.get("book_data")
            if book_data:
                # If book_data is provided, it means the user selected a book from the search results.
                # It's not sure if the author is in our db, so we need to check and add the author if necessary.
                print(f"Book data received: {book_data}")
                book_data_dict = json.loads(book_data.replace("'", '"'))
                author = book_data_dict.get("author")
                known_author = db.session.scalars(
                    select(Author).where(Author.name == author)
                ).first()
                if not known_author:
                    # If the author is not in the database, add them.
                    author = Author(
                        name=author,
                        birth_date=None,
                        date_of_death=None,
                    )
                    self.db.session.add(author)
                    self.db.session.commit()
                title = book_data_dict.get("title")
                isbn = book_data_dict.get("isbn")
                if not validate_int(
                    isbn, "ISBN", max_length=13, nullable=True
                ):
                    isbn = None

                publication_year = book_data_dict.get("publication_year")
                if not validate_int(
                    publication_year,
                    "Publication Year",
                    max_length=4,
                    nullable=True,
                ):
                    publication_year = None
                cover_image_url = book_data_dict.get("cover_image_url")
                if not cover_image_url.startswith("http"):
                    cover_image_url = None
                request_data = {
                    "title": title,
                    "isbn": isbn,
                    "publication_year": book_data_dict.get("publication_year"),
                    "cover_image_url": book_data_dict.get("cover_image_url"),
                    "author_id": known_author.id
                    if known_author
                    else author.id,
                }
                print("request_data", request_data)

            try:
                new_book = self.add_book_to_db(request_data)
            except Exception as e:
                print(e)
                # if fields have errors, err messages are returned
                for msg in e.args[0]:
                    if msg:
                        flash(msg, "error")
                return self.render_add_book_form(authors=all_authors)

            flash(f"Book {new_book.title} wurde hinzugefügt.", "success")  # pyright: ignore[reportOptionalMemberAccess]
            return self.render_add_book_form(authors=all_authors)

        return render_template("add_book.html", authors=all_authors)

    def render_add_book_form(self, authors: list[Author]) -> str:
        """Render the add book form with the list of authors."""
        return render_template("add_book.html", authors=authors)

    def add_book_to_db(self, form_data: dict[str, Any]) -> None | Book:
        """Add a book to the database."""
        title = form_data.get("title", "")
        author_id = form_data.get("author_id", "")
        isbn = form_data.get("isbn", "")
        publication_year = form_data.get("publication_year", "")
        cover_image_url = form_data.get("cover_image_url")

        if not title or not author_id:
            err_msg = "Title and author ID are required."
            raise ValueError(err_msg)
        # bundle possible errors to show all at once
        errors = [
            err
            for err in [
                validate_int(
                    publication_year,
                    "Publication Year",
                    max_length=4,
                    nullable=True,
                ),
                validate_int(isbn, "ISBN", max_length=13, nullable=True),
            ]
        ]
        if isbn and len(isbn) not in [10, 13]:
            errors.append("ISBN must be either 10 or 13 digits long.")

        author_id = db.session.get(Author, author_id)
        if not author_id:
            errors.append("Author ID does not exist.")
        else:
            author_id = author_id.id

        if any(errors):
            raise ValueError(errors)

        new_book = Book(
            title=title,
            isbn=isbn if isbn else None,
            publication_year=int(publication_year)
            if publication_year
            else None,
            cover_image_url=cover_image_url,
            author_id=int(author_id),  # from db, save # pyright: ignore[reportArgumentType]
        )

        self.db.session.add(new_book)
        self.db.session.commit()

        return new_book

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
    book_alchemy.reset_database()
    book_alchemy.create_tables()
    book_alchemy.run(debug=True, host="0.0.0.0")  # noqa: S104
