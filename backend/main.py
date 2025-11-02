import os
import io
import hashlib
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from openai import OpenAI

import chromadb
from chromadb.config import Settings

# ----------------- ENV -----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")  # Azure endpoint
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-05-01-preview")
OPENAI_DEPLOYMENT = os.getenv("OPENAI_DEPLOYMENT_NAME")
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT", "text-embedding-3-large")

AZURE_FORMREC_ENDPOINT = os.getenv("AZURE_FORMREC_ENDPOINT")
AZURE_FORMREC_KEY = os.getenv("AZURE_FORMREC_KEY")

CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma")

# ----------------- CLIENTS -----------------
# Azure Form Recognizer client
if AZURE_FORMREC_ENDPOINT and AZURE_FORMREC_KEY:
    form_client = DocumentAnalysisClient(
        AZURE_FORMREC_ENDPOINT,
        AzureKeyCredential(AZURE_FORMREC_KEY)
    )
else:
    form_client = None

# OpenAI (Azure)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE or None,
)

# Chroma
chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_DIR))
collection = chroma_client.get_or_create_collection("summarizer_docs")

# ----------------- FASTAPI APP -----------------
app = FastAPI(title="AI Document Summarizer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    doc_id: str
    question: str | None = None

# ----------------- UTILS -----------------
def chunk_text(text: str, max_len: int = 800) -> List[str]:
    words = text.split()
    chunks = []
    cur = []
    for w in words:
        cur.append(w)
        if len(cur) >= max_len:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    resp = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=texts
    )
    return [d.embedding for d in resp.data]

def upsert_doc(doc_id: str, chunks: List[str]):
    ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
    embeds = embed_texts(chunks)
    metas = [{"doc_id": doc_id, "chunk": i} for i in range(len(chunks))]
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeds,
        metadatas=metas
    )

def retrieve_chunks(doc_id: str, query: str, k: int = 6) -> List[str]:
    q_vec = embed_texts([query])[0]
    res = collection.query(
        query_embeddings=[q_vec],
        n_results=k,
        where={"doc_id": doc_id}
    )
    return res["documents"][0] if res["documents"] else []

def summarize_with_llm(sections: List[str]) -> str:
    context = "\n\n".join([f"[Chunk {i}]\n{sec}" for i, sec in enumerate(sections)])
    system = (
        "You are an AI assistant that summarizes documents. "
        "Keep the structure, mention section references as [Chunk i], and stay grounded."
    )
    user = f"Summarize the following document sections:\n\n{context}"
    resp = openai_client.chat.completions.create(
        model=OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

# ----------------- ROUTES -----------------
@app.get("/")
def root():
    return {"ok": True, "msg": "AI Summarizer Backend running"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Upload a PDF/Doc, extract text, chunk, embed, and store in Chroma."""
    data = await file.read()
    doc_id = hashlib.sha1(data).hexdigest()[:16]

    text = ""
    # Prefer Azure Document Intelligence
    if form_client is not None:
        poller = form_client.begin_analyze_document("prebuilt-layout", document=io.BytesIO(data))
        result = poller.result()
        for page in result.pages:
            for line in page.lines:
                text += line.content + "\n"
    else:
        # Fallback: try pdfminer
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(io.BytesIO(data))
        except Exception:
            text = data.decode(errors="ignore")

    if not text.strip():
        return {"error": "Could not extract text from document"}

    chunks = chunk_text(text, 800)
    upsert_doc(doc_id, chunks)

    return {"doc_id": doc_id, "chunks": len(chunks)}

@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    # If user asked a question → do targeted RAG
    if req.question:
        sections = retrieve_chunks(req.doc_id, req.question, k=8)
    else:
        # General summary → get all chunks for that doc
        res = collection.get(where={"doc_id": req.doc_id})
        sections = res.get("documents", [])[:8]
    summary = summarize_with_llm(sections)
    return {"summary": summary}
