#!/usr/bin/env python3
"""Run Hawkeye Jobs on a GitHub-hosted runner and publish a public job snapshot.

The SQLite database is ephemeral to the runner. Only public job-ad fields are
published; personal statuses remain in the browser's local storage.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_DIR = Path(os.environ.get("HAWKEYE_DATA_DIR", "/tmp/hawkeye-data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HAWKEYE_DATA_DIR"] = str(DATA_DIR)
os.environ.setdefault("HAWKEYE_BROWSER", "cdp")
os.environ.setdefault("HAWKEYE_CONTAINER", "1")

from countries import load_countries
from pipeline import run_search
from settings import load_app_settings, load_config
from store import Store


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def public_job(row: dict) -> dict:
    return {
        "id": str(row.get("id") or ""),
        "title": str(row.get("title") or "بدون عنوان")[:300],
        "url": str(row.get("url") or ""),
        "description": str(row.get("description") or "")[:2400],
        "source": str(row.get("source") or ""),
        "location": str(row.get("location") or ""),
        "keyword": str(row.get("keyword") or ""),
        "published": str(row.get("published") or ""),
        "first_seen_at": str(row.get("first_seen_at") or ""),
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config_source = ROOT / "data" / "search-config.json"
    config_target = DATA_DIR / "config.json"
    if not config_source.is_file():
        raise RuntimeError("data/search-config.json is missing")
    config_target.write_text(config_source.read_text(encoding="utf-8"), encoding="utf-8")

    settings = load_config()
    if not settings:
        raise RuntimeError("Search settings are incomplete")
    app_settings = load_app_settings()
    countries = load_countries()
    labels = {str(item["id"]): item["label"] for item in countries}
    events: list[dict] = []

    with Store() as store:
        store.recover_interrupted_runs()
        summary = run_search(
            settings,
            on_event=events.append,
            country_labels=labels,
            store=store,
            trigger="auto",
            job_age_days=app_settings.get("job_age_days", 14),
        )
        rows = store.list_jobs(limit=1500, include_dismissed=True)
        jobs_now = [public_job(row) for row in rows]

    if summary.state != "done":
        raise RuntimeError(f"Search did not finish normally: {summary.state}")

    successful = [e for e in events if e.get("type") == "query_done"]
    failed = [e for e in events if e.get("type") == "query_failed"]
    skipped = [e for e in events if e.get("type") == "query_skipped"]

    output_path = ROOT / "data" / "jobs.json"
    old = read_json(output_path, {})
    old_jobs = old.get("jobs", []) if isinstance(old, dict) else []
    if not isinstance(old_jobs, list):
        old_jobs = []

    # Merge by canonical URL so jobs found on earlier scheduled runs remain visible.
    merged: dict[str, dict] = {}
    for row in old_jobs + jobs_now:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url") or "").strip()
        if url.startswith(("https://", "http://")):
            merged[url.rstrip("/").lower()] = public_job(row)
    all_jobs = sorted(
        merged.values(),
        key=lambda item: item.get("first_seen_at") or "",
        reverse=True,
    )[:3000]

    document = {
        "updated_at": utc_now(),
        "summary": {
            "state": summary.state,
            "found_this_run": int(summary.found),
            "new_this_run": len(summary.new_jobs),
            "job_count": len(all_jobs),
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "skipped_queries": len(skipped),
        },
        "jobs": all_jobs,
    }
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    logging.info(
        "Search complete: %s found, %s new, %s jobs in published snapshot; %s successful and %s failed queries",
        summary.found, len(summary.new_jobs), len(all_jobs), len(successful), len(failed),
    )
    if not successful and failed:
        logging.error("Every attempted query failed; refusing to publish an empty/failed result set")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
