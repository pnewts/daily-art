"""Find new videos for Daily Art.

Runs once a month on GitHub (see .github/workflows/find-videos.yml):
1. Searches YouTube for each line in search_terms.txt.
2. Throws out videos we already have, can't embed, or that are too short/obscure.
3. Asks Claude to pick the best ones and write a short note for each.
4. Adds them to the end of videos.json and writes a summary for the pull request.

Needs two secrets in the environment: YOUTUBE_API_KEY and ANTHROPIC_API_KEY.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
VIDEOS_FILE = ROOT / "videos.json"
TERMS_FILE = Path(__file__).resolve().parent / "search_terms.txt"

HOW_MANY = 30            # how many new videos to propose each month
RESULTS_PER_SEARCH = 10  # YouTube results to look at for each search term
MIN_SECONDS = 60         # skip clips shorter than 1 minute
MAX_SECONDS = 3 * 60 * 60  # ...and anything longer than 3 hours
MIN_VIEWS = 1000         # skip very obscure uploads

CLAUDE_MODEL = "claude-opus-5-5"

TASTE = """\
I run a personal page that shows one wildly inspiring video of art per day, mostly performance:
theatre, dance, clowning, physical theatre and music. These artists set the tone: Philippe Gaulier,
Damien Jalet, Pina Bausch, Philip Glass, SITI Company and Spymonkey. I want work that is bold,
surprising, physical and moving, not just technically good."""


# ---------- YouTube ----------

def youtube_get(endpoint, params):
    """Call the YouTube Data API and return the JSON reply."""
    params = dict(params, key=os.environ["YOUTUBE_API_KEY"])
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as reply:
        return json.load(reply)


def search_ids(term):
    """Return the IDs of embeddable videos YouTube finds for one search term."""
    data = youtube_get("search", {
        "part": "id",
        "q": term,
        "type": "video",
        "videoEmbeddable": "true",
        "maxResults": RESULTS_PER_SEARCH,
    })
    # Some results can be channels or playlists with no videoId; skip those.
    ids = [item.get("id", {}).get("videoId") for item in data.get("items", [])]
    return [video_id for video_id in ids if video_id]


def video_details(ids):
    """Look up title, channel, length, views etc. for a list of video IDs (50 at a time)."""
    details = []
    for start in range(0, len(ids), 50):
        data = youtube_get("videos", {
            "part": "snippet,contentDetails,status,statistics",
            "id": ",".join(ids[start:start + 50]),
        })
        details.extend(data.get("items", []))
    return details


def seconds(iso_duration):
    """Turn YouTube's 'PT1H2M3S' format into a number of seconds."""
    match = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration or "")
    if not match:
        return 0
    d, h, m, s = (int(x or 0) for x in match.groups())
    return ((d * 24 + h) * 60 + m) * 60 + s


def is_good_candidate(video, known_ids):
    """Basic checks before Claude ever sees a video."""
    length = seconds(video.get("contentDetails", {}).get("duration"))
    views = int(video.get("statistics", {}).get("viewCount", 0))
    status = video.get("status", {})
    return (
        video["id"] not in known_ids
        and status.get("embeddable", False)
        and status.get("privacyStatus") == "public"
        and MIN_SECONDS <= length <= MAX_SECONDS
        and views >= MIN_VIEWS
    )


def find_candidates(terms, known_ids):
    """Search every term and return the videos worth showing to Claude."""
    found = []
    for term in terms:
        for video_id in search_ids(term):
            if video_id not in found:
                found.append(video_id)
    print(f"YouTube found {len(found)} different videos.")

    candidates = []
    for video in video_details(found):
        if is_good_candidate(video, known_ids):
            snippet = video["snippet"]
            candidates.append({
                "youtubeId": video["id"],
                "title": snippet.get("title", ""),
                "channel": snippet.get("channelTitle", ""),
                "minutes": round(seconds(video["contentDetails"]["duration"]) / 60),
                "views": int(video["statistics"].get("viewCount", 0)),
                "description": snippet.get("description", "")[:600],
            })
    print(f"{len(candidates)} passed the basic checks.")
    return candidates


# ---------- Claude ----------

# The exact shape of the answer we want back from Claude.
ANSWER_SHAPE = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "youtubeId": {"type": "string"},
                    "title": {"type": "string"},
                    "artist": {"type": "string"},
                    "year": {"type": ["integer", "null"]},
                    "note": {"type": "string"},
                },
                "required": ["youtubeId", "title", "artist", "year", "note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["picks"],
    "additionalProperties": False,
}


