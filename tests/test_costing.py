import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.costing import calculate  # noqa: E402


class CostingTests(unittest.TestCase):
    def test_demo_pickle(self):
        r = calculate({
            "units": 10, "margin": 30, "packaging": 40, "labour": 150, "other": 30,
            "ingredients": [{"name": "mango", "cost": 120}, {"name": "oil", "cost": 60},
                            {"name": "masala", "cost": 45}, {"name": "salt", "cost": 10}],
        })
        self.assertEqual(r["total"], 455)
        self.assertEqual(r["per_unit"], 45.5)
        self.assertLessEqual(r["price"]["low"], r["price"]["suggested"])
        self.assertLessEqual(r["price"]["suggested"], r["price"]["high"])
        self.assertGreater(r["price"]["suggested"], r["per_unit"])

    def test_rejects_empty_and_negative(self):
        with self.assertRaises(ValueError):
            calculate({"units": 5})
        with self.assertRaises(ValueError):
            calculate({"units": 5, "packaging": -3})
        with self.assertRaises(ValueError):
            calculate({"units": 0, "packaging": 10})


if __name__ == "__main__":
    unittest.main()
