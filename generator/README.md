# Ticket generator

Produces fake K-12 and office IT help desk tickets for testing the classifier. Python 3.13, standard library only.

## Run

From the repo root or from inside `generator/`:

```
python generator/generate.py [--seed N] [--count N] [--out DIR]
```

| Option | Default | Notes |
| --- | --- | --- |
| `--seed` | 42 | Same seed and count always give byte-identical files |
| `--count` | 30 | 1 up to the size of the scenario pool (the script says the limit) |
| `--out` | `generator/output` | Resolved relative to the script, gitignored |

It writes `tickets.json` (array, UTF-8) and `tickets.csv` (header row, same field order) and prints the category and priority counts.

## Fields

| Field | Notes |
| --- | --- |
| id | `T-0001` upward, in received_at order |
| received_at | ISO 8601 with UTC offset, inside a fixed two-week window, mostly school-day hours |
| channel | `webhook` or `email` |
| requester_role | A role such as teacher or front office staff. No names. |
| subject | Short subject line |
| body | A few sentences, in the voice of a busy user |
| expected_category | account/access, hardware, software, network, MDM/device, other |
| expected_priority | P1 to P4, as defined in `docs/architecture.md` |

The two `expected_*` fields are only for checking the classifier. Do not send them to it.

## How it works

`scenarios.py` holds a hand-written pool of scenarios for each category. Each scenario has its own priority, which follows from the situation described, plus several subject and body variants. `generate.py` spreads the ticket count across the categories, picks scenarios and variants with a seeded random generator, fills in details such as room numbers, and assigns times. Within one run no subject or body repeats.

## Rules

- All data is invented. No person names, schools, districts, companies or brands. Addresses and URLs use example.org or example.com only.
- No clock-based values. The time window is anchored to a fixed date in the script.

## Tests

```
python -m unittest discover -s generator
```
