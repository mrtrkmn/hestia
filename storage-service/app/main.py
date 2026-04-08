"""Storage Service — FastAPI entry point.

Requirements: 5.1, 5.5, 5.6, 16.5
"""

from fastapi import FastAPI

app = FastAPI(title="Storage Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/shares")
async def list_shares():
    return {"shares": []}


@app.post("/shares")
async def create_share():
    return {"status": "created"}
