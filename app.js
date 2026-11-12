// Daily Art: shows one video per day from videos.json.

// The day the app started. Day 0 shows the first video in the list,
// day 1 shows the second, and so on. When the list runs out, it starts over.
const START_DATE = "2026-11-12";

// Names for the two lists saved in the browser.
const FAVORITES_KEY = "dailyArt.favorites";
const HISTORY_KEY = "dailyArt.history";

// ---------- Small helpers ----------

// Turn a Date into "YYYY-MM-DD" using the local time zone.
function toDateString(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

// Whole days between two "YYYY-MM-DD" strings.
function daysBetween(from, to) {
  const msPerDay = 24 * 60 * 60 * 1000;
  return Math.round((Date.parse(to) - Date.parse(from)) / msPerDay);
}

// Show a "YYYY-MM-DD" date nicely, e.g. "Thursday, 12 November 2026".
function prettyDate(dateString) {
  const [y, m, d] = dateString.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

// Read and write lists in the browser's storage.
// If storage is unavailable (e.g. a private window), fall back to an empty list.
function loadList(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || [];
  } catch {
    return [];
  }
}

function saveList(key, list) {
  try {
    localStorage.setItem(key, JSON.stringify(list));
  } catch {
    // Nothing to do: the page still works, it just won't remember.
  }
}

// ---------- Picking the video ----------

// Which video belongs to a given date?
function videoForDate(videos, dateString) {
  const day = daysBetween(START_DATE, dateString);
  // The extra "+ videos.length" keeps the number positive for dates before the start.
  const index = ((day % videos.length) + videos.length) % videos.length;
  return videos[index];
}

// ---------- Showing things on the page ----------

function showVideo(video) {
  const player = document.getElementById("player");
  if (video.vimeoId) {
    player.src = `https://player.vimeo.com/video/${video.vimeoId}`;
  } else {
    player.src = `https://www.youtube-nocookie.com/embed/${video.youtubeId}?rel=0`;
  }
  player.title = video.title;

  document.getElementById("title").textContent = video.title;
  const year = video.year ? ` · ${video.year}` : "";
  document.getElementById("artist").textContent = video.artist + year;
  document.getElementById("note").textContent = video.note;
}

function updateFavoriteButton(video) {
  const button = document.getElementById("fav-button");
  const isFavorite = loadList(FAVORITES_KEY).includes(video.id);
  button.textContent = isFavorite ? "♥" : "♡";
  button.setAttribute("aria-pressed", String(isFavorite));
  button.title = isFavorite ? "Remove from favorites" : "Add to favorites";
}

// Fill a list (favorites or history) with links to videos.
function fillList(listId, emptyId, items) {
  const list = document.getElementById(listId);
  list.innerHTML = "";
  document.getElementById(emptyId).hidden = items.length > 0;

  for (const item of items) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = `?video=${encodeURIComponent(item.video.id)}`;
    a.textContent = item.video.title;

    const meta = document.createElement("span");
    meta.className = "meta";
    meta.textContent = item.label;
    a.appendChild(meta);

    li.appendChild(a);
    list.appendChild(li);
  }
}

function showFavorites(videos) {
  const items = loadList(FAVORITES_KEY)
    .map((id) => videos.find((v) => v.id === id))
    .filter(Boolean) // skip any video that was removed from the list
    .reverse() // newest favorite first
    .map((video) => ({ video, label: video.artist }));
  fillList("favorites", "favorites-empty", items);
}

function showHistory(videos, today) {
  const items = loadList(HISTORY_KEY)
    .filter((entry) => entry.date !== today) // today is already at the top
    .map((entry) => ({ entry, video: videos.find((v) => v.id === entry.videoId) }))
    .filter((item) => item.video)
    .sort((a, b) => b.entry.date.localeCompare(a.entry.date)) // most recent day first
    .map((item) => ({ video: item.video, label: prettyDate(item.entry.date) }));
  fillList("history", "history-empty", items);
}

