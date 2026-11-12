"""Remember the videos from a batch that was closed without merging.

Runs on GitHub when a "new videos" pull request is closed (see
.github/workflows/remember-rejected.yml). Every video in that batch that
isn't in the main list gets added to rejected.json, so the monthly search
never proposes it again.

Usage: python scripts/remember_rejected.py <the batch's videos.json>
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS_FILE = ROOT / "videos.json"
REJECTED_FILE = ROOT / "rejected.json"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    batch = load(sys.argv[1])
    kept_ids = {v["youtubeId"] for v in load(VIDEOS_FILE)}
    rejected = load(REJECTED_FILE) if REJECTED_FILE.exists() else []
    already = {r["youtubeId"] for r in rejected}

    today = date.today().isoformat()
    added = 0
    for video in batch:
        video_id = video.get("youtubeId")
        if video_id and video_id not in kept_ids and video_id not in already:
            rejected.append({"youtubeId": video_id, "title": video.get("title", ""), "rejected": today})
            already.add(video_id)
            added += 1

    REJECTED_FILE.write_text(json.dumps(rejected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Remembered {added} rejected videos ({len(rejected)} in total).")


if __name__ == "__main__":
    main()
