from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.api.routes import router
from app.api.dashboard import router as dashboard_router

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Grabon AI Merchant Underwriting Agent",
    description="Production-grade FastAPI application for merchant underwriting",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Make templates globally available
app.state.templates = templates

app.include_router(router)
app.include_router(dashboard_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
