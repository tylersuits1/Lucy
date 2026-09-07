# Google Drive Setup for Lucy (Phase 5)

The Drive sync code is built and already handles missing credentials
gracefully — but actually syncing anything needs a Google Cloud OAuth
client and two Drive folders, which only you can create. Once you've done
the steps below, tell Claude Code and it can finish the rest (running the
one-time authorization script needs your browser, but Claude Code can kick
it off for you if you're doing this on the dev Mac).

## 1. Create a Google Cloud project

Go to **[console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate)**,
name it something like "Lucy", and create it. (Any Google account works —
this doesn't need to be a paid/Workspace account.)

## 2. Enable the Google Drive API

With that project selected, go to
**[console.cloud.google.com/apis/library/drive.googleapis.com](https://console.cloud.google.com/apis/library/drive.googleapis.com)**
and click **Enable**.

## 3. Configure the OAuth consent screen

Go to **[console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)**.

- User type: **External** (unless you have a Google Workspace account).
- Fill in the required fields: app name ("Lucy"), your email as the user
  support email and developer contact.
- You can leave scopes at the default — Lucy requests the Drive scope
  directly when it authorizes.
- Under **Test users**, add your own Google account. The app stays in
  "Testing" mode (Google won't require app verification for personal use
  like this), but only accounts listed as test users can complete the
  consent flow while it's in that mode.

## 4. Create an OAuth client ID

Go to **[console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)**.

- **Create Credentials → OAuth client ID**
- Application type: **Desktop app** (not "Web application" — there's no
  redirect URL to configure this way, and it matches how
  `scripts/drive_authorize.py` runs the flow with a local browser).
- Name it "Lucy" and create it.
- Click **Download JSON** on the credential you just created.

## 5. Save the credential file

Move the downloaded JSON into the repo (this path is already gitignored,
so it won't accidentally get committed):

```bash
mkdir -p backend/secrets
mv ~/Downloads/client_secret_*.json backend/secrets/client_secret.json
```

## 6. Create the Drive folders

In [Google Drive](https://drive.google.com), create two folders:
- **Lucy Inbox** — drop files here for Lucy to ingest.
- **Lucy Exports** — reserved for a future "push" feature (not built yet).

## 7. Get each folder's ID

Open a folder in Drive; the ID is the last part of the URL:

```
https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        this is the folder ID
```

Add both to `backend/.env`:

```
DRIVE_INBOX_FOLDER_ID=<Lucy Inbox folder ID>
DRIVE_EXPORTS_FOLDER_ID=<Lucy Exports folder ID>
```

## 8. Run the one-time authorization

Once `backend/secrets/client_secret.json` exists and the folder IDs are in
`.env`, tell Claude Code — it'll run:

```bash
cd backend && source venv/bin/activate && python scripts/drive_authorize.py
```

This opens your browser for you to sign in and approve access (only
possible because this runs on your own machine with a real browser — it
can't run unattended on the headless server). Approving it saves
`backend/secrets/token.json`, which the backend then uses and refreshes
automatically from then on.

If you do this on the dev Mac, that token file needs copying to
`lucy-omarchy` afterward (it's gitignored, so `git pull` won't carry it) —
covered in `OMARCHY_SETUP.md`'s Phase 5 section.
