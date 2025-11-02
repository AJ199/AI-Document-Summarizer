# AI Document Summarizer (React + Azure OpenAI)

An AI-powered document summarization app that lets you:
- upload a PDF / image-based doc,
- extract text using **Azure Document Intelligence**,
- chunk + embed text into **Chroma**,
- run **RAG**-style summarization using **Azure OpenAI**,
- view the result in a React UI.

## Tech Stack
- Frontend: React (Vite)
- Backend: FastAPI (Python)
- AI: Azure OpenAI (chat + embeddings)
- OCR/Parsing: Azure Document Intelligence (Form Recognizer)
- Vector Store: ChromaDB
- Infra: Docker + docker-compose

## Running Locally (without Docker)

### 1) Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
