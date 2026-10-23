import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.api.routes import router

app = FastAPI(title="CodeGuard AI")

# Ensure the static directory exists before mounting
os.makedirs("static", exist_ok=True)

# 1. Mount the static folder so CSS/JS assets can be served
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Include your existing API routes
app.include_router(router)


# 3. Serve the frontend dashboard at the root URL
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return "static/index.html"
