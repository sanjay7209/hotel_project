from fastapi import FastAPI, Depends, HTTPException, Query, Body, Path
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import re
import models, schemas
from database import SessionLocal, engine, Base
from typing import List, Optional
from schemas import LoginRequest, LoginResponse, RoomBase, ReservationResponse, ReservationUpdate, CheckinResponse, RoomUpdate, CreateReservation, ArrivalResponse, DepartureResponse, ReservationUpdate
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_
from datetime import datetime

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Validate role
    allowed_roles = ["admin","frontdesk","manager"]
    if user.role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of {allowed_roles}")

    # Check if email or name already exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.name == user.name)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or Name already registered")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Create new user
    new_user = models.User(
        name=user.name,
        email=user.email,
        role=user.role,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=LoginResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_req.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not pwd_context.verify(login_req.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return LoginResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role
    )

@app.get("/rooms_availability/{roomtype}", response_model=List[RoomBase])
def get_available_rooms(
    roomtype: str = Path(..., description="Room type (Single, Double, etc.)"),
    date: str = Query(..., description="Check-in date in YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    # Convert date string to datetime
    check_in_date = datetime.strptime(date, "%Y-%m-%d")

    res = models.Reservations

    # Subquery: rooms reserved on that date and of the given type
    reserved_rooms = (
        db.query(res.room_number)
        .filter(
            and_(
                res.check_in <= check_in_date,
                res.check_out > check_in_date,
                res.status.in_(["booked", "checked_in"]),
                res.room_type == roomtype
            )
        )
    )

    # Build response
    response = [
        RoomBase(
            room_number=r.room_number,
            room_type=r.room_type,
            status=r.status,
            room_condition=r.room_condition
        )
        for r in reserved_rooms
    ]

    return response

    
@app.get("/inhouse/{rstatus}", response_model= List[ArrivalResponse])
def get_inhouse(rstatus = str, db: Session= Depends(get_db)):
    response = db.query(models.Reservations).filter(models.Reservations.status == rstatus).all()

    result = []
    for r in response:
        days = (r.check_out - r.check_in).days
        result.append(ArrivalResponse(            
            reservation_id = r.reservation_id,
            first_name = r.first_name,
            last_name=r.last_name,
            check_in=r.check_in,
            check_out=r.check_out,
            room_number=r.room_number,
            room_type=r.room_type,
            days=days
        )
        )
    return result

@app.post("/reservations/", response_model=schemas.ReservationResponse)
def create_reservation(reservation: schemas.CreateReservation, db: Session = Depends(get_db)):
    if reservation.room_type:
        room = db.query(models.Room).filter(
            models.Room.room_type == reservation.room_type,
            models.Room.status == "vacant"
        ).first()
        if not room:
            raise HTTPException(status_code=400, detail="No available rooms of the requested type")

    # Create reservation
    new_reservation = models.Reservations(
        first_name=reservation.first_name,
        last_name=reservation.last_name,
        email=reservation.email,
        phone_number=reservation.phone_number,
        check_in=reservation.check_in,
        check_out=reservation.check_out,
        total_amount=reservation.total_amount,
        address=reservation.address,
        credit_card_number=reservation.credit_card_number,
        cc_expiry=reservation.cc_expiry,
        status=reservation.status,
        room_type=reservation.room_type,
        room_number=None,
        created_by=reservation.created_by
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation

@app.get("/arrivals", response_model=List[ArrivalResponse])
def get_arrivals(
    check_in_date: str = Query(..., description="Date in YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    target_check_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()

    # Query reservations for that check-in date
    reservations = db.query(
        models.Reservations.reservation_id,
        models.Reservations.first_name,
        models.Reservations.last_name,
        models.Reservations.check_in,
        models.Reservations.check_out,
        models.Reservations.room_number,
        models.Reservations.room_type
    ).filter(
        and_(
            models.Reservations.check_in == target_check_in,
            models.Reservations.status == "booked"
        )
    ).all()

    # Build response with calculated 'days'
    response = []
    for r in reservations:
        days = (r.check_out - r.check_in).days
        response.append(ArrivalResponse(
            reservation_id=r.reservation_id,
            first_name=r.first_name,
            last_name=r.last_name,
            check_in=r.check_in,
            check_out=r.check_out,
            room_number=r.room_number,
            room_type=r.room_type,
            days=days
        ))

    return response

@app.get("/checkins", response_model=List[CheckinResponse])
def get_checkins( check_in_date: str = Query(..., description="Date in YYYY-MM-DD"),
    db: Session = Depends(get_db), rstatus : str = Query(...,)
):
    res = db.query(models.Reservations).filter(
        and_(
            models.Reservations.check_in == check_in_date,
            models.Reservations.status == rstatus 
        )
    ).all()

    response = []

    for r in res:
        response.append(CheckinResponse(
            reservation_id=r.reservation_id,
            first_name=r.first_name,
            last_name=r.last_name,
            check_in=r.check_in,
            check_out=r.check_out,
        ))

    return response



@app.get("/departures", response_model=List[DepartureResponse])
def get_departures(check_out_date: str = Query(..., description="Date in YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    target_date = datetime.strptime(check_out_date, "%Y-%m-%d").date()
    res = db.query(
        models.Reservations.reservation_id,
        models.Reservations.first_name,
        models.Reservations.last_name,
        models.Reservations.room_number,
        models.Reservations.room_type
    ).filter(target_date == models.Reservations.check_out).all()

    response = []

    for r in res:
        response.append(DepartureResponse(
            first_name= r.first_name,
            last_name= r.last_name,
            reservation_id= r.reservation_id,
            room_number= r.room_number,
            room_type= r.room_type
        )
        )
    return response


@app.get("/rooms/", response_model= List[RoomBase])
def get_rooms(db: Session=Depends(get_db)):

    res = db.query(models.Room).all()
    response = []
    for r in res:
        response.append(RoomBase(
            room_number = r.room_number,
            room_type = r.room_type,
            status = r.status,
            room_condition = r.room_condition
        )
        )
    return response

@app.get("/roomst/{roomtype}", response_model= List[RoomBase])
def get_rooms_ava(roomtype: str, db: Session=Depends(get_db)):

    res = db.query(models.Room).filter(
        and_(
            models.Room.room_type == roomtype,
            models.Room.status == 'vacant'
        )
        ).all()
    
    response = []
    for r in res:
        response.append(RoomBase(
            room_number = r.room_number,
            room_type = r.room_type,
            status = r.status,
            room_condition = r.room_condition
        )
        )
    return response


# -------- GET Reservation --------
@app.get("/reservation/", response_model=ReservationResponse)
def view_reservation(
    reservation_id: int = Query(..., alias="reservationid"),  # matches React query param
    db: Session = Depends(get_db)
):
    reservation = db.query(models.Reservations).filter(
        models.Reservations.reservation_id == reservation_id
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@app.get("/roomsn/", response_model=RoomUpdate)
def get_room(room_number: str = Query(..., alias="roomnumber"),
              db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.room_number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


# -------- PUT Reservation --------
@app.put("/reservation/", response_model=ReservationResponse)
def update_reservation(
    reservation_id: int = Query(..., alias="reservationid"),  # matches React query param
    request: ReservationUpdate = Body(...),  # Body is now required
    db: Session = Depends(get_db)
):
    # Find reservation
    reservation = db.query(models.Reservations).filter(
        models.Reservations.reservation_id == reservation_id
    ).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # Update only provided fields
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reservation, key, value)

    db.commit()
    db.refresh(reservation)
    return reservation


@app.put("/rooms/", response_model= RoomBase)
def edit_room(
    room_number: str = Query(..., alias="roomnumber"),
    request: schemas.RoomUpdate = Body(...),
    db: Session = Depends(get_db)
):
    # Find room
    room = db.query(models.Room).filter(models.Room.room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Update only provided fields
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)

    db.commit()
    db.refresh(room)
    return room


@app.put("/roomhk/", response_model=List[schemas.RoomBase])
def edit_roomhk(
    room_numbers: List[str] = Query(..., alias="roomnumber"),
    request: schemas.RoomUpdate = Body(...),
    db: Session = Depends(get_db),
):
    updated_rooms = []
    for r in room_numbers:
        print(r)

    for r in room_numbers:
        room = db.query(models.Room).filter(models.Room.room_number == r).first()
        if not room:
            raise HTTPException(status_code=404, detail=f"Room {r} not found")

        update_data = request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(room, key, value)

        updated_rooms.append(room)

    db.commit()

    # Refresh only updated rooms
    for room in updated_rooms:
        db.refresh(room)

    return updated_rooms


