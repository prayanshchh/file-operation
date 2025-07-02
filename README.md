# MCP Server

A FastAPI-based server for performing filesystem operations on uploaded workspaces, with MinIO for storage and LLM integration for file edits.

## Features
- Upload a ZIP folder, extract, and store in MinIO under a unique workspace ID
- List files/folders in a workspace
- Get file content or signed download URL
- Edit files using natural language prompts via LLM

## Setup

1. Copy `.env.example` to `.env` and fill in your values.
2. Build and start services:

```bash
docker-compose up --build
```

- FastAPI: [http://localhost:8000/docs](http://localhost:8000/docs)
- MinIO Console: [http://localhost:9001](http://localhost:9001) (user/pass: minioadmin)

## API Endpoints

### POST /upload
Upload a ZIP file. Returns workspace_id and file count.

### GET /files/{workspace_id}
List all files/folders in the workspace.

### GET /file/{workspace_id}/{path:path}
Get the content of a file as plain text.

### GET /signed-url/{workspace_id}/{path:path}
Get a signed URL to download a file.

### POST /edit
Edit files using a prompt. Body:
```
{
  "workspace_id": "...",
  "prompt": "Add a license header to all Python files"
}
```

## Environment Variables
See `.env.example` for all required variables.

## Development
- Python 3.10+
- FastAPI, MinIO, httpx, python-dotenv, pydantic 