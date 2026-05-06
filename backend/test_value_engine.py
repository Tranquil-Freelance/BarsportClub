"""
Comprehensive validation test for value_engine.py (Phases 2, 3, 4).
Run with: python backend/test_value_engine.py
"""
import math
import sys
import os

# Add backend/app to path so we can import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Mock SQLAlchemy imports since we're testing pure functions
import types

mock_sqlalchemy = types.ModuleType("sqlalchemy")
mock_sqlalchemy.text = lambda x: x

mock_async = types.ModuleType("sqlalchemy.ext.asyncio")
mock_async.AsyncSession = type("AsyncSession", (), {})

sys.modules["sqlalchemy"] = mock_sqlalchemy
sys.modules["sqlalchemy.ext.asyncio"] = mock_async
sys.modules["sqlalchemy.orm"] = types.ModuleType("sqlalchemy.orm")

# Now import all pure functions
from services.value_engine import (
    poisson_probability,
    generate_score_matrix,
    derive_standard_markets,
    derive_asian_handicap_prob,
    remove_margin_2way,
    remove_margin_3way,
    calculate_edge_metrics,
    evaluate_all_markets,
    calculate_stability,
    build_ai_features,
    generate_ai_risk_prompt,
    filter_and_rank_picks,
)


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 TESTS
# ═══════════════════════════════════════════════════════════════════════════


def test_poisson():
    print("=== Poisson PMF ===")
    for k in range(5):
        p = poisson_probability(1.5, k)
        print(f"  P(X={k} | lam=1.5) = {p:.6f}")

    total = sum(poisson_probability(1.5, k) for k in range(7))
    print(f"  Sum k=0..6 = {total:.6f}  (expect ~0.998)")
    assert abs(total - 0.998) < 0.01

    # Edge cases
    assert poisson_probability(0, 0) == 0.0
    assert poisson_probability(1.5, -1) == 0.0
    print("  Poisson OK\n")


def test_score_matrix():
    print("=== Score Matrix (lam_h=1.8, lam_a=1.2) ===")
    sm = generate_score_matrix(1.8, 1.2)

    matrix_sum = sum(sm["matrix"].values())
    total_sum = sum(sm["P_total"].values())
    diff_sum = sum(sm["P_diff"].values())

    print(f"  Matrix entries: {len(sm['matrix'])}")
    print(f"  Sum(matrix)  = {matrix_sum:.6f}")
    print(f"  Sum(P_total) = {total_sum:.6f}")
    print(f"  Sum(P_diff)  = {diff_sum:.6f}")

    assert abs(matrix_sum - 1.0) < 0.01
    assert abs(total_sum - 1.0) < 0.01
    assert abs(diff_sum - 1.0) < 0.01

    p_0_0 = poisson_probability(1.8, 0) * poisson_probability(1.2, 0)
    assert abs(sm["matrix"].get((0, 0), 0) - p_0_0) < 1e-10
    print(f"  P(0,0) = {p_0_0:.6f} (verified)")
    print("  Score Matrix OK\n")


def test_standard_markets():
    print("=== Standard Markets ===")
    sm = generate_score_matrix(1.8, 1.2)
    mk = derive_standard_markets(sm)

    for k, v in mk.items():
        print(f"  {k}: {v}")

    s1 = mk["home_win"] + mk["draw"] + mk["away_win"]
    s2 = mk["btts_yes"] + mk["btts_no"]
    s3 = mk["over_2_5"] + mk["under_2_5"]
    print(f"  1X2 sum  = {s1:.6f}")
    print(f"  BTTS sum = {s2:.6f}")
    print(f"  O/U sum  = {s3:.6f}")

    assert abs(s1 - 1.0) < 0.01
    assert abs(s2 - 1.0) < 0.01
    assert abs(s3 - 1.0) < 0.01
    print("  Standard Markets OK\n")


