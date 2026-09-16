import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.database import Base, engine
from app.api.leads import router as leads_router
from app.api.chat import router as chat_router


# Load environment variables
load_dotenv()


# Create FastAPI application
app = FastAPI(
    title="AI Sales Agent",
    version="0.1.0"
)
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

# Create database tables
Base.metadata.create_all(bind=engine)


# Register API routers
app.include_router(leads_router)
app.include_router(chat_router)


@app.get("/")
def home():
    return {
        "message": "AI Sales Agent API is running!"
    }