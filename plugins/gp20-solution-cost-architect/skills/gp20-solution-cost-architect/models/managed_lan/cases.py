"""Exercise cases for the conformance suite. Every case must be valid input."""

CASES = [
    ("Aurelian — gold / 24x7 / five countries", {
        "client_name": "Aurelian Global Holdings plc",
        "rfp_ref": "AG/2026/NET/114",
        "term_years": 5, "rollout_months": 9,
        "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
        "user_count": 14330,
        "country_mix": {"UK": 0.4455, "DE": 0.2475, "FR": 0.1485,
                        "NL": 0.1089, "PL": 0.0495},
        "survey_type": "hybrid", "sla_tier": "gold", "coverage": "24x7",
        "spares_strategy": "regional", "install_window": "out_of_hours",
        "_sources": {"sites": "rfp", "country_mix": "rfp", "sla_tier": "rfp",
                     "term_years": "rfp", "user_count": "rfp",
                     "rollout_months": "rfp"},
    }),
    ("Silver / 8x5 / UK only", {
        "client_name": "Test B", "term_years": 3,
        "sites": {"small": 20, "medium": 5},
        "country_mix": {"UK": 1.0},
        "survey_type": "predictive", "sla_tier": "silver", "coverage": "8x5",
        "spares_strategy": "central",
    }),
    ("Bronze / 12x5 / no monitoring or service desk", {
        "client_name": "Test C", "term_years": 3,
        "sites": {"small": 150}, "country_mix": {"PL": 1.0},
        "sla_tier": "bronze", "coverage": "12x5", "spares_strategy": "none",
        "monitoring": False, "service_desk": False,
    }),
]
