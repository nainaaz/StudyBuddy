from sqlmodel import Session, select
from typing import List
from app.models import User, MatchRequest

# KG10: Logic for partner matching algorithm.

# Calculate compatibility score between two users. Returns (course_overlap, same_style, same_availability)
def match_score(user1: User, user2: User) -> tuple[int, int, int]:
    # Course overlap
    user1_courses = {c.code for c in user1.courses}
    user2_courses = {c.code for c in user2.courses}
    course_overlap = len(user1_courses & user2_courses)
    # Same study style
    same_style = 1 if (user1.style and user1.style == user2.style) else 0
    # Same availability
    same_avail = 1 if (user1.availability and user1.availability == user2.availability) else 0
    return (course_overlap, same_style, same_avail)

# Get sorted list of potential study partners
def get_potential_partners(session: Session, current_user: User) -> List[User]:
    # All other users
    statement = select(User).where(User.id != current_user.id)
    all_users = session.exec(statement).all()
    # Already matched users
    matched_names = set(current_user.get_matches_list())
    # Sent requests
    sent_q = select(MatchRequest).where(MatchRequest.sender == current_user.name)
    sent_requests = {r.receiver for r in session.exec(sent_q).all()}
    # Incoming requests
    incoming_q = select(MatchRequest).where(MatchRequest.receiver == current_user.name)
    incoming_requests = {r.sender for r in session.exec(incoming_q).all()}
    # Filter out matched/requested users
    potential = [
        u for u in all_users
        if u.name not in matched_names
        and u.name not in sent_requests
        and u.name not in incoming_requests
    ]
    # Sort by score
    sorted_partners = sorted(
        potential,
        key=lambda u: match_score(current_user, u),
        reverse=True
    )
    return sorted_partners

# Send a match request from one user to another
def send_match_request(session: Session, sender_name: str, receiver_name: str):
    # Check if already exists
    q = select(MatchRequest).where(
        MatchRequest.sender == sender_name,
        MatchRequest.receiver == receiver_name
    )
    existing = session.exec(q).first()
    
    if not existing:
        request = MatchRequest(sender=sender_name, receiver=receiver_name)
        session.add(request)
        session.commit()

# All users who sent match requests to this user
def get_incoming_requests(session: Session, user_name: str) -> List[str]:
    q = select(MatchRequest).where(MatchRequest.receiver == user_name)
    requests = session.exec(q).all()
    return [r.sender for r in requests]

# Remove a match request
def remove_match_request(session: Session, sender_name: str, receiver_name: str):
    q = select(MatchRequest).where(
        MatchRequest.sender == sender_name,
        MatchRequest.receiver == receiver_name
    )
    request = session.exec(q).first()
    
    if request:
        session.delete(request)
        session.commit()

# Accept a match request
def accept_match(session: Session, user1_name: str, user2_name: str):
    from app.services.users import find_user_by_name
    
    user1 = find_user_by_name(session, user1_name)
    user2 = find_user_by_name(session, user2_name)
    
    if user1 and user2:
        # Add to each other's match lists
        matches1 = user1.get_matches_list()
        if user2_name not in matches1:
            matches1.append(user2_name)
            user1.set_matches_list(matches1)
        
        matches2 = user2.get_matches_list()
        if user1_name not in matches2:
            matches2.append(user1_name)
            user2.set_matches_list(matches2)
        
        session.add(user1)
        session.add(user2)
        session.commit()

# Remove mutual match between two users
def remove_match(session: Session, user1_name: str, user2_name: str):
    from app.services.users import find_user_by_name
    
    user1 = find_user_by_name(session, user1_name)
    user2 = find_user_by_name(session, user2_name)
    
    changed = False
    
    if user1:
        matches = user1.get_matches_list()
        if user2_name in matches:
            matches.remove(user2_name)
            user1.set_matches_list(matches)
            session.add(user1)
            changed = True
    
    if user2:
        matches = user2.get_matches_list()
        if user1_name in matches:
            matches.remove(user1_name)
            user2.set_matches_list(matches)
            session.add(user2)
            changed = True
    
    if changed:
        session.commit()