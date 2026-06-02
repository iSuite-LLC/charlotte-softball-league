# League Standings on Home Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the IMI league standings as a table on the Home tab (replacing the Top Avg / Top OPS leader cards), sourced from a weekly standings screenshot.

**Architecture:** Add a `standings` key to `data.json` (team + W/L/T/PF/PA only; GP/PD/PCT computed at render). Modify `renderHome()` in `index.html` to drop the two leader cards and append a standings table, with a fuzzy name-matcher that surfaces "vs us" results from the existing `schedule` data.

**Tech Stack:** Vanilla JS in a single `index.html`, JSON data file, Python (for nothing here — front-end only). Node is used once to unit-test the pure JS helpers.

---

## File Structure

- **Modify** `data.json` — add the `standings` object (data + snapshot date).
- **Modify** `index.html` — rewrite `renderHome()`: remove leader cards, add `normalizeTeamName()`, `computeStandingsRow()`, and standings-table rendering.
- **Create** `scripts/standings_helpers.test.mjs` — a tiny Node test that exercises the two pure helpers (`normalizeTeamName`, `computeStandingsRow`) without a browser. These helpers are also defined inline in `index.html`; this test guards their logic.

> Note: this folder is **not** a git repository. The "Commit" steps below are written as `git` commands per convention, but if `git` is unavailable just skip them — each task is still independently verifiable.

---

### Task 1: Seed the `standings` data in `data.json`

**Files:**
- Modify: `data.json` (add top-level `standings` key)

Transcribed from `League Standings 06.02.2026.png`, in the exact order shown. Only `team`, `W`, `L`, `T`, `PF`, `PA` are stored.

- [ ] **Step 1: Add the `standings` object**

Add this key to the top-level object in `data.json` (e.g. after `"season"`):

```json
"standings": {
  "lastUpdated": "2026-06-02",
  "teams": [
    { "team": "Ed's Dugout Drinkers", "W": 3, "L": 0, "T": 0, "PF": 56, "PA": 16 },
    { "team": "Kodiaks-MENS",         "W": 1, "L": 0, "T": 0, "PF": 25, "PA": 6 },
    { "team": "Slippery Slugs",       "W": 1, "L": 0, "T": 0, "PF": 21, "PA": 4 },
    { "team": "Back Door Sliders",    "W": 1, "L": 0, "T": 0, "PF": 18, "PA": 3 },
    { "team": "Boone Goons",          "W": 1, "L": 0, "T": 0, "PF": 7,  "PA": 0 },
    { "team": "Cobra Kai",            "W": 1, "L": 0, "T": 0, "PF": 20, "PA": 17 },
    { "team": "YankDeez",             "W": 1, "L": 0, "T": 0, "PF": 9,  "PA": 7 },
    { "team": "Dirtbags",             "W": 2, "L": 1, "T": 0, "PF": 39, "PA": 13 },
    { "team": "RawDogs – Thur",       "W": 1, "L": 1, "T": 0, "PF": 20, "PA": 17 },
    { "team": "Purple Cows",          "W": 1, "L": 1, "T": 0, "PF": 19, "PA": 19 },
    { "team": "Yap City – Men",       "W": 0, "L": 1, "T": 0, "PF": 17, "PA": 20 },
    { "team": "Thoinkees",            "W": 0, "L": 1, "T": 0, "PF": 5,  "PA": 10 },
    { "team": "Bad News Bears",       "W": 0, "L": 1, "T": 0, "PF": 0,  "PA": 7 },
    { "team": "Icon",                 "W": 0, "L": 2, "T": 0, "PF": 5,  "PA": 36 },
    { "team": "Goon Squad",           "W": 0, "L": 2, "T": 0, "PF": 10, "PA": 45 },
    { "team": "Rally Caps",           "W": 0, "L": 3, "T": 0, "PF": 12, "PA": 63 }
  ]
}
```

- [ ] **Step 2: Verify the JSON parses and the math reproduces the image**

