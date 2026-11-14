import csv
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generate  # noqa: E402
from scenarios import CATEGORIES, PRIORITIES, SCENARIOS  # noqa: E402

ALLOWED_EMAIL = re.compile(r"[A-Za-z0-9._+-]+@example\.(?:org|com)\b")


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_output(self):
        self.assertEqual(generate.generate(42, 30), generate.generate(42, 30))

    def test_same_seed_same_files(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            generate.write_files(generate.generate(7, 30), a)
            generate.write_files(generate.generate(7, 30), b)
            for name in ("tickets.json", "tickets.csv"):
                self.assertEqual((Path(a) / name).read_bytes(), (Path(b) / name).read_bytes())

    def test_different_seed_different_output(self):
        self.assertNotEqual(generate.generate(1, 30), generate.generate(2, 30))


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self.tickets = generate.generate(42, 30)

    def test_count(self):
        self.assertEqual(len(self.tickets), 30)
        self.assertEqual(len(generate.generate(42, 12)), 12)

    def test_field_order(self):
        for t in self.tickets:
            self.assertEqual(tuple(t.keys()), generate.FIELDS)

    def test_ids_follow_received_order(self):
        self.assertEqual([t["id"] for t in self.tickets],
                         [f"T-{n:04d}" for n in range(1, 31)])
        times = [datetime.fromisoformat(t["received_at"]) for t in self.tickets]
        self.assertEqual(times, sorted(times))

    def test_timestamps_have_offset_and_stay_in_window(self):
        start = datetime.combine(generate.ANCHOR_DATE, datetime.min.time(),
                                 tzinfo=generate.UTC_OFFSET)
        for t in self.tickets:
            dt = datetime.fromisoformat(t["received_at"])
            self.assertIsNotNone(dt.utcoffset())
            self.assertGreaterEqual(dt, start)
            self.assertLess((dt - start).days, generate.WINDOW_DAYS)

    def test_channels_and_values(self):
        for t in self.tickets:
            self.assertIn(t["channel"], generate.CHANNELS)
            self.assertIn(t["expected_category"], CATEGORIES)
            self.assertIn(t["expected_priority"], PRIORITIES)
            self.assertTrue(t["subject"].strip())
            self.assertTrue(t["body"].strip())

    def test_category_values_exact(self):
        self.assertEqual(CATEGORIES, ("account/access", "hardware", "software",
                                      "network", "MDM/device", "other"))
        self.assertEqual(PRIORITIES, ("P1", "P2", "P3", "P4"))

    def test_too_large_or_small_count_rejected(self):
        with self.assertRaises(ValueError):
            generate.generate(42, 0)
        with self.assertRaises(ValueError):
            generate.generate(42, generate.max_count() + 1)


class SpreadTests(unittest.TestCase):
    def test_minimum_spread_across_seeds(self):
        for seed in range(500):
            tickets = generate.generate(seed, 30)
            for c in CATEGORIES:
                n = sum(1 for t in tickets if t["expected_category"] == c)
                self.assertGreaterEqual(n, 3, f"seed {seed} category {c}")
            for p in PRIORITIES:
                n = sum(1 for t in tickets if t["expected_priority"] == p)
                self.assertGreaterEqual(n, 3, f"seed {seed} priority {p}")

    def test_unique_subjects_and_bodies(self):
        for seed in (0, 42, 99):
            tickets = generate.generate(seed, 30)
            self.assertEqual(len({t["subject"] for t in tickets}), 30)
            self.assertEqual(len({t["body"] for t in tickets}), 30)

    def test_max_count_is_unique(self):
        tickets = generate.generate(5, generate.max_count())
        self.assertEqual(len({t["subject"] for t in tickets}), len(tickets))
        self.assertEqual(len({t["body"] for t in tickets}), len(tickets))


class PoolTests(unittest.TestCase):
    def test_at_least_eight_scenarios_per_category(self):
        for c in CATEGORIES:
            self.assertGreaterEqual(sum(1 for s in SCENARIOS if s.category == c), 8, c)

    def test_every_category_has_several_priorities(self):
        for c in CATEGORIES:
            found = {s.priority for s in SCENARIOS if s.category == c}
            self.assertGreaterEqual(len(found), 3, c)

    def test_scenario_text_is_unique(self):
        subjects = [subject for s in SCENARIOS for subject, _ in s.variants]
        bodies = [body for s in SCENARIOS for _, body in s.variants]
        self.assertEqual(len(subjects), len(set(subjects)))
        self.assertEqual(len(bodies), len(set(bodies)))

    def test_variants_are_subject_body_pairs(self):
        for s in SCENARIOS:
            self.assertGreaterEqual(len(s.variants), 2)
            for variant in s.variants:
                self.assertIsInstance(variant, tuple)
                self.assertEqual(len(variant), 2)
                subject, body = variant
                self.assertIsInstance(subject, str)
                self.assertIsInstance(body, str)
                self.assertTrue(subject.strip())
                self.assertTrue(body.strip())
            self.assertIn(s.category, CATEGORIES)
            self.assertIn(s.priority, PRIORITIES)

    def test_every_scenario_has_explicit_roles(self):
        for s in SCENARIOS:
            self.assertIsInstance(s.roles, tuple)
            self.assertGreater(len(s.roles), 0, s.variants[0][0])
            self.assertEqual(len(s.roles), len(set(s.roles)), s.variants[0][0])
            for role in s.roles:
                self.assertTrue(role.strip())

    def test_ticket_text_and_role_come_from_one_scenario(self):
        for seed in (0, 42, 99):
            for t in generate.generate(seed, 30):
                matches = [
                    s for s in SCENARIOS
                    if s.category == t["expected_category"]
                    and s.priority == t["expected_priority"]
                    and t["requester_role"] in s.roles
                    and any(self._same(subject, t["subject"]) and body_start in t["body"]
                            for subject, body_start in
                            ((v[0], self._body_head(v[1])) for v in s.variants))
                ]
                self.assertTrue(matches, f"seed {seed} {t['id']} has no matching scenario")

    @staticmethod
    def _body_head(body):
        return body.split("{", 1)[0][:40]

    @staticmethod
    def _same(template, subject):
        pattern = re.escape(template.replace("URGENT: ", ""))
        pattern = re.sub(r"\\\{\w+\\\}", r"\\w+", pattern)
        return re.fullmatch(pattern, subject.replace("URGENT: ", "")) is not None

    def test_no_unfilled_placeholders(self):
        for seed in range(10):
            for t in generate.generate(seed, 30):
                self.assertNotRegex(t["subject"] + t["body"], r"[{}]")


class ContentRuleTests(unittest.TestCase):
    def test_at_signs_only_in_example_addresses(self):
        for seed in range(10):
            for t in generate.generate(seed, 30):
                for field in ("subject", "body", "requester_role"):
                    leftover = ALLOWED_EMAIL.sub("", t[field])
                    self.assertNotIn("@", leftover, t[field])

    def test_pool_at_signs_only_in_example_addresses(self):
        for s in SCENARIOS:
            for text in (part for variant in s.variants for part in variant):
                self.assertNotIn("@", ALLOWED_EMAIL.sub("", text), text)

    def test_urls_use_example_domains_only(self):
        url = re.compile(r"https?://\S+|www\.\S+")
        for s in SCENARIOS:
            for text in (part for variant in s.variants for part in variant):
                for match in url.findall(text):
                    self.assertRegex(match, r"example\.(org|com)")


class OutputFileTests(unittest.TestCase):
    def test_json_and_csv_match(self):
        tickets = generate.generate(42, 30)
        with tempfile.TemporaryDirectory() as out:
            json_path, csv_path = generate.write_files(tickets, out)
            with open(json_path, encoding="utf-8") as f:
                from_json = json.load(f)
            with open(csv_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(tuple(reader.fieldnames), generate.FIELDS)
                from_csv = list(reader)
        self.assertEqual(from_json, tickets)
        self.assertEqual(from_csv, tickets)

    def test_no_blank_lines_between_csv_rows(self):
        with tempfile.TemporaryDirectory() as out:
            _, csv_path = generate.write_files(generate.generate(42, 30), out)
            raw = csv_path.read_bytes()
        self.assertNotIn(b"\r\n", raw)
        self.assertNotIn(b"\n\n\n", raw)

    def test_script_runs_from_other_directory(self):
        with tempfile.TemporaryDirectory() as work, tempfile.TemporaryDirectory() as out:
            result = subprocess.run(
                [sys.executable, "-I", str(HERE / "generate.py"), "--seed", "3",
                 "--count", "10", "--out", out],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(Path(out) / "tickets.json", encoding="utf-8") as f:
                self.assertEqual(len(json.load(f)), 10)

    def test_default_output_path_is_beside_script(self):
        self.assertEqual(generate.DEFAULT_OUT, HERE / "output")


if __name__ == "__main__":
    unittest.main()
