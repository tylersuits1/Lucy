# Lucy — Family AI Assistant

Lucy is a self-hosted, local-first AI assistant for household use. It runs
entirely on a home server, is reachable from mobile and any computer via a
private network (Tailscale), answers questions using a RAG
(retrieval-augmented generation) pipeline over family documents/notes, can
ingest uploaded files and auto-organize them, and backs itself up to Google
Drive. No data leaves the local network except that one-way backup — Drive
is never an intake point, and the backup tool can only see files it created
itself in Drive, nothing else in the account.

## Architecture

```
[Web/mobile client] --(Tailscale, HTTPS)--> [FastAPI backend on Omarchy server]
                                                    |
                        +---------------------------+---------------------------+
                        |                            |                          |
                 [Ollama (LLM)]            [Chroma (vector DB, embedded)]  [Local filesystem]
                        |                            |                          |
                        +----------- RAG query flow -+                          |
                                                                                 |
                                                                    [Local filesystem] --backup--> [Google Drive]
```

- **Backend**: Python, FastAPI
- **LLM runtime**: Ollama, running locally on the server
- **Vector DB**: Chroma, embedded (no separate server process)
- **Canonical storage**: local filesystem, Markdown as the primary note
  format, plus a folder for original uploaded files (PDFs, images, docx, etc.)
- **Google Drive**: one-way daily backup via `rclone` (a systemd timer, not
  a Python dependency), scoped to Drive's `drive.file` permission — see
  `BACKUP_SETUP.md`
- **Remote access**: Tailscale mesh network — no public exposure
- **Frontend**: React/Next.js PWA (installable to iOS home screen), talks to
  the FastAPI backend over the Tailscale network

## Why these choices

- **Ollama over cloud APIs**: keeps family data entirely local — nothing
  leaves the network except the one-way Drive backup. No per-token cost, no
  dependency on a third party staying up or keeping pricing stable.
- **Chroma over alternatives (Qdrant, Pinecone, etc.)**: embeds directly into
  the FastAPI process, so there's no separate database server to run and
  maintain on modest hardware. Plenty capable for a family-scale knowledge
  base (thousands of documents, not millions). Migrating to something like
  Qdrant later is possible since the RAG logic sits above the vector store.
- **Tailscale over public hosting**: private mesh network means no port
  forwarding, no public attack surface, and no reverse-proxy/TLS-cert
  maintenance burden beyond what Tailscale + Caddy already handle.

## Project status

Phases 1-4 are built: core chat loop, the RAG pipeline, a PWA frontend
reachable from any device over Tailscale (deployed and confirmed working on
the Omarchy server, `lucy-omarchy`), and file upload with LLM-based
auto-organization (`POST /upload` extracts text — PDF/docx/OCR — classifies
it with Ollama, files it away, and makes it immediately searchable). Phase
5 (Google Drive backup) has a documented setup path (`BACKUP_SETUP.md`)
using `rclone` rather than app code — a live OAuth app pulling from a
shared Drive folder was scrapped as too large a privacy footprint; local
data now backs up to Drive one-way instead. See `Lucy(AI) About.md` for the
full phased build plan.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed
```

Requires [Ollama](https://ollama.com) running and reachable at `OLLAMA_HOST`
(defaults to `http://localhost:11434`), with the model in `OLLAMA_MODEL`
pulled:

```bash
ollama pull llama3.1:8b
```

Run the dev server:

```bash
uvicorn app.main:app --reload
```

Test it:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Lucy"}'
```

Interactive API docs are available at `http://localhost:8000/docs`.

## Non-goals (v1)

- No training a model from scratch — uses an existing open-weight model via
  Ollama.
- No LoRA fine-tuning in v1 (phase 2 addition once RAG works).
- No public internet exposure — remote access is via Tailscale only.
- Google Drive is sync-in/sync-out only, never the canonical database.
