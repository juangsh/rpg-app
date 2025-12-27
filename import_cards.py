# import_cards.py
# Executar: python import_cards.py
# Objetivo: Popular/atualizar a tabela "cards" apontando imagens .png no /static

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import Card

import os
import re
import unicodedata

# Garante que as tabelas existam (incluindo cards)
Base.metadata.create_all(bind=engine)

# === CONFIG ===
STATIC_ROOT = os.path.join("app", "static", "cards")  # app/static/cards
IMAGE_EXT = ".png"  # <<<<<< PADRÃO DEFINIDO AQUI

RARITY_ORDER = ["comum", "incomum", "rara", "epica", "lendaria", "mitica"]
WEAPON_CLASSES = ["combatente", "potencializador", "estrategico", "especialista"]


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def slugify(name: str) -> str:
    s = strip_accents(name).lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s-]+", "_", s)
    return s


def order_key(name: str) -> str:
    return strip_accents(name).lower().strip()


def upsert_card(db: Session, *, type_: str, rarity: str, class_type: str | None,
                name: str, slug: str, image_path: str):
    """
    Upsert simples baseado na constraint lógica (type, rarity, class_type, slug).
    """
    existing = (
        db.query(Card)
        .filter(Card.type == type_)
        .filter(Card.rarity == rarity)
        .filter(Card.class_type == class_type)
        .filter(Card.slug == slug)
        .first()
    )
    if existing:
        existing.name = name
        existing.order_name = order_key(name)
        existing.image_path = image_path
        return False
    else:
        c = Card(
            type=type_,
            rarity=rarity,
            class_type=class_type,
            name=name,
            order_name=order_key(name),
            slug=slug,
            image_path=image_path,
        )
        db.add(c)
        return True


def import_weapons_from_folders(db: Session) -> int:
    """
    Lê estrutura:
      app/static/cards/armas/<classe>/<raridade>/<slug>.png
    e popula tabela cards com type="arma".
    """
    created = 0
    updated = 0

    base_dir = os.path.join(STATIC_ROOT, "armas")

    for class_type in WEAPON_CLASSES:
        for rarity in RARITY_ORDER:
            folder = os.path.join(base_dir, class_type, rarity)
            if not os.path.isdir(folder):
                continue

            for fname in os.listdir(folder):
                # só PNG
                if not fname.lower().endswith(IMAGE_EXT):
                    continue

                slug = os.path.splitext(fname)[0]

                # Nome exibido: tenta "humanizar" o slug
                # Ex: "escudo_de_metal" -> "Escudo de metal"
                display_name = slug.replace("_", " ").strip().title()

                # Path público
                image_path = f"/static/cards/armas/{class_type}/{rarity}/{slug}{IMAGE_EXT}"

                is_created = upsert_card(
                    db,
                    type_="arma",
                    rarity=rarity,
                    class_type=class_type,
                    name=display_name,
                    slug=slug,
                    image_path=image_path,
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

    print(f"[INFO] Armas: criadas={created}, atualizadas={updated}")
    return created + updated


def main():
    db = SessionLocal()
    try:
        total = import_weapons_from_folders(db)
        db.commit()
        print(f"[OK] Import concluído. Cartas (armas) processadas: {total}")
    except Exception as e:
        db.rollback()
        print("[ERRO] Falha no import:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
