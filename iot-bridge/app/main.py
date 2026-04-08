"""IoT Bridge — FastAPI entry point.

Requirements: 10.4, 11.1, 11.2
"""

from fastapi import FastAPI

app = FastAPI(title="IoT Bridge", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/entities")
async def list_entities():
    return {"entities": []}


@app.get("/automations")
async def list_automations():
    return {"automations": []}
