from sqlalchemy import Column, Integer,String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    password =  Column(String)
    email = Column(String)
    notes = relationship("Note", back_populates="user") 
    
class Note(Base):
    __tablename__ ="notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    create_date = Column(DateTime)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(Text)
    user = relationship("User", back_populates="notes") 
