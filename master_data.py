from sqlalchemy.orm import Session
import models
from database import SessionLocal

def seed_rooms():
    db: Session = SessionLocal()
    rooms = [
        {"room_number": "101", "room_type": "Single", "status": "vacant", "room_condition": "clean", "created_by": 1},
        {"room_number": "102", "room_type": "Double", "status": "vacant", "room_condition": "clean", "created_by": 1},
        {"room_number": "103", "room_type": "Double", "status": "vacant", "room_condition": "clean", "created_by": 1},
        {"room_number": "104", "room_type": "Single", "status": "vacant", "room_condition": "clean", "created_by": 1},
        {"room_number": "105", "room_type": "Double", "status": "vacant", "room_condition": "clean", "created_by": 1},
    ]
    for room in rooms:
        existing = db.query(models.Room).filter_by(room_number=room["room_number"]).first()
        if not existing:
            db.add(models.Room(**room))
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_rooms()
