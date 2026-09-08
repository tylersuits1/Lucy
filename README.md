# Lucy — Family AI Assistant

Lucy is a self-hosted AI assistant for household use. It runs entirely on a
home server, is reachable from mobile and any computer via a private
network (Tailscale), answers questions using a RAG (retrieval-augmented
generation) pipeline over family documents/notes, can ingest uploaded files
and auto-organize them, and backs itself up to Google Drive. All data
storage and retrieval stays local — the LLM call itself goes to the Gemini
API (see "Why these choices" below for why that trade was made), and the
Drive backup is one-way (local → Drive only, `drive.file`-scoped so it can
only see files it created itself).

## Architecture

```
[Web/mobile client] --(Tailscale, HTTPS)--> [FastAPI backend on Omarchy server]
                                                    |
                        +---------------------------+---------------------------+
                        |                            |                          |
              [Gemini API (LLM)]          [Chroma (vector DB, embedded)]  [Local filesystem]
                        |                            |                          |
                        +----------- RAG query flow -+                          |
                                                                                 |
                                                                    [Local filesystem] --backup--> [Google Drive]
```

- **Backend**: Python, FastAPI
- **LLM runtime**: Gemini API (`gemini-3.1-flash-lite` by default) — see
  below for why this replaced a locally-run Ollama model
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

- **Gemini API over local Ollama**: originally ran a local model to keep
  everything on-box, but the server's 7.7GiB RAM couldn't handle it well —
  a single request pushed RAM usage to 7.1GiB and into swap. Moving the LLM
  call itself to Gemini's API removes that constraint entirely (nothing
  heavy to load locally) while keeping RAG, storage, and retrieval fully
  local — only the final generation step leaves the box, not the document
  store. Configured with billing enabled specifically because Google's free
  tier uses submitted content to improve their products; the paid tier
  doesn't, and at `gemini-3.1-flash-lite` pricing, family-scale usage costs
  cents.
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
it, files it away, and makes it immediately searchable). Phase 5 (Google
Drive backup) has a documented setup path (`BACKUP_SETUP.md`) using
`rclone` rather than app code — a live OAuth app pulling from a shared
Drive folder was scrapped as too large a privacy footprint; local data now
backs up to Drive one-way instead. The LLM backend was later switched from
a locally-run Ollama model to the Gemini API to resolve persistent RAM
pressure on the server hardware — see "Why these choices." See
`Lucy(AI) About.md` for the full phased build plan.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed
```

Requires a Gemini API key in `GEMINI_API_KEY` — get one at
[aistudio.google.com/apikey](https://aistudio.google.com/apikey) and
enable billing on it (free-tier content is used to improve Google's
products; paid-tier isn't). `GEMINI_MODEL` defaults to
`gemini-3.1-flash-lite`.

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

- No training or self-hosting a model — uses the Gemini API.
- No LoRA fine-tuning (not applicable now that the LLM is API-based, not
  self-hosted).
- No public internet exposure — remote access is via Tailscale only.
- Google Drive is sync-in/sync-out only, never the canonical database.
