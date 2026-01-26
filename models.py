from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

# Many-to-Many Relationship Table (Must be defined before Job class)
job_skills = Table('job_skills', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True)
    title = Column(String(200), index=True)
    company = Column(String(200))
    location = Column(String(100), index=True)
    salary_min = Column(Float, index=True)
    salary_max = Column(Float)
    description = Column(Text)  # RAG Raw Text
    skills_required = Column(JSON)  # Structured Skill List
    application_status = Column(String(50), default="New") # Tracking: New, Applied, Interviewing, Offer, Rejected

    
    # Optional if using relationship model (Currently using JSON field)
    # skills = relationship("Skill", secondary=job_skills, back_populates="jobs")

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True)
    skills = Column(JSON)  # ["Python", "React"]
    career_goal = Column(String(200))
    current_roadmap = Column(JSON)  # Stores generated roadmap state (NoSQL mode)

class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, index=True)
    # jobs = relationship("Job", secondary=job_skills, back_populates="skills")

class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, index=True)
    industry = Column(String(100))

engine = create_engine('sqlite:///career_aide.db')
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)