def test_asian_handicap():
    print("=== Asian Handicap ===")
    sm = generate_score_matrix(1.8, 1.2)

    for line in [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]:
        ah = derive_asian_handicap_prob(sm, line)
        s = ah["P_win"] + ah["P_push"] + ah["P_loss"]
        print(f"  line={line:+5.2f}: win={ah['P_win']:.4f} push={ah['P_push']:.4f} loss={ah['P_loss']:.4f} (sum={s:.4f})")
        assert abs(s - 1.0) < 0.01

    # Quarter-line verification: -0.25 = average of 0.0 and -0.5
    ah_m025 = derive_asian_handicap_prob(sm, -0.25)
    ah_0   = derive_asian_handicap_prob(sm, 0.0)
    ah_m05 = derive_asian_handicap_prob(sm, -0.5)
    expected_win = 0.5 * ah_0["P_win"] + 0.5 * ah_m05["P_win"]
    print(f"\n  Quarter-line check (-0.25): actual_win={ah_m025['P_win']:.4f} expected_win={expected_win:.4f}")
    assert abs(ah_m025["P_win"] - expected_win) < 0.001

    print("  Asian Handicap OK\n")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3 TESTS
# ═══════════════════════════════════════════════════════════════════════════


def test_remove_margin_2way():
    print("=== remove_margin_2way ===")
    # Fair coin: odds 2.00 / 2.00 → no margin
    res = remove_margin_2way(2.00, 2.00)
    print(f"  Fair coin (2.00, 2.00): p1={res['p1_true']} p2={res['p2_true']} margin={res['margin']}")
    assert abs(res["p1_true"] - 0.5) < 1e-6
    assert abs(res["p2_true"] - 0.5) < 1e-6
    assert abs(res["margin"] - 0.0) < 1e-6

    # Typical O/U: 1.91 / 1.91 → ~4.7% vig
    res = remove_margin_2way(1.91, 1.91)
    print(f"  Bookie O/U (1.91, 1.91): p1={res['p1_true']} p2={res['p2_true']} margin={res['margin']}")
    implied = 1.0 / 1.91
    expected_margin = 2 * implied - 1.0
    assert abs(res["margin"] - expected_margin) < 1e-6
    assert abs(res["p1_true"] + res["p2_true"] - 1.0) < 1e-6

    # Edge case: odds <= 1.0
    res = remove_margin_2way(1.0, 2.0)
    print(f"  Edge (1.0, 2.0): p1={res['p1_true']} p2={res['p2_true']} margin={res['margin']}")
    assert res["p1_true"] is None
    assert res["margin"] is None

    res = remove_margin_2way(0.5, 2.0)
    assert res["p1_true"] is None

    print("  remove_margin_2way OK\n")


def test_remove_margin_3way():
    print("=== remove_margin_3way ===")
    # Typical 1X2: home=2.10, draw=3.40, away=3.80
    res = remove_margin_3way(2.10, 3.40, 3.80)
    s = res["p1_true"] + res["pX_true"] + res["p2_true"]
    print(f"  1X2 (2.10, 3.40, 3.80): p1={res['p1_true']:.4f} pX={res['pX_true']:.4f} p2={res['p2_true']:.4f}")
    print(f"  Sum = {s:.6f}  margin = {res['margin']:.4f}")
    assert abs(s - 1.0) < 2e-5  # tolerate rounding to 6dp on 3 values
    assert res["margin"] > 0.0

    # Fair odds: all 3.00 → no margin
    res = remove_margin_3way(3.00, 3.00, 3.00)
    print(f"  Fair 1X2 (3.00, 3.00, 3.00): p1={res['p1_true']:.4f} margin={res['margin']:.4f}")
    assert abs(res["p1_true"] - 1.0/3.0) < 1e-6
    assert abs(res["margin"]) < 1e-6

    # Edge case: invalid odds
    res = remove_margin_3way(1.0, 3.00, 3.00)
    assert res["p1_true"] is None

    print("  remove_margin_3way OK\n")


def test_calculate_edge_metrics():
    print("=== calculate_edge_metrics ===")
    # Fair coin: p_model=0.55, odds=2.00, p_book=0.50
    res = calculate_edge_metrics(0.55, 2.00, p_book=0.50)
    print(f"  p_model=0.55 odds=2.00 p_book=0.50: ev={res['ev_base']} diff={res['diff']}")
    assert abs(res["ev_base"] - 0.10) < 1e-6  # (0.55 * 2.00) - 1 = 0.10
    assert abs(res["diff"] - 0.05) < 1e-6     # 0.55 - 0.50 = 0.05

    # No p_book
    res = calculate_edge_metrics(0.55, 2.00)
    print(f"  No p_book: ev={res['ev_base']} diff={res['diff']}")
    assert abs(res["ev_base"] - 0.10) < 1e-6
    assert res["diff"] is None

    # Edge case: odds <= 1.0
    res = calculate_edge_metrics(0.80, 1.0)
    print(f"  Odds=1.0: ev={res['ev_base']} diff={res['diff']}")
    assert res["ev_base"] is None

    # Edge case: p_model <= 0
    res = calculate_edge_metrics(0.0, 2.00)
    assert res["ev_base"] is None

    print("  calculate_edge_metrics OK\n")


