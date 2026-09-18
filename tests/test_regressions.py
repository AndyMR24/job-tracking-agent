import json
import shutil
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
            with self.assertRaises(KeyError): store.save_cv(999, "draft.pdf", [])
            self.assertEqual(store.list_jobs(), [])
            self.assertEqual(store.applications(), [])
            self.assertEqual(store.history(), [])
            store.close()

    def test_target_role_matching_is_narrow_but_keeps_variants(self):
        positive = ["Junior Data Scientist", "Data Science Associate", "Junior Data Analyst", "Data Engineer", "Machine Learning Engineer", "Junior Python Developer", "Python Software Developer", "Software Developer"]
        negative = ["Business Analyst", "Marketing Analyst", "Financial Analyst", "Frontend Developer"]
        for title in positive:
            with self.subTest(title=title):
                self.assertIn("Title is related", " ".join(evaluate(Job(title), self.profile, self.config).strong_matches))
        for title in negative:
            with self.subTest(title=title):
                self.assertNotIn("Title is related", " ".join(evaluate(Job(title), self.profile, self.config).strong_matches))

    def test_secondary_role_is_distinguishable_from_primary_role(self):
        secondary = evaluate(Job("Junior IT Consultant"), self.profile, self.config)
        primary = evaluate(Job("Junior Data Engineer"), self.profile, self.config)
        self.assertIn("secondary role", " ".join(secondary.strong_matches))
        self.assertNotIn("target role", " ".join(secondary.strong_matches))
        self.assertIn("target role", " ".join(primary.strong_matches))
        self.assertGreater(primary.score, secondary.score)

    def test_unrelated_junior_remote_job_is_not_recommended(self):
        result = evaluate(Job("Junior Payroll Assistant", arrangement="remote"), self.profile, self.config)
        self.assertFalse(result.excluded)
        self.assertNotEqual(result.assessment, "recommended")

    def test_compatible_seniority_is_not_a_major_score_bonus(self):
        junior = evaluate(Job("Payroll Assistant", seniority="junior"), self.profile, self.config)
        unknown = evaluate(Job("Payroll Assistant", seniority="unknown"), self.profile, self.config)
        self.assertEqual(junior.score, unknown.score)

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

    @unittest.skipUnless(shutil.which("pdflatex"), "pdflatex is not installed in this test environment")
    def test_cv_heading_reflects_requirement_match(self):
        with tempfile.TemporaryDirectory() as directory:
            matched = Path(directory) / "matched.pdf"
            unmatched = Path(directory) / "unmatched.pdf"
            generate(Job("Python Developer", requirements=[Requirement("Python")]), self.profile, matched)
            generate(Job("Business Analyst", requirements=[Requirement("Excel")]), self.profile, unmatched)
            from pypdf import PdfReader
            matched_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(matched)).pages)
            unmatched_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(unmatched)).pages)
            self.assertIn("Relevant projects", matched_text)
            self.assertIn("Projects", unmatched_text)
            self.assertNotIn("Relevant projects", unmatched_text)


if __name__ == "__main__": unittest.main()
