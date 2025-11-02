from fastapi import FastAPI
from db import get_connection, init_db

app = FastAPI()

init_db()

@app.get("/")
def home():
    return {"message": "Backend connected to PostgreSQL"}
