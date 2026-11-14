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
