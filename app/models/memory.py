from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    memory_type = Column(String(50), nullable=False)  # e.g., "personal_info", "preference"
    key = Column(String(100), nullable=False, unique=True)  # e.g., "location", "favorite_color"
    content = Column(Text, nullable=False)  # The actual content to remember

# Create database engine and session
DATABASE_URL = "sqlite:///./memories.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 