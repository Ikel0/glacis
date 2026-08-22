import unittest
from unittest.mock import patch

from glacis.contract import ContractError, validate
from glacis.decision import assess
from glacis.server import weather_context


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

    def test_weather_context_returns_public_observation(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"current":{"time":"2026-08-22T15:00","temperature_2m":22.6,"relative_humidity_2m":39}}'

        with patch("glacis.server.urlopen", return_value=Response()) as mocked:
            context = weather_context()
        self.assertTrue(context["live"])
        self.assertEqual(context["temperature_c"], 22.6)
        self.assertEqual(mocked.call_args.args[0].get_header("User-agent"), "Ikel-Glacis/1.0 (+https://github.com/Ikel0/glacis)")
