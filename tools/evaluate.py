"""Send generated tickets to the Uplink webhook and compare the results.

    python tools/evaluate.py [--url URL] [--input FILE] [--timeout SECONDS]

Reads generator/output/tickets.json, posts each ticket without its expected_*
fields, and compares the returned category and priority with the expected ones.
Exit code is 0 unless requests fail.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://localhost:5678/webhook/ticket"
DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "generator" / "output" / "tickets.json"
SEND_FIELDS = ("id", "received_at", "channel", "requester_role", "subject", "body")


def post_ticket(url, ticket, timeout):
    """POST one ticket. Returns (status, parsed_json_or_None, error_text_or_None)."""
    payload = {k: ticket[k] for k in SEND_FIELDS if k in ticket}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        status = exc.code
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, None, str(getattr(exc, "reason", exc))
    try:
        return status, json.loads(raw), None
    except ValueError:
        return status, None, "response was not JSON"


def priority_level(value):
    try:
        return int(str(value).strip().upper().lstrip("P"))
    except ValueError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate the Uplink triage webhook.")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"webhook URL (default {DEFAULT_URL})")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="tickets.json to read")
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds per request")
    args = parser.parse_args(argv)

    try:
        with open(args.input, encoding="utf-8") as f:
            tickets = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read {args.input}: {exc}", file=sys.stderr)
        return 1
    if not tickets:
        print("no tickets in input", file=sys.stderr)
        return 1

    total = len(tickets)
    cat_ok = pri_exact = pri_near = unclassified = 0
    failed = []

    for ticket in tickets:
        status, result, error = post_ticket(args.url, ticket, args.timeout)
        if error or status != 200 or not isinstance(result, dict):
            failed.append(ticket["id"])
            print(f"{ticket['id']}: REQUEST FAILED (status {status}): {error or result}")
            continue

        got_cat, got_pri = result.get("category"), result.get("priority")
        exp_cat, exp_pri = ticket["expected_category"], ticket["expected_priority"]
        if result.get("classified") is False:
            unclassified += 1

        notes = []
        if got_cat == exp_cat:
            cat_ok += 1
        else:
            notes.append(f"category {got_cat!r} (expected {exp_cat!r})")
        got_level, exp_level = priority_level(got_pri), priority_level(exp_pri)
        if got_pri == exp_pri:
            pri_exact += 1
            pri_near += 1
        else:
            if got_level is not None and exp_level is not None and abs(got_level - exp_level) <= 1:
                pri_near += 1
            notes.append(f"priority {got_pri!r} (expected {exp_pri!r})")
        if result.get("classified") is False:
            notes.append(f"not classified: {result.get('reason')}")
        if notes:
            print(f"{ticket['id']}: {'; '.join(notes)} | {ticket['subject']}")

    done = total - len(failed)
    print()
    print(f"Tickets sent:             {total}")
    print(f"Requests failed:          {len(failed)}")
    if done:
        print(f"Category accuracy:        {cat_ok}/{done} ({100 * cat_ok / done:.0f}%)")
        print(f"Priority exact:           {pri_exact}/{done} ({100 * pri_exact / done:.0f}%)")
        print(f"Priority within one:      {pri_near}/{done} ({100 * pri_near / done:.0f}%)")
        print(f"classified: false:        {unclassified}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