def test_evaluate_all_markets():
    print("=== evaluate_all_markets ===")
    # Build model_probs as derive_standard_markets would
    sm = generate_score_matrix(1.8, 1.2)
    mk = derive_standard_markets(sm)
    model_probs = {**mk, "_score_matrix": sm}

    # Build realistic real_odds
    real_odds = {
        "1x2": {"home": 2.10, "draw": 3.40, "away": 3.80},
        "over_under": {"line": 2.5, "over": 1.91, "under": 1.91},
        "btts": {"yes": 1.80, "no": 2.00},
        "asian_handicap": {
            "0.0":  {"home": 1.85, "away": 1.95},
            "-0.5": {"home": 2.00, "away": 1.80},
            "-0.25": {"home": 1.90, "away": 1.90},
        },
    }

    results = evaluate_all_markets(model_probs, real_odds)

    # Print all results
    for key, val in sorted(results.items()):
        print(f"  {key:20s}: p_model={val['p_model']:.4f}  p_book={val['p_book']}  ev={val['ev_base']}  diff={val['diff']}  odds={val['odds']}")

    # ── Invariant checks ────────────────────────────────────────────────
    expected_keys = [
        "1x2_home", "1x2_draw", "1x2_away",
        "over_2.5", "under_2.5",
        "btts_yes", "btts_no",
        "ah_0.0_home", "ah_0.0_away",
        "ah_-0.5_home", "ah_-0.5_away",
        "ah_-0.25_home", "ah_-0.25_away",
    ]
    for k in expected_keys:
        assert k in results, f"Missing key: {k}"

    # 1X2 p_book sum ≈ 1.0 (tolerate rounding to 6dp)
    p1 = results["1x2_home"]["p_book"]
    pX = results["1x2_draw"]["p_book"]
    p2 = results["1x2_away"]["p_book"]
    p1x2_sum = p1 + pX + p2
    assert abs(p1x2_sum - 1.0) < 2e-5, f"1X2 p_book sum = {p1x2_sum}"

    # O/U p_book sum ≈ 1.0
    p_over  = results["over_2.5"]["p_book"]
    p_under = results["under_2.5"]["p_book"]
    ou_sum = p_over + p_under
    assert abs(ou_sum - 1.0) < 1e-5, f"O/U p_book sum = {ou_sum}"

    # BTTS p_book sum ≈ 1.0
    p_yes = results["btts_yes"]["p_book"]
    p_no  = results["btts_no"]["p_book"]
    btts_sum = p_yes + p_no
    assert abs(btts_sum - 1.0) < 1e-5, f"BTTS p_book sum = {btts_sum}"

    # AH p_book sum ≈ 1.0
    for line_slug in ["0.0", "-0.5", "-0.25"]:
        home_key = f"ah_{line_slug}_home"
        away_key = f"ah_{line_slug}_away"
        if home_key in results and results[home_key]["p_book"] is not None:
            s = results[home_key]["p_book"] + results[away_key]["p_book"]
            assert abs(s - 1.0) < 2e-5, f"AH {line_slug} p_book sum = {s}"

    # EV formula verification
    home_model = results["1x2_home"]["p_model"]
    home_ev    = results["1x2_home"]["ev_base"]
    expected_ev = (home_model * real_odds["1x2"]["home"]) - 1.0
    assert abs(home_ev - expected_ev) < 1e-6, f"EV mismatch: {home_ev} vs {expected_ev}"

    print("  evaluate_all_markets OK\n")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4 TESTS
# ═══════════════════════════════════════════════════════════════════════════


