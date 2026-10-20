# INSTRUCTION.md - A Complete Beginner's Guide to PDF-ChatGPT

This guide assumes you have **never used** Python, Visual Studio Code, Git, FastAPI, the OpenAI API,
LangChain, FAISS, vector databases, or RAG before. Every step is spelled out. Follow them in order.

> **Tip:** Anywhere you see a gray code block, that is a command to type (or copy-paste) into a
> terminal, followed by pressing **Enter**.

---

## Table of Contents

1. [Installing Python](#1-installing-python)
2. [Installing Visual Studio Code](#2-installing-visual-studio-code)
3. [Installing Git](#3-installing-git)
4. [Installing Required VS Code Extensions](#4-installing-required-vs-code-extensions)
5. [Opening the Project](#5-opening-the-project)
6. [Creating a Virtual Environment](#6-creating-a-virtual-environment)
7. [Activating the Virtual Environment](#7-activating-the-virtual-environment)
8. [Installing Dependencies](#8-installing-dependencies)
9. [Creating the .env File](#9-creating-the-env-file)
10. [Obtaining an OpenAI API Key](#10-obtaining-an-openai-api-key)
11. [Running the Application](#11-running-the-application)
12. [Uploading Your First PDF](#12-uploading-your-first-pdf)
13. [Building Embeddings](#13-building-embeddings)
14. [Creating the Vector Database](#14-creating-the-vector-database)
15. [Running Semantic Search](#15-running-semantic-search)
16. [Asking Questions](#16-asking-questions)
17. [Testing Every Feature](#17-testing-every-feature)
18. [Running Automated Tests](#18-running-automated-tests)
19. [Updating Dependencies](#19-updating-dependencies)
20. [Project Architecture](#20-project-architecture)
21. [Folder Structure](#21-folder-structure)
22. [Common Errors](#22-common-errors)
23. [Troubleshooting](#23-troubleshooting)
24. [FAQ](#24-faq)
25. [Security Best Practices](#25-security-best-practices)
26. [Recommended Learning Resources](#26-recommended-learning-resources)
27. [Next Learning Steps](#27-next-learning-steps)

---

## 1. Installing Python

Python is the programming language this project is written in. You need version **3.12 or newer**.

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/).
2. Click the big yellow **Download Python 3.12.x** button.
3. Run the installer.
   - **Windows:** On the very first screen, **check the box "Add python.exe to PATH"** before clicking
     "Install Now". This step is easy to miss and causes most beginner problems.
   - **macOS:** Run the downloaded `.pkg` file and follow the prompts (all defaults are fine).
4. Verify the install by opening a terminal (see box below) and typing:

   ```bash
   python --version
   ```

   You should see something like `Python 3.12.4`. If you see `command not found` or `'python' is not
   recognized`, restart your computer and try again, or reinstall while checking the PATH box.

   > On macOS, if `python --version` doesn't work, try `python3 --version` instead - macOS ships an
   > older system Python under a different name.

**What is a terminal?**
- **Windows:** Press the Start key, type `cmd`, and press Enter to open Command Prompt.
- **macOS:** Press `Cmd+Space`, type `Terminal`, and press Enter.

---

## 2. Installing Visual Studio Code

Visual Studio Code (VS Code) is a free code editor.

1. Go to [https://code.visualstudio.com/](https://code.visualstudio.com/).
2. Click **Download** for your operating system.
3. Run the installer, accepting the defaults.
   - **Windows:** During install, check "Add to PATH" if offered.
4. Launch VS Code once to confirm it opens correctly.

---

## 3. Installing Git

Git lets you download ("clone") the project and track changes.

1. Go to [https://git-scm.com/downloads](https://git-scm.com/downloads).
2. Download and run the installer for your OS, accepting the default options.
3. Verify with:

   ```bash
   git --version
   ```

   You should see something like `git version 2.45.0`.

> If you already have the project as a downloaded `.zip` folder instead of using Git, you can skip
> straight to [Section 5](#5-opening-the-project) - just extract the zip somewhere convenient first.

---

## 4. Installing Required VS Code Extensions

Open VS Code, click the **Extensions** icon in the left sidebar (four squares), and install:

| Extension       | Publisher       | Purpose                                   |
|-----------------|-----------------|--------------------------------------------|
| Python          | Microsoft       | Python language support, debugging          |
| Pylance          | Microsoft       | Fast, accurate autocomplete and type checking |
| Ruff             | Astral Software | Linting and code formatting                 |

Search each name in the Extensions search bar and click **Install**. When you open this project, VS
Code will also prompt you to install these automatically (they're listed in `.vscode/extensions.json`).

---

## 5. Opening the Project

1. Download or clone the repository:

   ```bash
   git clone https://github.com/your-org/pdf-chatgpt.git
   ```

   (If you downloaded a `.zip` instead, extract it to a folder like `Documents/pdf-chatgpt`.)

2. Open VS Code.
3. Go to **File -> Open Folder...** and select the `pdf-chatgpt` folder.
4. Open the built-in terminal: **Terminal -> New Terminal** (or `` Ctrl+` ``). All remaining commands in
   this guide are typed into this terminal, inside the `pdf-chatgpt` folder.

---

## 6. Creating a Virtual Environment

A **virtual environment** is an isolated folder that holds this project's Python packages, so they
don't conflict with other projects on your computer.

```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

This creates a new folder named `venv/` inside the project. You only need to do this once.

---

## 7. Activating the Virtual Environment

Activation tells your terminal to use the packages inside `venv/` instead of your system Python. You
must do this **every time** you open a new terminal to work on this project.

```bash
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

When activated, your terminal prompt will show `(venv)` at the start of the line, like:

```
(venv) C:\Users\you\pdf-chatgpt>
```

> **PowerShell execution policy error?** If PowerShell blocks the script, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then try activating again.

---

## 8. Installing Dependencies

With the virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This downloads FastAPI, LangChain, FAISS, the OpenAI SDK, and everything else the project needs. It
may take a few minutes the first time. You'll know it worked when you see a line like
`Successfully installed fastapi-... uvicorn-... openai-...` with no red error text above it.

For running tests and linting too, also install:

```bash
pip install -r requirements-dev.txt
```

---

## 9. Creating the .env File

The `.env` file holds your personal configuration (like your OpenAI API key) and is never committed to
Git, keeping your secrets private.

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open the new `.env` file in VS Code (click it in the file explorer on the left) - you'll fill in the
OpenAI key in the next step.

---

## 10. Obtaining an OpenAI API Key

1. Go to [https://platform.openai.com/](https://platform.openai.com/) and sign up or log in.
2. Click your profile icon -> **API Keys** (or go directly to
   [platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
3. Click **Create new secret key**, give it a name like `pdf-chatgpt-dev`, and click **Create**.
4. **Copy the key immediately** - it starts with `sk-` and is shown only once.
5. Open `.env` in VS Code and replace the placeholder line:

   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

   with your real key:

   ```env
   OPENAI_API_KEY=sk-abc123...your-real-key...
   ```

6. Save the file (`Ctrl+S` / `Cmd+S`).
7. Make sure your OpenAI account has a payment method on file under **Settings -> Billing** - embeddings
   and chat responses are billed per token (typically fractions of a cent per question).

---

## 11. Running the Application

With the virtual environment activated and `.env` configured, start the server:

```bash
uvicorn app.main:app --reload
```

You should see log output ending with something like:

```
INFO     | Uvicorn running on http://0.0.0.0:8000
```

Open your web browser and go to **http://localhost:8000**. You should see the PDF-ChatGPT chat
interface.

> **Even easier:** double-click `Start App.bat` (Windows) or `Start App (Mac).command` (macOS) in the
> project folder - these scripts do steps 6-11 for you automatically every time.

To stop the server, click back in the terminal and press `Ctrl+C`.

---

## 12. Uploading Your First PDF

1. In the browser, look at the left sidebar under **Document Library**.
2. Click the upload icon (a small file icon next to "Document Library").
3. Choose a PDF from your computer - or, to test quickly, use the sample file already included at
   `data/sample_docs/sample-rag-guide.pdf`.
4. Wait for the status badge next to the file to change from **uploaded** -> **processing** ->
   **indexed**. This usually takes a few seconds for small PDFs.

If the badge turns **failed**, hover over the document to see the error (commonly: the PDF is
password-protected, or it's a scanned image with no real text layer).

---

## 13. Building Embeddings

You don't need to trigger this manually - it happens automatically the moment you upload a PDF. Behind
the scenes:

1. The text is extracted from each page (`app/services/pdf_service.py`).
2. The text is split into overlapping chunks (`app/services/chunking_service.py`).
3. Each chunk is sent to OpenAI's embedding model (`app/services/embedding_service.py`), which returns
   a vector of numbers representing that chunk's meaning.

You can see this happen in your terminal logs, e.g.:

```
INFO | app.services.embedding_service | Embedding 12 text chunks
```

---

## 14. Creating the Vector Database

Also automatic. After embeddings are generated, they are added to a **FAISS** index and saved to disk
under `data/vector_store/` (`app/services/vector_store_service.py`). You'll see two files appear there:

```
data/vector_store/index.faiss   <- the vector index itself
data/vector_store/index.pkl     <- metadata (which chunk came from which document/page)
```

This index persists between server restarts - you don't need to re-upload documents every time you
launch the app.

---

## 15. Running Semantic Search

Semantic search happens automatically every time you ask a question - but you can also try it directly
via the interactive API docs:

1. Go to **http://localhost:8000/api/docs**.
2. Expand **POST /api/chat**.
3. Click **Try it out**.
4. Enter a request body like:

   ```json
   {
     "question": "What is Retrieval-Augmented Generation?",
     "conversation_id": null
   }
   ```

5. Click **Execute** and scroll down to see the response, including the `sources` array showing exactly
   which document/page the answer came from.

---

## 16. Asking Questions

Back in the main chat UI (http://localhost:8000):

1. Type a question in the box at the bottom, e.g. *"What is this document about?"*
2. Press **Enter** (or click the send button).
3. Watch the answer stream in token by token, formatted with Markdown, and followed by source citations
   showing the document name, page number, and relevance score.
4. Ask a follow-up question - the app remembers the conversation (conversation memory), so you can say
   things like *"Can you explain that in simpler terms?"*

Use the **Search scope** dropdown in the header to restrict answers to a single uploaded document.

---

## 17. Testing Every Feature

Use this checklist to confirm everything works end-to-end:

| # | Feature                  | How to test                                                                  |
|---|----------------------------|-------------------------------------------------------------------------------|
| 1 | Upload PDF                  | Upload the sample PDF; confirm status becomes "indexed"                      |
| 2 | Multiple PDFs                | Upload a second, different PDF                                              |
| 3 | Document Library              | Confirm both PDFs appear in the sidebar with page/chunk counts               |
| 4 | Delete document                | Click the trash icon next to a document; confirm it disappears              |
| 5 | New conversation                | Click "New Conversation"; confirm the chat clears                            |
| 6 | Ask a question                   | Ask something answerable from your PDF; confirm a grounded answer + sources |
| 7 | Ask an unanswerable question       | Ask something unrelated; confirm the model says it can't find the answer  |
| 8 | Conversation memory                | Ask a follow-up question referring to the previous answer                  |
| 9 | Conversation history                | Reload the page, click a past conversation in the sidebar, confirm it loads |
| 10 | Streaming                          | Watch the answer appear progressively, not all at once                     |
| 11 | Markdown rendering                   | Ask "give me a bulleted list summary" and confirm bullets render properly  |
| 12 | Dark/light mode                       | Click the sun/moon icon top-left; confirm the theme switches and persists  |
| 13 | Responsive design                       | Resize your browser window narrow; confirm the sidebar collapses to a toggle |
| 14 | Swagger UI                                | Visit `/api/docs` and execute a request directly                          |
| 15 | Document-scoped search                     | Use the "Search scope" dropdown to restrict to one document                |

---

## 18. Running Automated Tests

The project ships with a `pytest` test suite covering PDF extraction, chunking, and the API layer.

```bash
pip install -r requirements-dev.txt # if not already installed
pytest tests -v
```

Expected output ends with something like:

```
9 passed, 1 skipped in 1.10s
```

The one skipped test requires a **real** `OPENAI_API_KEY` (it uploads a PDF and generates real
embeddings) - it's skipped automatically in offline/CI environments to avoid unnecessary API costs.

You can also lint and type-check the code:

```bash
ruff check app tests
mypy app
```

---

## 19. Updating Dependencies

To check for newer package versions:

```bash
pip list --outdated
```

To update a specific package:

```bash
pip install --upgrade fastapi
```

After upgrading, re-run the test suite (`pytest tests -v`) to confirm nothing broke, then update the
version pin in `requirements.txt` to match.

To recreate your environment from scratch (useful if things get into a weird state):

```bash
deactivate
# Windows: rmdir /s /q venv        macOS/Linux: rm -rf venv
python -m venv venv
# activate again (Section 7), then:
pip install -r requirements.txt
```

---

## 20. Project Architecture

PDF-ChatGPT follows **Clean Architecture**:

- **API layer** (`app/api/`) - handles HTTP requests/responses only.
- **Service layer** (`app/services/`) - the actual RAG pipeline logic (PDF parsing, chunking,
  embeddings, vector search, chat generation, memory).
- **Domain layer** (`app/domain/`) - plain data structures with no framework dependencies.
- **Infrastructure layer** (`app/infrastructure/`) - SQLite database access via SQLAlchemy.

See the full architecture diagram and explanation in [README.md](README.md#architecture).

---

## 21. Folder Structure

See [README.md](README.md#folder-structure) for the complete annotated folder tree.

---

## 22. Common Errors

| Error message                                              | Meaning & Fix                                                                 |
|---------------------------------------------------------------|--------------------------------------------------------------------------------|
| `'python' is not recognized as an internal or external command` | Python isn't on your PATH. Reinstall Python and check "Add to PATH".         |
| `No module named 'fastapi'`                                     | The virtual environment isn't activated, or dependencies weren't installed. Run Section 7 then Section 8. |
| `OPENAI_API_KEY is not configured`                                | `.env` is missing your key. Revisit Section 10.                              |
| `409 Conflict` when asking a question                              | No PDF has been indexed yet. Upload one first (Section 12).                  |
| `Address already in use` when starting uvicorn                      | Port 8000 is busy. Run `uvicorn app.main:app --reload --port 8001` instead.  |
| PDF status stuck on "processing" then turns "failed"                | The PDF likely has no extractable text (scanned images). Try a text-based PDF. |
| `ExecutionPolicy` error activating venv in PowerShell                | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.      |

---

## 23. Troubleshooting

If something isn't working:

1. **Read the terminal output.** The log line right above the error usually names the failing module.
2. **Check `logs/app.log`** for the full history of what the server did.
3. **Confirm your virtual environment is active** - your prompt should start with `(venv)`.
4. **Confirm `.env` has a real API key**, not the placeholder value.
5. **Restart the server** (`Ctrl+C`, then `uvicorn app.main:app --reload` again) - this re-reads `.env`
   and re-initializes the database.
6. **Delete and rebuild the vector index** if search results look wrong or stale:
   ```bash
   # macOS/Linux
   rm -rf data/vector_store/*
   # Windows
   del /q data\vector_store\*
   ```
   Then re-upload your PDFs.
7. Still stuck? Re-read [Common Errors](#22-common-errors) above, then check the [FAQ](#24-faq).

---

## 24. FAQ

**Q: Do I need a paid OpenAI account?**
A: You need billing enabled (a payment method on file), but usage for a few test PDFs typically costs
well under $1.

**Q: Can I use a different LLM provider (not OpenAI)?**
A: The chat and embedding logic is isolated in `app/services/chat_service.py` and
`app/services/embedding_service.py` - you could adapt these to another provider, but out of the box
this project targets OpenAI's Responses API.

**Q: Where is my data stored?**
A: Uploaded PDFs live in `data/uploads/`, the FAISS index in `data/vector_store/`, and conversation
history in the SQLite file `data/app.db`. Nothing leaves your machine except the text sent to OpenAI
for embeddings and chat generation.

**Q: Can multiple people use this at once?**
A: The default setup is single-tenant (no login system) and best suited for individual or small-team
use. See Future Improvements in README.md for multi-tenant ideas.

**Q: Why does my PDF fail to index?**
A: The most common cause is a **scanned PDF** - an image of text rather than real, selectable text.
`pypdf` can only extract text that's actually encoded in the PDF, not text baked into an image.

**Q: What happens if I close the terminal?**
A: The server stops. Close the browser tab too, or just reopen it after restarting the server - your
data (documents, index, conversations) is safely persisted to disk and will still be there.

---

## 25. Security Best Practices

- **Never commit your `.env` file.** It's already excluded via `.gitignore` - keep it that way.
- **Never share your OpenAI API key** in screenshots, chat messages, or public repos. If you
  accidentally expose one, revoke it immediately at platform.openai.com/api-keys and create a new one.
- **Set spend limits** on your OpenAI account (Settings -> Billing -> Usage limits) to avoid surprise
  charges from a bug or runaway script.
- **Don't expose this app directly to the public internet without authentication.** As shipped, anyone
  who can reach the server can upload documents and consume your OpenAI quota. Put it behind a VPN, add
  an auth layer, or restrict network access if deploying beyond your own machine.
- **Validate uploaded files.** The app already restricts uploads to `.pdf` files under a configurable
  size limit (`MAX_UPLOAD_MB`); don't loosen these checks in a public deployment.
- **Keep dependencies updated** (Section 19) - security patches for FastAPI, Starlette, and other
  libraries ship regularly.

---

## 26. Recommended Learning Resources

- **Python basics:** [official Python tutorial](https://docs.python.org/3/tutorial/)
- **FastAPI:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com/) - the official docs are excellent
  for beginners.
- **Git & GitHub:** [git-scm.com/book](https://git-scm.com/book/en/v2)
- **LangChain:** [python.langchain.com](https://python.langchain.com/)
- **RAG concepts:** search "Retrieval-Augmented Generation explained" for numerous free explainer
  articles and videos.
- **OpenAI API:** [platform.openai.com/docs](https://platform.openai.com/docs)
- **SQL / SQLAlchemy:** [docs.sqlalchemy.org](https://docs.sqlalchemy.org/)

---

## 27. Next Learning Steps

Once comfortable running and using this project, try:

1. **Modify the system prompt** in `app/core/constants.py` and observe how answer style changes.
2. **Add a new document type** (e.g., `.txt` support) by extending `pdf_service.py`'s sibling services.
3. **Add authentication** so only logged-in users can upload documents.
4. **Swap FAISS for a cloud vector database** (Pinecone, Qdrant, pgvector) for a multi-user deployment.
5. **Write a new API endpoint** (e.g., document summarization) following the existing service pattern.
6. **Read through `app/services/chat_service.py`** to understand exactly how retrieved chunks are
   turned into a grounded prompt, and how the OpenAI Responses API streaming works.
7. **Explore the test suite** in `tests/` and try adding a new test for a feature you modify.

Welcome to RAG application development - happy building!
