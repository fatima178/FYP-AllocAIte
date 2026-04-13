import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routers import upload, dashboard, auth, recommend, settings, tasks, chatbot, employees, employee_portal, invites

app = FastAPI()

def get_allowed_origins():
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    env_origins = os.getenv("ALLOWED_ORIGINS", "")
    if env_origins.strip():
        origins.extend(origin.strip() for origin in env_origins.split(",") if origin.strip())

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(origins))


ALLOWED_ORIGINS = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create database tables on boot
init_db()

# register routers
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(employee_portal.router, prefix="/api")
app.include_router(invites.router, prefix="/api")


@app.get("/")
def home():
    return {"message": "Backend connected successfully"}
