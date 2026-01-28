from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class BookRead(Base):
    __tablename__ = "books_read"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str] = mapped_column(String(500))
    pages: Mapped[int] = mapped_column(Integer, nullable=True)
    date_started: Mapped[date] = mapped_column(Date, nullable=True)
    date_finished: Mapped[date] = mapped_column(Date, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
