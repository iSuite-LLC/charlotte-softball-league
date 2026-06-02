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
