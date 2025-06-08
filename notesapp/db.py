from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_url = "sqlite:///./notes_db"

engine = create_engine(db_url, connect_args={"check_same_thread":False})
sessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db =  sessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        