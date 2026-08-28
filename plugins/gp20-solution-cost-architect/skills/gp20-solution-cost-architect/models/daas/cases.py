"""Exercise cases for the conformance suite. Every case must be valid input."""

CASES = [
    ("Aurelian — 17k devices / 8h swap / 4-year refresh", {
        "client_name": "Aurelian Global Holdings plc",
        "rfp_ref": "AG/2026/EUC/207",
        "term_years": 4, "rollout_months": 6,
        "devices": {"laptop_standard": 9800, "laptop_performance": 1400,
                    "desktop": 900, "tablet": 650, "phone": 4200},
        "user_count": 14330,
        "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15,
                        "NL": 0.10, "PL": 0.05},
        "refresh_years": 4, "swap_sla": "8h",
        "deployment_method": "ship_to_user", "image_strategy": "custom",
        "accessories": "standard", "disposal": "buyback",
        "_sources": {"devices": "rfp", "user_count": "rfp",
                     "term_years": "rfp", "country_mix": "rfp"},
    }),
    ("Small UK fleet / next business day / 3-year refresh", {
        "client_name": "Test B", "term_years": 3,
        "devices": {"laptop_standard": 400, "phone": 380},
        "country_mix": {"UK": 1.0},
        "refresh_years": 3, "swap_sla": "next_business_day",
        "deployment_method": "desk_side", "image_strategy": "standard",
        "accessories": "basic", "disposal": "recycle",
    }),
    ("5-year refresh / 4h swap / no buyback", {
        "client_name": "Test C", "term_years": 5,
        "devices": {"laptop_performance": 2200, "desktop": 1500},
        "country_mix": {"DE": 0.6, "PL": 0.4},
        "refresh_years": 5, "swap_sla": "4h",
        "deployment_method": "depot_collect", "image_strategy": "per_persona",
        "accessories": "premium", "disposal": "none", "service_desk": False,
    }),
]
