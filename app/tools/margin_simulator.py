"""Margin simulator – pure-Python, deterministic, unit-tested.

PFD formula:  PFD_dBW_m2_MHz = (EIRP_per_pol_dBm_MHz - 30) - 10*log10(4*pi*d_m^2)
Margin:       threshold - (PFD + aggregation_dB + required_margin_dB)

All outputs are labelled "SIMULATION".
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MarginResult:
    """Result of a margin simulation. Always labelled SIMULATION."""
    pfd_dbw_m2_mhz: float
    margin_db: float
    threshold_dbw_m2_mhz: float
    aggregation_db: float
    required_margin_db: float
    distance_m: float
    eirp_per_pol_dbm_mhz: float
    label: str = "SIMULATION"
    analogy_note: str = ""


def compute_pfd(eirp_per_pol_dbm_mhz: float, distance_m: float) -> float:
    """Power Flux Density in dBW/m²/MHz from a single polarization.

    PFD = (EIRP_dBm - 30) - 10*log10(4*pi*d²)
    The -30 converts dBm to dBW.
    """
    if distance_m <= 0:
        raise ValueError("distance_m must be positive")
    eirp_dbw = eirp_per_pol_dbm_mhz - 30.0
    spreading = 10.0 * math.log10(4.0 * math.pi * distance_m ** 2)
    return eirp_dbw - spreading


def compute_margin(
    eirp_per_pol_dbm_mhz: float,
    distance_m: float,
    threshold_dbw_m2_mhz: float,
    aggregation_db: float = 0.0,
    required_margin_db: float = 6.0,
    jurisdiction: str = "",
) -> MarginResult:
    """Compute safety margin between predicted interference and threshold.

    margin = threshold - (PFD + aggregation_dB + required_margin_dB)
    A positive margin means the ITM limit is not exceeded.
    """
    pfd = compute_pfd(eirp_per_pol_dbm_mhz, distance_m)
    total_interference = pfd + aggregation_db + required_margin_db
    margin = threshold_dbw_m2_mhz - total_interference

    analogy = ""
    if jurisdiction and jurisdiction.lower() not in ("us", "united states"):
        analogy = (
            f"US ITM thresholds used as analogy for {jurisdiction} "
            "(GAP-007: India has no numeric RA tolerance threshold in AIC 19/2025)"
        )

    return MarginResult(
        pfd_dbw_m2_mhz=round(pfd, 2),
        margin_db=round(margin, 2),
        threshold_dbw_m2_mhz=threshold_dbw_m2_mhz,
        aggregation_db=aggregation_db,
        required_margin_db=required_margin_db,
        distance_m=distance_m,
        eirp_per_pol_dbm_mhz=eirp_per_pol_dbm_mhz,
        analogy_note=analogy,
    )


def feet_to_meters(ft: float) -> float:
    return ft * 0.3048


def compute_separation_distance(
    cell_height_m: float,
    cell_distance_to_threshold_m: float,
    cell_lateral_offset_m: float,
    aircraft_height_agl_ft: float,
) -> float:
    """3D separation between cell antenna and aircraft (meters).

    Uses simple Euclidean distance with the cell at ground level plus height_m
    and the aircraft at height_agl_ft over the runway threshold.
    """
    aircraft_height_m = feet_to_meters(aircraft_height_agl_ft)
    vertical = abs(aircraft_height_m - cell_height_m)
    horizontal = math.sqrt(cell_distance_to_threshold_m ** 2 + cell_lateral_offset_m ** 2)
    return math.sqrt(vertical ** 2 + horizontal ** 2)
