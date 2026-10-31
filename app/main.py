from fastapi import FastAPI, Request, Form, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import Optional

from app.database import get_session, create_db_and_tables
from app.models import User, UserCreate, UserUpdate
from app.services import users as user_service
from app.services import courses as course_service
from app.services import matching as match_service


# Main FastAPI application with clean separation of concerns. Check logic in app/services


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

create_db_and_tables() # Initializing database

# Helper Function 1: Gets current logged-in user from cookie
def current_user(session: Session, request: Request) -> Optional[User]:
    name = request.cookies.get("user")
    if not name:
        return None
    return user_service.find_user_by_name(session, name)

# Helper Function 2: Partial course list for HTMX updates
def render_course_list_partial(request: Request, user: User):
    return templates.TemplateResponse("course_list.html", {
        "request": request,
        "user": user
    })

# UI Endpoint 1 (KG8): Home Page
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    logged_in = request.cookies.get("user") is not None
    return templates.TemplateResponse("home.html", {
        "request": request,
        "logged_in": logged_in
    })

# UI Endpoint 2 (KG8): Fill to create account
@app.get("/create", response_class=HTMLResponse)
def create_get(request: Request):
    return templates.TemplateResponse("create_account.html", {
        "request": request
    })

# UI Endpoint 3 (KG9): Creates new user account
@app.post("/create", response_class=HTMLResponse)
def create_post(
    request: Request,
    name: str = Form(...),
    password: str = Form(...),
    email: str = Form(""),
    year: str = Form(""),
    style: str = Form(""),
    availability: str = Form(""),
    course: str = Form(""),
    session: Session = Depends(get_session),
):
    try:
        user_data = UserCreate(
            name=name.strip(),
            password=password,
            email=email.strip() if email else None,
            year=year,
            style=style,
            availability=availability
        )
        user = user_service.create_user(session, user_data)
        if course.strip():
            course_service.add_course_to_user(session, user, course.strip())
        return templates.TemplateResponse("account_created.html", {
            "request": request,
            "name": user.name
        })
    
    except ValueError as e:
        return HTMLResponse(str(e), status_code=400)

# UI Endpoint 4 (KG8): Fill Login form
@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None
    })

# UI Endpoint 5 (KG2): Authenticates user and sets session cookie.
@app.post("/login")
def login_post(
    request: Request,
    name: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = user_service.authenticate_user(session, name.strip(), password)
    
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid name or password"
        })
    
    response = RedirectResponse(url="/partners", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user", value=user.name, httponly=True)
    return response

# UI Endpoint 6 (KG8): Logouts user and clears cookie.
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user")
    return response

# UI Endpoint 7 (KG9): Shows user profile.
@app.get("/profile", response_class=HTMLResponse)
def profile_get(request: Request, session: Session = Depends(get_session)):
    u = current_user(session, request)
    if not u:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    session.refresh(u)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": u
    })

