from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Database URL: This tells SQLAlchemy to create a local file named 'codeguard.db'
DATABASE_URL = "sqlite:///./codeguard.db"

# 2. Engine: The core interface to the database.
# check_same_thread=False is a necessary override for SQLite in FastAPI,
# as FastAPI handles multiple requests concurrently across different threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 3. SessionLocal: A factory that creates individual database sessions.
# autoflush=False ensures data isn't committed until we explicitly say so.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base: The parent class that all our future database tables will inherit from.
Base = declarative_base()


# 5. Dependency Injection: This function provides a fresh database session
# for every API request and ensures it is safely closed afterward.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
