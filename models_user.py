from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    contact = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    activities = relationship("Activity", backref="client", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    activity_date = Column(Date, nullable=False)
    person_name = Column(String(255))
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
