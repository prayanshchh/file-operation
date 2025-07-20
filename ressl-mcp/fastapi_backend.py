from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import tempfile
import os
import zipfile
from dotenv import load_dotenv
load_dotenv()
from minio_utils import (
    upload_zip_to_gcs,
    list_files_in_gcs,
    read_file_from_gcs,
    write_file_to_gcs,
    delete_file_from_gcs,
    apply_llm_edits_to_gcs,
    create_file_in_zip_in_gcs,
)
from agent import agent
from fastapi.middleware.cors import CORSMiddleware

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

app = FastAPI(title="Zip-to-GCS backend")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://file-operation.prayanshchhablani.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported.")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(await file.read())
        tmp_zip.flush()
        zip_filename = upload_zip_to_gcs(tmp_zip.name)
    return {"zip_filename": zip_filename}

@app.get("/list-files/{zip_filename}")
def list_files(zip_filename: str, prefix: str = ""):
    return {"files": list_files_in_gcs(zip_filename, prefix)}

@app.get("/file/{zip_filename}/{file_path:path}", response_class=PlainTextResponse)
def get_file(zip_filename: str, file_path: str):
    """
    file_path should be the path INSIDE the zip, e.g. 'folder/file.txt', NOT including the zip filename.
    Example: /file/uuid.zip/folder/file.txt
    """
    try:
        return read_file_from_gcs(zip_filename, file_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/agent-file")
async def agent_file(
    zip_filename: str = Form(...),
    file_path: str = Form(...),
    prompt: str = Form(...)
):
    file_content = read_file_from_gcs(zip_filename, file_path)
    result = await agent(prompt, zip_filename, file_path, file_content)
    return {"result": result}

# Write a file to GCS (outside ZIP workflow)
@app.post("/write-file")
async def write_file(
    workspace_id: str = Form(...),
    file_path: str = Form(...),
    content: str = Form(...)
):
    write_file_to_gcs(workspace_id, file_path, content)
    return {"status": "ok"}

# Delete a file from GCS (outside ZIP workflow)
@app.delete("/delete-file")
async def delete_file(
    workspace_id: str = Form(...),
    file_path: str = Form(...)
):
    delete_file_from_gcs(workspace_id, file_path)
    return {"status": "ok"}

@app.post("/apply-llm-edits")
async def apply_llm_edits(
    zip_filename: str = Form(...),
    instructions: str = Form(...),  # Pass as JSON string
):
    import json
    instr_list = json.loads(instructions)
    apply_llm_edits_to_gcs(zip_filename, instr_list)
    return {"status": "ok"}

# Create a file inside a zip in GCS
@app.post("/create-file-in-zip")
async def create_file_in_zip(
    zip_filename: str = Form(...),
    file_path: str = Form(...),
    content: str = Form("")
):
    create_file_in_zip_in_gcs(zip_filename, file_path, content)
    return {"status": "ok"}