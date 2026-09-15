import json
import tempfile
import unittest
from pathlib import Path

from job_agent.cv import generate
from job_agent.evaluator import evaluate
from job_agent.models import Job, Requirement
from job_agent.permissions import PermissionDenied, require_external_approval
from job_agent.profile import ValidationError, load_config, load_profile
from job_agent.storage import Store


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.root = Path(self.directory.name)
        source = json.loads(Path("data/profile.json").read_text(encoding="utf-8")); path = self.root / "profile.json"; path.write_text(json.dumps(source), encoding="utf-8")
        self.profile = load_profile(path); self.config = load_config("data/search_config.json")

    def tearDown(self): self.directory.cleanup()

    def test_profile_rejects_missing_facts(self):
        path = self.root / "bad.json"; path.write_text('{"identity":{}}')
        with self.assertRaises(ValidationError): load_profile(path)

    def test_junior_match_is_better_than_senior(self):
        junior = Job("Junior Python Developer", location="Aachen", arrangement="hybrid", requirements=[Requirement("Python", "mandatory")])
        senior = Job("Senior Python Developer", requirements=[Requirement("Python", "mandatory")])
        self.assertGreater(evaluate(junior, self.profile, self.config).score, evaluate(senior, self.profile, self.config).score)
        self.assertTrue(evaluate(senior, self.profile, self.config).excluded)

    def test_required_master_is_excluded_but_preferred_is_not(self):
        required = evaluate(Job("Data Analyst", requirements=[Requirement("Master's degree", "mandatory")]), self.profile, self.config)
        preferred = evaluate(Job("Data Analyst", requirements=[Requirement("Master's degree", "preferred")]), self.profile, self.config)
        self.assertTrue(required.excluded); self.assertFalse(preferred.excluded); self.assertLess(required.score, preferred.score)

    def test_mandatory_gap_is_stronger_than_optional_gap(self):
        must = evaluate(Job("Data Analyst", requirements=[Requirement("R", "mandatory")]), self.profile, self.config)
        nice = evaluate(Job("Data Analyst", requirements=[Requirement("R", "preferred")]), self.profile, self.config)
        self.assertLess(must.score, nice.score); self.assertNotIn("r", self.profile.skills)

    def test_unknown_and_location_are_visible(self):
        result = evaluate(Job("Data Analyst", location="Berlin", arrangement="onsite"), self.profile, self.config)
        self.assertTrue(result.uncertainties); self.assertTrue(result.concerns)

    def test_store_persists_and_exact_url_deduplicates(self):
        database = self.root / "agent.sqlite"; store = Store(database)
        job = Job("Junior Python Developer", source_url="https://example.test/1", requirements=[Requirement("Python", "mandatory")])
        first, created = store.save_job(job, evaluate(job, self.profile, self.config).to_dict()); second, duplicate = store.save_job(job, evaluate(job, self.profile, self.config).to_dict())
        self.assertTrue(created); self.assertFalse(duplicate); self.assertEqual(first, second); self.assertEqual(len(store.list_jobs()), 1)
        store.set_decision(first, "reject", "role mismatch")
        store.close()
        reopened = Store(database)
        self.assertEqual(reopened.get_job(first)[2]["status"], "rejected_by_user")
        reopened.close()

    def test_application_statuses_and_invalid_status(self):
        store = Store(self.root / "agent.sqlite"); job_id, _ = store.save_job(Job("Role"), {"score": 10})
        store.update_application(job_id, "applied", "2026-01-01", "Manual only")
        self.assertEqual(store.applications()[0]["status"], "applied")
        with self.assertRaises(ValueError): store.update_application(job_id, "saved", None, None)
        store.close()

    def test_cv_uses_profile_facts_without_claiming_employment(self):
        output = self.root / "draft.md"; generate(Job("Junior Python Developer", requirements=[Requirement("Python", "mandatory")]), self.profile, output)
        text = output.read_text(encoding="utf-8")
        self.assertIn("Python", text); self.assertNotIn("professional employment", text.lower()); self.assertNotIn("React", text)

    def test_external_data_needs_specific_approval_and_application_is_blocked(self):
        with self.assertRaises(PermissionDenied): require_external_approval(action="send_cv", destination="Example GmbH", data_summary="CV", approved=False)
        self.assertTrue(require_external_approval(action="send_cv", destination="Example GmbH", data_summary="CV", approved=True)["approved"])
        with self.assertRaises(PermissionDenied): require_external_approval(action="submit_application", destination="Example GmbH", data_summary="application", approved=True)


if __name__ == "__main__": unittest.main()
