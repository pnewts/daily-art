"""Send a phone notification with today's Daily Art video.

Runs on GitHub every morning (see .github/workflows/daily-reminder.yml).
The notification goes through ntfy (https://ntfy.sh) to the topic in the
NTFY_TOPIC secret. Tapping it opens the app.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
APP_URL = "https://pnewts.github.io/daily-art/"
TIME_ZONE = ZoneInfo("America/Los_Angeles")
SEND_HOUR = 8  # 8am Pacific


def start_date():
    """Read START_DATE from app.js, so the page and this script always agree."""
    text = (ROOT / "app.js").read_text(encoding="utf-8")
    found = re.search(r'START_DATE = "(\d{4}-\d{2}-\d{2})"', text)
    return date.fromisoformat(found.group(1))


def video_for(day):
    """Pick the video for a date, using the same rule as videoForDate() in app.js."""
    videos = json.loads((ROOT / "videos.json").read_text(encoding="utf-8"))
    index = (day - start_date()).days % len(videos)  # Python's % never goes negative
    return videos[index]


def should_send(now, manual):
    """Only send during the 8 o'clock hour in Los Angeles (or whenever run by hand)."""
    return manual or now.hour == SEND_HOUR


def send(topic, video):
    """Post the notification to ntfy."""
    request = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=f"{video['title']} — {video['artist']}".encode("utf-8"),
        headers={
            "Title": "Daily Art",
            "Click": APP_URL,
            "Tags": "performing_arts",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as reply:
        reply.read()


def main():
    now = datetime.now(TIME_ZONE)
    manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if not should_send(now, manual):
        print(f"It's {now:%H:%M} in Los Angeles, not the {SEND_HOUR} o'clock hour. Not sending.")
        return

    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        sys.exit("The NTFY_TOPIC secret is missing, so no notification was sent.")

    video = video_for(now.date())
    send(topic, video)
    print(f"Sent: {video['title']} — {video['artist']}")


if __name__ == "__main__":
    main()
