from sqlalchemy import Column, Integer, String, DECIMAL, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

# ---------------- User ----------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'manager', 'frontdesk')", name="usercheck"),
    )

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ---------------- Reservations ----------------
class Reservations(Base):
    __tablename__ = "reservations"

    reservation_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    phone_number = Column(String(15), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    address = Column(String(200), nullable=False)
    credit_card_number = Column(String(20), nullable=False)
    cc_expiry = Column(String(5), nullable=False)  # Format MM/YY
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    status = Column(String(20), nullable=False, default="booked")
    room_type = Column(String(20), nullable=True)  # Must be one of 'Single','Double'

    room_number = Column(String(10), ForeignKey("rooms.room_number"), nullable=True)

    # Relationship
    room = relationship("Room", back_populates="reservations")


# ---------------- Room ----------------
class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        CheckConstraint("room_type IN ('Single', 'Double')", name="room_type"),
        CheckConstraint("status IN ('vacant', 'occupied', 'maintenance', 'housekeeping')", name="room_status"),
        CheckConstraint("room_condition IN ('clean', 'dirty', 'under_maintenance')", name="room_condition"),
    )

    room_number = Column(String(10), primary_key=True, index=True)
    room_type = Column(String(20), nullable=False)  # Must be one of 'Single','Double'
    status = Column(String(20), nullable=False, default="vacant")
    room_condition = Column(String(20), nullable=False, default="clean")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    # Relationship
    reservations = relationship("Reservations", back_populates="room")
