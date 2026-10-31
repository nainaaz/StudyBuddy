from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

# KG5: Data models for StudyBuddy.

# Link table for many-to-many relationship between Users and Courses
class UserCourseLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
    course_id: Optional[int] = Field(default=None, foreign_key="course.id", primary_key=True)

# Database Course model with validation
class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(min_length=3, max_length=15, index=True)
    users: List["User"] = Relationship(back_populates="courses", link_model=UserCourseLink)

# Database User model with validation
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=50, index=True)
    password: str = Field(min_length=6)
    email: Optional[EmailStr] = None
    year: Optional[str] = None
    style: Optional[str] = None
    availability: Optional[str] = None
    matches: Optional[str] = Field(default="")
    courses: List[Course] = Relationship(back_populates="users", link_model=UserCourseLink)
    
    def get_matches_list(self) -> List[str]:
        # Comma-separated matches into list
        return [m.strip() for m in (self.matches or "").split(",") if m.strip()]
    
    def set_matches_list(self, lst: List[str]):
        # Store list as comma-separated string
        self.matches = ",".join(lst)

# Match request tracking between users
class MatchRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: str = Field(index=True)
    receiver: str = Field(index=True)

# KG3: Request/Response structure for creating a new user with validation
class UserCreate(SQLModel):
    name: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6)
    email: Optional[EmailStr] = None
    year: Optional[str] = None
    style: Optional[str] = None
    availability: Optional[str] = None

# Request/Response structure for updating new user with optional fields
class UserUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    password: Optional[str] = Field(default=None, min_length=6)
    email: Optional[EmailStr] = None
    year: Optional[str] = None
    style: Optional[str] = None
    availability: Optional[str] = None

# Request/Response structure for creating a course
class CourseCreate(SQLModel):
    code: str = Field(min_length=3, max_length=15)

# Request/Response structure for updating a course
class CourseUpdate(SQLModel):
    code: Optional[str] = Field(default=None, min_length=3, max_length=15)