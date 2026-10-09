"""
Re-run test-name matching on saved lab_results.

Results are matched to test_definitions once, at upload. Run this after
adding or changing test definitions (e.g. after seed_test_definitions.py)
so existing reports show up in trends without re-uploading them.

Only test_definition_id is changed. Values, ranges and statuses are left
as they were saved.

Run from the backend/ directory (with the venv activated):
    python ../data/rematch_lab_results.py            # dry run: report only
    python ../data/rematch_lab_results.py --apply    # write the changes

Requires backend/.env with SUPABASE_URL and SUPABASE_SERVICE_KEY.
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.database.client import get_supabase  # noqa: E402
from app.parser.normalizer import match_definition  # noqa: E402

PAGE_SIZE = 1000


def _all_lab_results(supabase):
    rows, start = [], 0
    while True:
        page = (
            supabase.table("lab_results")
            .select("id, test_name_raw, test_definition_id")
            .order("id")
            .range(start, start + PAGE_SIZE - 1)
            .execute()
            .data
        )
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def rematch(apply: bool) -> None:
    supabase = get_supabase()
    definitions = supabase.table("test_definitions").select("*").execute().data or []
    names = {d["id"]: d["canonical_name"] for d in definitions}
    print(f"test_definitions: {len(definitions)}")
    if not definitions:
        print("Nothing to match against. Run seed_test_definitions.py first.")
        return

    results = _all_lab_results(supabase)
    new_ids = {}
    for row in results:
        matched = match_definition(row["test_name_raw"], definitions)
        new_ids[row["id"]] = matched["id"] if matched else None
    changes = [(row, new_ids[row["id"]]) for row in results if new_ids[row["id"]] != row["test_definition_id"]]

    print(f"lab_results: {len(results)}")
    print(f"matched before: {sum(1 for r in results if r['test_definition_id'])}, "
          f"after: {sum(1 for v in new_ids.values() if v)}")
    print(f"rows to change: {len(changes)}")
    by_test = Counter(names.get(new_id, "(unmatched)") for _, new_id in changes)
    for name, count in by_test.most_common():
        print(f"  {name}: {count}")

    if not apply:
        print("\nDry run. Re-run with --apply to write these changes.")
        return

    for row, new_id in changes:
        supabase.table("lab_results").update({"test_definition_id": new_id}).eq("id", row["id"]).execute()
    print(f"\nUpdated {len(changes)} rows.")


if __name__ == "__main__":
    rematch(apply="--apply" in sys.argv)
