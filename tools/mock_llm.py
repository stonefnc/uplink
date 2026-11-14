"""TEST STUB. Not a real model.

A tiny local server that answers POST /v1/chat/completions with a classification
picked by keyword rules, in the standard chat completions response shape. Use it
to check the Uplink workflow end to end without a real endpoint.

    python tools/mock_llm.py [--host 0.0.0.0] [--port 8000]

Point LLM_BASE_URL at it (from a container: http://host.docker.internal:8000/v1).
Any API key is accepted.
"""

import argparse
import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Checked in order; the first rule with a matching keyword wins.
CATEGORY_RULES = (
    ("MDM/device", ("enroll", "managed", "policy", "compliant", "work profile", "locked by administrator",
                    "management system", "kiosk", "lock it")),
    ("network", ("wi-fi", "wifi", "wireless", "internet", "vpn", "network", "filter", "blocked",
                 "shared drive", "wired")),
    ("account/access", ("log in", "login", "sign in", "sign-in", "password", "locked out", "account",
                        "verification", "access", "mfa", "signed out")),
    ("hardware", ("printer", "projector", "laptop", "monitor", "keyboard", "screen", "camera", "headset",
                  "cart", "badge printer", "noise", "mouse")),
    ("software", ("app", "software", "license", "install", "export", "gradebook", "browser", "crash",
                  "attendance system", "report")),
)

PRIORITY_RULES = (
    ("P1", ("everyone", "nobody", "whole", "entire", "building", "all of", "burning", "hot to the touch",
            "hacked", "taken over", "down at", "testing starts", "assessment", "no wireless")),
    ("P2", ("cannot", "can't", "will not", "won't", "locked out", "dead", "due today", "due by",
            "tonight", "stuck", "no dial tone")),
    ("P4", ("request", "would like", "could i", "can i get", "question", "when is", "training",
            "no rush", "not urgent", "whenever", "please add", "is it possible")),
)

REASONS = {
    "P1": "Affects many people or a critical function.",
    "P2": "Someone is blocked with no workaround.",
    "P3": "Degraded but a workaround exists.",
    "P4": "Request or question, no urgency.",
}


def _ticket_text(messages):
    """Return the ticket portion of the last user message, lowercased."""
    text = ""
    for message in messages:
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content", "")
            text = content if isinstance(content, str) else json.dumps(content)
    match = re.search(r"<ticket>(.*?)</ticket>", text, re.S)
    return (match.group(1) if match else text).lower()


def classify(text):
    category = "other"
    for name, words in CATEGORY_RULES:
        if any(w in text for w in words):
            category = name
            break
    priority = "P3"
    for name, words in PRIORITY_RULES:
        if any(w in text for w in words):
            priority = name
            break
    return {"category": category, "priority": priority, "reason": REASONS[priority]}


class Handler(BaseHTTPRequestHandler):
    server_version = "MockLLM/0.1"

    def _send(self, status, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path != "/v1/chat/completions":
            self._send(404, {"error": {"message": "not found: " + self.path}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length) or b"{}")
            messages = request["messages"]
            if not isinstance(messages, list):
                raise ValueError("messages must be a list")
        except (ValueError, KeyError, TypeError) as exc:
            self._send(400, {"error": {"message": "bad request: " + str(exc)}})
            return

        result = classify(_ticket_text(messages))
        self._send(200, {
            "id": "mock-" + str(int(time.time() * 1000)),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": str(request.get("model", "mock-model")),
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(result)},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        })

    def do_GET(self):
        self._send(200, {"status": "ok", "note": "test stub, not a real model"})

    def log_message(self, fmt, *args):
        sys.stderr.write("[mock_llm] %s - %s\n" % (self.address_string(), fmt % args))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Test stub for a chat completions endpoint.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"mock_llm (test stub) listening on {args.host}:{args.port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