Run:
```bash
python -c "import json; d=json.load(open('data.json')); t=[x for x in d['standings']['teams'] if x['team']=='Dirtbags'][0]; gp=t['W']+t['L']+t['T']; print('GP',gp,'PD',t['PF']-t['PA'],'PCT',round((t['W']+0.5*t['T'])/gp*100,2))"
```
Expected output: `GP 3 PD 26 PCT 66.67` (matches the image's Dirtbags row: GP 3, PD 26, 66.67%).

- [ ] **Step 3: Commit**

```bash
git add data.json
git commit -m "data: add league standings (2026-06-02 snapshot)"
```

---

### Task 2: Pure helpers + Node unit test

**Files:**
- Create: `scripts/standings_helpers.test.mjs`

This task writes a standalone, browser-free copy of the two pure helpers and tests them. In Task 3 the *same* functions are pasted into `index.html`. Keeping a tested reference copy here means the logic is verified even though `index.html` has no test harness.

- [ ] **Step 1: Write the failing test (with the helpers it tests)**

Create `scripts/standings_helpers.test.mjs`:

```javascript
import assert from "node:assert";

// --- Helpers under test (mirrored verbatim into index.html in Task 3) ---

// Normalize a team name for fuzzy matching: lowercase, drop a trailing
// qualifier after a dash/en-dash (e.g. "– Thur", "-MENS"), strip remaining
// punctuation, collapse whitespace.
export function normalizeTeamName(name) {
  if (!name) return "";
  let s = String(name).toLowerCase();
  s = s.split(/\s*[–-]\s*/)[0];          // keep text before first dash/en-dash
  s = s.replace(/[^a-z0-9 ]/g, " ");      // punctuation -> space
  s = s.replace(/\s+/g, " ").trim();      // collapse whitespace
  return s;
}

// Given a stored standings team row, return it augmented with computed fields.
export function computeStandingsRow(t) {
  const GP = t.W + t.L + t.T;
  const PD = t.PF - t.PA;
  const PCT = GP > 0 ? (t.W + 0.5 * t.T) / GP : 0;
  return { ...t, GP, PD, PCT };
}

// --- Tests ---

// normalizeTeamName: the real-world mismatches from the schedule
assert.strictEqual(normalizeTeamName("RawDogs – Thur"), "rawdogs");
assert.strictEqual(normalizeTeamName("RawDogs"), "rawdogs");
assert.strictEqual(normalizeTeamName("Kodiaks-MENS"), "kodiaks");
assert.strictEqual(normalizeTeamName("Kodiaks-Mens"), "kodiaks");
assert.strictEqual(normalizeTeamName("Yap City – Men"), "yap city");
assert.strictEqual(normalizeTeamName("Dirtbags"), "dirtbags");
assert.strictEqual(normalizeTeamName("Goon Squad"), "goon squad");
assert.strictEqual(normalizeTeamName("Ed's Dugout Drinkers"), "ed s dugout drinkers");
assert.strictEqual(normalizeTeamName(""), "");
assert.strictEqual(normalizeTeamName(null), "");

// matching is symmetric on normalized forms
assert.strictEqual(
  normalizeTeamName("RawDogs") === normalizeTeamName("RawDogs – Thur"),
  true
);

// computeStandingsRow: reproduces image values
const dirt = computeStandingsRow({ team: "Dirtbags", W: 2, L: 1, T: 0, PF: 39, PA: 13 });
assert.strictEqual(dirt.GP, 3);
assert.strictEqual(dirt.PD, 26);
assert.strictEqual(Math.round(dirt.PCT * 10000) / 100, 66.67);

const eds = computeStandingsRow({ team: "Ed's", W: 3, L: 0, T: 0, PF: 56, PA: 16 });
assert.strictEqual(eds.PCT, 1);

const icon = computeStandingsRow({ team: "Icon", W: 0, L: 2, T: 0, PF: 5, PA: 36 });
assert.strictEqual(icon.PCT, 0);
assert.strictEqual(icon.PD, -31);

// zero games played -> no divide-by-zero
const fresh = computeStandingsRow({ team: "New", W: 0, L: 0, T: 0, PF: 0, PA: 0 });
assert.strictEqual(fresh.GP, 0);
assert.strictEqual(fresh.PCT, 0);

console.log("standings_helpers: all assertions passed");
```

- [ ] **Step 2: Run the test to verify it passes**

Run:
```bash
node scripts/standings_helpers.test.mjs
```
Expected: `standings_helpers: all assertions passed` and exit code 0.

(If the helper logic were wrong, `node:assert` throws an `AssertionError` and exits non-zero. The test and implementation are written together here because the implementation is a few lines of pure logic with no meaningful intermediate failing state to stage.)

- [ ] **Step 3: Commit**

```bash
git add scripts/standings_helpers.test.mjs
git commit -m "test: standings name-normalization and row-computation helpers"
```

---

### Task 3: Render standings on Home, remove leader cards

**Files:**
- Modify: `index.html` — `renderHome()` (currently lines ~229-293) and add two helper functions near the other top-level helpers (e.g. after `fmtTime`, ~line 168).

- [ ] **Step 1: Add the two pure helpers to `index.html`**

Insert after the `fmtTime` function (before `toast`), so they're in scope for `renderHome`:

```javascript
// Normalize a team name for fuzzy matching: lowercase, drop a trailing
// qualifier after a dash/en-dash, strip punctuation, collapse whitespace.
function normalizeTeamName(name) {
  if (!name) return "";
  let s = String(name).toLowerCase();
  s = s.split(/\s*[–-]\s*/)[0];
  s = s.replace(/[^a-z0-9 ]/g, " ");
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

// Augment a stored standings row with computed GP / PD / PCT.
function computeStandingsRow(t) {
  const GP = t.W + t.L + t.T;
  const PD = t.PF - t.PA;
  const PCT = GP > 0 ? (t.W + 0.5 * t.T) / GP : 0;
  return { ...t, GP, PD, PCT };
}
```

- [ ] **Step 2: Remove the leader-card logic from `renderHome()`**

In `renderHome()`, delete the two leader-computation blocks:

```javascript
  // Top stat leaders
  const players = Object.entries(stats_summary || {});
  const sortedByAVG = [...players].filter(([, s]) => s.AB >= 1)
                                   .sort((a, b) => b[1].AVG - a[1].AVG).slice(0, 3);
  const sortedByOPS = [...players].filter(([, s]) => s.AB >= 1)
                                   .sort((a, b) => b[1].OPS - a[1].OPS).slice(0, 3);
```

and the two rendering blocks:

```javascript
  if (sortedByAVG.length) {
    html += `<div class="card"><h3>Top Avg</h3>`;
    sortedByAVG.forEach(([nick, s]) => {
      html += `<div class="row"><span>${nick}</span><span>${s.AVG.toFixed(3)}</span></div>`;
    });
    html += `</div>`;
  }
  if (sortedByOPS.length) {
    html += `<div class="card"><h3>Top OPS</h3>`;
    sortedByOPS.forEach(([nick, s]) => {
      html += `<div class="row"><span>${nick}</span><span>${s.OPS.toFixed(3)}</span></div>`;
    });
    html += `</div>`;
  }
```

Also update the destructure at the top of `renderHome()` — `stats_summary` is no longer used by Home, so change:

```javascript
  const { season, schedule, stats_summary } = DATA;
```
to:
```javascript
  const { season, schedule } = DATA;
```

- [ ] **Step 3: Append the standings table inside `renderHome()`**

Immediately before the final `home.innerHTML = html;` line, add:

```javascript
  // League standings
  const standings = DATA.standings;
  if (standings && Array.isArray(standings.teams) && standings.teams.length) {
    // Map normalized opponent name -> array of played-game result strings.
    const playedByOpp = {};
    schedule.filter(g => g.status === "played").forEach(g => {
      const key = normalizeTeamName(g.opponent);
      if (!key) return;
      const r = g.result || {};
      (playedByOpp[key] = playedByOpp[key] || []).push(r);
    });

    const cols = [
      { key: "W" }, { key: "L" }, { key: "T" },
      { key: "PF" }, { key: "PA" }, { key: "PD" },
      { key: "PCT" }, { key: "GP" },
    ];

    let rows = "";
    standings.teams.forEach(raw => {
      const t = computeStandingsRow(raw);
      const isUs = normalizeTeamName(t.team) === "icon";
      const meetings = playedByOpp[normalizeTeamName(t.team)] || [];
      const vsUs = meetings.map(r => {
        const cls = r.outcome === "W" ? "win" : "loss";
        return `${r.score || "?"} <span class="badge ${cls}">${r.outcome || "?"}</span>`;
      }).join("<br>");
      const trStyle = isUs ? ` style="background:rgba(123,182,230,0.25);font-weight:600;"` : "";
      rows += `<tr${trStyle}>
        <td>${t.team}</td>
        <td>${vsUs}</td>
        ${cols.map(c => {
          const v = t[c.key];
          const cell = c.key === "PCT" ? (v * 100).toFixed(2) + "%" : v;
          return `<td>${cell}</td>`;
        }).join("")}
      </tr>`;
    });

    const header = ["TEAM", "VS US", "W", "L", "T", "PF", "PA", "PD", "PCT", "GP"];
    html += `<div class="card">
      <h3>League Standings${standings.lastUpdated ? ` · ${standings.lastUpdated}` : ""}</h3>
      <div style="overflow-x:auto;">
        <table>
          <thead><tr>${header.map(h => `<th>${h}</th>`).join("")}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
  }
