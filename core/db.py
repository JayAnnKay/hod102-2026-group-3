"""Single place that hands out a database connection.

DATABASE_URL lives in .env (git-ignored) and already includes
?sslmode=require. Everything that touches the DB imports get_connection
so the connection logic exists in exactly one place.
"""
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_connection():
    """Open a new connection to the Supabase Postgres database."""
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")  # force SSL