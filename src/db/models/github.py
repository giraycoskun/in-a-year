from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class GithubContribution(Base):
    __tablename__ = "github_contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    repo_name: Mapped[str] = mapped_column(String(500))
    contribution_type: Mapped[str] = mapped_column(String(50))  # commit, pr, issue, review
    contribution_date: Mapped[datetime] = mapped_column(DateTime)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
