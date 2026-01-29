"""
Tests for DID-HAD package.

Compares Python implementation against known Stata outputs.
"""

import pytest
import numpy as np
import pandas as pd

from did_had import DidHad


# Expected Stata outputs (from the official did_had package)
STATA_EFFECTS = {
    1: {"estimate": 4.28198, "se": 0.55814, "ci_lower": 2.71751, "ci_upper": 4.90538, "bw": 0.36133, "n_in_bw": 371},
    2: {"estimate": 3.59260, "se": 0.66675, "ci_lower": 2.02563, "ci_upper": 4.63925, "bw": 0.27104, "n_in_bw": 282},
    3: {"estimate": 4.25466, "se": 0.67544, "ci_lower": 2.71354, "ci_upper": 5.36123, "bw": 0.31407, "n_in_bw": 324},
    4: {"estimate": 3.97161, "se": 0.68909, "ci_lower": 2.35019, "ci_upper": 5.05137, "bw": 0.41630, "n_in_bw": 429},
    5: {"estimate": 4.20530, "se": 0.67993, "ci_lower": 2.62381, "ci_upper": 5.28907, "bw": 0.34105, "n_in_bw": 354},
}

STATA_PLACEBOS = {
    1: {"estimate": -0.00186, "se": 0.61902, "ci_lower": -1.71477, "ci_upper": 0.71176, "bw": 0.37026, "n_in_bw": 383},
    2: {"estimate": 0.07676, "se": 0.73390, "ci_lower": -1.74859, "ci_upper": 1.12827, "bw": 0.38635, "n_in_bw": 401},
    3: {"estimate": 0.07018, "se": 0.83046, "ci_lower": -1.85882, "ci_upper": 1.39653, "bw": 0.25068, "n_in_bw": 268},
    4: {"estimate": -0.56023, "se": 0.86000, "ci_lower": -3.26103, "ci_upper": 0.11012, "bw": 0.20648, "n_in_bw": 226},
}


@pytest.fixture
def tutorial_data():
    """Load the tutorial dataset."""
    url = (
        "https://raw.githubusercontent.com/chaisemartinPackages/"
        "did_had/main/tutorial_data.dta"
    )
    return pd.read_stata(url)


def test_effects_match_stata(tutorial_data):
    """Test that effect estimates match Stata output."""
    bw_eff = {1: 0.36133, 2: 0.27104, 3: 0.31407, 4: 0.41630, 5: 0.34105}
    bw_pl = {1: 0.37026, 2: 0.38635, 3: 0.25068, 4: 0.20648}

    model = DidHad(kernel="tri", nnmatch=3)
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=5,
        placebo=4,
        bandwidth_effect=bw_eff,
        bandwidth_placebo=bw_pl,
    )

    # Check effects
    for horizon, expected in STATA_EFFECTS.items():
        row = results.effects[results.effects["horizon"] == horizon].iloc[0]

        assert np.isclose(row["estimate"], expected["estimate"], rtol=1e-4), \
            f"Effect_{horizon} estimate: {row['estimate']:.5f} != {expected['estimate']:.5f}"

        assert np.isclose(row["se"], expected["se"], rtol=1e-4), \
            f"Effect_{horizon} SE: {row['se']:.5f} != {expected['se']:.5f}"

        assert np.isclose(row["ci_lower"], expected["ci_lower"], rtol=1e-4), \
            f"Effect_{horizon} CI lower: {row['ci_lower']:.5f} != {expected['ci_lower']:.5f}"

        assert np.isclose(row["ci_upper"], expected["ci_upper"], rtol=1e-4), \
            f"Effect_{horizon} CI upper: {row['ci_upper']:.5f} != {expected['ci_upper']:.5f}"

        assert row["n_in_bw"] == expected["n_in_bw"], \
            f"Effect_{horizon} N in BW: {row['n_in_bw']} != {expected['n_in_bw']}"


def test_placebos_match_stata(tutorial_data):
    """Test that placebo estimates match Stata output."""
    bw_eff = {1: 0.36133, 2: 0.27104, 3: 0.31407, 4: 0.41630, 5: 0.34105}
    bw_pl = {1: 0.37026, 2: 0.38635, 3: 0.25068, 4: 0.20648}

    model = DidHad(kernel="tri", nnmatch=3)
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=5,
        placebo=4,
        bandwidth_effect=bw_eff,
        bandwidth_placebo=bw_pl,
    )

    # Check placebos
    for horizon, expected in STATA_PLACEBOS.items():
        row = results.placebos[results.placebos["horizon"] == horizon].iloc[0]

        # Use atol for values near zero
        assert np.isclose(row["estimate"], expected["estimate"], rtol=1e-4, atol=1e-4), \
            f"Placebo_{horizon} estimate: {row['estimate']:.5f} != {expected['estimate']:.5f}"

        assert np.isclose(row["se"], expected["se"], rtol=1e-4), \
            f"Placebo_{horizon} SE: {row['se']:.5f} != {expected['se']:.5f}"

        assert np.isclose(row["ci_lower"], expected["ci_lower"], rtol=1e-4), \
            f"Placebo_{horizon} CI lower: {row['ci_lower']:.5f} != {expected['ci_lower']:.5f}"

        assert np.isclose(row["ci_upper"], expected["ci_upper"], rtol=1e-4), \
            f"Placebo_{horizon} CI upper: {row['ci_upper']:.5f} != {expected['ci_upper']:.5f}"

        assert row["n_in_bw"] == expected["n_in_bw"], \
            f"Placebo_{horizon} N in BW: {row['n_in_bw']} != {expected['n_in_bw']}"


