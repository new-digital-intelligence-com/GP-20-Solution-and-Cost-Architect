"""Exercise cases for the Programme and Service Governance tower."""

AURELIAN_ESTATE = {
    "client_name": "Aurelian Global Holdings plc",
    "rfp_ref": "AGH/2026/LOT-3",
    "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
    "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15, "NL": 0.11, "PL": 0.04},
    "user_count": 14330,
    "device_total": 16950,
    "_sources": {"sites": "rfp", "country_mix": "rfp", "user_count": "rfp",
                 "device_total": "rfp"},
}

CASES = [
    ("Aurelian Lot 3 — governing the four delivery lots", {
        **AURELIAN_ESTATE,
        "term_years": 5,
        "lots": 4,
        "complexity": "high",
        "reporting": "enhanced",
        "delivery_country": "UK",
        "_sources": {**AURELIAN_ESTATE["_sources"], "lots": "rfp"},
    }),
    ("Single lot, low complexity, standard reporting", {
        "client_name": "Test B",
        "rfp_ref": "TB/2026/PM",
        "sites": {"small": 40},
        "country_mix": {"UK": 1.0},
        "user_count": 2400,
        "term_years": 3,
        "lots": 1,
        "complexity": "low",
        "reporting": "standard",
    }),
    ("Three lots, regulated reporting, two countries", {
        "client_name": "Test C",
        "rfp_ref": "TC/2026/PM",
        "sites": {"medium": 18, "large": 4},
        "country_mix": {"UK": 0.7, "DE": 0.3},
        "user_count": 5200,
        "term_years": 4,
        "lots": 3,
        "complexity": "standard",
        "reporting": "regulated",
        "delivery_country": "UK",
    }),
]
