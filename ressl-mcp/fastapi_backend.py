from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse, JSONResponse
import tempfile
from dotenv import load_dotenv
load_dotenv()
import os
from minio_utils import (
    upload_zip_to_minio,
    list_files_in_minio,
    read_file_from_minio,
    write_file_to_minio,
    delete_file_from_minio,
    apply_llm_edits_to_minio,
    create_file_in_zip_in_minio,
)
from agent import agent

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")

app = FastAPI(title="Zip-to-MinIO backend")

@app.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported.")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(await file.read())
        tmp_zip.flush()
        zip_filename = upload_zip_to_minio(tmp_zip.name)
    return {"zip_filename": zip_filename}

@app.get("/list-files/{zip_filename}")
def list_files(zip_filename: str, prefix: str = ""):
    return {"files": list_files_in_minio(zip_filename, prefix)}

@app.get("/file/{zip_filename}/{file_path:path}", response_class=PlainTextResponse)
def get_file(zip_filename: str, file_path: str):
    """
    file_path should be the path INSIDE the zip, e.g. 'folder/file.txt', NOT including the zip filename.
    Example: /file/uuid.zip/folder/file.txt
    """
    try:
        return read_file_from_minio(zip_filename, file_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/edit-file")
async def edit_file(
    zip_filename: str = Form(...),
    file_path: str = Form(...),
    prompt: str = Form(...)
):
    file_content = read_file_from_minio(zip_filename, file_path)
    result = await agent(prompt, zip_filename, file_path, file_content)
    return {"result": result}

# Write a file to MinIO (outside ZIP workflow)
@app.post("/write-file")
async def write_file(
    workspace_id: str = Form(...),
    file_path: str = Form(...),
    content: str = Form(...)
):
    write_file_to_minio(workspace_id, file_path, content)
    return {"status": "ok"}

# Delete a file from MinIO (outside ZIP workflow)
@app.delete("/delete-file")
async def delete_file(
    workspace_id: str = Form(...),
    file_path: str = Form(...)
):
    delete_file_from_minio(workspace_id, file_path)
    return {"status": "ok"}

@app.post("/apply-llm-edits")
async def apply_llm_edits(
    zip_filename: str = Form(...),
    instructions: str = Form(...),  # Pass as JSON string
):
    import json
    instr_list = json.loads(instructions)
    apply_llm_edits_to_minio(zip_filename, instr_list)
    return {"status": "ok"}

# Create a file inside a zip in MinIO
@app.post("/create-file-in-zip")
async def create_file_in_zip(
    zip_filename: str = Form(...),
    file_path: str = Form(...),
    content: str = Form("")
):
    create_file_in_zip_in_minio(zip_filename, file_path, content)
    return {"status": "ok"}