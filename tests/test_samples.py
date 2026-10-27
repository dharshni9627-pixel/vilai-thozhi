import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from services.costing import calculate  # noqa: E402

with open(os.path.join(ROOT, "sample_data", "demo_products.json"), encoding="utf-8") as fh:
    SAMPLES = json.load(fh)


class SampleDataTests(unittest.TestCase):
    def test_tc20_samples_exist(self):
        self.assertGreaterEqual(len(SAMPLES), 5)

    def test_tc21_expected_values_match(self):
        for s in SAMPLES:
            with self.subTest(sample=s["id"]):
                r = calculate(s["input"])
                e = s["expected"]
                self.assertEqual(r["total"], e["total"])
                self.assertEqual(r["per_unit"], e["per_unit"])
                self.assertEqual(r["price"]["low"], e["low"])
                self.assertEqual(r["price"]["suggested"], e["suggested"])
                self.assertEqual(r["price"]["high"], e["high"])

    def test_tc22_samples_are_tamil(self):
        for s in SAMPLES:
            with self.subTest(sample=s["id"]):
                self.assertTrue(any("\u0B80" <= ch <= "\u0BFF" for ch in s["input"]["name"]))


if __name__ == "__main__":
    unittest.main()
