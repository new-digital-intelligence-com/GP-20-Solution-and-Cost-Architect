"""Exercise cases for the Remote Support tower."""

AURELIAN_ESTATE = {
    "client_name": "Aurelian Global Holdings plc",
    "rfp_ref": "AGH/2026/LOT-5",
    "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
    "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15, "NL": 0.11, "PL": 0.04},
    "user_count": 14330,
    "device_total": 16950,
    "_sources": {"sites": "rfp", "country_mix": "rfp", "user_count": "rfp",
                 "device_total": "rfp"},
}

CASES = [
    ("Aurelian Lot 5 — intake from the desk lot, standard capability", {
        **AURELIAN_ESTATE,
        "term_years": 5,
        # Published by the service-desk lot's drivers, not guessed here.
        "escalations_pa": 23533,
        "capability": "standard",
        "tiers": "l2_l3",
        "coverage": "24x7",
        "monitoring": "proactive",
        "delivery_country": "PL",
        "_sources": {**AURELIAN_ESTATE["_sources"], "escalations_pa": "derived"},
    }),
    ("No desk lot — intake derived from the estate, basic capability", {
        **AURELIAN_ESTATE,
        "term_years": 3,
        "capability": "basic",
        "tiers": "l2",
        "coverage": "8x5",
        "monitoring": "reactive",
    }),
    ("Small estate, advanced capability, no monitoring", {
        "client_name": "Test C",
        "rfp_ref": "TC/2026/RS",
        "sites": {"small": 8},
        "country_mix": {"UK": 1.0},
        "user_count": 900,
        "device_total": 1100,
        "term_years": 4,
        "escalations_pa": 1400,
        "capability": "advanced",
        "tiers": "l2",
        "coverage": "12x5",
        "monitoring": "none",
        "delivery_country": "UK",
    }),
]