# UI Endpoint 8 (KG9): Updates user profile.
@app.post("/profile")
def profile_post(
    request: Request,
    year: str = Form(""),
    style: str = Form(""),
    availability: str = Form(""),
    session: Session = Depends(get_session),
):
    u = current_user(session, request)
    if not u:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    update_data = UserUpdate(year=year, style=style, availability=availability)
    user_service.update_user(session, u, update_data)
    
    return RedirectResponse("/profile", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 9 (KG8): Adds course to user profile.
@app.post("/add_course")
def add_course(
    request: Request,
    new_course: str = Form(""),
    session: Session = Depends(get_session)
):
    u = current_user(session, request)
    if not u:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    if new_course.strip():
        course_service.add_course_to_user(session, u, new_course.strip())
    
    session.refresh(u)
    # Partial update for HTMX
    if request.headers.get("HX-Request") == "true":
        return render_course_list_partial(request, u)
    
    return RedirectResponse("/profile", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 10 (KG8): Deletes course from user profile.
@app.post("/delete_course/{course_code}")
def delete_course(
    course_code: str,
    request: Request,
    session: Session = Depends(get_session)
):
    u = current_user(session, request)
    if not u:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    from urllib.parse import unquote
    course_code = unquote(course_code)
    
    course_service.remove_course_from_user(session, u, course_code)
    session.refresh(u)
    
    if request.headers.get("HX-Request") == "true":
        return render_course_list_partial(request, u)
    
    return RedirectResponse("/profile", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 11 (KG8): Shows potential study partners sorted by compatibility.
@app.get("/partners", response_class=HTMLResponse)
def partners(request: Request, session: Session = Depends(get_session)):
    current = current_user(session, request)
    if not current:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    sorted_partners = match_service.get_potential_partners(session, current)
    
    return templates.TemplateResponse("partners.html", {
        "request": request,
        "current": current,
        "others": sorted_partners
    })

# UI Endpoint 12 (KG8): Sends match request to another user.
@app.post("/send_request/{receiver}")
def send_request(
    receiver: str,
    request: Request,
    session: Session = Depends(get_session)
):
    sender = request.cookies.get("user")
    if not sender:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    match_service.send_match_request(session, sender, receiver)
    return RedirectResponse("/partners", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 13 (KG8): Shows incoming match requests.
@app.get("/incoming", response_class=HTMLResponse)
def incoming(request: Request, session: Session = Depends(get_session)):
    name = request.cookies.get("user")
    if not name:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    sender_names = match_service.get_incoming_requests(session, name)
    senders = [user_service.find_user_by_name(session, s) for s in sender_names]
    senders = [u for u in senders if u]
    
    return templates.TemplateResponse("incoming.html", {
        "request": request,
        "senders": senders
    })

# UI Endpoint 14 (KG8): Accepts incoming match requests.
@app.post("/accept/{sender}")
def accept(
    sender: str,
    request: Request,
    session: Session = Depends(get_session)
):
    receiver = request.cookies.get("user")
    if not receiver:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    match_service.remove_match_request(session, sender, receiver)
    match_service.accept_match(session, receiver, sender)
    
    return RedirectResponse("/incoming", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 15 (KG8): Declines incoming match requests.
@app.post("/decline/{sender}")
def decline(
    sender: str,
    request: Request,
    session: Session = Depends(get_session)
):
    receiver = request.cookies.get("user")
    if not receiver:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    match_service.remove_match_request(session, sender, receiver)
    return RedirectResponse("/incoming", status_code=status.HTTP_303_SEE_OTHER)

# UI Endpoint 16 (KG8): Shows confirmed study partners and their emails.
@app.get("/matches", response_class=HTMLResponse)
def matches(request: Request, session: Session = Depends(get_session)):
    name = request.cookies.get("user")
    if not name:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    user = user_service.find_user_by_name(session, name)
    matched_users = []
    
    for match_name in user.get_matches_list():
        candidate = user_service.find_user_by_name(session, match_name)
        if candidate:
            matched_users.append(candidate)
    
    return templates.TemplateResponse("matches.html", {
        "request": request,
        "matches": matched_users
    })

# UI Endpoint 17 (KG8): Remove a confirmed study partners and not see their emails.
@app.post("/remove_match/{partner}")
def remove_match(
    partner: str,
    request: Request,
    session: Session = Depends(get_session)
):
    name = request.cookies.get("user")
    if not name:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    match_service.remove_match(session, name, partner)
    return RedirectResponse("/matches", status_code=status.HTTP_303_SEE_OTHER)

# API Endpoint 1 (KG7,KG4): Creates new user.
@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def api_create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    try:
        user = user_service.create_user(session, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# API Endpoint 2 (KG7,KG6): All users as JSON
@app.get("/api/users")
def api_list_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return users

# API Endpoint 3 (KG1): Single user get by id.
@app.get("/api/users/{user_id}")
def api_get_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    user = user_service.find_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# API Endpoint 4 (KG3): Update user.
@app.put("/api/users/{user_id}")
def api_update_user(
    user_id: int,
    data: UserUpdate,
    session: Session = Depends(get_session)
):
    user = user_service.find_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    updated_user = user_service.update_user(session, user, data)
    return updated_user

# API Endpoint 5 (KG2): Delete user.
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_user(
    user_id: int,
    session: Session = Depends(get_session)
):
    user = user_service.find_user_by_id(session, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_service.delete_user(session, user)
    return None