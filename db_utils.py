from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_auth_engine():
    # Replace with your real database URI
    return create_engine("postgresql://user:password@localhost/auth_db")

def get_user_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