def test_results_summary(tutorial_data):
    """Test that summary method works."""
    model = DidHad(kernel="tri")
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=2,
        placebo=1,
        bandwidth=0.3,
    )

    summary = results.summary()
    assert "DID-HAD Estimation Results" in summary
    assert "Effect_1" in summary
    assert "Placebo_1" in summary


def test_att_calculation(tutorial_data):
    """Test ATT (average treatment effect) calculation."""
    bw_eff = {1: 0.36133, 2: 0.27104, 3: 0.31407, 4: 0.41630, 5: 0.34105}

    model = DidHad(kernel="tri", nnmatch=3)
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=5,
        placebo=0,
        bandwidth_effect=bw_eff,
    )

    att = results.att()
    expected_att = np.mean([4.28198, 3.59260, 4.25466, 3.97161, 4.20530])

    assert np.isclose(att, expected_att, rtol=1e-4), \
        f"ATT: {att:.5f} != {expected_att:.5f}"


def test_save_results(tutorial_data, tmp_path):
    """Test saving results to different formats."""
    model = DidHad(kernel="tri")
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=2,
        bandwidth=0.3,
    )

    # Test CSV
    csv_path = tmp_path / "results.csv"
    model.save_results(str(csv_path), format="csv")
    assert csv_path.exists()

    # Test pickle
    pkl_path = tmp_path / "results.pkl"
    model.save_results(str(pkl_path), format="pickle")
    assert pkl_path.exists()


def test_quasi_untreated_group_test(tutorial_data):
    """Test quasi-untreated group test statistics."""
    bw_eff = {1: 0.36133}

    model = DidHad(kernel="tri", nnmatch=3)
    results = model.fit(
        df=tutorial_data,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=1,
        bandwidth_effect=bw_eff,
    )

    row = results.effects.iloc[0]

    # Expected T statistic and p-value from Stata
    expected_T = 3.96182
    expected_pval = 0.20154

    assert np.isclose(row["qg_T"], expected_T, rtol=1e-4), \
        f"QUG T: {row['qg_T']:.5f} != {expected_T:.5f}"

    assert np.isclose(row["qg_pval"], expected_pval, rtol=1e-4), \
        f"QUG p-value: {row['qg_pval']:.5f} != {expected_pval:.5f}"


if __name__ == "__main__":
    # Quick verification
    print("Loading tutorial data...")
    url = (
        "https://raw.githubusercontent.com/chaisemartinPackages/"
        "did_had/main/tutorial_data.dta"
    )
    df = pd.read_stata(url)

    print("Running DID-HAD estimation...")
    bw_eff = {1: 0.36133, 2: 0.27104, 3: 0.31407, 4: 0.41630, 5: 0.34105}
    bw_pl = {1: 0.37026, 2: 0.38635, 3: 0.25068, 4: 0.20648}

    model = DidHad(kernel="tri", nnmatch=3)
    results = model.fit(
        df=df,
        outcome="y",
        group="g",
        time="t",
        treatment="d",
        effects=5,
        placebo=4,
        bandwidth_effect=bw_eff,
        bandwidth_placebo=bw_pl,
    )

    print(results)

    print("\n" + "=" * 60)
    print("VERIFICATION: Comparing with Stata outputs")
    print("=" * 60)

    all_match = True

    # Check effects
    print("\nEffects:")
    for horizon, expected in STATA_EFFECTS.items():
        row = results.effects[results.effects["horizon"] == horizon].iloc[0]
        est_match = np.isclose(row["estimate"], expected["estimate"], rtol=1e-4)
        se_match = np.isclose(row["se"], expected["se"], rtol=1e-4)
        status = "MATCH" if est_match and se_match else "MISMATCH"
        if not (est_match and se_match):
            all_match = False
        print(f"  Effect_{horizon}: Python={row['estimate']:.5f}, Stata={expected['estimate']:.5f} [{status}]")

    # Check placebos
    print("\nPlacebos:")
    for horizon, expected in STATA_PLACEBOS.items():
        row = results.placebos[results.placebos["horizon"] == horizon].iloc[0]
        est_match = np.isclose(row["estimate"], expected["estimate"], rtol=1e-4, atol=1e-4)
        se_match = np.isclose(row["se"], expected["se"], rtol=1e-4)
        status = "MATCH" if est_match and se_match else "MISMATCH"
        if not (est_match and se_match):
            all_match = False
        print(f"  Placebo_{horizon}: Python={row['estimate']:.5f}, Stata={expected['estimate']:.5f} [{status}]")

    print("\n" + "=" * 60)
    if all_match:
        print("ALL ESTIMATES MATCH STATA OUTPUT!")
    else:
        print("SOME ESTIMATES DO NOT MATCH - CHECK IMPLEMENTATION")
    print("=" * 60)
