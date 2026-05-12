from datetime import datetime
from sqlalchemy import BigInteger, String, Text, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    telethon_session: Mapped[str | None] = mapped_column(Text)
    is_session_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    suggestions: Mapped[list["Suggestion"]] = relationship(back_populates="user", lazy="select")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", lazy="select")
    stats: Mapped[list["CommunicationStat"]] = relationship(back_populates="user", lazy="select")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    incoming_message: Mapped[str] = mapped_column(Text)
    context_summary: Mapped[str | None] = mapped_column(Text)
    analysis: Mapped[str | None] = mapped_column(Text)
    variants: Mapped[list] = mapped_column(JSON, default=list)
    tone: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="suggestions")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    text: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    progress_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="goals")


class CommunicationStat(Base):
    __tablename__ = "communication_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    ease: Mapped[int] = mapped_column(Integer, default=50)
    tension: Mapped[int] = mapped_column(Integer, default=50)
    initiative: Mapped[int] = mapped_column(Integer, default=50)
    warmth: Mapped[int] = mapped_column(Integer, default=50)
    clarity: Mapped[int] = mapped_column(Integer, default=50)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="stats")


class DailyDigest(Base):
    __tablename__ = "daily_digests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    date: Mapped[str] = mapped_column(String(20))
    what_worked: Mapped[str | None] = mapped_column(Text)
    near_misses: Mapped[str | None] = mapped_column(Text)
    best_reply: Mapped[str | None] = mapped_column(Text)
    funniest_moment: Mapped[str | None] = mapped_column(Text)
    dead_dialogs: Mapped[list] = mapped_column(JSON, default=list)
    goals_progress: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
