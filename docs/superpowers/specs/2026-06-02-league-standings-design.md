# League Standings on Home Tab — Design

**Date:** 2026-06-02
**Status:** Approved pending spec review

## Goal

Show the full IMI league standings on the site, sourced from a weekly standings
screenshot, and make it easy to refresh each week. Standings live on the **Home**
tab, replacing the existing "Top Avg" and "Top OPS" leader cards. (Those leaders
remain available on the Stats tab, so no information is lost.)

## Data model

Add one new top-level key to `data.json`:

```json
"standings": {
  "lastUpdated": "2026-06-02",
  "teams": [
    { "team": "Ed's Dugout Drinkers", "W": 3, "L": 0, "T": 0, "PF": 56, "PA": 16 },
    { "team": "Kodiaks-MENS",         "W": 1, "L": 0, "T": 0, "PF": 25, "PA": 6 },
    { "team": "Icon",                 "W": 0, "L": 2, "T": 0, "PF": 5,  "PA": 36 }
  ]
}
```

- `teams` is an array in the exact order shown in the source standings image
  (the league sorts by PCT then PD); the site preserves that order — no re-sorting.
- Only six fields are transcribed per team: `team`, `W`, `L`, `T`, `PF`, `PA`.
- Everything else is **computed at render time** so the math always agrees and
  there's less to mistype:
  - `GP = W + L + T`
  - `PD = PF - PA`
  - `PCT = GP > 0 ? (W + 0.5 * T) / GP : 0`  (displayed as a percentage, e.g. `66.67%`)
- `standings.lastUpdated` is the date of the standings snapshot. It is independent
  of `season.lastUpdated` (the site-header timestamp), which keeps its existing
  meaning and format.

## UI

Modify `renderHome()` only. No new nav tab, no new panel, no HTML structure change
to `index.html`'s `<nav>`/`<main>`.

1. Remove the `sortedByAVG` / "Top Avg" card and `sortedByOPS` / "Top OPS" card
   blocks from `renderHome()`.
2. After the existing Season Record / Next Game / Last Game cards, append a
   **League Standings** card containing a table.

### Table

- Wrapped in `<div style="overflow-x:auto;">` (same pattern as the Stats full table)
  so the wide table scrolls horizontally on phones.
- Columns, left to right: **Team · vs Us · W · L · T · PF · PA · PD · PCT · GP**.
- Reuses the existing global `table` / `th` / `td` styles. Headers are static
  (not clickable — league order is fixed).
- The row whose team normalizes to `"icon"` is highlighted with a carolina-blue
  tint (e.g. inline `background: rgba(123,182,230,0.25)` on the `<tr>`).

### "vs Us" column

For each standings team, scan `DATA.schedule` for games with `status === "played"`
whose `opponent` fuzzy-matches the standings team name. For each match, render the
score plus a W/L badge using the existing `.badge.win` / `.badge.loss` classes
(e.g. `2-18 [L]`). Multiple meetings stack vertically in the cell. No match → empty cell.

### Fuzzy name matching

A helper normalizes a team name before comparison:

- lowercase
- strip a trailing day/league qualifier after a dash or en-dash
  (e.g. `"RawDogs – Thur"` → `"rawdogs"`, `"Kodiaks-MENS"` → `"kodiaks"`,
  `"Yap City – Men"` → `"yap city"`)
- remove remaining punctuation and collapse whitespace

Two names match if their normalized forms are equal. This resolves all current
cases (`RawDogs` ↔ `RawDogs – Thur`, `Kodiaks-Mens` ↔ `Kodiaks-MENS`,
`Dirtbags` ↔ `Dirtbags`, `Goon Squad` ↔ `Goon Squad`). A rare mismatch would
surface as a missing badge, which is caught during the weekly update.

## Weekly update workflow

1. Export/screenshot the league standings and save the PNG anywhere in the
   project folder (filename doesn't matter).
2. Tell Claude: *"standings updated"*.
3. Claude reads the image, rewrites `standings.teams` (team, W, L, T, PF, PA for
   every team, in order), and sets `standings.lastUpdated` to the snapshot date.
4. Refresh the page. (~1 minute.)

## Testing

- Manual: open `index.html`, confirm the standings table renders on Home, Icon row
  is highlighted, and the two played games (Dirtbags 2-18 L, RawDogs 3-18 L) appear
  as W/L badges in the vs-us column; Kodiaks (postponed) and Goon Squad (upcoming)
  show no badge.
- The existing Python test suite (`tests/`) covers `build_stats.py` / lineup PDFs,
  not the front-end; no change needed there. If `data.json` is validated anywhere,
  ensure the new `standings` key doesn't break it.

## Out of scope (YAGNI)

- No automated OCR pipeline — transcription is a manual Claude step.
- No clickable team links / per-team detail pages (the source image's blue links
  are not reproduced).
- No sorting controls on the standings table.
- No separate League tab.
