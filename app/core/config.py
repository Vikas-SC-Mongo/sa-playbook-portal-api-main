import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv(
        "MONGO_URI", "mongodb+srv://sa-portal-latest:0BNF07U4POEEjwKK@sa-portal.ut5me.mongodb.net/?retryWrites=true&w=majority&appName=SA-PORTAL")
    DB_NAME = os.getenv("DB_NAME", "sa_playbook")


config = Config()
