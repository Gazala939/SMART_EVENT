# SetUp the database Connection and session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# db url
DATABASE_URL = "sqlite:///./smartevent.db"

# create Engine 
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# create Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# create Base Class
Base = declarative_base()

# provide fresh db session per request and close
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()