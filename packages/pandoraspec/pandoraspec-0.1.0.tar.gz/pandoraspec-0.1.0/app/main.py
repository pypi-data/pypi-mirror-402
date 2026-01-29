from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel
from typing import Optional
import uuid

from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="PanDoraSpec - DORA Compliance Audit")

# Add CORS support for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    vendor_name: str
    schema_url: str
    api_key: Optional[str] = None

# Mount reports directory
if not os.path.exists("reports"):
    os.makedirs("reports")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

@app.post("/audit/submit")
async def submit_audit(
    vendor_name: str = Form(...),
    schema_url: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    from .worker import run_dora_audit
    
    final_schema_url = None
    
    if file:
        # Create uploads directory if not exists
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        
        # unique filename
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join("uploads", filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Use absolute path for the worker
        final_schema_url = os.path.abspath(file_path)
    elif schema_url:
        final_schema_url = schema_url.strip()
        # Heuristic to check if it's a direct spec URL or a base URL
        if not any(final_schema_url.lower().endswith(ext) for ext in [".json", ".yaml", ".yml"]):
            final_schema_url = final_schema_url.rstrip('/') + "/openapi.json"
    else:
        return {"error": "Either schema_url or file must be provided"}

    task = run_dora_audit.delay(
        vendor_name=vendor_name,
        schema_url=final_schema_url,
        api_key=api_key
    )
    return {"audit_id": task.id, "status": "pending"}

@app.get("/audit/{audit_id}")
async def get_audit_status(audit_id: str):
    from .worker import celery_app
    res = celery_app.AsyncResult(audit_id)
    
    if res.ready():
        if res.status == 'SUCCESS':
            return {"audit_id": audit_id, "status": "completed", "result": res.result}
        else:
            return {"audit_id": audit_id, "status": "failed", "error": str(res.result)}
    
    status = res.status.lower()
    if status == 'started':
        status = 'processing'
        
    return {"audit_id": audit_id, "status": status}

@app.get("/audit/{audit_id}/report")
async def get_report(audit_id: str):
    return {"audit_id": audit_id, "download_url": f"/reports/{audit_id}.pdf"}
