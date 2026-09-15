# Job Searching Agent user manual

This is a local-first Python CLI for discovering public job listings, comparing them against a local factual profile, tracking choices, and creating local Markdown CV drafts. It never submits an application, contacts employers, sends a CV, or stores passwords.

## Install and setup

Use Python 3.11 or later. From this directory, run `python -m pip install -e .`, then `job-agent validate`; alternatively, run commands directly as `python -m job_agent.cli validate`. The editable factual profile is `data/profile.json`; preferences are separate in `data/search_config.json`. Do not put desired roles or preferences in the profile.

`SOURCE_CV.pdf` is retained as reference material and its editable path is `master_cv_path` in `data/search_config.json`. The canonical factual source used by the application is `data/profile.json`, which was transcribed from `MASTER_PROFILE.md`. `job-agent validate` confirms whether the configured CV file exists. If the CV and profile conflict, update the source deliberately; this MVP does not silently resolve conflicts.

## Discovering jobs

For a public web search, use `job-agent search "junior Python developer Germany"`. This only sends the public query to DuckDuckGo; it sends no profile, CV, or contact information. Search result pages commonly lack detailed requirements, so review them before treating them as complete listings.

For reliable, detailed ingestion, create a JSON array and run `job-agent ingest jobs.json`. Each item needs `title`; it may contain `company`, `location`, `arrangement` (`remote`, `hybrid`, `onsite`, or `unknown`), `description`, `source`, `source_url`, `external_job_id`, and `requirements`. Requirements are objects such as `{"text":"Python","kind":"mandatory"}`. Missing information stays unknown.

## Reviewing jobs and decisions

Run `job-agent list`, `job-agent view JOB_ID`, `job-agent save JOB_ID`, or `job-agent reject JOB_ID --reason "too far"`. Use `job-agent history` to see local audit events. Exact source URLs or exact external job IDs prevent a listing from being stored repeatedly; no fuzzy duplicate detection is performed.

Fit scores show match to known profile facts and current preferences, not hiring likelihood. Each detail view separates confirmed matches, potential gaps, important concerns, and uncertainties. Senior roles and an explicitly required Master's degree are normally excluded. Project/thesis evidence is never reported as professional employment. Sponsorship or authorization wording is marked for verification rather than interpreted legally.

## CV drafts and applications

After ingesting a job, run `job-agent tailor JOB_ID`. This creates `output/cv_job_JOB_ID.md` locally and records its source categories. It selects and orders only profile facts; it cannot add skills or professional experience. Review and edit the factual sources before using a draft.

The user applies manually. Track manual progress with `job-agent application JOB_ID applied --date 2026-09-15 --notes "Submitted manually"`, then use `job-agent applications`. Valid tracked states are `applied`, `interview`, `offer`, `rejected_by_company`, and `withdrawn`.

## Storage, privacy, and troubleshooting

The default SQLite database is `data/job_agent.sqlite3`. It contains public job records, decisions, application notes, local CV-version metadata, and audit records. It intentionally contains no passwords and no facility for external personal-data transmission. `job-agent permission-check ACTION DESTINATION DATA --approve` can record a one-time, named approval locally for a future integration, but does not transmit data itself; it always blocks `submit_application`. Delete or move the database yourself if you want a fresh history.

If `validate` fails, correct the reported JSON field. If a search fails, check network access or use `ingest` with saved public job data. Run tests with `python -m unittest discover -s tests`.

