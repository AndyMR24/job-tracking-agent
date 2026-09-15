# Development notes

Run tests with `python -m unittest discover -s tests`. The project uses only the standard library at runtime and for tests.

`profile.py` validates editable factual data. `normalizer.py` gives incomplete listings a consistent shape without inventing fields. `evaluator.py` makes conservative, transparent rule-based assessments. `storage.py` is local SQLite state and audit logging. `cv.py` produces local Markdown drafts from profile facts. `search.py` performs an optional general public web search, while `cli.py` coordinates the workflow.

The MVP intentionally uses only exact URL/job-ID duplicate prevention and basic work-authorization flags. It has no credential handling, browser/application automation, or personal-data network transmission path.
