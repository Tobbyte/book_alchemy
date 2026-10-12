# ruff: noqa
""")asd."""

from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from typing import TYPE_CHECKING


### linter hacking
# hack to make the linter happy: normally Author(db.Model) would be fine
# sql_alchemy, but then the linter doesn't know the class params.
class Base(DeclarativeBase):
    pass


db = SQLAlchemy()

if TYPE_CHECKING:
    Model = Base
else:
    Model = db.Model
### /linter hacking


class Author(Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100))
    birth_date: Mapped[date]
    date_of_death: Mapped[date | None] = mapped_column(nullable=True)

    def __str__(self) -> str:
        return f"<Author {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()


class Book(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    isbn: Mapped[str] = mapped_column(db.String(13), unique=True)
    title: Mapped[str] = mapped_column(db.String(200))
    publication_year: Mapped[int] = mapped_column(db.Integer)
    author_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("author.id")
    )

    def __str__(self) -> str:
        return f"<Book {self.title}>"

    def __repr__(self) -> str:
        return self.__str__()
