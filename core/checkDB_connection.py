import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

conn = psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")  # force SSL
cur = conn.cursor()
cur.execute("select 1;")
print("connection OK ✅", cur.fetchone())