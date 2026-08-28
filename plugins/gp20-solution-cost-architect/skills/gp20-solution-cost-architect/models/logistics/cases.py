"""Exercise cases for the Logistics tower."""

AURELIAN_ESTATE = {
    "client_name": "Aurelian Global Holdings plc",
    "rfp_ref": "AGH/2026/LOT-2",
    "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
    "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15, "NL": 0.11, "PL": 0.04},
    "user_count": 14330,
    "device_total": 16950,
    "_sources": {"sites": "rfp", "country_mix": "rfp", "user_count": "rfp",
                 "device_total": "rfp"},
}

CASES = [
    ("Aurelian Lot 2 — forward stock against a 4h commitment", {
        **AURELIAN_ESTATE,
        "term_years": 5,
        "stock_strategy": "forward",
        # Both published by the field service lot.
        "fix_tier": "gold",
        "dispatches_pa": 3017,
        "disposal": "secure_erase",
        "delivery_country": "PL",
        "_sources": {**AURELIAN_ESTATE["_sources"], "fix_tier": "derived",
                     "dispatches_pa": "derived"},
    }),
    ("Central stock against the same 4h commitment — incoherent on purpose", {
        **AURELIAN_ESTATE,
        "term_years": 5,
        "stock_strategy": "central",
        "fix_tier": "gold",
        "dispatches_pa": 3017,
        "disposal": "recycle",
    }),
    ("Small estate, central stock, no disposal, staging elsewhere", {
        "client_name": "Test C",
        "rfp_ref": "TC/2026/LOG",
        "sites": {"small": 22, "medium": 3},
        "country_mix": {"UK": 1.0},
        "user_count": 1080,
        "device_total": 1240,
        "term_years": 3,
        "stock_strategy": "central",
        "fix_tier": "silver",
        "disposal": "none",
        "staging_included": False,
        "delivery_country": "UK",
    }),
]
