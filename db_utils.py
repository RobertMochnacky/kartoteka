from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models_user import Base as UserBase
import psycopg2

def create_user_db(user_db_name, db_url="postgresql://postgres:postgres@db:5432/postgres"):
    """Create a new database for the user"""
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'CREATE DATABASE {user_db_name}')
    cur.close()
    conn.close()

def init_user_db(user_db_url):
    engine = create_engine(user_db_url)
    UserBase.metadata.create_all(engine)

def get_user_session(user_db_url):
    engine = create_engine(user_db_url)
    Session = scoped_session(sessionmaker(bind=engine))
    return Session
