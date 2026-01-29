import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///aptrade.db")
engine = create_engine(DATABASE_URL)
