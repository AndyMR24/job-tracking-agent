from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cv import generate
from .evaluator import evaluate
from .normalizer import normalize
from .permissions import require_external_approval
from .profile import ValidationError, load_config, load_profile
from .search import SearchProviderChallengeError, public_search
from .storage import Store

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "data" / "profile.json"
DEFAULT_CONFIG = ROOT / "data" / "search_config.json"
DEFAULT_DB = ROOT / "data" / "job_agent.sqlite3"


def paths(args): return load_profile(args.profile), load_config(args.config), Store(args.database)
def print_evaluation(e):
    print(f"Fit: {e['score']}/100 - {e['assessment']} (a profile/preference match, not hiring probability)")
    for label, key in (("Strong matches", "strong_matches"), ("Potential gaps", "potential_gaps"), ("Important concerns", "concerns"), ("Uncertainties", "uncertainties")):
        print(f"\n{label}:"); print("\n".join(f"- {x}" for x in e[key]) or "- None")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local-first Job Searching Agent. It never submits applications.")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE)); parser.add_argument("--config", default=str(DEFAULT_CONFIG)); parser.add_argument("--database", default=str(DEFAULT_DB))
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("validate")
    ingest = subs.add_parser("ingest"); ingest.add_argument("file", help="JSON list of public job records")
    search = subs.add_parser("search"); search.add_argument("query", nargs="?", help="Public web query; no personal data is transmitted")
    listing = subs.add_parser("list"); listing.add_argument("--include-rejected", action="store_true")
    view = subs.add_parser("view"); view.add_argument("job_id", type=int)
    for name in ("save", "reject"):
        item = subs.add_parser(name); item.add_argument("job_id", type=int); item.add_argument("--reason")
    app = subs.add_parser("application"); app.add_argument("job_id", type=int); app.add_argument("status"); app.add_argument("--date"); app.add_argument("--notes")
    subs.add_parser("applications"); subs.add_parser("history")
    permission = subs.add_parser("permission-check", help="Record a one-time approval check; it does not transmit anything.")
    permission.add_argument("action"); permission.add_argument("destination"); permission.add_argument("data_summary"); permission.add_argument("--approve", action="store_true")
    tailor = subs.add_parser("tailor"); tailor.add_argument("job_id", type=int); tailor.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        profile, config, store = paths(args)
        if args.command == "validate":
            master_cv = config.get("master_cv_path")
            if master_cv and not Path(master_cv).exists(): print(f"Profile and configuration are valid. Master CV path needs attention: {master_cv}")
            else: print("Profile and configuration are valid.")
            return
        if args.command in {"ingest", "search"}:
            if args.command == "ingest": raw_jobs = json.loads(Path(args.file).read_text(encoding="utf-8"))
            else:
                query = args.query or " ".join(config["search_terms"]); store.audit("search_started")
                raw_jobs = public_search(query); store.audit("search_completed", details=f"{len(raw_jobs)} public results")
            if args.command == "search" and not raw_jobs:
                print("No jobs found.")
            for raw in raw_jobs:
                raw.setdefault("known_requirement_terms", [s["name"] for s in profile.data["skills"]]); job = normalize(raw); result = evaluate(job, profile, config); job_id, created = store.save_job(job, result.to_dict()); print(f"{'New' if created else 'Known'} job {job_id}: {job.title} ({result.score}/100)")
        elif args.command == "list":
            for row in store.list_jobs(args.include_rejected): print(f"{row['id']:>3}  {json.loads(row['evaluation'])['score']:>3}/100  {row['status']:<18} {json.loads(row['payload'])['title']}")
        elif args.command == "view":
            job, ev, row = store.get_job(args.job_id); print(f"{job.title}\nCompany: {job.company or 'unknown'}\nLocation: {job.location or 'unknown'}\nURL: {job.source_url or 'unknown'}\n"); print_evaluation(ev)
        elif args.command in {"save", "reject"}: store.set_decision(args.job_id, args.command, args.reason); print(f"Job {args.job_id} updated.")
        elif args.command == "application": store.update_application(args.job_id, args.status, args.date, args.notes); print("Application status recorded. No application was submitted.")
        elif args.command == "applications":
            for row in store.applications(): print(f"{row['job_id']}  {row['status']}  {json.loads(row['payload'])['title']}")
        elif args.command == "history":
            for row in store.history(): print(f"{row['created_at']}  {row['event']}  job={row['job_id'] or '-'}")
        elif args.command == "permission-check":
            approval = require_external_approval(action=args.action, destination=args.destination, data_summary=args.data_summary, approved=args.approve)
            store.audit("external_action_approved", details=json.dumps(approval)); print("Specific approval recorded locally. No data was transmitted.")
        elif args.command == "tailor":
            job, _, _ = store.get_job(args.job_id); output = args.output or str(ROOT / "output" / f"cv_job_{args.job_id}.md"); path, facts = generate(job, profile, output); store.save_cv(args.job_id, str(path), facts); print(f"Local truthful CV draft created: {path}")
    except SearchProviderChallengeError:
        print("Search provider returned a challenge/block instead of search results.")
    except (ValidationError, ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

if __name__ == "__main__": main()
