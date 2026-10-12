# ruff: noqa
"""Asd."""

from datetime import date
import os
from typing import Any

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

from data_models import Author, Book, db
from sqlalchemy import select
from werkzeug import Response


class BookAlchemyApp:
    """Asd."""

    def __init__(self, app: Flask):
        """Asd."""
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
        )
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
            "home.html", books=db.session.scalars(select(Book)).all()
        )

    def add_author(self) -> str | tuple[Response, int]:
        # Logic to add an author to the database
        if request.method == "POST":
            try:
                self.add_author_to_db(request.form)
            except Exception as e:
                print(f"Error adding author: {e}")
                return render_template(
                    "add_author.html",
                    error_message="An error occurred while adding the author.",
                )
            return redirect(url_for("index")), 303

        return render_template("add_author.html")

    def add_author_to_db(self, form_data: dict[str, Any]) -> None:
        """Add an author to the database."""
        name = form_data.get("name")
        birth_date = form_data.get("birthdate")
        print(birth_date)
        date_of_death = form_data.get("date_of_death")

        if not name or not birth_date:
            # Handle missing required fields
            print("Name and birth date are required.")
            return
        try:
            birth_date = date.fromisoformat(birth_date)
            date_of_death = (
                date.fromisoformat(date_of_death) if date_of_death else None
            )
        except ValueError:
            print("Invalid birth date format. Use YYYY-MM-DD.")
            return

        new_author = Author(
            name=name,
            birth_date=birth_date,
            date_of_death=date_of_death or None,
        )

        self.db.session.add(new_author)
        self.db.session.commit()

    def add_book(self) -> str | tuple[Response, int]:
        # Logic to add a book to the database
        if request.method == "POST":
            try:
                self.add_book_to_db(request.form)
            except Exception as e:
                print(f"Error adding book: {e}")
                return render_template(
                    "add_book.html",
                    authors=db.session.scalars(select(Author)).all(),
                    error_message="An error occurred while adding the book.",
                )
            return redirect(url_for("index")), 303

        return render_template(
            "add_book.html", authors=db.session.scalars(select(Author)).all()
        )

    def add_book_to_db(self, form_data: dict[str, Any]) -> None:
        """Add a book to the database."""
        title = form_data.get("title")
        isbn = form_data.get("isbn")
        publication_year = form_data.get("publication_year")
        author_id = form_data.get("author_id")

        if not title or not author_id:
            # Handle missing required fields
            print("Title and author ID are required.")
            return

        try:
            publication_year = (
                int(publication_year) if publication_year else None
            )
            author_id = int(author_id)
        except ValueError:
            print("Invalid publication year or author ID format.")
            return

        new_book = Book(
            title=title,
            isbn=self.nullify_empty_string(isbn),
            publication_year=publication_year,
            author_id=author_id,
        )

        self.db.session.add(new_book)
        self.db.session.commit()

    @staticmethod
    def nullify_empty_string(value: str | None) -> str | None:
        """Convert empty strings to None."""
        if value is not None and value.strip() == "":
            return None
        return value

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
    book_alchemy.run(debug=True, host="0.0.0.0")  # noqa: S104
