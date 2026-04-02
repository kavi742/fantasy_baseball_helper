from datetime import datetime

from sqlalchemy import String, Date, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[str] = mapped_column(String, unique=True, index=True)  # MLB game pk
    game_date: Mapped[str] = mapped_column(Date, index=True)
    away_team: Mapped[str] = mapped_column(String)
    home_team: Mapped[str] = mapped_column(String)
    away_team_abbrev: Mapped[str] = mapped_column(String)
    home_team_abbrev: Mapped[str] = mapped_column(String)
    game_time: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_inning: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inning_state: Mapped[str | None] = mapped_column(String, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pitchers: Mapped[list["Pitcher"]] = relationship(
        "Pitcher", back_populates="game", cascade="all, delete-orphan"
    )


class Pitcher(Base):
    __tablename__ = "pitchers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id"))
    side: Mapped[str] = mapped_column(String)  # "home" or "away"
    player_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # MLB player pk
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)  # None = TBD
    hand: Mapped[str | None] = mapped_column(String, nullable=True)  # L / R — Phase 2
    era: Mapped[str | None] = mapped_column(String, nullable=True)  # Phase 2

    game: Mapped["Game"] = relationship("Game", back_populates="pitchers")
