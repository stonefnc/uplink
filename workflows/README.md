# Workflows

Exported n8n workflow JSON lives in this folder.

## uplink-triage.json

Webhook intake, classification, draft response, routing and logging. It takes a ticket, asks the LLM for a category, a priority and a short draft reply, sends the ticket down the branch for its category, logs it, and returns the result. The contract is in `docs/architecture.md`.

Flow: Webhook, Normalize ticket, Valid ticket?, Build request, Classify (LLM), Parse classification, Route by category, one "Route" node per category, Log ticket, Respond. An invalid ticket gets a 400 from the other branch.

After changing `docker-compose.yml` or `.env`, run `docker compose up -d` again so the container picks the change up.

### Import

The `workflows/` folder is mounted read-only at `/workflows` in the container. With the container running:

```
docker compose exec -u node n8n n8n import:workflow --input=/workflows/uplink-triage.json
```

Imported workflows are inactive. Publish it:

```
docker compose exec -u node n8n n8n publish:workflow --id=UplinkTriage0001
```

A running n8n picks the change up within about ten seconds; no restart is needed. You can also publish from the editor. The workflow has a fixed id, so importing again updates it in place instead of creating a second copy.

### Test and production URLs

- Production: `http://localhost:5678/webhook/ticket`. Works only while the workflow is published.
- Test: `http://localhost:5678/webhook-test/ticket`. Works once, after you click "Execute workflow" in the editor, and shows the data on the canvas.

### Example

```
curl -X POST http://localhost:5678/webhook/ticket \
  -H "Content-Type: application/json" \
  -d '{"subject": "Projector flickering in room 114", "body": "It cuts out every ten minutes. I am using the whiteboard for now.", "requester_role": "teacher"}'
```

Only `subject` or `body` is required. `id`, `received_at`, `channel` and `requester_role` are optional.

### Offline tests

```
node --test workflows/test
```

These load the workflow JSON, check its structure and run each Code node in a sandbox. They do not start n8n.

### Trying it without a real endpoint

```
python tools/mock_llm.py
```

Set `LLM_BASE_URL=http://host.docker.internal:8000/v1` and any `LLM_API_KEY` and `LLM_MODEL` in `.env`. The mock is a keyword-rule stub for testing, not a model. Then run `python tools/evaluate.py` to send the generated tickets and compare results.

## uplink-email-intake.json

Email intake. It watches an IMAP mailbox and posts each unread email to the triage webhook as a ticket, so `uplink-triage.json` must be imported and published too. Details are in `docs/architecture.md`.

### Mailbox credential

The workflow refers to an n8n credential named "Uplink mailbox". Create it from the template:

1. Copy `workflows/credentials/imap.example.json` to `workflows/credentials/imap.json` (gitignored) and fill in the host, port, user and password.
2. Import it, then delete the file:

```
docker compose exec -u node n8n n8n import:credentials --input=/workflows/credentials/imap.json
```

n8n stores the credential encrypted with `N8N_ENCRYPTION_KEY`. You can also create or edit it in the editor under Credentials.

### Import and publish

```
docker compose exec -u node n8n n8n import:workflow --input=/workflows/uplink-email-intake.json
docker compose exec -u node n8n n8n publish:workflow --id=UplinkEmail00001
```

### Trying it with the local test mailbox

`docker-compose.test.yml` adds a throwaway mail server with one mailbox. It is for testing only.

```
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
docker compose exec -u node n8n n8n import:credentials --input=/workflows/credentials/imap.test.json
python tools/send_test_email.py --count 3
```

Import and publish both workflows first. The emails show up in the ticket log within a minute, with ids starting `E-`. Importing `imap.test.json` replaces a real "Uplink mailbox" credential, so import the real one again afterwards.

### Gmail

Gmail works with the IMAP workflow above. In the Google account, turn on 2-Step Verification and create an app password; the normal account password is refused. In `imap.json` use host `imap.gmail.com`, port `993`, `"secure": true`, the full address as `user` and the app password as `password`.

## uplink-outlook-intake.json

Email intake for an Outlook or Microsoft 365 mailbox. Microsoft no longer accepts a username and password over IMAP, so this workflow uses the Outlook trigger with a Microsoft sign-in instead. Apart from the trigger it is the same as the IMAP workflow: it polls every minute for unread mail and posts each message to the triage webhook. It does not mark messages read.

This workflow has passed offline tests and imports into n8n, but it has not been run against a real mailbox.

### Setup

1. In the Microsoft Entra admin center, register an application. Choose the account types that match the mailbox (personal, work, or both). Add a Web redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`. Create a client secret.
2. In the n8n editor, create a credential of type "Microsoft Outlook OAuth2 API" named "Uplink Outlook". Paste the application (client) ID and the client secret, then choose Connect and sign in with the mailbox account.
3. Import the workflow:

```
docker compose exec -u node n8n n8n import:workflow --input=/workflows/uplink-outlook-intake.json
```

4. Open "Uplink Outlook intake" in the editor. In the "Outlook trigger" node, select the "Uplink Outlook" credential. Under Filters, add "Folders to Include" and pick Inbox; without it, mail in every folder is read.
5. Publish it from the editor, or with `n8n publish:workflow --id=UplinkOutlook001`.

A work or school account may need an administrator to approve the application before sign-in succeeds.
