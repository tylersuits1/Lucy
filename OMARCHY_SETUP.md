# Omarchy Server Setup — Instructions for Claude Code

**Audience:** this file is written to be read and executed by Claude Code
running *on the target machine* (the old Intel Mac that will run Omarchy
Linux as Lucy's home server). It also documents the manual, human-only steps
that have to happen before Claude Code can do anything.

**Goal of this pass:** get Omarchy installed, get Ollama + the Llama 3.1 8B
model running, clone this repo, get the Phase 1 `/chat` endpoint answering
for real (not just erroring with "Ollama unreachable"), and get the machine
reachable over Tailscale. Nothing beyond that — Phase 2+ (RAG, uploads, Drive
sync, systemd service, Caddy) comes later.

If you are Claude Code reading this: work through **Part B** top to bottom,
running commands directly. Stop and clearly tell the user whenever you hit a
step marked **HUMAN ACTION REQUIRED** — those need a browser, a password, or
a physical action only the user can do. Don't skip verification commands;
confirm each step worked before moving to the next.

---

## Part A — Before Claude Code can do anything (user does this manually)

These happen outside of Claude Code, because the machine doesn't have an OS,
a network, or Claude installed yet at the start of this process.

### A1. Confirm the Mac model and back up anything on it

- Find the exact model: Apple menu → About This Mac, or check the label
  under the machine. If unsure how, use [Apple's "Identify your Mac"
  guide](https://support.apple.com/en-us/108052).
- **This install erases the whole disk.** Omarchy does not currently support
  dual-booting with macOS — the manual is explicit that it only supports
  "being the only OS installed" on Mac hardware. Back up anything you want
  to keep off that machine first (external drive, iCloud, whatever).
- Note whether it has a **T2 chip** (Macs from 2018–2020) or is older/no T2.
  Omarchy has had official T2 support since v3.0 (patched kernel, audio, the
  Broadcom Wi-Fi/Bluetooth firmware, fan control all handled automatically
  by the installer). Non-T2 Intel Macs are supported too but with fewer
  automatic fixes. Reference: [Omarchy Mac Support
  manual](https://omarchy.org/manual/mac-support/).

### A2. Download the Omarchy ISO and write it to a USB drive

1. Go to **[omarchy.org](https://omarchy.org)** and click **ISO** to
   download it. A `.sha256` checksum file is published alongside it — grab
   that too and verify the download matches before writing it to a USB
   stick.
2. Get a USB drive (8GB+ is plenty).
3. Write the ISO to the USB stick using
   **[balenaEtcher](https://etcher.balena.io)** (works from your current
   Mac). Download it, open it, select the Omarchy ISO, select the USB
   drive, flash.

### A3. Disable Secure Boot and allow external boot (T2 Macs)

If this is a T2-equipped Mac (2018–2020), you must disable Apple's Secure
Boot before the USB stick will boot at all:

1. Shut the Mac down completely.
2. Power on and immediately hold **Cmd+R** until you see a loading screen —
   this boots macOS Recovery.
3. Select your user, enter your password if asked.
4. From the menu bar: **Utilities → Startup Security Utility**.
5. Authenticate again with your password.
6. Under **Secure Boot**, choose **No Security**.
7. Under **External Boot**, choose **Allow booting from external or
   removable media**.
8. Restart.

### A4. Ethernet (if this is a MacBook without built-in Ethernet)

Wi-Fi will **not** work until Omarchy's installer has already set up the
Broadcom firmware — which happens *during* install, but the installer itself
needs network access to fetch packages. If the machine only has Wi-Fi (no
built-in Ethernet port, e.g. any MacBook), get a **USB-C (or USB-A) to
Ethernet adapter** and plug it into your router before booting the
installer. Mac Minis/iMacs with a built-in Ethernet port don't need this.

### A5. Boot the installer and run it

1. Insert the USB stick, restart the Mac, and immediately hold **Option**
   (⌥) until the boot picker appears.
2. Select the **orange "EFI Boot"** device.
3. The Omarchy Configurator boots. Answer its prompts (keyboard layout,
   username, password, timezone) and pick the internal disk when asked
   where to install — **this wipes it**.
4. Install takes roughly 1–5 minutes depending on hardware.
5. One quirk: full-disk encryption is on by default, and **a Bluetooth
   keyboard cannot enter the unlock password at boot**. Use a wired
   keyboard (or a 2.4GHz USB-dongle wireless one) for at least the first
   boot after install, or during install if using an external keyboard at
   all.
6. Reboot into Omarchy (Hyprland desktop).
7. Connect it to your home Wi-Fi (or leave Ethernet plugged in) from the
   desktop's network settings so it has normal internet access.

### A6. Install and log into Claude Code on this machine

Open a terminal (Alacritty, Omarchy's default terminal) and run:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Then run `claude` and complete the login flow it opens in your browser
(same Anthropic account you use elsewhere).

### A7. Get this file (and the rest of the repo) onto the machine

Once Claude Code is running, hand it this exact file. The easiest path:
tell Claude Code to clone the Lucy repo — it can drive GitHub auth itself
(Part B, step 1) and this file will come down as part of the clone at
`~/Lucy/OMARCHY_SETUP.md`. You don't need to manually copy anything over.

**Once A1–A6 are done, open Claude Code on the Omarchy machine and tell it:
"Follow OMARCHY_SETUP.md Part B" (or paste this file's contents to it).**

---

## Part B — Steps for Claude Code to execute on the Omarchy machine

Run these in order. After each step, verify before continuing — if a
command fails, stop and report the error rather than pushing forward.

### B1. Get the repo onto this machine

Check for the GitHub CLI and authenticate:

```bash
command -v gh || sudo pacman -S --needed --noconfirm github-cli
gh auth status || gh auth login
```

`gh auth login` will ask: GitHub.com → HTTPS → **login with a web browser**.
It prints a one-time code and a URL.

> **HUMAN ACTION REQUIRED:** open the URL it prints (e.g.
> `https://github.com/login/device`) on any device's browser, enter the
> code, and approve. Tell Claude Code once you've done this so it can
> continue.

Then clone the repo:

```bash
gh repo clone tylersuits1/Lucy ~/Lucy
cd ~/Lucy
```

Verify: `ls` should show `README.md`, `backend/`, `OMARCHY_SETUP.md`, etc.

### B2. Sanity-check hardware

```bash
uname -m          # expect x86_64
free -h           # check total RAM
df -h /            # check free disk space
```

Llama 3.1 8B (the default quantized pull) is ~4.7GB on disk and comfortably
runs with 8GB+ RAM, though it'll be slow if the machine has to swap. If
`free -h` shows less than ~8GB total RAM, tell the user — a smaller model
(e.g. `llama3.2:3b`) may be a better fit for this hardware, and that's a
one-line change to `OLLAMA_MODEL` in `.env` later.

### B3. Update the system and install base tooling

```bash
sudo pacman -Syu --noconfirm
```

> **HUMAN ACTION REQUIRED:** `sudo` will prompt for the account password
> the user set during install.

```bash
sudo pacman -S --needed --noconfirm python python-pip base-devel git
```

(Omarchy ships with a lot of dev tooling out of the box, so several of
these may already be installed — `--needed` skips ones that are.)

### B4. Install Ollama and pull the model

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable --now ollama
```

Verify the service is up:

```bash
curl -s http://localhost:11434/api/tags
```

(Should return `{"models":[...]}`, not a connection error.)

Pull the model specified in the project's `.env.example`:

```bash
ollama pull llama3.1:8b
```

This downloads ~4.7GB — it'll take a while on a slow connection. Verify:

```bash
ollama list
```

Should show `llama3.1:8b` in the list.

### B5. Set up the Python backend

```bash
cd ~/Lucy/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The defaults in `.env` (`OLLAMA_HOST=http://localhost:11434`,
`OLLAMA_MODEL=llama3.1:8b`) are already correct for this machine — no edits
needed unless B2 suggested a smaller model.

### B6. Smoke-test the chat endpoint for real

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Say hello in one short sentence."}'
```

The `/chat` call should now return an actual model-generated reply (not the
502 "Failed to reach Ollama" error seen during development on the Mac
laptop). If it still errors, check `ollama list` and `systemctl status
ollama` before anything else.

Stop the test server once confirmed: `kill %1` (or `pkill -f uvicorn`).

### B7. Install Tailscale and join the tailnet

```bash
sudo pacman -S --needed --noconfirm tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up
```

This prints a URL like `https://login.tailscale.com/a/xxxxxxxxxxxx`.

> **HUMAN ACTION REQUIRED:** open that URL in a browser on any
> already-logged-in device (phone is fine) and approve the new machine. If
> this is the very first device on the tailnet, it'll ask you to sign up —
> **[tailscale.com](https://tailscale.com)** supports signing in with an
> existing Google/GitHub/Microsoft account, no separate password needed.

Verify once approved:

```bash
tailscale status
tailscale ip -4
```

Note the Tailscale IP (or the MagicDNS name shown in `tailscale status`,
usually something like `omarchy-server.your-tailnet.ts.net`) — that's the
address the frontend and your phone will use to reach Lucy later. Nothing
else needs to be done with it yet; there's no PWA or reverse proxy in front
of it in this phase.

### B8. Report back

Confirm and summarize for the user:
- Ollama running with the model pulled and answering
- `/chat` returning real replies locally on the box
- Tailscale connected, with the machine's Tailscale hostname/IP noted
- Anything that deviated from this doc (different RAM/disk than expected,
  a package that needed a different name, etc.)

**Not in scope for this pass** (later phases, don't build yet): the
systemd unit in `deploy/lucy-backend.service` so the backend survives
reboots, Caddy, the RAG/Chroma pipeline, file upload, and Drive sync. Those
come in later phases per the main project brief.

---

# Lucy-Omarchy Phase 2

**Goal of this pass:** get the RAG pipeline (Chroma + local embeddings) that
was just built and tested on the dev Mac running here on `lucy-omarchy` too,
with real family notes ingested and `/chat` giving answers grounded in them
instead of generic replies.

**Already true going into this** (from Phase 1): repo cloned at `~/Lucy`,
venv at `~/Lucy/backend/venv`, Ollama running with `llama3.1:8b` pulled,
Tailscale connected (hostname `lucy-omarchy`, IP `100.87.24.48`). This
machine has **7.7GiB RAM** — under the ~8GB comfort threshold — so watch for
slowness once the embedding model is loaded alongside Ollama.

If you are Claude Code reading this: work through **Part C** in order,
verifying each step. The step marked **HUMAN ACTION REQUIRED** needs the
user to decide on and supply real content — don't guess family details on
their behalf.

## Part C — Steps for Claude Code to execute (RAG pipeline)

### C1. Pull the Phase 2 code

```bash
cd ~/Lucy
git pull
```

Verify: `ls backend/app/rag/` should now show `embed.py` and `retrieve.py`
alongside the existing `ollama_client.py`, and `backend/scripts/ingest_notes.py`
should exist.

### C2. Install the new Python dependencies

This pulls in `chromadb` and `sentence-transformers` — the latter depends
on `torch`, a much larger install than anything from Phase 1. Two things
bite on a GPU-less Linux box like this one, so handle both up front rather
than waiting for the plain install to fail:

1. **PyPI's default `torch` wheel for Linux bundles ~1.5GB of NVIDIA CUDA
   libraries** this machine can't use (no GPU). Install the CPU-only build
   explicitly instead.
2. **`/tmp` is a small RAM-backed tmpfs on most Arch/systemd systems**
   (sized as a fraction of total RAM — on this machine's 7.7GiB that's only
   a few GB), and `pip`'s temp download/build files land there by default.
   A `torch`-sized install can blow through it and fail with `Disk quota
   exceeded` even though the real disk has plenty of room. Point `TMPDIR`
   at a real directory on disk to avoid it.

```bash
cd ~/Lucy/backend
source venv/bin/activate
mkdir -p ~/pip-tmp
TMPDIR=~/pip-tmp pip install torch --index-url https://download.pytorch.org/whl/cpu
TMPDIR=~/pip-tmp pip install -r requirements.txt
```

Check disk space if anything still looks tight:

```bash
df -h /
```

A slow install here is expected and one-time — it's not a sign anything's
wrong.

### C3. Add real family notes

> **HUMAN ACTION REQUIRED:** Chroma has nothing to retrieve until real notes
> exist in `~/Lucy/backend/data/notes/`. Decide what Lucy should know first
> — house rules, schedules, important dates, whatever's actually useful —
> and get it into that folder as one or more `.md` files. Options:
> - Dictate the content to Claude Code and have it write the file directly.
> - Copy existing notes over from another machine with `scp`.
> - If you just want to confirm the pipeline works before writing anything
>   real, have Claude Code create a placeholder note with one clear fact
>   (e.g. "trash pickup is Tuesdays") — the same acceptance test used on the
>   dev Mac.

### C4. Run the ingestion script

```bash
cd ~/Lucy/backend
source venv/bin/activate
python scripts/ingest_notes.py
```

Expect one line per file with its chunk count, then a total. The first run
downloads the `all-MiniLM-L6-v2` embedding model (~90MB) from Hugging Face —
a `Warning: You are sending unauthenticated requests to the HF Hub` message
is expected and harmless.

Re-run this script any time notes are added or edited. It's safe to re-run:
chunks are upserted by file path, so re-ingesting a changed file replaces
its old chunks rather than duplicating them.

### C5. Confirm /chat gives a grounded answer

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "<a question whose answer is in one of the ingested notes>"}'
kill %1
```

The reply should reflect the actual fact from the note, not a generic or
made-up answer. If it doesn't: confirm C4 reported chunks > 0 for that file,
and try rephrasing the question closer to the note's wording — embedding
search matches on meaning but still does better with closer phrasing.

### C6. Report back

Tell the user:
- How many notes/chunks were ingested
- The test question asked and whether the answer was correctly grounded
- Any slowness or memory pressure noticed given the 7.7GiB RAM, now that
  the embedding model is loaded alongside Ollama

**Not in scope for this pass:** file upload/auto-classification, Google
Drive sync, the frontend, systemd/Caddy — later phases per the main project
brief.

---

# Lucy-Omarchy Phase 3

**Goal of this pass:** deploy the PWA frontend that was just built on the dev
Mac, and put both the backend and frontend under systemd so Lucy survives
reboots. When this is done, Lucy should be usable from a phone: open a URL,
ask a question, get an answer, and it should keep working after the server
reboots — this machine is meant to run always-on, since Tailscale access
only works while it's actually reachable on the tailnet.

**Already true going into this:** repo cloned at `~/Lucy`, backend venv set
up with the RAG pipeline working, Ollama running, Tailscale connected
(hostname `lucy-omarchy`, IP `100.87.24.48`).

If you are Claude Code reading this: work through **Part D** in order. The
reboot-survival check (D6) ends this terminal session — say so before
running it, and pick back up verification afterward once reconnected.

## Part D — Steps for Claude Code to execute (frontend + systemd)

### D1. Pull the Phase 3 code

```bash
cd ~/Lucy
git pull
```

Verify: `ls frontend/src/app/` should show `page.tsx`, `layout.tsx`,
`manifest.ts`, `icon.tsx`, `apple-icon.tsx`. `ls deploy/` should show
`lucy-backend.service`, `lucy-frontend.service`, and `Caddyfile`.

### D2. Install Node.js

```bash
node --version || sudo pacman -S --needed --noconfirm nodejs npm
```

Omarchy is dev-focused and may already have Node installed — `--needed`
skips it if so.

### D3. Install frontend dependencies

```bash
cd ~/Lucy/frontend
npm install
```

### D4. Point the frontend at the backend's Tailscale address

This is the one step that's easy to get wrong: the API URL gets baked into
the browser-side JavaScript at build time, and that JavaScript runs in the
**viewer's** browser (a phone), not on this server. `localhost` would
resolve to the phone itself and fail. Use this machine's Tailscale IP or
MagicDNS hostname instead:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` so it reads:

```
NEXT_PUBLIC_API_BASE_URL=http://100.87.24.48:8000
```

(Or `http://lucy-omarchy:8000` if MagicDNS is enabled and resolving on the
devices you'll use — the raw IP is more foolproof if unsure.)

### D5. Build and start both services under systemd

Build the frontend (this is what actually bakes in the API URL from D4):

```bash
cd ~/Lucy/frontend
npm run build
```

Install the systemd unit templates, substituting the real user and home
directory:

```bash
cd ~/Lucy/deploy
sed -e "s|__LUCY_USER__|$USER|g" -e "s|__LUCY_HOME__|$HOME|g" lucy-backend.service | sudo tee /etc/systemd/system/lucy-backend.service > /dev/null
sed -e "s|__LUCY_USER__|$USER|g" -e "s|__LUCY_HOME__|$HOME|g" lucy-frontend.service | sudo tee /etc/systemd/system/lucy-frontend.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now lucy-backend lucy-frontend
```

> **HUMAN ACTION REQUIRED:** the `sudo` calls need the account password.

Verify both are actually up:

```bash
systemctl status lucy-backend --no-pager
systemctl status lucy-frontend --no-pager
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000
```

### D6. Confirm it survives a reboot

> **HUMAN ACTION REQUIRED / heads up:** this ends the current terminal
> session. Tell the user before running it.

```bash
sudo reboot
```

After it comes back up (give it a minute or two), reconnect and verify
without starting anything manually:

```bash
systemctl status lucy-backend --no-pager
systemctl status lucy-frontend --no-pager
curl -s http://localhost:8000/health
```

Both should already be running — that's the whole point of D5.

### D7. Test from an actual phone

> **HUMAN ACTION REQUIRED:** this part only the user can do.
> 1. Install the Tailscale app on the phone from the App Store / Play
>    Store, and sign into the same account used to set up `lucy-omarchy`
>    (originally at [tailscale.com](https://tailscale.com)).
> 2. With Tailscale connected on the phone, open
>    `http://100.87.24.48:3000` in the phone's browser.
> 3. Ask Lucy something and confirm a real answer comes back.
> 4. On iOS Safari: tap the Share icon → **Add to Home Screen** to install
>    it as an app icon.

### D8. Report back

Tell the user:
- Whether both systemd services came back up cleanly after the reboot
  test, with no manual intervention
- Whether the phone test worked, and what URL was used
- Anything that deviated from this doc

**Not in scope for this pass:** the Caddyfile in `deploy/` is there for
later if you want one clean address instead of two ports — optional, not
required for Phase 3 to be considered done. File upload/auto-organization
and Drive sync are Phases 4 and 5.

---

# Lucy-Omarchy Phase 4

**Goal of this pass:** deploy file upload + auto-organization. After this,
attaching a file in the PWA (the new "+" button next to the message box)
should extract its text, have Ollama classify it, file it into
`data/files/<category>/`, write a companion note, and make it immediately
answerable via chat.

**Already true going into this:** Phases 1-3 done and running under
systemd on `lucy-omarchy`.

## Part E — Steps for Claude Code to execute (file upload)

### E1. Pull the Phase 4 code

```bash
cd ~/Lucy && git pull
```

Verify: `ls backend/app/ingestion/` should show `extract.py`,
`classify.py`, and `organize.py`; `ls backend/app/routers/` should include
`upload.py`.

### E2. Install Tesseract (system package, needed for image OCR)

```bash
tesseract --version || sudo pacman -S --needed --noconfirm tesseract tesseract-data-eng
```

> **HUMAN ACTION REQUIRED:** the `sudo` call needs the account password.

This is a system package, not a Python one — `pip install` alone won't
provide it. `pytesseract` (the Python wrapper) just shells out to this
binary.

### E3. Install the new Python dependencies

```bash
cd ~/Lucy/backend
source venv/bin/activate
pip install -r requirements.txt
```

Adds `python-multipart` (FastAPI needs it to parse file uploads),
`pypdf`, `python-docx`, `pytesseract`, and `Pillow`. All pure-Python or
already have prebuilt wheels — nothing like the Phase 2 torch/CUDA issue
should come up here.

### E4. Rebuild the frontend and restart both services

The frontend needs rebuilding too — it now has the attach button:

```bash
cd ~/Lucy/frontend
npm run build
sudo systemctl restart lucy-backend lucy-frontend
```

### E5. Smoke-test the upload pipeline

```bash
echo "The water heater warranty runs through 2027." > /tmp/test-upload.txt
curl -s -X POST http://localhost:8000/upload -F "file=@/tmp/test-upload.txt"
```

Expect a JSON response with `category`, `filename`, `tags`, `summary`,
and `chunks_ingested` (should be ≥ 1) — not a 502. If it 502s, check that
Ollama is still running (`ollama list`) before anything else; the
classification step depends on it just like `/chat` does.

Then confirm it's actually answerable:

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How long is the water heater warranty?"}'
```

Should reference 2027, grounded in the note the upload just created.

Clean up the test artifacts so they don't linger as fake family data:

```bash
find ~/Lucy/backend/data/files ~/Lucy/backend/data/notes -iname "*water-heater*" -delete
```

(Chroma will still have a stale chunk referencing the deleted note until
the collection is rebuilt — harmless for now, but worth knowing; a future
phase could add a "remove/reingest" script if this becomes annoying.)

### E6. Test a real upload from the phone

> **HUMAN ACTION REQUIRED:** tap the "+" button in the PWA, pick an actual
> document (a PDF, a photo of something, whatever), and confirm the
> filing result shown in the chat looks sensible, then ask Lucy about it.

### E7. Report back

Tell the user:
- Whether the smoke test and the real phone upload both worked
- What category/tags/summary Ollama produced for the real test file
- Anything that deviated from this doc

**Not in scope for this pass:** a Google Drive backup (Phase 5) comes
next — but as a one-way local-to-cloud backup, not a live intake sync (see
below for why that plan changed).

---

# Lucy-Omarchy Phase 5

**Plan changed from the original brief:** file upload (Phase 4) already
covers getting documents into Lucy. A live OAuth app with standing access
to pull from a shared "Lucy Inbox" Drive folder turned out to be a bigger
privacy footprint than this project should have, given the whole point is
staying local and private. So Phase 5 is now a **one-way backup**
(local → Drive, never the reverse) instead of a sync/intake mechanism.
The Drive OAuth pull-sync code that was briefly built has been removed
from the repo entirely.

**Goal of this pass:** `backend/data/notes/` and `backend/data/files/` get
backed up to Google Drive daily via `rclone`, using Drive's most
restrictive `drive.file` access scope (the backup can only see files it
creates itself — never anything else in the Drive account). No Google
Cloud Console project needed this time; rclone has its own built-in OAuth
client for personal use.

**Full step-by-step instructions are in `BACKUP_SETUP.md`** at the repo
root — it covers installing rclone, running `rclone config` (including
the headless-server authorization flow via `rclone authorize` run
elsewhere), installing the `deploy/lucy-backup.service` +
`lucy-backup.timer` systemd units, and verifying it end-to-end. Pull the
latest code first (`cd ~/Lucy && git pull`) so those unit files exist,
then follow `BACKUP_SETUP.md` directly — there's no separate "Part G"
here since that doc already has the full sequence in Claude-Code-runnable
form, with **HUMAN ACTION REQUIRED** called out at the `rclone config`
step (it's an interactive wizard) and the authorization step (needs a
browser somewhere).

**Not in scope for this pass:** restoring from backup is documented in
`BACKUP_SETUP.md` but only needs running if something actually breaks —
no need to test a full restore as part of this deploy pass.

---

# Lucy-Omarchy — Remote Health Check & Kill Switch

**Goal of this pass:** three new commands, typed directly into the normal
Lucy chat box like any message — no new UI:
- **`/health`** — CPU/RAM/disk, whether Ollama is running, uptime, and a
  link to a live `btop` view in your browser.
- **`/kill`** — stops the Ollama service specifically (the actual RAM/CPU
  hog per the Phase 2 findings — up to 7.1GiB on this machine), so you can
  relieve pressure on the box without SSHing in. Everything else (the web
  app, file storage) stays up.
- **`/start`** — brings Ollama back so chat/uploads work again.

These are handled entirely in the backend before anything reaches the LLM
— typing `/kill` always does exactly one thing, deterministically. Not
built on the model's judgment.

**Security note worth reading before running this:** `/kill` and `/start`
need the backend (running as an unprivileged user) to run
`sudo systemctl stop/start ollama`. Part G below adds a **narrowly-scoped
passwordless sudo rule** — literally just those two exact commands,
nothing else — via a dedicated file in `/etc/sudoers.d/`, validated with
`visudo -c` before trusting it. Read G4 before running it; don't broaden
the scope beyond what's written there.

Also: the `btop` web terminal (linked from `/health`) is more sensitive
than everything else Lucy exposes — `btop` lets you interactively kill
*any* process, not just Ollama, from within its UI. Unlike the rest of
Lucy (which relies on the tailnet itself as the trust boundary), this one
gets an actual login prompt. Pick a real password in G5, not something
trivial.

## Part G — Steps for Claude Code to execute (health/kill switch)

### G1. Pull the code

```bash
cd ~/Lucy && git pull
```

Verify: `ls backend/app/system/` shows `health.py` and `control.py`.

### G2. Install the new Python dependency

```bash
cd ~/Lucy/backend
source venv/bin/activate
pip install -r requirements.txt
```

Adds `psutil` — pure C extension, prebuilt wheel, no system packages
needed.

### G3. Install ttyd and btop

```bash
sudo pacman -S --needed --noconfirm ttyd btop
```

> **HUMAN ACTION REQUIRED:** sudo password. (Omarchy likely already has
> `btop` — `--needed` skips it if so.)

### G4. Add the scoped sudo rule for the kill switch

```bash
echo "$USER ALL=(root) NOPASSWD: /usr/bin/systemctl stop ollama, /usr/bin/systemctl start ollama" | sudo tee /etc/sudoers.d/lucy-service-control > /dev/null
sudo chmod 440 /etc/sudoers.d/lucy-service-control
sudo visudo -c
```

> **HUMAN ACTION REQUIRED:** sudo password. `visudo -c` validates the
> syntax of *all* sudoers files afterward — if it reports a problem with
> `lucy-service-control`, fix or delete that file before moving on. Don't
> leave a broken sudoers file in place, and don't widen this rule beyond
> the two exact commands shown — that's what keeps the kill switch from
> becoming a general-purpose root shell.

### G5. Choose credentials for the btop web terminal, then install it

> **HUMAN ACTION REQUIRED:** pick a real username and password now — the
> `/health` link will prompt for them every time.

```bash
cd ~/Lucy/deploy
sed -e "s|__LUCY_USER__|$USER|g" -e "s|__TTYD_USER__|<pick a username>|g" -e "s|__TTYD_PASSWORD__|<pick a password>|g" lucy-btop.service | sudo tee /etc/systemd/system/lucy-btop.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now lucy-btop
```

### G6. Restart the backend

```bash
sudo systemctl restart lucy-backend
```

### G7. Test all three commands for real

From the PWA on your phone (or `curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "/health"}'` here first if you want to check locally):

- Send `/health` — expect CPU/RAM/disk/Ollama-status/uptime, plus a link
  like `http://100.87.24.48:7681`. Open it, log in with the G5 credentials,
  confirm you see live `btop`.
- Send `/kill` — expect confirmation Ollama stopped. Ask a normal
  question — it should fail (that's correct; Ollama's down on purpose).
- Send `/start` — expect confirmation it's restarting. Wait a few seconds,
  ask a normal question again — should work.

### G8. Report back

Tell the user:
- Whether all three commands worked from the actual phone/PWA
- Whether the btop link opened and the login prompt worked
- Anything that deviated from this doc

---

# Lucy-Omarchy — Fix: Stay Awake With the Lid Closed

**Why this exists:** confirmed by direct incident — closing the lid took
`lucy-omarchy` fully offline (unreachable over Tailscale), even though it
was plugged into AC power at the time. This machine is meant to run
24/7, tucked away somewhere with the lid closed (see the "Always On
Needs" notes) — so this isn't optional, it's a requirement for the whole
project to actually work as intended.

Since closing the lid dropped the machine *even on AC power*, the default
`HandleLidSwitchExternalPower` behavior either isn't set to `ignore`, or
something outside `logind` (most likely `hypridle`, which Omarchy's
Hyprland desktop runs by default for laptop power-saving) is suspending
it independently. Fix both layers rather than guessing which one it was.

## Part H — Steps for Claude Code to execute

### H1. Mask the sleep targets at the systemd level

This is the authoritative fix — it makes the machine structurally unable
to sleep, no matter what tries to trigger it (lid, idle timer, GUI,
`hypridle`, anything):

```bash
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

> **HUMAN ACTION REQUIRED:** sudo password.

Verify:

```bash
systemctl status sleep.target
```

Should show `Loaded: masked`.

### H2. Tell logind to ignore the lid switch entirely

Defense in depth, and fixes the actual reported symptom directly:

```bash
sudo sed -i \
  -e 's/^#\?HandleLidSwitch=.*/HandleLidSwitch=ignore/' \
  -e 's/^#\?HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' \
  -e 's/^#\?HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' \
  /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
```

> **HUMAN ACTION REQUIRED:** sudo password. Restarting `systemd-logind`
> can momentarily disrupt an active desktop session — fine for a headless
> always-on box, just don't be surprised if a local display session
> hiccups when you run this.

Verify:

```bash
grep -E '^HandleLidSwitch' /etc/systemd/logind.conf
```

Should show all three set to `ignore`.

### H3. Check for hypridle overriding this independently

```bash
cat ~/.config/hypr/hypridle.conf 2>/dev/null
```

If it exists and has a `suspend` (or `dpms`/`lock` chained into a
suspend) action on a timeout, either comment out that block or disable
the service entirely:

```bash
systemctl --user disable --now hypridle
```

(`hypridle` runs as a *user* service tied to the graphical session, not
system-wide — note `--user`, no `sudo` needed here.)

### H4. Real test — the one that actually matters

> **HUMAN ACTION REQUIRED:** close the lid, leave it closed for a few
> minutes, then check Tailscale from your phone. `lucy-omarchy` should
> still show as connected, and the PWA should still respond.

### H5. Report back

Tell the user:
- Whether `sleep.target` shows masked
- Whether the lid-close test actually stayed connected
- Whether `hypridle` was found running and what was done about it

---

# Lucy-Omarchy — Migrate to Gemini API (replaces Ollama)

**Why:** this machine has been RAM-constrained since Phase 2 (up to
7.1 of 7.7GiB during a single request) — Ollama was the entire cause.
Moving the LLM call to Google's Gemini API removes that problem outright;
nothing heavy needs to load locally anymore. RAG (Chroma, retrieval,
upload/classify/organize) is unchanged — only the final "send this to an
LLM" step moves off-box.

**Also removed as part of this:** the `/kill` and `/start` chat commands
existed specifically to relieve Ollama's RAM pressure. That problem no
longer exists, so they're gone from the code. `/health` still works
(CPU/RAM/disk/uptime + the btop link) — just drops the Ollama-status
line. The **sudoers rule from Part G4** (`systemctl stop/start ollama`)
is now unused — harmless to leave, but fine to remove too if you'd
rather tidy it up (`sudo rm /etc/sudoers.d/lucy-service-control`). The
`ttyd`/`btop` web terminal from Part G is unaffected and still useful for
general monitoring.

## Part I — Steps for Claude Code to execute

### I1. Get a Gemini API key first (human-only)

> **HUMAN ACTION REQUIRED:** go to
> [aistudio.google.com/apikey](https://aistudio.google.com/apikey),
> create a key, then **enable billing on it** (look for a "Set up
> billing" / plan upgrade prompt in AI Studio) rather than leaving it on
> the free tier. This matters: Google's own docs say free-tier content is
> used to improve their products; paid-tier explicitly isn't. At the
> pricing for `gemini-3.1-flash-lite` ($0.25/$1.50 per million tokens),
> family-scale usage costs cents, not dollars — the earlier $10 mentioned
> covers a very long time.

### I2. Pull the code

```bash
cd ~/Lucy && git pull
```

Verify: `ls backend/app/rag/` should show `gemini_client.py`, **not**
`ollama_client.py`. `ls backend/app/system/` should show `health.py`
only — `control.py` should be gone.

### I3. Add the API key and install the new dependency

```bash
cd ~/Lucy/backend
source venv/bin/activate
pip install -r requirements.txt
```

Edit `.env` — remove the old `OLLAMA_HOST`/`OLLAMA_MODEL` lines if still
present, add:

```
GEMINI_API_KEY=<the key from I1>
GEMINI_MODEL=gemini-3.1-flash-lite
```

### I4. Restart the backend

```bash
sudo systemctl restart lucy-backend
```

### I5. Test for a real reply

```bash
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Say hello in one short sentence."}'
```

Should return an actual Gemini-generated reply now — no Ollama involved
at all. Also re-test an upload (`POST /upload` with a test file, or the
"+" button in the PWA) to confirm classification still works end to end.

### I6. Optional cleanup — remove Ollama entirely

Since nothing uses it anymore, freeing the ~4.7GB model + the service
itself is reasonable:

```bash
sudo systemctl disable --now ollama
ollama rm llama3.1:8b
sudo pacman -Rs ollama
```

> **HUMAN ACTION REQUIRED:** sudo password. This is optional — nothing
> breaks if you leave Ollama installed and stopped, it just sits there
> unused.

### I7. Report back

Tell the user:
- Whether `/chat` returned a real Gemini reply
- Whether upload/classification still works end to end
- Whether Ollama was removed or left in place
- Any deviation from this doc

---

## Part J — Steps for Claude Code to execute (auth + per-user chat history)

Built on the dev Mac: JWT login, a SQLite `users`/`conversations`/`messages`
schema, `/auth/login`, `/history`, `/history/{id}`, and `/chat` now requires
a bearer token and persists every message. Conversations are private by
default; the PWA's "+ Family" button starts one flagged shared, visible to
every logged-in user. `/upload` now also requires auth (used only to stamp
"uploaded by" on the resulting note — uploaded documents themselves stay
visible to the whole household, per the existing shared-Chroma-collection
design).

### J1. Pull the code

```bash
cd ~/Lucy && git pull
```

Verify: `ls backend/app/` should now show `auth.py`, `db.py`,
`conversations.py`, `persona.py` alongside the existing files.

### J2. Install the new dependencies and set a JWT secret

```bash
cd ~/Lucy/backend
source venv/bin/activate
pip install -r requirements.txt
```

Generate a secret and add it to `.env`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

```
JWT_SECRET=<paste the generated value>
```

The backend refuses to start without `JWT_SECRET` set — this is
intentional (an empty signing key would make every token forgeable).

### J3. Create the two household logins

```bash
python scripts/create_user.py
# repeat for the second user
```

> **HUMAN ACTION REQUIRED:** Tyler and his wife each need to be present
> (or told their password out of band) to set their own password — don't
> pick one on their behalf.

### J4. Restart the backend

```bash
sudo systemctl restart lucy-backend
```

### J5. Test the login + chat round trip

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "<username from J3>", "password": "<their password>"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Say hello in one short sentence."}'

curl -s http://localhost:8000/history -H "Authorization: Bearer $TOKEN"
```

Should return a real reply (occasionally with an italicized dog-flavor
line before/after it — that's `app/persona.py`, working as intended) and
then a one-item history list. Also confirm `curl -s -X POST
http://localhost:8000/chat -d '{"message": "hi"}'` **without** the
`Authorization` header now returns `401`.

### J6. Rebuild and restart the frontend

The PWA now has a login screen and a history panel — needs a rebuild:

```bash
cd ~/Lucy/frontend
npm install
npm run build
sudo systemctl restart lucy-frontend
```

### J7. Report back

Tell the user:
- Whether login, `/chat` with a token, and `/history` all worked
- Whether the unauthenticated `/chat` request correctly got a 401
- Whether the PWA's login screen and history panel render correctly from
  a browser on the tailnet
- Any deviation from this doc

---

## Part K — Steps for Claude Code to execute (Cloudflare Tunnel — public exposure)

**This is an architecture change from the original "Tailscale only, no
public exposure" plan** (see `Lucy(AI) About.md`'s non-goals) — the
household decided a real domain + login is worth it for reachability
without requiring Tailscale on every device. The JWT auth in Part J is
the access-control layer this depends on; do Part J first.

### K1. Cloudflare account + domain (human-only)

> **HUMAN ACTION REQUIRED:** add `tylersuits.com` to a Cloudflare account
> (free plan is fine) and point the domain's nameservers at Cloudflare.
> This can take a few hours to propagate — start it first, do the rest of
> this Part while waiting.

### K2. Install cloudflared

```bash
sudo pacman -S cloudflared
```

### K3. Authenticate and create the tunnel

> **HUMAN ACTION REQUIRED:** `cloudflared tunnel login` opens a browser —
> needs Tyler physically at the machine (or a forwarded browser session).

```bash
cloudflared tunnel login
cloudflared tunnel create lucy-tunnel
```

Note the tunnel ID printed — needed for K4.

### K4. Configure the tunnel

Copy `deploy/cloudflared-config.yml.example` to `~/.cloudflared/config.yml`,
filling in `<TUNNEL_ID>` and `<LINUX_USER>` from K3. This routes
`/auth`, `/chat`, `/upload`, `/history`, `/health` to the FastAPI backend
(`:8000`) and everything else (the PWA itself) to the Next.js frontend
(`:3000`), all under the one `lucy.tylersuits.com` hostname — no CORS
complexity, no second hostname to manage.

### K5. Route DNS and start the tunnel as a service

```bash
cloudflared tunnel route dns lucy-tunnel lucy.tylersuits.com
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```

Verify: `systemctl status cloudflared` shows `active (running)`.

### K6. Point the frontend at the public origin

Since the tunnel now serves both frontend and backend from
`lucy.tylersuits.com`, update `frontend/.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=https://lucy.tylersuits.com
```

```bash
cd ~/Lucy/frontend
npm run build
sudo systemctl restart lucy-frontend
```

### K7. Verify from outside the tailnet

From a phone on cellular data (not Wi-Fi, not Tailscale — this is the
actual test of public reachability): visit `https://lucy.tylersuits.com`,
log in, send a message, confirm a reply comes back. Then Add to Home
Screen and confirm it opens full-screen with no browser chrome.

### K8. (Recommended) Cloudflare Access — a second login wall

> **HUMAN ACTION REQUIRED:** in the Cloudflare Zero Trust dashboard,
> create an Access application for `lucy.tylersuits.com`, restrict it to
> Tyler + his wife's specific email addresses (one-time-code or Google
> login). This sits in front of the tunnel — a request has to clear
> Cloudflare Access *before* it ever reaches FastAPI, so it's a real
> second layer on top of the app's own JWT login, not a redundant one.

### K9. Re-check the security checklist

Confirm, and fix anything not yet true:
- `GEMINI_API_KEY` and `JWT_SECRET` are in `.env`, and `.env` is
  git-ignored (it already is — verify nothing slipped into a commit:
  `git log --all --full-history -- backend/.env`)
- Cloudflare Access is configured (K8) — if skipped, say so explicitly
- `cloudflared` and `lucy-backend`/`lucy-frontend` are all
  `systemctl enable`d (survive reboot), not just started
- No rate limiting exists yet on `/auth/login` or `/chat` — flag this as
  outstanding rather than silently skipping it; household-scale traffic
  makes it low-urgency but it's a real gap once the app is on the public
  internet

### K10. Report back

Tell the user:
- Whether `lucy.tylersuits.com` is reachable and resolves via Cloudflare
- Whether the phone test in K7 worked over cellular data specifically
  (not just Tailscale/Wi-Fi — that wouldn't prove public reachability)
- Whether Cloudflare Access is set up, or still needs Tyler to do the
  Zero Trust dashboard step himself
- The rate-limiting gap from K9, as an open item
- Any deviation from this doc
