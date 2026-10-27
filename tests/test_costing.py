import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.costing import calculate, explain, round_price  # noqa: E402

DEMO = {
    "units": 10, "margin": 30, "packaging": 40, "labour": 150, "other": 30,
    "ingredients": [{"name": "mango", "cost": 120}, {"name": "oil", "cost": 60},
                    {"name": "masala", "cost": 45}, {"name": "salt", "cost": 10}],
}


class CostingTests(unittest.TestCase):
    def test_tc01_demo_totals_and_prices(self):
        r = calculate(DEMO)
        self.assertEqual(r["total"], 455)
        self.assertEqual(r["per_unit"], 45.5)
        self.assertEqual(r["price"], {"low": 55, "suggested": 60, "high": 70})

    def test_tc02_price_order_and_above_cost(self):
        r = calculate(DEMO)
        self.assertLessEqual(r["price"]["low"], r["price"]["suggested"])
        self.assertLessEqual(r["price"]["suggested"], r["price"]["high"])
        self.assertGreater(r["price"]["suggested"], r["per_unit"])

    def test_tc03_breakdown_percentages_sum_to_100(self):
        r = calculate(DEMO)
        self.assertAlmostEqual(sum(b["percent"] for b in r["breakdown"]), 100, delta=0.3)
        self.assertEqual({b["key"] for b in r["breakdown"]}, {"ingredients", "packaging", "labour", "other"})

    def test_tc04_rounding_rules(self):
        self.assertEqual(round_price(7.2), 8)      # under 20: next whole rupee
        self.assertEqual(round_price(19.01), 20)
        self.assertEqual(round_price(20), 20)      # 20 and above: next multiple of 5
        self.assertEqual(round_price(20.01), 25)
        self.assertEqual(round_price(145.25), 150)

    def test_tc05_default_margin_is_30(self):
        data = {k: v for k, v in DEMO.items() if k != "margin"}
        self.assertEqual(calculate(data)["margin"], 30)

    def test_tc06_minimum_margin_floor(self):
        r = calculate({**DEMO, "margin": 10})  # low margin would be -5, floored to 5
        self.assertGreater(r["price"]["low"], r["per_unit"])

    def test_tc07_single_unit_batch(self):
        r = calculate({"units": 1, "packaging": 10})
        self.assertEqual(r["per_unit"], 10)

    def test_tc08_ingredient_without_name_is_kept(self):
        r = calculate({"units": 2, "ingredients": [{"name": "", "cost": 50}]})
        self.assertEqual(r["total"], 50)
        self.assertEqual(r["ingredients"][0]["name"], "-")

    def test_tc09_rejects_no_costs(self):
        with self.assertRaises(ValueError):
            calculate({"units": 5})

    def test_tc10_rejects_negative_cost(self):
        with self.assertRaises(ValueError):
            calculate({"units": 5, "packaging": -3})

    def test_tc11_rejects_zero_units(self):
        with self.assertRaises(ValueError):
            calculate({"units": 0, "packaging": 10})

    def test_tc12_rejects_non_numeric(self):
        with self.assertRaises(ValueError):
            calculate({"units": 5, "packaging": "abc"})

    def test_tc13_explanations_in_both_languages(self):
        e = explain(calculate(DEMO))
        self.assertIn("455", e["en"])
        self.assertIn("₹455", e["ta"])


if __name__ == "__main__":
    unittest.main()
