import sys
import os
from sqlalchemy import create_engine, MetaData, Table

sys.path.append(os.getcwd())
from src.backend.database.db_connection import engine

metadata = MetaData()
metadata.reflect(bind=engine)

for table_name in ["admins", "doctors", "patients"]:
    if table_name in metadata.tables:
        table = metadata.tables[table_name]
        print(f"Table: {table_name}")
        for c in table.columns:
            print(f"  - {c.name} ({c.type}) nullable={c.nullable}")
    else:
        print(f"Table {table_name} not found.")
