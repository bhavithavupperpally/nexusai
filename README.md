# PDF-ChatGPT

**Chat with your PDF documents using Retrieval-Augmented Generation (RAG) powered by Google Gemini.**

PDF-ChatGPT is a production-ready, resume-worthy, and enterprise-style RAG application built with FastAPI, LangChain,
FAISS, and the official **Google GenAI SDK (Gemini)**. Upload one or more PDFs, and ask natural-language questions
that are answered using only the content of your documents — with citations back to the exact page, token streaming,
and structured outputs, all operable at **₹0 cost** on Google Gemini's generous free tier.

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Flash%20%2B%20Embeddings-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

> New to Python, VS Code, or RAG entirely? See **[INSTRUCTION.md](INSTRUCTION.md)** for a beginner's walkthrough.

---

## Table of Contents

- [What is RAG?](#what-is-rag)
- [Key Concepts](#key-concepts)
  - [Embeddings](#embeddings)
  - [Chunking](#chunking)
  - [Semantic Search](#semantic-search)
  - [Vector Databases](#vector-databases)
  - [FAISS](#faiss)
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Visual Studio Code Setup](#visual-studio-code-setup)
- [Google Gemini API Setup (Free Tier — ₹0)](#google-gemini-api-setup-free-tier--0)
- [Running the Application](#running-the-application)
- [API Reference (Swagger)](#api-reference-swagger)
- [Testing](#testing)
- [Free Tier Deployment Guide](#free-tier-deployment-guide)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## What is RAG?

**Retrieval-Augmented Generation (RAG)** is an architecture that grounds a large language model's answers
in an external knowledge source instead of relying purely on what the model memorized during training.

Without RAG, an LLM can only answer from its training data — it has no access to *your* private PDFs,
and it may hallucinate incorrect facts. RAG solves this by:

1. Breaking uploaded documents into small, searchable **chunks**.
2. Converting each chunk into a dense numeric vector (an **embedding**) capturing semantic meaning.
3. Storing those vectors in a **vector database** (FAISS on disk).
4. When a user asks a question, embedding the *question* and finding the most similar chunks (**semantic search**).
5. Supplying those retrieved chunks to the LLM (Google Gemini) as context, and prompting it to answer **using only that context**.

The result: grounded, accurate answers traceable to the source document and page number.

```
PDF Upload -> Text Extraction -> Chunking -> Gemini Embeddings -> Vector Database (FAISS)
                                                                            │
                                                                            ▼
User Question ────────────────────────────────────────────────────► Retriever (semantic search)
                                                                            │
                                                                            ▼
                                                                      Relevant Chunks
                                                                            │
                                                                            ▼
                                                                      Google Gemini  ──►  Answer + Citations
```

---

## Key Concepts

### Embeddings

An embedding is a dense vector of floating-point numbers representing semantic meaning. Texts with similar
meanings produce vectors with high cosine similarity. PDF-ChatGPT supports **high-performance local embeddings**
via `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) by default, running 100% locally on CPU.

**Why Local Embeddings?**
- **Zero API Quota / Rate Limits:** Cloud embedding APIs (like Gemini free tier) impose limits of 100–150 requests per minute, failing with `429 RESOURCE_EXHAUSTED` on large PDFs (e.g. 400+ pages, 1,200+ chunks).
- **100% Free & Private:** Embeddings run entirely on your local machine without sending document chunks over the network.
- **Fast:** Batch encoding encodes ~1,200 chunks in under 20 seconds on standard CPU.
- **Configurable:** You can switch to Google Gemini embeddings (`gemini-embedding-001`) anytime by setting `EMBEDDING_PROVIDER=gemini` in `.env`.

### Chunking

LLMs have finite context windows, and embedding an entire 100-page PDF as a single vector loses fine-grained facts.
**Chunking** divides documents into overlapping pieces (by default 1,000 characters with a 150-character overlap)
using LangChain's `RecursiveCharacterTextSplitter`. It splits on paragraph boundaries, sentences, and words to avoid
cutting ideas mid-sentence.

### Semantic Search

Semantic search retrieves information by *meaning*, not simple keyword matching. Questions like "What is the fee?"
can find passages stating "the subscription rate is ₹0" even without shared keywords.

### Vector Databases & FAISS

**FAISS** (Facebook AI Similarity Search) provides high-performance vector similarity search. The index is
persisted to disk under `data/vector_store/`, surviving app restarts without requiring heavy external database
infrastructure. The service automatically handles dimension compatibility and resets indexes safely if models change.

---

## Features

| Feature                     | Description                                                                 |
|------------------------------|-------------------------------------------------------------------------------|
| **₹0 Cost AI Engine**        | Powered by Google Gemini (`gemini-2.5-flash` + `text-embedding-004`) on the free tier |
| **PDF Extraction**           | Robust per-page text extraction with `pypdf`, handling clean binary offsets  |
| **Document Library**         | Real-time sidebar tracking uploaded files, chunk counts, and page statistics |
| **LangChain Chunking**       | Paragraph-aware overlapping text chunking                                     |
| **FAISS Vector Database**    | Persistent on-disk vector similarity search with metadata tracking           |
| **Token Streaming (SSE)**    | Server-Sent Events delivering token-by-token real-time streaming in the UI    |
| **Structured Output**        | Native JSON schema enforcement returning answers, key points, and confidence |
| **Exact Citations**          | Every answer cites the source document and page number `[Document, p. X]`    |
| **Conversation Memory**      | SQLite-persisted multi-turn conversation history                             |
| **Interactive UI**           | Vanilla JS single-page app with Markdown, syntax highlighting, and dark mode |
| **FastAPI Backend**          | High-performance async API with automated Swagger/OpenAPI documentation      |

---

## Architecture

PDF-ChatGPT follows **Clean Architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Delivery layer:  app/api/        (FastAPI routers, DI, HTTP)    │
├─────────────────────────────────────────────────────────────────┤
│  Use cases:       app/services/   (RAG pipeline, chat, ingestion)│
├─────────────────────────────────────────────────────────────────┤
│  Domain:          app/domain/     (entities, schemas - no deps)  │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure:  app/infrastructure/ (SQLAlchemy, repositories) │
└─────────────────────────────────────────────────────────────────┘
```

- **`app/api`** — REST endpoints for documents, chat streaming, and health checks.
- **`app/services`** — Modular business services: `PDFExtractionService`, `ChunkingService`, `EmbeddingService` (Gemini), `VectorStoreService` (FAISS), `RetrievalService`, `ChatService` (Gemini), and `MemoryService`.
- **`app/domain`** — Pure Pydantic v2 schemas and domain dataclasses.
- **`app/infrastructure`** — SQLite database, ORM models, and repository pattern.
- **`app/static`** — Responsive chat UI (HTML5, modern CSS, vanilla JavaScript).

---

## Folder Structure

```
pdf-chatgpt/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan, static mounting
│   ├── config.py                # Pydantic Settings (Gemini & storage config)
│   ├── logging_config.py        # Rotating file + console logging
│   ├── api/                     # API routers (health, documents, chat)
│   ├── core/                    # Constants, prompts, and custom exceptions
│   ├── domain/                  # Schemas (Pydantic v2) and models
│   ├── infrastructure/          # SQLite DB engine, models, repository
│   ├── services/                # Gemini chat & embeddings, FAISS, PDF parsing
│   └── static/                  # Single-page web UI (HTML, CSS, JS)
├── data/
│   ├── uploads/                 # Uploaded PDFs (git-ignored)
│   ├── vector_store/            # FAISS index files (git-ignored)
│   └── sample_docs/             # Sample PDF for testing
├── logs/                        # Application logs (git-ignored)
├── tests/                       # Complete pytest suite (mocked & unit tests)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git exclusion rules
├── .gitattributes              # Binary preservation rules for PDFs
├── requirements.txt             # Production dependencies (google-genai, etc.)
├── requirements-dev.txt         # Dev & testing dependencies
├── pyproject.toml               # Tool configuration (pytest, ruff)
├── Start App.bat                # Windows one-click launcher
└── README.md                    # Project documentation
```

---

## Installation

### 1. Prerequisites
- **Python 3.12 or 3.13** installed ([python.org](https://www.python.org/downloads/)).
- Git installed.

### 2. Clone the repository
```bash
git clone https://github.com/your-username/pdf-chatgpt.git
cd pdf-chatgpt
```

### 3. Create and activate virtual environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv .venv
.\.venv\Scripts\activate.bat

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt

# For running tests and dev tools:
pip install -r requirements-dev.txt
```

---

## Google Gemini API Setup (Free Tier — ₹0)

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account and click **Create API Key**.
3. Copy your API key.
4. Copy `.env.example` to `.env`:
   ```bash
   # Windows
   copy .env.example .env

   # macOS / Linux
   cp .env.example .env
   ```
5. Open `.env` and set your key:
   ```env
   # Chat generation via Google Gemini
   GEMINI_API_KEY=AIzaSy...your-gemini-key
   GEMINI_CHAT_MODEL=gemini-flash-lite-latest

   # Embeddings: local (recommended: free, offline, no 429 limits) or gemini
   EMBEDDING_PROVIDER=local
   LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

> **Security Note:** Never commit `.env` or share your API key. `.env` is automatically ignored in `.gitignore`.

---

## Running the Application

### Option A: Via Command Line
With your virtual environment activated:
```bash
uvicorn app.main:app --reload
```
The server will start at:
- **Web UI:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (or [/api/docs](http://localhost:8000/api/docs))
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Option B: Windows One-Click Launcher
Double-click **`Start App.bat`**. It automatically detects the virtual environment, verifies dependencies, checks configuration, and launches the application.

---

## Testing

The project includes unit and integration tests. All default tests use mocks for external Gemini calls so they run fast, offline, and at **₹0 cost**:

```bash
# Run tests with the project virtual environment
pytest tests -v
```

### Test Suite Structure
- `tests/test_pdf_service.py`: Validates 3-page PDF extraction and error handling.
- `tests/test_chunking_service.py`: Validates paragraph-aware chunking and page indices.
- `tests/test_gemini_services.py`: Validates Gemini embeddings, streaming, structured output, and vector store reset.
- `tests/test_api_documents.py`: Validates document upload and indexing pipeline end-to-end.
- `tests/test_api_health.py`: Validates health status and configuration indicators.

---

## Free Tier Deployment Guide

This application can be deployed on popular free-tier cloud platforms.

### Free Hosting Options
1. **Render (Web Service - Free Tier)**
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Set environment variable: `GEMINI_API_KEY`
   - *Limitation:* Free instances spin down after inactivity (cold start ~50s) and have ephemeral file storage unless a disk is attached.
2. **Hugging Face Spaces (Docker Free Tier)**
   - Uses CPU Basic (free).
   - Add a `Dockerfile` and configure `GEMINI_API_KEY` as a Space secret.
3. **Local Tunnel (ngrok / Cloudflare Tunnel) — 100% Free**
   - Run the app locally on your machine with persistent storage and share a secure URL.

---

## Troubleshooting

| Issue | Cause & Solution |
|---|---|
| `GEMINI_API_KEY is not configured` (HTTP 412) | Ensure `GEMINI_API_KEY` is set in `.env` and restart the server. |
| `Trailer cannot be read: Unexpected type` | PDF line endings were corrupted by CRLF conversion. Keep binary mode via `.gitattributes`. |
| `VectorStoreNotReadyError` (HTTP 409) | No PDF has been indexed yet. Upload a document before querying. |
| Model quota or rate limit error | Google AI Studio free tier limits requests per minute (RPM). Add brief delays or check quota in AI Studio. |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
