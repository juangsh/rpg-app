from app.db import SessionLocal
from app.models import Card

db = SessionLocal()

deleted = db.query(Card).filter(Card.image_path.like("%.jpg")).delete()
db.commit()

print(f"[OK] Registros removidos: {deleted}")

db.close()
