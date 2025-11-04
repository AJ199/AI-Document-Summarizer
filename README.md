# AI Document Summarizer

## Overview
The AI Document Summarizer is a full-stack system that automatically condenses lengthy documents into grounded, section-level summaries.  
It combines Azure Cognitive Services, Azure OpenAI (GPT-4o-mini), and vector retrieval to deliver factual, structured insights with an intuitive React interface.

## Tech Stack
React, FastAPI, Azure OpenAI, Azure Cognitive Services, Vector Database

## Architecture
The system follows a three-tier architecture:

1. Frontend (React.js) – Handles file uploads (PDF/Text), displays interactive highlights, and enables real-time feedback loops.  
2. Backend (FastAPI) – Orchestrates preprocessing, text segmentation, embedding, and summarization through Azure OpenAI.  
3. Vector Layer – Embedding store supporting retrieval-augmented summarization for factual accuracy.

## Key Features
- Grounded summaries through semantic chunking and vector search  
- Interactive UI with highlighting and feedback  
- Modular backend (easily switch between OpenAI, Azure, or Bedrock models)

## What I Learned
- Building retrieval-augmented pipelines  
- Combining frontend interactivity with backend AI reasoning
