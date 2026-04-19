# """Development helpers for resetting or creating database tables.

# Usage:
#   uv run python -m src.backend.database.dev_db create
#   uv run python -m src.backend.database.dev_db reset --yes
#     uv run python -m src.backend.database.dev_db alter-auth
# """

# from __future__ import annotations

# import argparse

# from sqlalchemy import inspect, text

# from src.backend.database.db_connection import engine
# from src.backend.database.models import Base


# def create_tables() -> None:
#     Base.metadata.create_all(bind=engine)
#     print("Tables ensured (create_all).")


# def reset_tables(force: bool) -> None:
#     if not force:
#         raise SystemExit(
#             "Refusing to drop tables without --yes. "
#             "Run: uv run python -m src.backend.database.dev_db reset --yes"
#         )
#     Base.metadata.drop_all(bind=engine)
#     Base.metadata.create_all(bind=engine)
#     print("All tables dropped and recreated.")


# def alter_auth_tables() -> None:
#     """Patch auth-table schema drift without dropping data."""
#     with engine.begin() as conn:
#         inspector = inspect(conn)
#         table_names = set(inspector.get_table_names())

#         if "patients" in table_names:
#             conn.execute(
#                 text(
#                     """
#                     ALTER TABLE patients
#                     ADD COLUMN IF NOT EXISTS full_name VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256) NOT NULL DEFAULT '',
#                     ADD COLUMN IF NOT EXISTS email VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20),
#                     ADD COLUMN IF NOT EXISTS age INTEGER,
#                     ADD COLUMN IF NOT EXISTS gender VARCHAR(10),
#                     ADD COLUMN IF NOT EXISTS address TEXT
#                     """
#                 )
#             )

#             patient_cols = {col["name"] for col in inspector.get_columns("patients")}
#             if "name" in patient_cols and "full_name" not in patient_cols:
#                 conn.execute(text("ALTER TABLE patients RENAME COLUMN name TO full_name"))

#         if "doctors" in table_names:
#             conn.execute(
#                 text(
#                     """
#                     ALTER TABLE doctors
#                     ADD COLUMN IF NOT EXISTS full_name VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS email VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS contact_number VARCHAR(20),
#                     ADD COLUMN IF NOT EXISTS gender VARCHAR(10),
#                     ADD COLUMN IF NOT EXISTS specialization VARCHAR(50),
#                     ADD COLUMN IF NOT EXISTS workload_count INTEGER DEFAULT 0,
#                     ADD COLUMN IF NOT EXISTS on_duty_status BOOLEAN DEFAULT TRUE,
#                     ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256) NOT NULL DEFAULT ''
#                     """
#                 )
#             )

#             doctor_cols = {col["name"] for col in inspector.get_columns("doctors")}
#             if "name" in doctor_cols and "full_name" not in doctor_cols:
#                 conn.execute(text("ALTER TABLE doctors RENAME COLUMN name TO full_name"))

#         if "admins" in table_names:
#             conn.execute(
#                 text(
#                     """
#                     ALTER TABLE admins
#                     ADD COLUMN IF NOT EXISTS full_name VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS email VARCHAR(100),
#                     ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256) NOT NULL DEFAULT ''
#                     """
#                 )
#             )

#             admin_cols = {col["name"] for col in inspector.get_columns("admins")}
#             if "name" in admin_cols and "full_name" not in admin_cols:
#                 conn.execute(text("ALTER TABLE admins RENAME COLUMN name TO full_name"))

#     print("Auth tables altered for development schema updates.")


# def parse_args() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(description="Database dev utility")
#     parser.add_argument(
#         "action",
#         choices=["create", "reset", "alter-auth"],
#         help=(
#             "create: ensure missing tables, "
#             "reset: drop and recreate all tables, "
#             "alter-auth: patch patient/doctor/admin auth tables"
#         ),
#     )
#     parser.add_argument(
#         "--yes",
#         action="store_true",
#         help="required with reset to confirm destructive operation",
#     )
#     return parser.parse_args()


# def main() -> None:
#     args = parse_args()

#     if args.action == "create":
#         create_tables()
#         return

#     if args.action == "alter-auth":
#         alter_auth_tables()
#         return

#     reset_tables(force=args.yes)


# if __name__ == "__main__":
#     main()
