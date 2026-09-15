# Progress and TODOs

Last verified: 2026-09-15

## Completed and verified

- [x] Editable profile and separate search configuration validate successfully.
- [x] Editable installation succeeds with `python -m pip install --no-deps -e .`.
- [x] Automated test suite passes: 9 tests.
- [x] Example JSON ingestion works and stores jobs locally.
- [x] Job listing, detail view, fit explanation, save, and audit history work.
- [x] Truthful local Markdown CV generation works.
- [x] Manual application status tracking and application listing work.
- [x] External-data approval check records approval locally without transmitting data.
- [x] Public search command runs without sending profile or CV data.
- [x] SQLite persistence and exact URL/job-ID duplicate prevention work.
- [x] GitHub repository is linked and the working tree was clean before this verification update.

## Current limitations / TODOs

- [ ] Improve public-search result extraction and add fixtures for changing search-result HTML.
- [ ] Add explicit conflict detection between `MASTER_PROFILE.md`, the structured profile, and the master CV.
- [ ] Add CLI setup/edit helpers so users do not need to edit JSON manually.
- [ ] Add richer requirement extraction from full job descriptions while preserving unknown states.
- [ ] Add tests for malformed web responses and incomplete imported job records.
- [ ] Add tests for rejection decisions, invalid job IDs, and blocked `submit_application` CLI behavior.
- [ ] Add a rendered CV review step and optional PDF export only after validating truthful content.
- [ ] Add a controlled way to configure source-specific public search providers.
- [ ] Add a release/update workflow and CI test run on GitHub.

## Known manual-test observations

- The original manual referenced `SOURCE_CV.pdf.pdf`; the repository contains `SOURCE_CV.pdf`. The configuration and manual have been corrected.
- The first editable-install attempt failed because setuptools discovered `data` as a top-level package. Explicit package discovery was added to `pyproject.toml` and must be rechecked after the next clean install.
- The public search command completed without output in this environment, so live result availability is not yet considered fully verified; the deterministic JSON ingestion path is verified.
