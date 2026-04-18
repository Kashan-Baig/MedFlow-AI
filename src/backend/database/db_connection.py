"""Database connection setup."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL,
# This is critical for Neon to prevent connection drops
    connect_args={"sslmode": "require"},
    pool_pre_ping=True
)
    
# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================
# FIXED FOR SCRIPTS (IMPORTANT)
# =========================
def get_db():
    """
    Returns a real session (NOT generator).
    Safe for CLI workflows, scripts, chatbot.
    """
    return SessionLocal()