```

- [ ] **Step 4: Verify the helpers still pass their Node test (no drift)**

The functions pasted into `index.html` must match the tested copy. Re-run:
```bash
node scripts/standings_helpers.test.mjs
```
Expected: `standings_helpers: all assertions passed`.

Then visually diff the two function bodies in `index.html` against `scripts/standings_helpers.test.mjs` to confirm they're identical (ignoring the `export` keyword).

- [ ] **Step 5: Manually verify in the browser**

Open `index.html` in a browser (or `python -m http.server` in the project folder, then visit the page so `fetch` works — `file://` may block `fetch`).

Run:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000/` and confirm on the **Home** tab:
- A "League Standings · 2026-06-02" card appears where Top Avg / Top OPS used to be.
- 16 team rows in the image's order; **Icon** row is highlighted (light blue) and bold.
- **VS US** column: Dirtbags shows `2-18 [L]`, RawDogs – Thur shows `3-18 [L]`; all other rows (incl. Kodiaks-MENS and Goon Squad) are blank.
- PCT column reads `100.00%` for Ed's, `66.67%` for Dirtbags, `0.00%` for Icon.
- Top Avg / Top OPS cards are gone from Home; Stats tab still shows its leaders unchanged.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat: show league standings on Home tab, replacing stat-leader cards"
```

