"""Exercise cases for the Field Service tower."""

AURELIAN_ESTATE = {
    "client_name": "Aurelian Global Holdings plc",
    "rfp_ref": "AGH/2026/LOT-1",
    "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
    "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15, "NL": 0.11, "PL": 0.04},
    "user_count": 14330,
    "device_total": 16950,
    "_sources": {"sites": "rfp", "country_mix": "rfp", "user_count": "rfp",
                 "device_total": "rfp"},
}

CASES = [
    ("Aurelian Lot 1 — 4h on-site, 24x7, five countries", {
        **AURELIAN_ESTATE,
        "term_years": 5,
        "sla_tier": "gold",
        "coverage": "24x7",
        "remote_capability": "standard",
        "_sources": {**AURELIAN_ESTATE["_sources"],
                     "sla_tier": "rfp", "coverage": "user"},
    }),
    ("Next business day, 8x5, UK only — no floor", {
        "client_name": "Northgate Retail",
        "rfp_ref": "NR/2026/FS",
        "sites": {"small": 140, "medium": 12},
        "country_mix": {"UK": 1.0},
        "term_years": 3,
        "sla_tier": "bronze",
        "coverage": "8x5",
        "remote_capability": "standard",
    }),
    ("No remote tower — every incident is a visit", {
        **AURELIAN_ESTATE,
        "term_years": 3,
        "sla_tier": "silver",
        "coverage": "12x5",
        "remote_capability": "none",
        "imac_included": False,
    }),
]
