# Architecture

## Flow

1. Intake: a ticket arrives by webhook, or by email through an IMAP mailbox.
2. Classify: an LLM assigns a category and a priority, with a one-line reason.
3. Draft: the LLM writes a short first response for the technician to review.
4. Route: the ticket goes to a branch based on its category.
5. Log: one record per ticket is written to SQLite or a CSV file.

The LLM is called through a chat completions endpoint. Base URL, key and model come from environment variables (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).

## Webhook contract (step 3)

`POST /webhook/ticket` with a JSON body. The workflow is `workflows/uplink-triage.json`.

Request fields:

| Field | Required | Notes |
| --- | --- | --- |
| subject | one of subject or body | Trimmed, one line, capped at 300 characters |
| body | one of subject or body | Trimmed, capped at 8000 characters |
| id | no | Generated from the timestamp if absent (`W-` plus digits) |
| received_at | no | Current time if absent or not a valid date |
| channel | no | Default `webhook` |
| requester_role | no | Default empty |

Any other field is dropped, including `expected_*`. They never reach the LLM.

Response 200, JSON:

```
{
  "ticket_id": "...", "received_at": "...", "channel": "...",
  "requester_role": "...", "subject": "...",
  "category": "...", "priority": "P1-P4", "reason": "one line, 200 characters max",
  "classified": true,
  "draft_response": "2 to 4 sentences, 1200 characters max",
  "model": "<value of LLM_MODEL>",
  "route": "...", "logged": true
}
```

`log_error` is added, with a short cause, only when `logged` is false.

Response 400, JSON: `{"error": "subject or body is required"}` when both are empty or missing.

### Failure behaviour

A failed classification does not fail the request. If the LLM call fails, times out, returns no choices, or returns something that is not usable JSON with a recognised category and priority, the response is still 200 with category `other`, priority `P3`, `classified: false` and a reason of the form `classification failed: <short cause>`. The HTTP call has a 30 second timeout and one retry. The same fallback is used if `LLM_BASE_URL`, `LLM_API_KEY` or `LLM_MODEL` is missing.

The reply parser strips code fences, takes the first JSON object, and maps near-forms to the exact values (for example "account access", "mdm", "p2", "2", "P2 - high").

When classification fails the draft is empty, and the ticket is still routed (to `general`) and logged.

### Draft response

Category, priority, reason and draft come from one LLM call. The draft is a short reply for the technician to review and send; the workflow does not send it to anyone.

### Routing

A Switch node sends the ticket down one branch per category. Each branch sets `route`:

| Category | Route |
| --- | --- |
| account/access | identity |
| hardware | hardware |
| software | software |
| network | network |
| MDM/device | device-management |
| other | general |

The branches only label the ticket for now. A notification or hand-off for a team goes on its branch, between the route node and "Log ticket".

### Logging

"Log ticket" appends one record per ticket. `LOG_BACKEND` is `sqlite` (a `tickets` table) or `csv` (a header row, then one row per ticket). `LOG_PATH` is the file inside the container; `./data` on the host is mounted at `/data`. Set both when switching, for example `LOG_BACKEND=csv` and `LOG_PATH=/data/uplink-log.csv`.

A logging problem does not fail the request: the response has `logged: false` and `log_error`. In CSV, a cell that starts with `=`, `+`, `-` or `@` gets a leading apostrophe so a spreadsheet does not run it as a formula.

The Code node writes the file itself, which needs two Node built-in modules. `docker-compose.yml` allows them with `NODE_FUNCTION_ALLOW_BUILTIN=fs,node:sqlite`. Trade-off: any Code node on this instance can then read and write files the container user can reach. As with environment access, that is acceptable for a single-user instance.

### Email intake

A second workflow, "Uplink email intake", watches an IMAP mailbox. For each unread email it builds a ticket (subject, plain-text body or text taken from the HTML, the email's date, `channel: email`, and an id starting with `E-` derived from the Message-ID) and posts it to the triage webhook. From there the email is handled exactly like a webhook ticket, so there is one place for classification, routing and logging.

- The sender's address is not passed on, logged or sent to the LLM.
- The email is marked read after it is picked up. Nothing is sent back to the sender; the draft only goes to the log.
- The mailbox login is an n8n credential named "Uplink mailbox". It is not in the workflow file. See `workflows/README.md`.
- The workflow posts to `http://localhost:5678/webhook/ticket` inside the container. Set `UPLINK_INTAKE_URL` to change that.
- If the triage webhook is not reachable, the email is still marked read and is not retried.

### Environment access

n8n 2.x blocks `$env` in expressions and Code nodes by default (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`). The workflow reads `LLM_BASE_URL`, `LLM_API_KEY` and `LLM_MODEL` that way, so `docker-compose.yml` sets `N8N_BLOCK_ENV_ACCESS_IN_NODE` to `false`.

Trade-off: any workflow on this instance can then read every environment variable in the container, including the API key and the encryption key. That is acceptable for a single-user, self-hosted instance where only the owner builds workflows. The alternative is an n8n credential for the key, which keeps it out of expressions but has to be created in the editor and cannot be shipped in the workflow JSON.

## Categories

- account/access: logins, passwords, permissions, shared accounts
- hardware: laptops, printers, projectors, peripherals
- software: apps, installs, licenses, errors
- network: Wi-Fi, wired, internet, VPN
- MDM/device: enrollment, policies, managed device issues
- other: anything that does not fit above

## Priorities

- P1: outage or safety issue affecting many people, or a blocked critical function. Act now.
- P2: one person or small group fully blocked, no workaround. Same day.
- P3: degraded or inconvenient, workaround exists. Within a few days.
- P4: request, question or minor issue. Schedule when convenient.

## Log record

| Field | Notes |
| --- | --- |
| ticket_id | From intake |
| received_at | From intake |
| channel | webhook or email |
| requester_role | From intake |
| subject | From intake |
| category | Classifier output |
| priority | Classifier output |
| reason | One-line reason for the priority |
| draft_response | First response draft |
| route | Branch the ticket was sent to |
| classified | 1, or 0 when the fallback was used |
| model | Value of `LLM_MODEL` |
| processed_at | When the workflow finished |

## Build steps

1. Scaffold: folders, Docker setup, docs.
2. Generator: 30 fake tickets to JSON and CSV.
3. Webhook intake and classify.
4. Draft response, route by category, log.
5. IMAP intake.
