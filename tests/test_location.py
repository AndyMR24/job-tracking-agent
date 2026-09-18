import unittest

from job_agent.evaluator import evaluate
from job_agent.location import LocationStatus, extract_city, resolve_location
from job_agent.models import Job
from job_agent.profile import load_config, load_profile


class LocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile("data/profile.json")
        cls.config = load_config("data/search_config.json")

    def test_common_city_formats_resolve_conservatively(self):
        self.assertEqual(extract_city("München, München (Kreis)"), "München")
        self.assertEqual(extract_city("Köln, Köln"), "Köln")
        self.assertIsNone(extract_city("Germany"))
        self.assertIsNone(extract_city("München, Berlin"))

    def test_within_and_outside_radius(self):
        self.assertEqual(resolve_location("Aachen", self.config["location_preferences"]).status, LocationStatus.WITHIN_RADIUS)
        self.assertEqual(resolve_location("München, München (Kreis)", self.config["location_preferences"]).status, LocationStatus.OUTSIDE_RADIUS)

    def test_outside_radius_requires_explicit_remote_exception(self):
        config = self.config
        self.assertTrue(evaluate(Job("Data Analyst", location="München, München (Kreis)", arrangement="remote"), self.profile, config).excluded is False)
        for arrangement in ("hybrid", "onsite", "unknown"):
            with self.subTest(arrangement=arrangement):
                result = evaluate(Job("Data Analyst", location="München, München (Kreis)", arrangement=arrangement), self.profile, config)
                self.assertTrue(result.excluded)

    def test_missing_or_unresolved_location_is_unknown(self):
        preferences = self.config["location_preferences"]
        self.assertEqual(resolve_location(None, preferences).status, LocationStatus.UNKNOWN)
        self.assertEqual(resolve_location("Europe", preferences).status, LocationStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
