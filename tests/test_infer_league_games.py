from scripts.infer_league_games import infer

Z = lambda t: dict(team=t, W=0, L=0, T=0, PF=0, PA=0)
NEW = [dict(team=t, W=w, L=l, T=0, PF=f, PA=a) for t, w, l, f, a in [
    ("Gamecocks", 1, 0, 19, 2), ("Brew Jays", 1, 0, 12, 3), ("Goin' Yard", 1, 0, 12, 7),
    ("2 Out Terrors (Black)", 1, 0, 16, 13), ("Farm Bureau Protech's", 1, 0, 17, 15),
    ("Vandelay Industries", 1, 1, 35, 18), ("Last Minute", 0, 0, 0, 0),
    ("Kekambas", 0, 1, 15, 17), ("Hoffman Building Technologies", 0, 2, 10, 24),
    ("Icon", 0, 2, 4, 41)]]
PREV = [Z(t["team"]) for t in NEW if t["team"] != "Last Minute"]
OURS = [dict(a="Vandelay Industries", a_score=22, b="Icon", b_score=2),
        dict(a="Gamecocks", a_score=19, b="Icon", b_score=2)]

def test_fall_week1_fully_resolved():
    games, unresolved = infer(PREV, NEW, "2026-10-12", OURS)
    assert unresolved == {}
    got = {(g["a"], g["a_score"], g["b"], g["b_score"]) for g in games}
    assert got == {("2 Out Terrors (Black)", 16, "Vandelay Industries", 13),
                   ("Farm Bureau Protech's", 17, "Kekambas", 15),
                   ("Brew Jays", 12, "Hoffman Building Technologies", 3),
                   ("Goin' Yard", 12, "Hoffman Building Technologies", 7)}

def test_ambiguous_left_unresolved():
    new = [dict(team="A", W=1, L=0, T=0, PF=5, PA=3), dict(team="B", W=1, L=0, T=0, PF=5, PA=3),
           dict(team="C", W=0, L=1, T=0, PF=3, PA=5), dict(team="D", W=0, L=1, T=0, PF=3, PA=5)]
    games, unresolved = infer([Z(t["team"]) for t in new], new, "2026-01-01")
    assert games == [] and set(unresolved) == {"A", "B", "C", "D"}
