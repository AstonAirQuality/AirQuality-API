# enviroment variables dependacies
from os import environ as env

from dotenv import load_dotenv
from sqlalchemy import create_engine

# sqlalchemy dependacies
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

engine = create_engine(env["DATABASE_URL"])

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
