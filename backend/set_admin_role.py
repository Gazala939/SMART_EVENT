from database import SessionLocal
from models import User

ADMIN_EMAIL = "admin@gmail.com"

db = SessionLocal()

try:
    user = db.query(User).filter(
        User.email == ADMIN_EMAIL
    ).first()

    if user:
        user.role = "ADMIN"
        db.commit()
        db.refresh(user)

        print("Admin role updated successfully!")
        print("Email:", user.email)
        print("Role:", user.role)
    else:
        print("User not found.")

finally:
    db.close()