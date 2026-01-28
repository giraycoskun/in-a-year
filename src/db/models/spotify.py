from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class SpotifyPlay(Base):
    __tablename__ = "spotify_plays"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_name: Mapped[str] = mapped_column(String(500))
    artist_name: Mapped[str] = mapped_column(String(500))
    album_name: Mapped[str] = mapped_column(String(500), nullable=True)
    played_at: Mapped[datetime] = mapped_column(DateTime)
    ms_played: Mapped[int] = mapped_column(Integer)
