"""Exercise cases for the Service Desk tower. Every case must be valid input."""

# The same estate the field-service and remote-support lots price. Shared
# deliberately: three lots of one tender must fingerprint identically, and the
# only way to be sure of that is to describe the estate once.
AURELIAN_ESTATE = {
    "client_name": "Aurelian Global Holdings plc",
    "rfp_ref": "AGH/2026/LOT-4",
    "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
    "country_mix": {"UK": 0.45, "DE": 0.25, "FR": 0.15, "NL": 0.11, "PL": 0.04},
    "user_count": 14330,
    "device_total": 16950,
    "_sources": {"sites": "rfp", "country_mix": "rfp", "user_count": "rfp",
                 "device_total": "rfp"},
}

CASES = [
    ("Aurelian Lot 4 — 14k users, 5 languages, 24x7", {
        **AURELIAN_ESTATE,
        "term_years": 5, "onboarding_months": 3,
        "languages": ["EN", "DE", "FR", "NL", "PL"],
        "coverage": "24x7",
        "self_service": "knowledge_base", "fcr_target": 0.75,
        "delivery_country": "PL",
        "_sources": {**AURELIAN_ESTATE["_sources"], "languages": "rfp",
                     "term_years": "rfp"},
    }),
    ("English only, 8x5, low FCR", {
        "client_name": "Test B", "term_years": 3,
        "sites": {"small": 40},
        "user_count": 2400, "languages": ["EN"],
        "coverage": "8x5",
        "self_service": "none", "fcr_target": 0.65,
        "delivery_country": "UK",
    }),
    ("Small estate, AI deflection, high FCR, 24x7x365", {
        "client_name": "Test C", "term_years": 5,
        "sites": {"small": 8},
        "user_count": 900, "device_total": 1100,
        "languages": ["EN", "DE"],
        "coverage": "24x7x365",
        "self_service": "ai_assistant", "fcr_target": 0.85,
        "delivery_country": "PL",
    }),
]
