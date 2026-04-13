from sqlalchemy import Column, Integer, String, Text

from .database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    link = Column(String(500), nullable=True)
    salary = Column(String(255), nullable=True)
    status = Column(String(100), nullable=False, default="Applied")
    notes = Column(Text, nullable=True)
