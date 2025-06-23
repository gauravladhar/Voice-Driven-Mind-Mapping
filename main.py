
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router  # Your actual router file with endpoints

app = FastAPI(
    title="Voice Knowledge Graph API",
    version="1.0.0",
    description="Takes in user voice or text, chunks it into thought nodes, and builds an evolving mind map."
)

# CORS CONFIGURATION
origins = [
    "http://localhost:5173",         # Vite dev server
    "http://127.0.0.1:5175",
    "http://172.20.10.3:5175",       # Access from another device to your local IP
    "http://172.20.10.2:5173",       # Optional — only if making cross-port requests internally
    "https://229f5dea995c.ngrok.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # Use ["*"] for open access during dev (not safe for prod)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTES
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "API is running! Visit /docs for interactive documentation."}

