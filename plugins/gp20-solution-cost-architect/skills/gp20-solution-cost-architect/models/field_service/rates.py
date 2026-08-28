"""
Field Service tower — rate card.

ILLUSTRATIVE DATA ONLY. Synthetic rates for demonstration. Not NSC pricing.

This tower prices people going to places: break-fix attendance, IMAC work,
smart hands. It does not price the parts they fit (logistics), the diagnosis
that dispatched them (remote support), or the programme that governs them
(project management).
"""

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

# --- Incident generation, per asset per annum --------------------------------
# What breaks. Note these are *incidents*, not dispatches — most are resolved
# without anyone travelling, which is what REMOTE_FIX_RATE below governs.
AP_INCIDENT_RATE_PA = 0.32
SWITCH_INCIDENT_RATE_PA = 0.55
DEVICE_INCIDENT_RATE_PA = 0.41
SITE_INFRA_INCIDENT_RATE_PA = 1.8      # cabling, power, environment, per site

# --- What actually needs a visit ---------------------------------------------
# The fraction of incidents closed remotely, by the capability of the remote
# support function. Every point here is a truck roll that does not happen, so
# this is where the two towers meet commercially.
REMOTE_FIX_RATE = {
    "none": 0.00,          # no remote tower — everything is a dispatch
    "basic": 0.42,         # scripted triage, remote control
    "standard": 0.61,      # tooling, automation, experienced 2nd line
    "advanced": 0.74,      # proactive monitoring, self-heal, deep automation
}

# --- IMAC (installs, moves, adds, changes) -----------------------------------
IMAC_PER_USER_PA = 0.22
IMAC_HOURS = 1.1

# --- Effort ------------------------------------------------------------------
HOURS_PER_DISPATCH = 3.2               # including travel-adjacent handling
PRODUCTIVE_HOURS_PA = 1_450            # per FTE after leave, training, admin
WORKING_DAYS_PA = 220

# --- Service level -----------------------------------------------------------
SLA_MULTIPLIER = {"bronze": 1.00, "silver": 1.15, "gold": 1.40, "platinum": 1.90}
SLA_RESPONSE = {
    "bronze": "Next business day",
    "silver": "8 business hours",
    "gold": "4 business hours",
    "platinum": "2 business hours",
}
# Coverage applied to *volume-driven* effort is only an efficiency penalty:
# shift handover, lower out-of-hours productivity, harder scheduling. It is NOT
# where 24×7 gets expensive — that is the standing-presence floor below, which
# is a different thing being paid for. Multiplying volume by the floor's factor
# as well charges twice for one commitment, and is the first thing a bid
# reviewer finds.
COVERAGE_EFFICIENCY = {"8x5": 1.00, "12x5": 1.10, "24x7": 1.25}
COVERAGE_LABEL = {"8x5": "8×5 business hours", "12x5": "12×5 extended day",
                  "24x7": "24×7 continuous"}

# --- The coverage floor ------------------------------------------------------
# A committed on-site response time cannot be served from a central travelling
# pool: each country needs standing local presence sized for a shift rota,
# whatever the incident volume says. This is the tower's defining behaviour.
PRESENCE_FTE_PER_POST = {"8x5": 1.15, "12x5": 1.70, "24x7": 4.80}
ON_SITE_RESPONSE_TIERS = {"gold", "platinum"}
SITES_PER_POST = 60                    # drive time bounds how far a post reaches

# --- Mobilisation (one-off) --------------------------------------------------
MOBILISATION_DAYS_PER_SITE = 0.45      # site access, keys, induction, survey
MOBILISATION_FIXED_DAYS = 12.0
TOOLING_PER_ENGINEER = 1_850.0         # vehicle kit, test gear, safety
VEHICLE_PER_ENGINEER_PA = 6_400.0

# --- Country rate card (loaded day rates, GBP) -------------------------------
COUNTRY_RATES = {
    "UK": {"field": 540, "sdm": 720, "travel": 68},
    "DE": {"field": 575, "sdm": 760, "travel": 62},
    "FR": {"field": 530, "sdm": 700, "travel": 58},
    "NL": {"field": 560, "sdm": 740, "travel": 54},
    "PL": {"field": 295, "sdm": 430, "travel": 41},
}

# Service delivery manager, banded by annual run cost
SDM_BANDS = [(1_000_000, 0.5), (3_000_000, 1.0), (7_000_000, 1.8),
             (float("inf"), 2.5)]

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.12
DEFAULT_MARGIN_PCT = 0.22
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
DEFAULT_MOBILISATION_MONTHS = 4
