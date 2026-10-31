from sqlmodel import Session, select
from app.models import Course, User

# KG10: Logic for courses operations.

# Create a course by code
def ensure_course(session: Session, code: str) -> Course:
    code = code.strip()
    statement = select(Course).where(Course.code == code)
    course = session.exec(statement).first()
    
    if not course:
        course = Course(code=code)
        session.add(course)
        session.commit()
        session.refresh(course)
    
    return course

# Add a course to a user
def add_course_to_user(session: Session, user: User, course_code: str) -> Course:
    course = ensure_course(session, course_code)
    # Check if already enrolled
    if course not in user.courses:
        user.courses.append(course)
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return course

# Remove a course from a user
def remove_course_from_user(session: Session, user: User, course_code: str) -> bool:
    statement = select(Course).where(Course.code == course_code)
    course = session.exec(statement).first()
    
    if course and course in user.courses:
        user.courses.remove(course)
        session.add(user)
        session.commit()
        return True
    
    return False