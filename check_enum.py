import sys
import os
from sqlalchemy import text
from src.backend.database.db_connection import SessionLocal

def main():
    try:
        db = SessionLocal()
        result = db.execute(text("""
            SELECT unnest(enum_range(NULL::appointmentstatus))::text;
        """)).fetchall()
        print("Valid enum values in DB:", [r[0] for r in result])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
