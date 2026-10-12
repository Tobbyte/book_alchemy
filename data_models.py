# ruff: noqa
""")asd."""

from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import TYPE_CHECKING


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Author(Base):
    __tablename__ = "author"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100))
    birth_date: Mapped[date]
    date_of_death: Mapped[date | None] = mapped_column(nullable=True)

    def __str__(self) -> str:
        return f"<Author {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()


class Book(Base):
    __tablename__ = "book"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(
        db.String(13), unique=True, nullable=True
    )  # str for easy char length constraint
    title: Mapped[str] = mapped_column(db.String(200))
    publication_year: Mapped[int] = mapped_column(db.Integer, nullable=True)
    author_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("author.id")
    )
    author: Mapped["Author"] = relationship()

    def __str__(self) -> str:
        return f"<Book {self.title}>"

    def __repr__(self) -> str:
        return self.__str__()
