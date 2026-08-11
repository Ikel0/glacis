import unittest

from glacis.contract import ContractError, validate
from glacis.decision import assess


def reading(**extra):
    value = {"reading_id": "r-1", "shipment_id": "S-1", "sensor_id": "T-1", "observed_at": "2026-08-11T08:00:00Z", "temperature_c": 4, "target_min_c": 2, "target_max_c": 8, "location": "hub"}
    value.update(extra)
    return value


class GlacisTests(unittest.TestCase):
    def test_in_range_reading_is_nominal(self):
        self.assertEqual(assess(validate(reading()))["state"], "within_range")

    def test_far_above_range_is_critical(self):
        result = assess(validate(reading(temperature_c=12)))
        self.assertEqual(result["state"], "critical")
        self.assertEqual(result["delta_c"], 4)

    def test_invalid_range_is_rejected(self):
        with self.assertRaises(ContractError):
            validate(reading(target_min_c=8, target_max_c=8))
