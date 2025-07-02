# MCP Server

## Demo

A demo of the application is available below:

![MCP demo](demo.webm)
---

## Overview

**MCP Server** is a full-stack application for AI-powered file operations on user workspaces, built with:

- **FastAPI** (Python) for the backend API
- **MinIO** (S3-compatible object storage) for storing user ZIP workspaces and files
- **LLM (via agent integration)** for natural language file editing
- **React + Vite + Tailwind** for the frontend UI

---

## Key Features

- **Upload ZIP folders**: Users upload a ZIP archive, which is stored in MinIO with a unique ID.
- **File browser & viewer**: Browse, view, and copy the contents of files inside the uploaded ZIP.
- **Prompt-based file editing**: Use natural language prompts to edit, create, or manipulate files inside the ZIP using an LLM agent.
- **Dynamic file list**: The file list updates in real time after every agent action.
- **Flexible file selection**: Users can select a file, enter a custom file path, or prompt the agent without specifying a file.
- **Modern UI**: Responsive, beautiful React frontend with smooth UX.

---

## Technologies Used

- **FastAPI**: High-performance Python web framework for the backend API.
- **MinIO**: S3-compatible object storage for storing ZIPs and file data.
- **Python LLM agent**: Integrates with OpenAI or other LLMs for prompt-based file editing.
- **React + Vite**: Fast, modern frontend with hot reload and TypeScript support.
- **Tailwind CSS**: Utility-first CSS for rapid, beautiful UI development.
- **Docker Compose**: For easy local development and service orchestration.

---

## How It Works

1. **Upload**: User uploads a ZIP file via the frontend. The backend stores it in MinIO and returns a unique ZIP ID.
2. **Browse**: The frontend fetches and displays the file list from the ZIP (via `/list-files/{zip_id}`).
3. **View**: Clicking a file fetches its content from the backend and displays it in a viewer.
4. **Prompt**: User can select a file, enter a custom file path, or leave it blank, and submit a prompt to the agent (via `/agent-file`). The agent can edit, create, or manipulate files using LLM.
5. **Update**: After each agent action, the file list is refreshed to reflect changes.

---

## API Endpoints

- `POST /upload-zip`: Upload a ZIP file. Returns `zip_filename` (unique ID).
- `GET /list-files/{zip_filename}`: List all files in the uploaded ZIP.
- `GET /file/{zip_filename}/{file_path}`: Get the content of a file as plain text.
- `POST /agent-file`: Edit or create files using a prompt and (optionally) a file path.
- `POST /write-file`, `DELETE /delete-file`, `POST /apply-llm-edits`, `POST /create-file-in-zip`: Advanced file operations (see backend code for details).

---

## Setup & Development

### Prerequisites

- Python 3.10+
- Node.js (for frontend)
- Docker & Docker Compose (for MinIO and easy orchestration)

### Backend

1. **Install dependencies**:
   ```bash
   cd ressl-mcp
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:  
   Copy `.env.example` to `.env` and fill in your MinIO and LLM credentials.

3. **Start MinIO (S3 storage)**:
   ```bash
   docker-compose up -d
   ```

4. **Run FastAPI backend**:
   ```bash
   uvicorn fastapi_backend:app --host 0.0.0.0 --port 8000
   ```

### Frontend

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the frontend**:
   ```bash
   npm run dev
   ```
   The app will be available at [http://localhost:5173](http://localhost:5173).

---

## Environment Variables

- See `.env.example` for all required variables (MinIO endpoint, access keys, LLM API keys, etc).

---

## Tech Stack

- **Backend**: FastAPI, MinIO, httpx, python-dotenv, pydantic, fastmcp, python-multipart, uvicorn
- **Frontend**: React, Vite, Tailwind CSS, TypeScript, Axios, React Icons

---

## License

MIT (or your license here) 