---

## Self-Review

**Spec coverage:**
- Data model (`standings` key, 6 fields, computed GP/PD/PCT) → Task 1 + `computeStandingsRow` (Tasks 2/3). ✓
- Separate `standings.lastUpdated` independent of `season.lastUpdated` → Task 1 (header line uses `standings.lastUpdated` only; `season.lastUpdated` untouched). ✓
- Remove Top Avg / Top OPS → Task 3 Step 2. ✓
- Standings table on Home, league order preserved, columns Team·vsUs·W·L·T·PF·PA·PD·PCT·GP, overflow-x scroll, existing table styles → Task 3 Step 3. ✓
- Icon row highlighted (carolina tint) → Task 3 Step 3 (`isUs`). ✓
- vs-us column with fuzzy match + W/L badges, stacking multiple meetings → Task 3 Step 3 (`playedByOpp`, `meetings.map`). ✓
- Fuzzy `normalizeTeamName` (lowercase, strip dash qualifier, punctuation, whitespace) → Tasks 2/3, tested against all current cases. ✓
- Weekly workflow → documented in the spec; no code task needed. ✓
- Out-of-scope items (no OCR, no team links, no sorting, no separate tab) → respected; none added. ✓

**Placeholder scan:** No TBD/TODO/"handle edge cases" — every code step shows complete code. ✓

**Type consistency:** `normalizeTeamName` and `computeStandingsRow` have identical signatures/bodies in Tasks 2 and 3. Row objects use `W/L/T/PF/PA` (stored) and `GP/PD/PCT` (computed) consistently. `result` objects use `.score`/`.outcome` matching the existing `renderSchedule` usage. ✓
