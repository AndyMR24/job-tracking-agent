import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from job_agent.cv import generate
from job_agent.evaluator import evaluate
from job_agent.models import Job, Requirement
from job_agent.profile import load_config, load_profile
from job_agent.search import SearchProviderChallengeError, public_search
from job_agent.storage import Store


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile("data/profile.json")
        cls.config = load_config("data/search_config.json")

    def test_nonexistent_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory) / "jobs.sqlite")
            with self.assertRaises(KeyError): store.set_decision(999, "save")
            with self.assertRaises(KeyError): store.set_decision(999, "reject")
            with self.assertRaises(KeyError): store.update_application(999, "applied", None, None)
            with self.assertRaises(KeyError): store.save_cv(999, "draft.md", [])
            self.assertEqual(store.list_jobs(), [])
            self.assertEqual(store.applications(), [])
            self.assertEqual(store.history(), [])
            store.close()

    def test_target_role_matching_is_narrow_but_keeps_variants(self):
        positive = ["Junior Data Scientist", "Data Science Associate", "Junior Data Analyst", "Machine Learning Engineer", "Junior Python Developer", "Python Software Developer", "Software Developer"]
        negative = ["Business Analyst", "Marketing Analyst", "Financial Analyst", "Frontend Developer"]
        for title in positive:
            with self.subTest(title=title):
                self.assertIn("Title is related", " ".join(evaluate(Job(title), self.profile, self.config).strong_matches))
        for title in negative:
            with self.subTest(title=title):
                self.assertNotIn("Title is related", " ".join(evaluate(Job(title), self.profile, self.config).strong_matches))

    def test_sponsorship_variants_are_flagged_without_exclusion(self):
        for wording in ("visa sponsorship required", "this role requires sponsorship", "employer sponsorship is unavailable"):
            with self.subTest(wording=wording):
                result = evaluate(Job("Python Developer", description=wording), self.profile, self.config)
                self.assertTrue(result.uncertainties)
                self.assertFalse(result.excluded)

    def test_search_challenge_is_distinguished_from_zero_results(self):
        challenge = type("Response", (), {"__enter__": lambda self: self, "__exit__": lambda self, *args: None, "read": lambda self: b"captcha unusual traffic"})
        empty = type("Response", (), {"__enter__": lambda self: self, "__exit__": lambda self, *args: None, "read": lambda self: b"<html><body>normal results page</body></html>"})
        with patch("job_agent.search.urlopen", return_value=challenge()):
            with self.assertRaises(SearchProviderChallengeError): public_search("test")
        with patch("job_agent.search.urlopen", return_value=empty()):
            self.assertEqual(public_search("test"), [])

    def test_cv_heading_reflects_requirement_match(self):
        with tempfile.TemporaryDirectory() as directory:
            matched = Path(directory) / "matched.md"
            unmatched = Path(directory) / "unmatched.md"
            generate(Job("Python Developer", requirements=[Requirement("Python")]), self.profile, matched)
            generate(Job("Business Analyst", requirements=[Requirement("Excel")]), self.profile, unmatched)
            self.assertIn("## Relevant projects", matched.read_text(encoding="utf-8"))
            self.assertIn("## Projects", unmatched.read_text(encoding="utf-8"))
            self.assertNotIn("## Relevant projects", unmatched.read_text(encoding="utf-8"))


if __name__ == "__main__": unittest.main()
