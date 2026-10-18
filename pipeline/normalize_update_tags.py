"""Apply the update-tag convention to every hand-curated data file (see CLAUDE.md, "Update tags").
Run once per pull, after the research step and before build_final_payloads.py:

    python3 pipeline/normalize_update_tags.py [--pull-date YYYY-MM-DD]   # default: today, US/Eastern

- Records the pull date in data/content_overrides.json ("pull_date"); every renderer measures
  "Updated mm/dd/yy" / "No update mm/dd/yy" badges against it.
- Rewrites this pull's tags to "UPDATE (mm/dd/yy): ..." (legacy "UPDATE (this pull, YYYY-MM-DD)"
  is accepted and converted) and prunes every tag from an earlier pull, keeping its text.
- Replaces "this pull" phrasing with the actual dated pull.
- Stamps "last_updated" on Point 1/3 override entries that carry a current tag. Entries written
  fresh this pull without a tag need "last_updated" set by whoever wrote them.
Idempotent: safe to re-run any number of times on the same pull date.
"""
import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from render_common import has_current_tag, normalize_obj, normalize_text

OVERRIDES = "data/content_overrides.json"
SECTORS = "data/point2/sectors.json"
ASSET_CLASSES = "data/point4/asset_classes.json"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pull-date", default=datetime.now(ZoneInfo("America/New_York")).date().isoformat())
    pull_date = ap.parse_args().pull_date

    ov = load(OVERRIDES)
    ov["pull_date"] = pull_date
    for section in ("macro_flags", "movers", "recommendations"):
        for key, entry in ov.get(section, {}).items():
            if has_current_tag(entry, pull_date):
                entry["last_updated"] = pull_date
            ov[section][key] = normalize_obj(entry, pull_date)
    syn = ov.get("point1_synthesis", {})
    for key in ("current", "previous"):
        if key in syn:
            syn[key] = normalize_obj(syn[key], pull_date)
    for key in ("point3_freshness_note", "point1_since_last_pull"):
        if ov.get(key):
            ov[key] = normalize_text(ov[key], pull_date, base_date=pull_date)
    save(OVERRIDES, ov)

    for path in (SECTORS, ASSET_CLASSES):
        save(path, normalize_obj(load(path), pull_date))

    print(f"Normalized update tags for pull date {pull_date}")


if __name__ == "__main__":
    main()
