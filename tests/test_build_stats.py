"""Tests for stats derivation."""
from scripts.build_stats import compute_player_summary


def test_basic_line():
    """3-for-4 with a walk, double, HR, 2 RBI -> AVG .750, OBP .800, SLG 1.500."""
    lines = [{
        "PA": 5, "AB": 4, "1B": 1, "2B": 1, "3B": 0, "HR": 1,
        "BB": 1, "K": 0, "RBI": 2, "R": 1, "errors": 0,
    }]
    summary = compute_player_summary(lines)
    assert summary["G"] == 1
    assert summary["AB"] == 4
    assert summary["H"] == 3
    assert summary["AVG"] == 0.750
    assert summary["OBP"] == 0.800   # (3 + 1) / (4 + 1)
    assert summary["SLG"] == 1.750   # (1 + 2 + 0 + 4) / 4  [TB=7, AB=4]
    assert summary["OPS"] == round(0.800 + 1.750, 3)
    assert summary["HR"] == 1
    assert summary["RBI"] == 2


def test_zero_ab():
    """Player with all BBs returns .000 AVG and SLG, not NaN/error."""
    lines = [{"PA": 2, "AB": 0, "1B": 0, "2B": 0, "3B": 0, "HR": 0,
              "BB": 2, "K": 0, "RBI": 0, "R": 0, "errors": 0}]
    summary = compute_player_summary(lines)
    assert summary["AVG"] == 0.0
    assert summary["SLG"] == 0.0
    assert summary["OBP"] == 1.0  # 2 walks in 2 PA


def test_multi_game_aggregate():
    """Two games: line1 (1-for-3) + line2 (2-for-4) -> 3-for-7 = .429."""
    lines = [
        {"PA": 3, "AB": 3, "1B": 1, "2B": 0, "3B": 0, "HR": 0,
         "BB": 0, "K": 0, "RBI": 0, "R": 0, "errors": 0},
        {"PA": 4, "AB": 4, "1B": 1, "2B": 1, "3B": 0, "HR": 0,
         "BB": 0, "K": 0, "RBI": 1, "R": 1, "errors": 0},
    ]
    summary = compute_player_summary(lines)
    assert summary["G"] == 2
    assert summary["AB"] == 7
    assert summary["H"] == 3
    assert summary["AVG"] == round(3/7, 3)
