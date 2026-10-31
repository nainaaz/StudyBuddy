## StudyBuddy:
A web application for students to find study partners based on shared courses, study styles, and availability.

## Features:
- User registration and authentication
- Profile management with study preferences
- Course enrollment tracking
- Study partner matching algorithm
- Match request system (send/accept/decline)
- Full CRUD operations via REST API
- Dynamic UI updates with HTMX

## Project Structure:
StudyBuddy/
├── app/
│   ├── main.py              // FastAPI routes - Presentation Layer
│   ├── models.py            // SQLModel data models - Data Model Layer
│   ├── database.py          // Database - Data Access Layer
│   ├── services/
│   │   ├── users.py         // User logic - Business logic layer
│   │   ├── courses.py       // Course logic - Business logic layer
│   │   └── matching.py      // Partner matching logic - Business logic layer
│   └── templates/           // Jinja2 HTML templates
│       ├── home.html
│       ├── create_account.html
│       ├── login.html
│       ├── profile.html
│       ├── course_list.html
│       ├── partners.html
│       ├── incoming.html
│       ├── matches.html
│       └── account_created.html
├── static/
│   └── styles.css
├── requirements.txt         // Dependencies
├── README.md
└── KGD.pdf                  // Knowledge Goal Demonstration document

## Prerequisites:
- Python 3.10 or higher
- PostgreSQL database server

## Installation & Setup

### 1. Install PostgreSQL

macOS (using Homebrew):
brew install postgresql@14
brew services start postgresql@14

Windows:
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database

// Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE studybuddy;
CREATE USER ishaan WITH PASSWORD 'ishaan123';
GRANT ALL PRIVILEGES ON DATABASE studybuddy TO ishaan;
\q

**Note:** To use different credentials, update the `DATABASE_URL` in `app/database.py`: DATABASE_URL = "postgresql://your_user:your_password@localhost/your_database"

### 3. Install Python Dependencies

// Create virtual environment
python3 -m venv venv

// Activate virtual environment on macOS/Linux:
source venv/bin/activate
// Activate virtual environment on Windows:
venv\Scripts\activate

// Install dependencies
pip install -r requirements.txt
(check pip install email-validator if also installed just in case)

## Running the Application

### 1. Start the Server

uvicorn app.main:app --reload
The server will start at `http://127.0.0.1:8000`

### 2. Access the Application

Go to home page: http://127.0.0.1:8000/
- **Note:** API Documentation is at http://127.0.0.1:8000/docs

### 3. Using the Application

1. Create an account at http://127.0.0.1:8000/create
2. Login at http://127.0.0.1:8000/login
3. Update your profile with graduation year, study style, and availability
4. Add courses to your profile
5. Look at recommended study partners sorted by compatibility
6. Send match requests to potential partners
7. View incoming requests and accept/decline
8. View matches and see your confirmed study partners with their contact email and reach out to them

## API Endpoints:

- `POST /api/users` : Create new user
- `GET /api/users` : List all users
- `GET /api/users/{user_id}` : Get specific user
- `PUT /api/users/{user_id}` : Update user
- `DELETE /api/users/{user_id}` : Delete user

## Testing:

**Note**:Use http://127.0.0.1:8000/docs to test all API endpoints.

1. Test User Registration:
   - Go to Create Account
   - Fill in all fields including a course code (e.g., "CS 326")
   - Submit and verify account created page appears

2. Test Login:
   - Go to Login
   - Enter credentials
   - Verify redirect to Partners

3. Test Profile Update:
   - Go to /profile
   - Change year, style, or availability
   - Click Save
   - Refresh page to verify changes persisted

4. Test Partner Matching:
   - Create multiple accounts with different courses
   - Login as one user
   - Go to Partners
   - Verify users with shared courses appear first

5. Test Match Requests:
   - Send request to another user
   - Login as that user
   - Go to Incoming
   - Accept or decline the request
   - Verify match appears in Matches

## Teckstack

- Backend: FastAPI, SQLModel, PostgreSQL
- Frontend: Jinja2 templates, HTMX, CSS
- Database: SQLModel
- Validation: Pydantic
- Server: Uvicorn

// Database Relationships:
- Users <-> Courses (many-to-many)
- Users store confirmed matches as comma-separated names

## Limitations:
- Passwords are stored in plain text (not suitable for production)
- No email verification
- Match algorithm is basic (could be enhanced with more factors)
- No user profile pictures

Thanks for taking a look at my project! 
- Naina Singh, nainasingh@umass.edu