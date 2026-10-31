from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = "postgresql://ishaan:ishaan123@localhost/studybuddy"

engine = create_engine(DATABASE_URL, echo=True)

# KG4: Database session generator
def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
