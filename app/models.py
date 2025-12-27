from sqlalchemy import String, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Integer as ColInteger, String as ColString, UniqueConstraint

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10), default="player")  # master | player
    force_password_change: Mapped[bool] = mapped_column(Boolean, default=True)

    character: Mapped["Character"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete",
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(120), default="NOVO PERSONAGEM")
    age: Mapped[str] = mapped_column(String(30), default="")
    occupation: Mapped[str] = mapped_column(String(120), default="")
    level: Mapped[str] = mapped_column(String(30), default="1")
    affiliation: Mapped[str] = mapped_column(String(120), default="")
    personality: Mapped[str] = mapped_column(String(20), default="hero")  # hero|antihero|villain

    heroism: Mapped[int] = mapped_column(Integer, default=50)
    agility: Mapped[int] = mapped_column(Integer, default=50)
    intellect: Mapped[int] = mapped_column(Integer, default=50)
    strength: Mapped[int] = mapped_column(Integer, default=50)
    willpower: Mapped[int] = mapped_column(Integer, default=50)
    vigor: Mapped[int] = mapped_column(Integer, default=50)

    hp: Mapped[int] = mapped_column(Integer, default=25)
    hero_points: Mapped[int] = mapped_column(Integer, default=5)

    notes: Mapped[str] = mapped_column(Text, default="")
    inventory_text: Mapped[str] = mapped_column(Text, default="")
    skills_text: Mapped[str] = mapped_column(Text, default="")

    user: Mapped["User"] = relationship(back_populates="character")


class Card(Base):
    __tablename__ = "cards"

    id = Column(ColInteger, primary_key=True, index=True)

    # "arma" | "inimigo" | "local"
    type = Column(ColString, nullable=False, index=True)

    # "comum" | "incomum" | "rara" | "epica" | "lendaria" | "mitica"
    rarity = Column(ColString, nullable=False, index=True)

    # Só para armas: "combatente" | "potencializador" | "estrategico" | "especialista"
    # Para inimigos/locais: None
    class_type = Column(ColString, nullable=True, index=True)

    # Nome exibido
    name = Column(ColString, nullable=False)

    # Nome normalizado para ordenação A–Z (sem acento)
    order_name = Column(ColString, nullable=False, index=True)

    # slug do arquivo (sem acento, underscore)
    slug = Column(ColString, nullable=False, index=True)

    # caminho público da imagem
    image_path = Column(ColString, nullable=False)

    __table_args__ = (
        UniqueConstraint("type", "rarity", "class_type", "slug", name="uq_card_identity"),
    )
