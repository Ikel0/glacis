import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from glacis.contract import ContractError, validate
from glacis.decision import assess
from glacis.server import weather_context
from glacis.store import ReadingConflictError, save


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

    def test_non_finite_or_unexpected_values_are_rejected(self):
        with self.assertRaisesRegex(ContractError, "finite"):
            validate(reading(temperature_c=float("nan")))
        with self.assertRaisesRegex(ContractError, "unexpected"):
            validate(reading(debug=True))

    def test_same_reading_id_cannot_hide_a_different_payload(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "glacis.db"
            first = reading()
            self.assertTrue(save(first, assess(first), database))
            self.assertFalse(save(first, assess(first), database))
            with self.assertRaises(ReadingConflictError):
                changed = reading(temperature_c=9)
                save(changed, assess(changed), database)

    def test_weather_context_returns_public_observation(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"current":{"time":"2026-08-22T15:00","temperature_2m":22.6,"relative_humidity_2m":39}}'

        with patch("glacis.server.urlopen", return_value=Response()) as mocked:
            context = weather_context()
        self.assertTrue(context["live"])
        self.assertEqual(context["temperature_c"], 22.6)
        self.assertFalse(context["decision_use"])
        self.assertEqual(context["source_url"], "https://open-meteo.com/en/docs")
        self.assertEqual(mocked.call_args.args[0].get_header("User-agent"), "Ikel-Glacis/1.0 (+https://github.com/Ikel0/glacis)")
