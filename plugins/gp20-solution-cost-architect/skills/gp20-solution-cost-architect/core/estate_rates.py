"""
Estate design standards — the constants that turn a described estate into
countable things.

These are *not* commercial rates. They are engineering standards: how many
access points a medium site takes, how many users sit behind a switch port.
They live here rather than in a tower's rate card because every tower must
count the same estate the same way. A field-service lot that thinks there are
101 sites and a logistics lot that thinks there are 98 is a bid the client will
add up and reject.

ILLUSTRATIVE DATA ONLY. Synthetic standards for demonstration, not NSC's.
"""

from __future__ import annotations

# --- Site banding ------------------------------------------------------------
# Bands are by user population, because that is what tenders state.
SITE_BANDS = ("small", "medium", "large", "campus")
USERS_PER_SITE_BAND = {"small": 30, "medium": 140, "large": 550, "campus": 1800}

# --- Network derivation ------------------------------------------------------
APS_PER_SITE_BAND = {"small": 4, "medium": 14, "large": 45, "campus": 140}
PORTS_PER_SWITCH = 24
# Wireless-led estate: most users are on WLAN. Wired ports serve APs,
# printers, IoT, and a minority of fixed desks.
USERS_PER_PORT = 0.55

# --- Device derivation -------------------------------------------------------
DEVICE_TYPES = ("standard_laptop", "performance_laptop", "desktop", "tablet")
DEVICE_LABEL = {
    "standard_laptop": "Standard laptop",
    "performance_laptop": "Performance laptop",
    "desktop": "Desktop",
    "tablet": "Tablet",
}
# When a tender states a user count but not a device split.
DEFAULT_DEVICE_MIX = {"standard_laptop": 0.78, "performance_laptop": 0.12,
                      "desktop": 0.07, "tablet": 0.03}
DEVICES_PER_USER = 1.18          # shared kit, spares in use, dual-device roles

# --- Hardware unit costs (for the estate BoM) --------------------------------
AP_UNIT_COST = 385.0
SWITCH_UNIT_COST = 2_150.0
DEVICE_UNIT_COST = {
    "standard_laptop": 940.0,
    "performance_laptop": 1_680.0,
    "desktop": 720.0,
    "tablet": 505.0,
}

# --- Geography ---------------------------------------------------------------
SUPPORTED_COUNTRIES = ("UK", "DE", "FR", "NL", "PL")

# --- Language coverage -------------------------------------------------------
# ISO-style codes rather than names, because that is what a tender's language
# schedule uses and what the service-desk tower consumes. Keep the two in step:
# a mismatch here surfaces as a validation error the moment a desk lot runs.
SUPPORTED_LANGUAGES = ("EN", "DE", "FR", "NL", "PL", "ES", "IT")
LANGUAGE_NAME = {"EN": "English", "DE": "German", "FR": "French",
                 "NL": "Dutch", "PL": "Polish", "ES": "Spanish",
                 "IT": "Italian"}
COUNTRY_LANGUAGE = {"UK": "EN", "DE": "DE", "FR": "FR", "NL": "NL", "PL": "PL"}
