"""Send generated tickets as emails to the local test mailbox.

Usage:
    python tools/send_test_email.py [--count N] [--host HOST] [--port PORT]

Reads generator/output/tickets.json and sends the first N tickets by SMTP to
the test mail server from docker-compose.test.yml. Only subject and body are
sent; the expected_* fields stay on this side. Standard library only.
"""

import argparse
import json
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

TICKETS = Path(__file__).resolve().parent.parent / "generator" / "output" / "tickets.json"
SENDER = "requester@example.org"
RECIPIENT = "helpdesk@example.org"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Send test tickets by email.")
    parser.add_argument("--count", type=int, default=3, help="number of tickets to send (default 3)")
    parser.add_argument("--host", default="localhost", help="SMTP host (default localhost)")
    parser.add_argument("--port", type=int, default=3025, help="SMTP port (default 3025)")
    parser.add_argument("--tickets", default=str(TICKETS), help="path to tickets.json")
    args = parser.parse_args(argv)

    try:
        with open(args.tickets, encoding="utf-8") as f:
            tickets = json.load(f)
    except FileNotFoundError:
        sys.exit(f"{args.tickets} not found. Run: python generator/generate.py")

    chosen = tickets[: max(0, args.count)]
    with smtplib.SMTP(args.host, args.port, timeout=15) as smtp:
        for ticket in chosen:
            message = EmailMessage()
            message["From"] = SENDER
            message["To"] = RECIPIENT
            message["Subject"] = ticket["subject"]
            message["Date"] = formatdate(localtime=False)
            message["Message-ID"] = make_msgid(domain="example.org")
            message.set_content(ticket["body"])
            smtp.send_message(message)
            print(f"sent {ticket['id']}: {ticket['subject']}")
    print(f"Sent {len(chosen)} email(s) to {RECIPIENT} via {args.host}:{args.port}")


if __name__ == "__main__":
    main()
