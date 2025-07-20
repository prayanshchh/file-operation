import os
from google.cloud import storage
from typing import List
import tempfile
import zipfile
import io
import logging
import uuid
from dotenv import load_dotenv
load_dotenv()

GCS_BUCKET = os.getenv("GCS_BUCKET")

gcs_client = None
bucket = None

logger = logging.getLogger("gcs_utils")

def _ensure_client_initialized():
    """Initialize GCS client if not already done"""
    global gcs_client, bucket
    if gcs_client is None:
        try:
            gcs_client = storage.Client()
            bucket = gcs_client.bucket(GCS_BUCKET)
        except Exception as e:
            print(f"Warning: Could not initialize Google Cloud Storage client: {e}")
            print("Please set up authentication using one of these methods:")
            print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            print("2. Run 'gcloud auth application-default login'")
            print("3. Use service account key file")
            raise Exception("Google Cloud Storage client not initialized")

# GCS function names
def upload_zip_to_gcs(zip_path: str) -> str:
    """Upload a zip file to GCS and return the filename"""
    _ensure_client_initialized()
    zip_uuid = str(uuid.uuid4()) + ".zip"
    blob = bucket.blob(zip_uuid)
    blob.upload_from_filename(zip_path)
    return zip_uuid

def list_files_in_gcs(zip_filename: str, prefix: str = "") -> list:
    """List files inside a zip stored in GCS"""
    _ensure_client_initialized()
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            file_list = [f for f in zip_ref.namelist() if f.startswith(prefix)] if prefix else zip_ref.namelist()
    return file_list

def read_file_from_gcs(zip_filename: str, file_path: str) -> str:
    """Read a file from inside a zip stored in GCS"""
    _ensure_client_initialized()
    content = ""
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print("I am file_List: ", file_list)
            if file_path not in file_list:
                return "file doesn't exist"
            with zip_ref.open(file_path) as f:
                content = f.read().decode()
    return content

def write_file_to_gcs(zip_filename: str, file_path: str, content: str):
    """Write a file to inside a zip stored in GCS"""
    _ensure_client_initialized()
    apply_llm_edits_to_gcs(zip_filename, [{
        "file": file_path,
        "action": "replace",
        "content": content,
    }])

def delete_file_from_gcs(zip_filename: str, file_path: str):
    """Delete a file from inside a zip stored in GCS"""
    _ensure_client_initialized()
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        original_zip_path = tmp_zip.name
    with tempfile.NamedTemporaryFile(delete=False) as new_zip_file:
        with zipfile.ZipFile(original_zip_path, 'r') as zin, \
             zipfile.ZipFile(new_zip_file.name, 'w') as zout:
            for item in zin.infolist():
                if item.filename != file_path:
                    zout.writestr(item, zin.read(item.filename))
    blob.upload_from_filename(new_zip_file.name)

def apply_llm_edits_to_gcs(zip_filename: str, instructions: list):
    """Apply LLM edits to files inside a zip stored in GCS"""
    _ensure_client_initialized()
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        original_zip_path = tmp_zip.name
    with tempfile.NamedTemporaryFile(delete=False) as new_zip_file:
        with zipfile.ZipFile(original_zip_path, 'r') as zin, \
             zipfile.ZipFile(new_zip_file.name, 'w') as zout:
            replace_map = {instr['file']: instr for instr in instructions if instr['action'] in ('replace', 'append')}
            delete_set = {instr['file'] for instr in instructions if instr['action'] == 'delete'}
            for item in zin.infolist():
                if item.filename not in replace_map and item.filename not in delete_set:
                    zout.writestr(item, zin.read(item.filename))
            for instr in instructions:
                if instr['action'] == 'replace':
                    zout.writestr(instr['file'], instr['content'])
                elif instr['action'] == 'append':
                    try:
                        old_content = zin.read(instr['file']).decode()
                    except KeyError:
                        old_content = ''
                    zout.writestr(instr['file'], old_content + instr['content'])
    blob.upload_from_filename(new_zip_file.name)

def create_file_in_zip_in_gcs(zip_filename: str, file_path: str, content: str = ""):
    """Create a new file inside a zip stored in GCS"""
    _ensure_client_initialized()
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        original_zip_path = tmp_zip.name
    with tempfile.NamedTemporaryFile(delete=False) as new_zip_file:
        with zipfile.ZipFile(original_zip_path, 'r') as zin, \
             zipfile.ZipFile(new_zip_file.name, 'w') as zout:
            file_exists = False
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
                if item.filename == file_path:
                    file_exists = True
            if not file_exists:
                zout.writestr(file_path, content)
    blob.upload_from_filename(new_zip_file.name)

# Additional GCS functions
def upload_file_to_gcs(zip_filename: str, file_path: str, local_path: str):
    logger.info(f"[upload_file_to_gcs] Uploading {local_path} to {zip_filename}/{file_path}")
    _ensure_client_initialized()
    blob = bucket.blob(zip_filename)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        if blob.exists():
            blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'a') as zipf:
            zipf.write(local_path, arcname=file_path)
    blob.upload_from_filename(tmp_zip.name)
    logger.info(f"[upload_file_to_gcs] Uploaded {local_path} to {zip_filename}/{file_path}")

def append_to_file_in_gcs(zip_filename: str, file_path: str, content: str):
    apply_llm_edits_to_gcs(zip_filename, [{
        "file": file_path,
        "action": "append",
        "content": content,
    }])

def extract_zip_from_gcs(workspace_id: str, extract_to: str):
    _ensure_client_initialized()
    blob = bucket.blob(f"{workspace_id}/archive.zip")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

def list_files_in_zip_from_gcs(workspace_id: str) -> list:
    _ensure_client_initialized()
    blob = bucket.blob(f"{workspace_id}/archive.zip")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            file_list = zip_ref.namelist()
    return file_list

def read_file_from_zip_in_gcs(workspace_id: str, file_path: str) -> str:
    _ensure_client_initialized()
    blob = bucket.blob(f"{workspace_id}/archive.zip")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        blob.download_to_filename(tmp_zip.name)
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            with zip_ref.open(file_path) as f:
                content = f.read().decode()
    return content 