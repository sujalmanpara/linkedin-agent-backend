from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite fallback if PostgreSQL not available
try:
    engine = create_engine(settings.DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        pass
    print("✓ Connected to PostgreSQL")
except Exception as e:
    print(f"⚠️  PostgreSQL not available ({e}), falling back to SQLite")
    engine = create_engine(
        "sqlite:///./linkedin_agent.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
