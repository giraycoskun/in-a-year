from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    media_type: Mapped[str] = mapped_column(String(50))  # movie, episode
    watched_at: Mapped[datetime] = mapped_column(DateTime)
    runtime_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    season: Mapped[int] = mapped_column(Integer, nullable=True)
    episode: Mapped[int] = mapped_column(Integer, nullable=True)
