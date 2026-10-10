"""Tests for pure-Python margin simulator tool.

Must reproduce CLM-109 values within ±0.2 dB and label outputs as SIMULATION.
"""
import pytest
from app.tools.margin_simulator import (
    compute_pfd,
    compute_margin,
    feet_to_meters,
    compute_separation_distance,
    MarginResult,
)


def test_feet_to_meters():
    assert round(feet_to_meters(35.0), 3) == 10.668


def test_clm_109_adjacent_band_reproduction():
    """CLM-109 specifies:
    Adjacent-band BS EIRP 65 dBm/MHz (dual-pol; 62 per polarization)
    gives 0.4 dBW/m²/MHz at 35 ft; adding 6 dB margin gives 6.4 vs ITM 9.5 dBW/m²/MHz.
    """
    d_m = feet_to_meters(35.0)
    # 62 dBm per polarization
    pfd = compute_pfd(eirp_per_pol_dbm_mhz=62.0, distance_m=d_m)
    # Expected: 0.4 dBW/m2/MHz within +-0.2 dB
    assert abs(pfd - 0.4) <= 0.2, f"PFD {pfd} not within 0.2 dB of 0.4"

    res = compute_margin(
        eirp_per_pol_dbm_mhz=62.0,
        distance_m=d_m,
        threshold_dbw_m2_mhz=9.5,
        aggregation_db=0.0,
        required_margin_db=6.0,
    )
    assert res.label == "SIMULATION"
    # total interference = 0.4 + 6.0 = 6.4
    # margin = 9.5 - 6.4 = 3.1
    expected_total = pfd + 6.0
    assert abs(expected_total - 6.4) <= 0.2
    assert abs(res.margin_db - 3.1) <= 0.2


def test_clm_109_inband_spurious_reproduction():
    """CLM-109 specifies:
    In-band spurious -28.4 dBm/MHz EIRP (-31.4 per pol) gives -93 dBW/m2/MHz at 35 ft;
    adding 6 dB margin and 5 dB aggregation gives -82, equal to ITM -82 dBW/m2/MHz.
    """
    d_m = feet_to_meters(35.0)
    pfd = compute_pfd(eirp_per_pol_dbm_mhz=-31.4, distance_m=d_m)
    assert abs(pfd - (-93.0)) <= 0.2, f"Inband PFD {pfd} not within 0.2 dB of -93"

    res = compute_margin(
        eirp_per_pol_dbm_mhz=-31.4,
        distance_m=d_m,
        threshold_dbw_m2_mhz=-82.0,
        aggregation_db=5.0,
        required_margin_db=6.0,
    )
    assert res.label == "SIMULATION"
    # total interference = -93 + 6 + 5 = -82
    # margin = -82 - (-82) = 0.0
    assert abs(res.margin_db - 0.0) <= 0.2


def test_separation_distance():
    # Aircraft at 250 ft AGL over threshold, cell 1200m away, 350m lateral, 30m high
    d = compute_separation_distance(
        cell_height_m=30.0,
        cell_distance_to_threshold_m=1200.0,
        cell_lateral_offset_m=350.0,
        aircraft_height_agl_ft=250.0,
    )
    assert d > 1200.0
    assert d < 1300.0


def test_invalid_distance():
    with pytest.raises(ValueError):
        compute_pfd(62.0, 0.0)
