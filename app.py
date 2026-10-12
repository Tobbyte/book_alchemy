# ruff: noqa
"""Asd."""

from datetime import date
import os
from typing import Any

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from data_models import Author, Book, db


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

    def index(self) -> str:
        return render_template("home.html")

    def add_author(self) -> str:
        # Logic to add an author to the database
        if request.method == "POST":
            self.add_author_to_db(request.form)

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

    def run(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Start the Flask app."""
        self.app.run(**kwargs)


app = Flask(__name__)

if __name__ == "__main__":
    book_alchemy = BookAlchemyApp(app)
    book_alchemy.create_tables()
    book_alchemy.run(debug=True, host="0.0.0.0")  # noqa: S104
