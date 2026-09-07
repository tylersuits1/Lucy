# Backing Up Lucy's Data to Google Drive

This replaces the earlier plan of giving Lucy a live OAuth connection to
pull files from a shared Drive folder. That approach meant a standing app
with broad Drive access constantly watching an inbox — a bigger privacy
footprint than fits a project whose whole point is staying local and
private.

Instead: Lucy's data stays entirely local (as it always has), and a daily
job on `lucy-omarchy` pushes a one-way backup copy to Google Drive using
**[rclone](https://rclone.org)** — local is always the source of truth,
Drive is just an off-site copy in case the machine dies. Only
`backend/data/notes/` and `backend/data/files/` get backed up;
`backend/data/chroma/` (the vector index) is skipped since it's fully
regenerable by re-running `scripts/ingest_notes.py` after a restore — no
need to back up a rebuildable cache.

Nicer side effect: rclone has its own built-in OAuth client for personal
use, so **no Google Cloud Console project is needed this time** — that
whole dance from the earlier plan goes away. And it's configured with the
`drive.file` access scope, which means the backup can only ever see and
manage files it created itself — it can't browse, read, or touch anything
else in the Drive account.

## 1. Install rclone

```bash
sudo pacman -S --needed --noconfirm rclone
```

## 2. Configure the Google Drive remote

Run the interactive wizard:

```bash
rclone config
```

Walk through it:
- `n` for a new remote
- name it `gdrive`
- storage type: `drive` (Google Drive)
- client_id / client_secret: leave both **blank** (uses rclone's own
  built-in credentials — fine for personal backup use)
- scope: choose **`drive.file`** — "Access to files created by rclone
  only." This is the important privacy-limiting choice; don't pick the
  full `drive` scope.
- root_folder_id / service_account_file: leave blank
- "Edit advanced config?": `n`

Then it asks to auto-authorize via browser:

- **If you're doing this with a physical display attached to
  `lucy-omarchy`** (or over a remote desktop session), say `y` and a
  browser opens on the machine itself to complete the Google sign-in.
- **If this is a true headless SSH session** (no display), say `n`.
  rclone will print something like:
  ```
  Please go to the following link: https://...
  ```
  Instead of opening that link on the server, run this on a different
  machine that *does* have a browser and rclone installed (your dev Mac —
  `brew install rclone` there first if needed):
  ```bash
  rclone authorize "drive" "drive.file"
  ```
  That opens your browser, you approve access, and it prints a JSON
  token blob back in the terminal. Paste that whole blob into the
  waiting prompt on `lucy-omarchy`.

Confirm the remote when it asks, then `q` to quit the config wizard.

## 3. Verify it works

```bash
rclone lsd gdrive:
rclone mkdir gdrive:LucyBackup
rclone ls gdrive:LucyBackup
```

The first command should list your Drive's top-level folders (or be
empty if `drive.file` scope means it can't see anything yet — that's
expected and correct; it'll be able to see `LucyBackup` once rclone
creates it in the next command).

## 4. Install the backup timer

The service/timer unit files are already in `deploy/` in the repo. Install
them the same way as the other systemd units:

```bash
cd ~/Lucy/deploy
sed -e "s|__LUCY_USER__|$USER|g" -e "s|__LUCY_HOME__|$HOME|g" lucy-backup.service | sudo tee /etc/systemd/system/lucy-backup.service > /dev/null
sudo cp lucy-backup.timer /etc/systemd/system/lucy-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now lucy-backup.timer
```

**Important:** `rclone config` in step 2 must be run as the *same user*
this service runs as (whatever `$USER` was during install), since
rclone's config file lives in that user's home directory
(`~/.config/rclone/rclone.conf`). If you ran `rclone config` as a
different user or with `sudo`, the timer's backup runs will fail to find
the `gdrive` remote.

## 5. Test it now, don't wait for the timer

```bash
sudo systemctl start lucy-backup.service
journalctl -u lucy-backup.service -n 30 --no-pager
rclone ls gdrive:LucyBackup
```

You should see your notes and files listed under `LucyBackup/notes` and
`LucyBackup/files` in Drive.

## Restoring from backup (if it's ever needed)

```bash
rclone copy gdrive:LucyBackup/notes ~/Lucy/backend/data/notes
rclone copy gdrive:LucyBackup/files ~/Lucy/backend/data/files
cd ~/Lucy/backend && source venv/bin/activate && python scripts/ingest_notes.py
```

That last step rebuilds the Chroma index from the restored notes, since
the index itself was never backed up.
