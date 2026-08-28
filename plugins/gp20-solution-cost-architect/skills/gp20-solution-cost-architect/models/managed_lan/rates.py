"""
GP-20 Solution & Cost Architect — Rate Card
ILLUSTRATIVE DATA ONLY. Synthetic rates for demonstration. Not NSC pricing.

Single source of truth for the model's constants. The Excel workbook's
`Rates` sheet is generated from this module, so Python and Excel cannot drift.
"""

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

# --- Estate derivation -------------------------------------------------------
APS_PER_SITE_BAND = {"small": 4, "medium": 14, "large": 45, "campus": 140}
USERS_PER_SITE_BAND = {"small": 30, "medium": 140, "large": 550, "campus": 1800}
PORTS_PER_SWITCH = 24
# Wireless-led estate: most users are on WLAN. Wired ports serve APs,
# printers, IoT, and a minority of fixed desks.
USERS_PER_PORT = 0.55

# --- Deployment effort rates (days) -----------------------------------------
SURVEY_DAYS_PER_AP = {"predictive": 0.020, "hybrid": 0.035, "onsite": 0.055}
AP_INSTALL_DAYS = 0.060
SWITCH_INSTALL_DAYS = 0.35
MOBILISATION_DAYS_PER_SITE = 1.2  # travel, site access, local coordination, sign-off
DESIGN_DAYS_FIXED = 15.0
DESIGN_DAYS_PER_SITE = 0.12
PM_OVERHEAD_PCT = 0.15
OOH_UPLIFT = 1.35  # out-of-hours install multiplier

# --- Run-rate drivers --------------------------------------------------------
AP_INCIDENT_RATE_PA = 0.32          # incidents per AP per year
SWITCH_INCIDENT_RATE_PA = 0.55      # incidents per switch per year
HOURS_PER_INCIDENT = 3.2            # incl. travel-adjacent handling
PRODUCTIVE_HOURS_PA = 1_450         # per field FTE after leave/training/admin
WORKING_DAYS_PA = 220

SLA_MULTIPLIER = {"bronze": 1.00, "silver": 1.15, "gold": 1.40, "platinum": 1.90}
SLA_RESPONSE = {
    "bronze": "Next business day",
    "silver": "8 business hours",
    "gold": "4 business hours",
    "platinum": "2 business hours",
}
COVERAGE_MULTIPLIER = {"8x5": 1.00, "12x5": 1.35, "24x7": 3.20}

# --- Coverage floor ----------------------------------------------------------
# A committed on-site response time cannot be served from a central travelling
# pool: each country needs a standing local presence sized for shift rota.
# FTE required to man one post continuously, allowing for leave and training.
PRESENCE_FTE_PER_POST = {"8x5": 1.15, "12x5": 1.70, "24x7": 4.80}
# Tiers that commit to on-site response and therefore trigger the floor.
ON_SITE_RESPONSE_TIERS = {"gold", "platinum"}
# One additional post per N sites in-country (drive time bounds a post's reach).
SITES_PER_POST = 60

# NOC sizing: one FTE per N APs monitored, before coverage multiplier
APS_PER_NOC_FTE = 2_600
# Service desk: contacts per user per year, minutes per contact
SD_CONTACTS_PER_USER_PA = 2.4
SD_MINUTES_PER_CONTACT = 11.0

# Service delivery manager, banded by annual run cost
SDM_BANDS = [(1_000_000, 0.5), (3_000_000, 1.0), (7_000_000, 1.8), (float("inf"), 2.5)]

# --- Country rate card (loaded day rates, GBP) -------------------------------
COUNTRY_RATES = {
    #            field   noc    service_desk  sdm    travel_per_incident
    "UK": {"field": 540, "noc": 470, "service_desk": 330, "sdm": 720, "travel": 68},
    "DE": {"field": 575, "noc": 495, "service_desk": 355, "sdm": 760, "travel": 62},
    "FR": {"field": 530, "noc": 460, "service_desk": 335, "sdm": 700, "travel": 58},
    "NL": {"field": 560, "noc": 485, "service_desk": 350, "sdm": 740, "travel": 54},
    "PL": {"field": 295, "noc": 260, "service_desk": 185, "sdm": 430, "travel": 41},
}
# Centralised functions land in the lowest-cost hub; 24x7 splits across two.
HUB_PRIMARY = "PL"
HUB_SECONDARY = "UK"

# --- Hardware & consumables --------------------------------------------------
AP_UNIT_COST = 385.0
SWITCH_UNIT_COST = 2_150.0
TOOLING_PER_SITE = 95.0
SPARES_PCT = {"none": 0.00, "central": 0.025, "regional": 0.045, "onsite": 0.085}

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.12
DEFAULT_MARGIN_PCT = 0.22
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
DEFAULT_ROLLOUT_MONTHS = 9

SUPPORTED_COUNTRIES = list(COUNTRY_RATES.keys())
SITE_BANDS = list(APS_PER_SITE_BAND.keys())
