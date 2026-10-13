"""Data models for the BookAlchemy app."""

from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


db = SQLAlchemy(model_class=Base)


class Author(Base):
    """Data model for an author."""

    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100))
    birth_date: Mapped[date | None] = mapped_column(nullable=True)
    date_of_death: Mapped[date | None] = mapped_column(nullable=True)

    def __str__(self) -> str:
        """Return a string representation of the Author object."""
        return f"<Author {self.name}>"

    def __repr__(self) -> str:
        """Return a string representation of the Author object."""
        return self.__str__()


class Book(Base):
    """Data model for a book."""

    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(
        db.String(13),
        unique=True,
        nullable=True,
    )  # str for easy char length constraint
    title: Mapped[str] = mapped_column(db.String(200))
    publication_year: Mapped[int] = mapped_column(db.Integer, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(
        db.String(500),
        nullable=True,
    )
    author_id: Mapped[int] = mapped_column(
        db.Integer,
        db.ForeignKey("author.id"),
    )
    author: Mapped["Author"] = relationship()

    def __str__(self) -> str:
        """Return a string representation of the Book object."""
        return f"<Book {self.title}>"

    def __repr__(self) -> str:
        """Return a string representation of the Book object."""
        return self.__str__()