def test_calculate_stability():
    print("=== calculate_stability ===")
    # Consistent team: low std dev
    stable = calculate_stability([0.3, 0.2, 0.4, 0.1, 0.3])
    print(f"  Stable team [0.3,0.2,0.4,0.1,0.3]: std={stable}")
    assert stable < 0.2, f"Expected low std dev, got {stable}"

    # Erratic team: high std dev
    erratic = calculate_stability([1.5, -1.2, 2.0, -1.8, 0.5])
    print(f"  Erratic team [1.5,-1.2,2.0,-1.8,0.5]: std={erratic}")
    assert erratic > 1.0, f"Expected high std dev, got {erratic}"

    # Edge case: < 2 elements → default penalty
    empty = calculate_stability([])
    print(f"  Empty array: {empty}")
    assert empty == 1.5

    single = calculate_stability([0.5])
    print(f"  Single element: {single}")
    assert single == 1.5

    # Custom default penalty
    custom = calculate_stability([], default_penalty=2.0)
    assert custom == 2.0

    print("  calculate_stability OK\n")


def test_build_ai_features():
    print("=== build_ai_features ===")
    match_context = {
        "lambda_home": 1.8,
        "lambda_away": 1.2,
    }
    market_eval = {
        "p_model": 0.5119,
        "p_book": 0.4608,
        "ev_base": 0.0749,
        "diff": 0.0511,
        "odds": 2.10,
        "_market_type": "1x2_home",
    }
    features = build_ai_features(match_context, market_eval, 0.12, 0.45)

    # Verify exact key set
    expected_keys = {
        "lam_home", "lam_away", "p_model", "p_book",
        "ev_base", "diff", "stability_home", "stability_away",
        "market_type", "odds", "variance_match",
    }
    assert set(features.keys()) == expected_keys, f"Key mismatch: {set(features.keys()) ^ expected_keys}"

    # Verify values
    assert features["lam_home"] == 1.8
    assert features["lam_away"] == 1.2
    assert features["variance_match"] == 3.0  # 1.8 + 1.2
    assert features["stability_home"] == 0.12
    assert features["stability_away"] == 0.45
    assert features["market_type"] == "1x2_home"

    # Edge: None values should be converted to 0.0
    market_eval_none = {
        "p_model": None,
        "p_book": None,
        "ev_base": None,
        "diff": None,
        "odds": None,
        "_market_type": "test",
    }
    features_none = build_ai_features(match_context, market_eval_none, 0.0, 0.0)
    assert features_none["p_model"] == 0.0
    assert features_none["odds"] == 0.0

    print(f"  variance_match={features['variance_match']} market_type={features['market_type']}")
    print("  build_ai_features OK\n")


def test_generate_ai_risk_prompt():
    print("=== generate_ai_risk_prompt ===")
    features = {
        "lam_home": 1.8,
        "lam_away": 1.2,
        "p_model": 0.5119,
        "p_book": 0.4608,
        "ev_base": 0.0749,
        "diff": 0.0511,
        "stability_home": 0.12,
        "stability_away": 0.45,
        "market_type": "1x2_home",
        "odds": 2.10,
        "variance_match": 3.0,
    }
    messages = generate_ai_risk_prompt(features)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    # System prompt should mention risk manager
    assert "quantitative betting risk manager" in messages[0]["content"]

    # User prompt should contain feature values
    user_content = messages[1]["content"]
    assert "1.8" in user_content
    assert "0.5119" in user_content
    assert "variance_match" in user_content
    assert "3.0" in user_content

    print(f"  System prompt length: {len(messages[0]['content'])} chars")
    print(f"  User prompt length: {len(messages[1]['content'])} chars")
    print("  generate_ai_risk_prompt OK\n")


