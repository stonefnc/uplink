# Uplink

Uplink is an IT help desk ticket triage workflow built on n8n and run with Docker. A ticket comes in, an LLM sets its category and priority and drafts a short first response for the technician, then the ticket is routed by category and logged.

## Prerequisites

- Docker with Docker Compose
- A chat completions endpoint and an API key for it

## Quick start

1. Copy `.env.example` to `.env` and fill in the values.
2. Run `docker compose up -d`.
3. Open http://localhost:5678.

## Folder layout

```
Uplink/
  docker-compose.yml   n8n service
  docker-compose.test.yml  local test mailbox, for trying email intake
  .env.example         settings template
  workflows/           exported n8n workflows, credential templates and offline tests
  tools/               test LLM stub, evaluation script and test email sender
  generator/           fake ticket generator and tests
  data/                ticket log (SQLite or CSV), not committed
  docs/architecture.md flow, categories, priorities, build steps
```

## Status

All five build steps are done: scaffold, ticket generator, a webhook workflow that classifies a ticket, drafts a first response, routes it by category and logs it to SQLite or CSV, and an email workflow that feeds an IMAP mailbox into it. Both workflows have been run in n8n 2.47.7; email intake has been run against the local test mailbox only. See `docs/architecture.md`.
