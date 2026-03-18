from app.database.connection import engine, Base
from app.models.models import *

def run_migrations():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    run_migrations()
