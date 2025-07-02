import logging
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from minio_utils import (
    write_file_to_minio,
    delete_file_from_minio,
    create_file_in_zip_in_minio,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("RESSL-MCP Server")

@mcp.tool(
    description=(
        "Edit (overwrite) a file *inside* a ZIP stored in MinIO. "
        "`zip_filename`: The full object key of the ZIP in MinIO (e.g., 'adfab5e….zip'). "
        "`file_path`: The path *inside* the ZIP (may include subdirectories, e.g., 'folder/file.txt'). "
        "`new_content`: The new content to write to the file."
    )
)
def edit_file(zip_filename: str, file_path: str, new_content: str) -> str:
    """Overwrite the file with new content inside the ZIP."""
    try:
        write_file_to_minio(zip_filename, file_path, new_content)
        return "OK"
    except Exception as e:
        logger.error(f"Error editing file: {e}")
        raise

@mcp.tool(
    description=(
        "Create a new file *inside* a ZIP stored in MinIO (if it does not exist). "
        "`zip_filename`: The full object key of the ZIP in MinIO (e.g., 'adfab5e….zip'). "
        "`file_path`: The path *inside* the ZIP (may include subdirectories, e.g., 'folder/file.txt'). "
        "`content`: The content to write to the new file (optional, defaults to empty)."
    )
)
def create_file(zip_filename: str, file_path: str, content: str) -> str:
    """Create a new file with optional content inside the ZIP. Does not overwrite if exists."""
    try:
        create_file_in_zip_in_minio(zip_filename, file_path, content)
        return "OK"
    except Exception as e:
        logger.error(f"Error creating file: {e}")
        raise

@mcp.tool(
    description=(
        "Delete a file *inside* a ZIP stored in MinIO. "
        "`zip_filename`: The full object key of the ZIP in MinIO (e.g., 'adfab5e….zip'). "
        "`file_path`: The path *inside* the ZIP (may include subdirectories, e.g., 'folder/file.txt')."
    )
)
def delete_file(zip_filename: str, file_path: str) -> str:
    """Delete a file from inside the ZIP."""
    try:
        delete_file_from_minio(zip_filename, file_path)
        return "OK"
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise

app = mcp.http_app(stateless_http=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run_async("streamable-http", host="0.0.0.0", port=3000)) 