def test_filter_and_rank_picks():
    print("=== filter_and_rank_picks ===")
    # Simulate 10 AI-evaluated markets with varying ev_final, p_model, stabilities
    ai_markets = [
        # (key, ev_final, p_model, stab_h, stab_a)
        ("over_2.5",    0.0963, 0.5740, 0.12, 0.45),  # high EV, high prob, stable home
        ("btts_yes",    0.0514, 0.5841, 0.12, 0.45),
        ("1x2_home",    0.0749, 0.5119, 0.12, 0.45),  # positive EV, passes filter
        ("ah_-0.5_home", 0.0237, 0.5119, 0.12, 0.45),  # below min_ev=0.05 → filtered
        ("1x2_away",   -0.0350, 0.2539, 1.50, 1.50),  # negative EV → filtered
        ("ah_0.0_home", -0.0531, 0.5119, 0.12, 0.45),  # negative EV → filtered
        ("under_2.5",  -0.1917, 0.4232, 0.12, 0.45),   # negative EV → filtered
        ("btts_no",    -0.1682, 0.4159, 0.12, 0.45),   # negative EV → filtered
        ("1x2_draw",   -0.2133, 0.2314, 0.12, 0.45),   # negative EV + below min_p_model
        ("ah_-0.25_home", -0.0275, 0.5119, 0.12, 0.45), # below min_ev → filtered
    ]

    markets = [
        {
            "market_key": k,
            "ev_final": ev,
            "p_model": pm,
            "stability_home": sh,
            "stability_away": sa,
        }
        for k, ev, pm, sh, sa in ai_markets
    ]

    picks = filter_and_rank_picks(markets, min_ev=0.05, min_p_model=0.35, max_results=5)

    # Should have 3 picks: over_2.5 (ev=0.0963), 1x2_home (ev=0.0749), btts_yes (ev=0.0514)
    print(f"  Total picks: {len(picks)}")
    for p in picks:
        print(f"    Rank {p['rank']}: {p['market_key']:15s} ev={p['ev_final']:.4f} score={p['score']:.4f} "
              f"priority={p['market_priority']} stab=({p['stability_home']:.2f},{p['stability_away']:.2f})")

    assert len(picks) == 3, f"Expected 3 picks, got {len(picks)}"

    # Rank 1 should be highest score (over_2.5 has ev=0.0963 with avg_stability ~0.285)
    # score = ev * (1.0 / avg_stability) = 0.0963 * (1.0 / 0.285) ≈ 0.338
    assert picks[0]["market_key"] == "over_2.5", f"Rank 1 should be over_2.5, got {picks[0]['market_key']}"
    assert picks[0]["rank"] == 1

    # Verify descending score order
    for i in range(len(picks) - 1):
        assert picks[i]["score"] >= picks[i + 1]["score"], (
            f"Score order violation at {i}: {picks[i]['score']} < {picks[i+1]['score']}"
        )

    # Test with no passing markets
    no_picks = filter_and_rank_picks(markets, min_ev=1.0)  # unreachable threshold
    assert no_picks == [], f"Expected empty list, got {no_picks}"
    print("  Empty result on unreachable threshold: OK")

    # Test with None ev_final
    none_markets = [{"market_key": "test", "ev_final": None, "p_model": 0.5, "stability_home": 0.1, "stability_away": 0.1}]
    none_picks = filter_and_rank_picks(none_markets)
    assert none_picks == [], f"Expected empty for None ev_final, got {none_picks}"
    print("  None ev_final handled: OK")

    # Test priority tie-break: same score → over_under before BTTS before 1x2
    tie_markets = [
        {"market_key": "1x2_home",   "ev_final": 0.10, "p_model": 0.50,
         "stability_home": 0.1, "stability_away": 0.1},
        {"market_key": "over_2.5",   "ev_final": 0.10, "p_model": 0.50,
         "stability_home": 0.1, "stability_away": 0.1},
        {"market_key": "btts_yes",   "ev_final": 0.10, "p_model": 0.50,
         "stability_home": 0.1, "stability_away": 0.1},
    ]
    tie_picks = filter_and_rank_picks(tie_markets, min_ev=0.05, min_p_model=0.35, max_results=3)
    # Same score → priority order: over_under(0) → btts(1) → 1x2(4)
    assert tie_picks[0]["market_key"] == "over_2.5", f"Priority fail: {tie_picks[0]['market_key']}"
    assert tie_picks[1]["market_key"] == "btts_yes", f"Priority fail: {tie_picks[1]['market_key']}"
    assert tie_picks[2]["market_key"] == "1x2_home", f"Priority fail: {tie_picks[2]['market_key']}"
    print("  Priority tie-break: over_under > btts > 1x2 verified")

    print("  filter_and_rank_picks OK\n")


# ═══════════════════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Phase 2
    test_poisson()
    test_score_matrix()
    test_standard_markets()
    test_asian_handicap()
    # Phase 3
    test_remove_margin_2way()
    test_remove_margin_3way()
    test_calculate_edge_metrics()
    test_evaluate_all_markets()
    # Phase 4
    test_calculate_stability()
    test_build_ai_features()
    test_generate_ai_risk_prompt()
    test_filter_and_rank_picks()
    print("=== ALL TESTS PASSED ===")
