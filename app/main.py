from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api.routes import users

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LinkedIn AI Agent API",
    version="1.0.0",
    description="AI-powered LinkedIn automation. Users provide credentials + LLM key, we handle automation."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Routes
app.include_router(users.router, prefix="/api/users", tags=["Users"])


@app.get("/")
async def root():
    return {
        "service": "LinkedIn AI Agent",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
