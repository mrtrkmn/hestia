"""File Processor — FastAPI entry point.

Internal HTTP API consumed by the API Gateway.

Requirements: 1.1-1.5, 2.1-2.4, 3.1-3.5
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from app.schemas import ProcessRequest, ProcessResponse, ErrorResponse
from app.processors.pdf import PDFError
from app.processors.image import ImageError
from app.processors.media import MediaError

app = FastAPI(title="File Processor", version="1.0.0")


@app.post("/process", response_model=ProcessResponse)
async def process_file(req: ProcessRequest):
    """Submit a file processing job."""
    return ProcessResponse(job_id="pending", status="pending", message="Job submitted")


@app.get("/health")
async def health():
    return {"status": "ok"}
