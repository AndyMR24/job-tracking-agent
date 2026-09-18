import base64
import json
import unittest
from urllib.parse import quote
from unittest.mock import patch

from job_agent.ba import BASource
from job_agent.himalayas import HimalayasSource
from job_agent.nomado24 import Nomado24Source


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self): return json.dumps(self.payload).encode()


class SourceAdapterTests(unittest.TestCase):
    def test_nomado24_maps_fields_and_optional_values(self):
        payload = {"jobs": [{"id": "n1", "title": "Data Analyst", "companyName": "Nomado", "location": "Aachen", "remote": True, "workArrangement": "remote", "url": "https://nomado.test/1", "salaryMin": 50000, "currency": "EUR"}, {"id": "n2", "title": "Minimal"}]}
        with patch("job_agent.nomado24.urllib.request.urlopen", return_value=Response(payload)):
            jobs = Nomado24Source().search("Data Analyst")
        self.assertEqual(jobs[0]["source"], "nomado24"); self.assertEqual(jobs[0]["company"], "Nomado"); self.assertEqual(jobs[0]["arrangement"], "remote")
        self.assertIsNone(jobs[1]["company"]); self.assertIsNone(jobs[1]["location"])

    def test_himalayas_preserves_location_restrictions(self):
        payload = {"jobs": [{"guid": "h1", "title": "Python Developer", "company": {"name": "Himalayas Co"}, "remote": True, "locationRestrictions": ["Germany"], "timezoneRestrictions": ["CET"], "applicationLink": "https://himalayas.test/1"}]}
        with patch("job_agent.himalayas.urllib.request.urlopen", return_value=Response(payload)):
            job = HimalayasSource().search("Python")[0]
        self.assertEqual(job["source"], "himalayas"); self.assertEqual(job["arrangement"], "remote"); self.assertEqual(job["metadata"]["location_restrictions"], ["Germany"]); self.assertIsNone(job["location"])

    def test_ba_maps_search_and_detail_and_encodes_reference(self):
        reference = "10001-1003580280-S"
        search = {"ergebnisliste": [{"stellenangebotsTitel": "Data Analyst", "firma": "BA Employer", "referenznummer": reference, "stellenlokationen": [{"ort": "Aachen", "region": "NRW", "land": "Deutschland"}], "homeofficemoeglich": True}]}
        detail = {"stellenangebotsTitel": "Data Analyst", "stellenangebotsBeschreibung": "Full description", "referenznummer": reference, "angebotsart": "ARBEIT"}
        responses = [Response(search), Response(detail)]
        with patch("job_agent.ba.urllib.request.urlopen", side_effect=responses) as mocked:
            job = BASource().search("Data Analyst", "Aachen", size=1)[0]
        self.assertEqual(job["source"], "ba"); self.assertEqual(job["description"], "Full description"); self.assertEqual(job["location"], "Aachen, NRW, Deutschland"); self.assertEqual(job["arrangement"], "unknown")
        expected = base64.b64encode(reference.encode()).decode()
        self.assertIn(quote(expected, safe=""), mocked.call_args_list[1].args[0].full_url)


if __name__ == "__main__": unittest.main()