def ask_claude(candidates, examples, already_have):
    """Ask Claude to choose the best candidates and write a note for each."""
    prompt = f"""{TASTE}

Below are candidate YouTube videos found by an automatic search. Choose up to {HOW_MANY} that best fit
my taste and would make a great "video of the day". Fewer is fine if the candidates are weak.

I already have the pieces listed under "Pieces I already have". Do not pick another video of any of
those pieces (a different trailer, excerpt or recording of the same work still counts as the same piece).

Leave out: tutorials, classes, lectures and interviews (unless truly exceptional), reaction videos,
fan edits, amateur or student work, shaky phone recordings, news reports, compilations, and anything
that is mainly an advert. Prefer official channels of companies, theatres and festivals. Avoid
choosing several videos of the same piece, and keep a good mix of artists and art forms.

For each pick give:
- youtubeId: copied exactly from the candidate list
- title: the name of the piece (not the raw YouTube title)
- artist: the artist and/or company
- year: the year the piece was made, or null if you are not sure
- note: 2 to 4 warm, vivid sentences on what makes it remarkable, in the style of the examples.
  Only state facts you are confident about or that the title and description support. Never invent
  details; when unsure, describe what the viewer will see instead.

Examples of notes I like:
{json.dumps(examples, indent=2, ensure_ascii=False)}

Pieces I already have:
{already_have}

Candidates:
{json.dumps(candidates, indent=2, ensure_ascii=False)}"""

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    response = client.beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": ANSWER_SHAPE},
        },
        # If Claude declines the request, let the API retry on a suitable fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    )

    if response.stop_reason == "refusal":
        sys.exit("Claude declined the request, so no videos were added this month.")
    if response.stop_reason == "max_tokens":
        sys.exit("Claude's answer was cut off (too long), so no videos were added this month.")

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)["picks"]


# ---------- Putting it together ----------

def make_entries(picks, candidates):
    """Turn Claude's picks into videos.json entries, ignoring any ID that wasn't a real candidate."""
    real_ids = {c["youtubeId"] for c in candidates}
    today = date.today().isoformat()
    entries, used = [], set()
    for pick in picks:
        video_id = pick["youtubeId"]
        if video_id not in real_ids or video_id in used:
            print(f"Skipping unexpected or repeated ID from Claude: {video_id}")
            continue
        used.add(video_id)
        entries.append({
            "id": f"yt-{video_id}",
            "title": pick["title"],
            "artist": pick["artist"],
            "year": pick["year"],
            "youtubeId": video_id,
            "note": pick["note"],
            "added": today,
            "source": "auto",
        })
    return entries[:HOW_MANY]


def write_summary(entries, path):
    """Write the pull request description: one section per proposed video."""
    lines = [
        f"This month's automatic search found **{len(entries)} new videos**.",
        "",
        "Tap each link to preview it. **Merge** to add them all to your daily rotation, or **Close** to skip this batch.",
        "Want only some? Ask Claude to remove the ones you don't like before merging.",
        "",
    ]
    for number, entry in enumerate(entries, start=1):
        year = f" ({entry['year']})" if entry["year"] else ""
        lines += [
            f"### {number}. {entry['title']}{year}",
            f"**{entry['artist']}** · https://www.youtube.com/watch?v={entry['youtubeId']}",
            "",
            entry["note"],
            "",
        ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    summary_path = sys.argv[1] if len(sys.argv) > 1 else "pr-body.md"

    videos = json.loads(VIDEOS_FILE.read_text(encoding="utf-8"))
    known_ids = {v.get("youtubeId") for v in videos}
    terms = [line.strip() for line in TERMS_FILE.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]

    candidates = find_candidates(terms, known_ids)
    if not candidates:
        print("No new candidates this month.")
        return

    # A few hand-picked notes show Claude the style to aim for.
    examples = [{"title": v["title"], "artist": v["artist"], "note": v["note"]}
                for v in videos if v.get("source") != "auto"][:4]

    # Every piece already in the list, so Claude doesn't pick another video of the same work.
    already_have = "\n".join(f"- {v['title']} ({v['artist']})" for v in videos)

    entries = make_entries(ask_claude(candidates, examples, already_have), candidates)
    if not entries:
        print("Claude didn't pick any videos this month.")
        return

    # New videos always go at the END, so past days stay the same.
    videos.extend(entries)
    VIDEOS_FILE.write_text(json.dumps(videos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_summary(entries, summary_path)
    print(f"Added {len(entries)} videos to videos.json.")


if __name__ == "__main__":
    main()