// Remember that this date's video was shown (once per day).
function recordHistory(today, video) {
  const history = loadList(HISTORY_KEY);
  if (!history.some((entry) => entry.date === today)) {
    history.push({ date: today, videoId: video.id });
    saveList(HISTORY_KEY, history);
  }
}

// ---------- Moving favorites between devices ----------

const CODE_PREFIX = "daily-art:";

function showSyncMessage(text) {
  document.getElementById("sync-message").textContent = text;
}

// Copy a short code like "daily-art:bausch-vollmond,jalet-skid" to the clipboard.
async function copyFavorites() {
  const favorites = loadList(FAVORITES_KEY);
  if (favorites.length === 0) {
    showSyncMessage("You have no favorites to copy yet.");
    return;
  }
  const code = CODE_PREFIX + favorites.join(",");
  try {
    await navigator.clipboard.writeText(code);
    showSyncMessage(`Copied ${favorites.length} favorites. Paste the code into the app on your other device.`);
  } catch {
    // Some browsers don't allow copying; show the code so it can be copied by hand.
    prompt("Copy this code:", code);
  }
}

// Ask for a code and add its favorites to the ones already saved (never removes any).
function addFavoritesFromCode(videos) {
  const code = (prompt("Paste your favorites code:") || "").trim();
  if (!code) return false; // cancelled

  if (!code.startsWith(CODE_PREFIX)) {
    showSyncMessage("That doesn't look like a favorites code. It should start with \"daily-art:\".");
    return false;
  }

  const knownIds = new Set(videos.map((v) => v.id));
  const favorites = loadList(FAVORITES_KEY);
  let added = 0;
  for (const id of code.slice(CODE_PREFIX.length).split(",")) {
    const cleanId = id.trim();
    if (knownIds.has(cleanId) && !favorites.includes(cleanId)) {
      favorites.push(cleanId);
      added++;
    }
  }
  saveList(FAVORITES_KEY, favorites);
  showSyncMessage(added === 0
    ? "No new favorites in that code. You already have them all."
    : `Added ${added} favorite${added === 1 ? "" : "s"}.`);
  return added > 0;
}

// ---------- Start the app ----------

async function start() {
  const response = await fetch("videos.json");
  const videos = await response.json();

  // The address can include "?date=YYYY-MM-DD" to pretend it's another day (handy for testing),
  // or "?video=some-id" to rewatch a specific video from Favorites or Past days.
  const params = new URLSearchParams(location.search);
  const today = params.get("date") || toDateString(new Date());
  const chosenId = params.get("video");
  const chosen = chosenId && videos.find((v) => v.id === chosenId);

  const todaysVideo = videoForDate(videos, today);
  recordHistory(today, todaysVideo);

  const video = chosen || todaysVideo;
  document.getElementById("date-line").textContent = prettyDate(today);
  document.getElementById("back-to-today").hidden = !chosen;
  showVideo(video);
  updateFavoriteButton(video);
  showFavorites(videos);
  showHistory(videos, today);

  // Tapping the heart adds or removes the video from favorites.
  document.getElementById("fav-button").addEventListener("click", () => {
    let favorites = loadList(FAVORITES_KEY);
    if (favorites.includes(video.id)) {
      favorites = favorites.filter((id) => id !== video.id);
    } else {
      favorites.push(video.id);
    }
    saveList(FAVORITES_KEY, favorites);
    updateFavoriteButton(video);
    showFavorites(videos);
  });

  // Buttons for moving favorites between devices.
  document.getElementById("copy-favorites").addEventListener("click", copyFavorites);
  document.getElementById("paste-favorites").addEventListener("click", () => {
    if (addFavoritesFromCode(videos)) {
      updateFavoriteButton(video);
      showFavorites(videos);
    }
  });
}

start().catch((error) => {
  document.getElementById("note").textContent =
    "Sorry, the video list couldn't be loaded. " + error.message;
});
