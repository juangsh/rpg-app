from app.db import SessionLocal, engine, Base
from app.models import User
from app.auth import hash_password

MASTER_USERNAME = "mestre"
MASTER_PASSWORD = "mestre123"  # <= mantenha curto

def main():
    # defesa: evita o erro do bcrypt com senha longa
    if len(MASTER_PASSWORD.encode("utf-8")) > 72:
        raise ValueError("MASTER_PASSWORD é maior que 72 bytes. Troque por uma senha menor.")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == MASTER_USERNAME).first()
        if user:
            print("Usuário mestre já existe:", MASTER_USERNAME)
            return

        user = User(
            username=MASTER_USERNAME,
            password_hash=hash_password(MASTER_PASSWORD),
            role="master",
            force_password_change=0,
        )
        db.add(user)
        db.commit()

        print("✅ Mestre criado com sucesso!")
        print("Username:", MASTER_USERNAME)
        print("Senha:", MASTER_PASSWORD)

    finally:
        db.close()

if __name__ == "__main__":
    main()
