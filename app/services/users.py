from sqlmodel import Session, select
from typing import Optional
from app.models import User, UserCreate, UserUpdate

# KG10: Logic for user operations.

# Find user by name
def find_user_by_name(session: Session, name: str) -> Optional[User]:
    statement = select(User).where(User.name == name)
    return session.exec(statement).first()

# Find user by ID
def find_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

# KG3: Create a new user unless existing
def create_user(session: Session, user_data: UserCreate) -> User:
    existing = find_user_by_name(session, user_data.name)
    # Check if user already exists
    if existing:
        raise ValueError("User with that name already exists. Please choose a different name.")
    
    user = User(
        name=user_data.name,
        password=user_data.password,
        email=user_data.email,
        year=user_data.year,
        style=user_data.style,
        availability=user_data.availability
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Update user with data
def update_user(session: Session, user: User, data: UserUpdate) -> User:
    if data.name is not None:
        user.name = data.name
    if data.password is not None:
        user.password = data.password
    if data.email is not None:
        user.email = data.email
    if data.year is not None:
        user.year = data.year
    if data.style is not None:
        user.style = data.style
    if data.availability is not None:
        user.availability = data.availability
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Delete a user from the database
def delete_user(session: Session, user: User):
    session.delete(user)
    session.commit()

# Authenticate user by name and password
def authenticate_user(session: Session, name: str, password: str) -> Optional[User]:
    user = find_user_by_name(session, name)
    if user and user.password == password:
        return user
    return None
