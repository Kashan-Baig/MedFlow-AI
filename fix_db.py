import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
from src.backend.database.db_connection import engine

with engine.connect() as conn:
    print("Modifying admins table.")
    conn.execute(text("UPDATE admins SET full_name = name WHERE full_name IS NULL"))
    conn.execute(text("ALTER TABLE admins ALTER COLUMN full_name SET NOT NULL"))
    conn.execute(text("ALTER TABLE admins DROP COLUMN IF EXISTS name"))
    conn.commit()
    print("Successfully modified admins table.")
