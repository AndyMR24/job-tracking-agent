# Job Searching Agent user manual

This is a local-first Python CLI for discovering public job listings, comparing them against a local factual profile, tracking choices, and creating local LaTeX-generated PDF CV drafts. The agent helps organize and evaluate opportunities; it never submits an application, contacts employers, sends a CV, or stores passwords. Unknown job information remains unknown rather than being silently guessed.

## Install and setup

Use Python 3.11 or later. From this directory, run `python -m pip install -e .`, then `job-agent validate`; alternatively, run commands directly as `python -m job_agent.cli validate`. The editable factual profile is `data/profile.json`; preferences are separate in `data/search_config.json`. Do not put desired roles or preferences in the profile.

`SOURCE_CV.pdf` is retained as reference material and its editable path is `master_cv_path` in `data/search_config.json`. The canonical factual source used by the application is `data/profile.json`, which was transcribed from `MASTER_PROFILE.md`. `job-agent validate` confirms whether the configured CV file exists. If the CV and profile conflict, update the source deliberately; this MVP does not silently resolve conflicts.

## Discovering jobs

For a normal configured search, run `job-agent search`. The command searches every query in `data/search_config.json` once, running the `primary` queries before the `secondary` queries. Each configured query is sent through the public Adzuna, Nomado24, Himalayas, and Bundesagentur für Arbeit (BA Jobsuche) adapters; results are combined and passed through the same normalization, fit evaluation, and local SQLite storage pipeline as imported jobs. To restrict the run to one adapter, add `--source adzuna`, `--source nomado24`, `--source himalayas`, or `--source ba`. A job returned more than once by the same source is processed once when its source and external identifier match; there is no fuzzy title or company matching. Normalized jobs retain their source provenance (`adzuna`, `nomado24`, `himalayas`, or `ba`) for diagnostics and deduplication.

For a specific manual search, use `job-agent search --query "Data Engineer"` or the backward-compatible positional form `job-agent search "Data Engineer"`. A supplied manual query bypasses all configured searches and performs exactly one Adzuna request by default. Add `--source` to run that query against one specific source instead, for example `job-agent search --query "Data Engineer" --source ba`. Add a location filter with `--location Köln` where supported. Searches send only the public query/location plus locally loaded Adzuna credentials where required; they send no profile, CV, or contact information. Public source adapters may provide different levels of detail: Adzuna commonly returns snippets, while BA may request a small number of details after search results. Review listings before treating them as complete job descriptions.

The configured search families are intentionally separate from suitability scoring. Edit `search_queries.primary` and `search_queries.secondary` in `data/search_config.json` to adjust the normal search scope. Both fields must contain non-empty text queries. The ordering affects request order only; a secondary result is not scored lower than a primary result.

After processing a search, the command prints a summary showing the number of queries actually executed, unique jobs processed, newly stored jobs, previously known jobs, and evaluator-excluded jobs. `No jobs found.` is still printed when the combined search returns no jobs.

Location suitability uses the configurable `location_preferences` object: `origin`, `max_distance_km`, and `remote_only_beyond_distance`. Resolved city locations within the radius remain eligible; resolved locations outside it are excluded unless the job already has the explicit `remote` arrangement and the remote exception is enabled. Unknown or vague locations remain uncertain rather than being assumed nearby or remote. City coordinates are resolved locally with the offline `geonamescache` dataset; the radius is only an approximate geographic proxy for the commute preference, not a train-time calculation.

For reliable, detailed ingestion, create a JSON array and run `job-agent ingest jobs.json`. Each item needs `title`; it may contain `company`, `location`, `arrangement` (`remote`, `hybrid`, `onsite`, or `unknown`), `description`, `source`, `source_url`, `external_job_id`, and `requirements`. Requirements are objects such as `{"text":"Python","kind":"mandatory"}`. Missing information stays unknown. Imported jobs enter the same normalization, evaluation, deduplication, and storage workflow as search results.

## Reviewing jobs and decisions

Run `job-agent list`, `job-agent view JOB_ID`, `job-agent save JOB_ID`, or `job-agent reject JOB_ID --reason "too far"`. Use `job-agent history` to see local audit events. Exact source URLs or exact external job IDs prevent a listing from being stored repeatedly; no fuzzy duplicate detection is performed.

Fit scores show match to known profile facts and current preferences, not hiring likelihood. Each detail view separates confirmed matches, potential gaps, important concerns, and uncertainties. Senior roles and an explicitly required Master's degree are normally excluded. Project/thesis evidence is never reported as professional employment. Sponsorship or authorization wording is marked for verification rather than interpreted legally.

Role relevance is scored separately from early-career compatibility: configured primary target roles receive the strongest title signal, configured secondary consulting queries receive a smaller relevance signal, and junior/entry/graduate/trainee/intern/associate wording no longer provides a large standalone score bonus. An unrelated junior or remote title can remain borderline or uncertain, but is not recommended solely because of its seniority or work arrangement.

## CV drafts and applications

After ingesting a job, run `job-agent tailor JOB_ID`. This creates `output/cv_job_JOB_ID.pdf` and the exact source `output/cv_job_JOB_ID.tex` locally, and records its source categories. The thesis is always included, while other projects and skills are tailored to the job when possible. It selects and orders only profile facts; it cannot add skills or professional experience. Review and edit the factual sources before using a draft.

The user applies manually. Track manual progress with `job-agent application JOB_ID applied --date 2026-09-15 --notes "Submitted manually"`, then use `job-agent applications`. Valid tracked states are `applied`, `interview`, `offer`, `rejected_by_company`, and `withdrawn`.

## Storage, privacy, and troubleshooting

The default SQLite database is `data/job_agent.sqlite3`. It contains public job records, decisions, application notes, local CV-version metadata, and audit records. It intentionally contains no passwords and no facility for external personal-data transmission. `job-agent permission-check ACTION DESTINATION DATA --approve` can record a one-time, named approval locally for a future integration, but does not transmit data itself; it always blocks `submit_application`. Delete or move the database yourself if you want a fresh history.

If `validate` fails, correct the reported JSON field. If an Adzuna search fails, check that `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` are available in the local `.env` file or environment, then use `ingest` with saved public job data. The search source does not follow Adzuna redirect URLs. Run tests with `python -m unittest discover -s tests`.


