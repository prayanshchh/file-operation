import os
from minio import Minio
from minio.error import S3Error
from typing import List
import tempfile
import zipfile
import io
import logging
import uuid

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "mcp-workspaces")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

logger = logging.getLogger("minio_utils")

def upload_file_to_minio(zip_filename: str, file_path: str, local_path: str):
    logger.info(f"[upload_file_to_minio] Uploading {local_path} to {zip_filename}/{file_path}")
    minio_path = f"{zip_filename}/{file_path}"
    minio_client.fput_object(MINIO_BUCKET, minio_path, local_path)
    logger.info(f"[upload_file_to_minio] Uploaded {local_path} to {minio_path}")

def list_files_in_minio(zip_filename: str, prefix: str = "") -> list:
    # List files inside the zip file in MinIO
    minio_path = zip_filename
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            file_list = [f for f in zip_ref.namelist() if f.startswith(prefix)] if prefix else zip_ref.namelist()
    response.close()
    response.release_conn()
    return file_list

def read_file_from_minio(zip_filename: str, file_path: str) -> str:
    content = ""
    # Read file content from zip file in MinIO
    minio_path = zip_filename
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            # Normalize file_path for comparison
            file_list = zip_ref.namelist()
            print("I am file_List: ", file_list)
            if file_path not in file_list:
                response.close()
                response.release_conn()
                return "file doesn't exist"
            with zip_ref.open(file_path) as f:
                content = f.read().decode()
    response.close()
    response.release_conn()
    return content

def write_file_to_minio(zip_filename: str, file_path: str, content: str):
    """
    Overwrite (erase all content and write new content) the specified file inside the zip in MinIO.
    """
    # Use apply_llm_edits_to_minio to replace the file
    apply_llm_edits_to_minio(zip_filename, [{
        "file": file_path,
        "action": "replace",
        "content": content,
    }])

def append_to_file_in_minio(zip_filename: str, file_path: str, extra: str):
    """
    Append content to a file inside a zip in MinIO. If the file does not exist, create it with the content.
    """
    files = list_files_in_minio(zip_filename)
    if file_path in files:
        current_content = read_file_from_minio(zip_filename, file_path)
        new_content = current_content + extra
    else:
        new_content = extra
    # Use apply_llm_edits_to_minio to replace the file
    apply_llm_edits_to_minio(zip_filename, [{
        "file": file_path,
        "action": "replace",
        "content": new_content,
    }])

def delete_file_from_minio(zip_filename: str, file_path: str):
    """
    Delete a file from inside a zip in MinIO.
    """
    minio_path = zip_filename
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        original_zip_path = tmp_zip.name
    response.close()
    response.release_conn()

    # Prepare a new ZIP without the file to be deleted
    with tempfile.NamedTemporaryFile(delete=False) as new_zip_file:
        with zipfile.ZipFile(original_zip_path, 'r') as zin, \
             zipfile.ZipFile(new_zip_file.name, 'w') as zout:
            for item in zin.infolist():
                if item.filename != file_path:
                    zout.writestr(item, zin.read(item.filename))

    # Overwrite the old zip in MinIO with the new one
    minio_client.fput_object(MINIO_BUCKET, minio_path, new_zip_file.name)

def upload_zip_to_minio(zip_path: str) -> str:
    """Upload a zip file to MinIO root with a UUID filename. Returns the zip filename."""
    zip_uuid = str(uuid.uuid4()) + ".zip"
    minio_path = zip_uuid
    minio_client.fput_object(MINIO_BUCKET, minio_path, zip_path)
    return zip_uuid

def extract_zip_from_minio(workspace_id: str, extract_to: str):
    minio_path = f"{workspace_id}/archive.zip"
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    response.close()
    response.release_conn()

def apply_llm_edits_to_minio(zip_filename: str, instructions: list):
    minio_path = zip_filename
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        original_zip_path = tmp_zip.name
    response.close()
    response.release_conn()

    with tempfile.NamedTemporaryFile(delete=False) as new_zip_file:
        with zipfile.ZipFile(original_zip_path, 'r') as zin, \
             zipfile.ZipFile(new_zip_file.name, 'w') as zout:
            # Build a set of files to be replaced or deleted
            replace_map = {instr['file']: instr for instr in instructions if instr['action'] in ('replace', 'append')}
            delete_set = {instr['file'] for instr in instructions if instr['action'] == 'delete'}

            # Copy over all files except those being replaced or deleted
            for item in zin.infolist():
                if item.filename not in replace_map and item.filename not in delete_set:
                    zout.writestr(item, zin.read(item.filename))

            # Add/replace files
            for instr in instructions:
                if instr['action'] == 'replace':
                    zout.writestr(instr['file'], instr['content'])
                elif instr['action'] == 'append':
                    try:
                        old_content = zin.read(instr['file']).decode()
                    except KeyError:
                        old_content = ''
                    zout.writestr(instr['file'], old_content + instr['content'])
                # 'delete' is handled by not copying the file

    # Delete the old zip from MinIO
    minio_client.remove_object(MINIO_BUCKET, minio_path)
    minio_client.fput_object(MINIO_BUCKET, minio_path, new_zip_file.name)

def list_files_in_zip_from_minio(workspace_id: str) -> list:
    minio_path = f"{workspace_id}/archive.zip"
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            file_list = zip_ref.namelist()
    response.close()
    response.release_conn()
    return file_list

def read_file_from_zip_in_minio(workspace_id: str, file_path: str) -> str:
    minio_path = f"{workspace_id}/archive.zip"
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        with zipfile.ZipFile(tmp_zip.name, 'r') as zip_ref:
            with zip_ref.open(file_path) as f:
                content = f.read().decode()
    response.close()
    response.release_conn()
    return content

def create_file_in_zip_in_minio(zip_filename: str, file_path: str, content: str = ""):
    minio_path = zip_filename
    response = minio_client.get_object(MINIO_BUCKET, minio_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_zip:
        tmp_zip.write(response.read())
        tmp_zip.flush()
        original_zip_path = tmp_zip.name
    response.close()
    response.release_conn()

    # Prepare a new ZIP with the new file added (if it doesn't exist)
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

    minio_client.fput_object(MINIO_BUCKET, minio_path, new_zip_file.name) 