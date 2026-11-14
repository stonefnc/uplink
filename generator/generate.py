"""Generate fake IT help desk tickets for testing the classifier.

Usage:
    python generator/generate.py [--seed N] [--count N] [--out DIR]

All data is invented. The same seed and count always give identical files.
"""

import argparse
import csv
import json
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scenarios import CATEGORIES, PRIORITIES, SCENARIOS  # noqa: E402

FIELDS = (
    "id",
    "received_at",
    "channel",
    "requester_role",
    "subject",
    "body",
    "expected_category",
    "expected_priority",
)

DEFAULT_SEED = 42
DEFAULT_COUNT = 30
DEFAULT_OUT = Path(__file__).resolve().parent / "output"

# Start of the two-week window (a Monday) and the fixed UTC offset used.
ANCHOR_DATE = date(2026, 3, 2)
WINDOW_DAYS = 14
UTC_OFFSET = timezone(timedelta(hours=-5))

CHANNELS = ("webhook", "email")
CHANNEL_WEIGHTS = (6, 4)

URGENT_PREFIX_CHANCE = {"P1": 0.4, "P2": 0.15, "P3": 0.0, "P4": 0.0}
CLOSERS = ("", "", "", "Thanks.", "Thank you.", "Please advise.", "Thanks in advance.")
PHONE_SIGNATURE = "\n\nSent from my phone."
PHONE_SIGNATURE_CHANCE = 0.15

BUILDINGS = ("A", "B", "C", "D")


def max_count():
    """Largest ticket count that can be produced without repeating text."""
    return sum(s.capacity for s in SCENARIOS)


def _fill(text, values):
    return text.format_map(values)


def _random_time(rng):
    """Return (day_offset, time) with most tickets on school days in school hours."""
    weekdays = [d for d in range(WINDOW_DAYS) if (ANCHOR_DATE + timedelta(days=d)).weekday() < 5]
    roll = rng.random()
    if roll < 0.88:
        day = rng.choice(weekdays)
        minutes = rng.randrange(7 * 60, 16 * 60 + 30)
    elif roll < 0.94:
        day = rng.choice(weekdays)
        minutes = rng.randrange(16 * 60 + 30, 21 * 60)
    else:
        weekend = [d for d in range(WINDOW_DAYS) if d not in weekdays]
        day = rng.choice(weekend)
        minutes = rng.randrange(8 * 60, 20 * 60)
    return day, time(minutes // 60, minutes % 60, rng.randrange(60))


def _plan_categories(rng, count):
    """Spread the ticket count across categories, in a seeded shuffled order."""
    capacity = {c: sum(s.capacity for s in SCENARIOS if s.category == c) for c in CATEGORIES}
    order = rng.sample(CATEGORIES, len(CATEGORIES))
    quotas = {c: 0 for c in CATEGORIES}
    remaining = count
    while remaining:
        for c in order:
            if remaining and quotas[c] < capacity[c]:
                quotas[c] += 1
                remaining -= 1
    slots = [c for c in CATEGORIES for _ in range(quotas[c])]
    rng.shuffle(slots)
    return slots


def generate(seed=DEFAULT_SEED, count=DEFAULT_COUNT):
    """Return a list of ticket dicts (fields in FIELDS order)."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if count > max_count():
        raise ValueError(f"count {count} is above the maximum of {max_count()}")

    rng = random.Random(seed)
    slots = _plan_categories(rng, count)

    uses = {i: 0 for i in range(len(SCENARIOS))}
    used_variants = {i: [] for i in range(len(SCENARIOS))}
    priority_counts = {p: 0 for p in PRIORITIES}
    drafts = []

    for category in slots:
        candidates = [
            i for i, s in enumerate(SCENARIOS)
            if s.category == category and uses[i] < s.capacity
        ]
        if not candidates:
            raise ValueError(f"no scenarios left for category {category}")
        # Prefer scenarios used least, then the priority seen least so far.
        fewest = min(uses[i] for i in candidates)
        candidates = [i for i in candidates if uses[i] == fewest]
        rarest = min(priority_counts[SCENARIOS[i].priority] for i in candidates)
        candidates = [i for i in candidates if priority_counts[SCENARIOS[i].priority] == rarest]
        idx = rng.choice(candidates)
        scenario = SCENARIOS[idx]

        # A subject and body are always taken together, as one written pair.
        variant_options = [k for k in range(scenario.capacity) if k not in used_variants[idx]]
        variant_idx = rng.choice(variant_options)
        used_variants[idx].append(variant_idx)
        uses[idx] += 1
        priority_counts[scenario.priority] += 1

        values = {
            "room": rng.randrange(101, 321),
            "bldg": rng.choice(BUILDINGS),
            "n": rng.randrange(12, 41),
        }
        raw_subject, raw_body = scenario.variants[variant_idx]
        subject = _fill(raw_subject, values)
        body = _fill(raw_body, values)

        if rng.random() < URGENT_PREFIX_CHANCE[scenario.priority]:
            subject = "URGENT: " + subject
        closer = rng.choice(CLOSERS)
        if closer and body.rstrip()[-1] in ".?!":
            body = body + " " + closer

        channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        if channel == "email" and rng.random() < PHONE_SIGNATURE_CHANCE:
            body += PHONE_SIGNATURE

        day, clock = _random_time(rng)
        received = datetime.combine(ANCHOR_DATE + timedelta(days=day), clock, tzinfo=UTC_OFFSET)

        drafts.append({
            "received": received,
            "channel": channel,
            "requester_role": rng.choice(scenario.roles),
            "subject": subject,
            "body": body,
            "expected_category": scenario.category,
            "expected_priority": scenario.priority,
        })

    drafts.sort(key=lambda d: d["received"])
    tickets = []
    for n, d in enumerate(drafts, start=1):
        tickets.append({
            "id": f"T-{n:04d}",
            "received_at": d["received"].isoformat(),
            "channel": d["channel"],
            "requester_role": d["requester_role"],
            "subject": d["subject"],
            "body": d["body"],
            "expected_category": d["expected_category"],
            "expected_priority": d["expected_priority"],
        })
    return tickets


def write_files(tickets, out_dir):
    """Write tickets.json and tickets.csv into out_dir. Returns both paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "tickets.json"
    csv_path = out_dir / "tickets.csv"

    with open(json_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)
        f.write("\n")

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(tickets)

    return json_path, csv_path


def _count_by(tickets, key, order):
    return {v: sum(1 for t in tickets if t[key] == v) for v in order}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate fake help desk tickets.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="random seed (default 42)")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT,
                        help=f"number of tickets, 1 to {max_count()} (default 30)")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="output folder (default generator/output)")
    args = parser.parse_args(argv)

    try:
        tickets = generate(args.seed, args.count)
    except ValueError as exc:
        parser.error(str(exc))

    json_path, csv_path = write_files(tickets, args.out)
    print(f"Wrote {len(tickets)} tickets (seed {args.seed}):")
    print(f"  {json_path}")
    print(f"  {csv_path}")
    print("Categories:", _count_by(tickets, "expected_category", CATEGORIES))
    print("Priorities:", _count_by(tickets, "expected_priority", PRIORITIES))


if __name__ == "__main__":
    main()
