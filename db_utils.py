from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

def get_auth_engine():
    return create_engine(Config.AUTH_DATABASE_URI)

def get_user_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
