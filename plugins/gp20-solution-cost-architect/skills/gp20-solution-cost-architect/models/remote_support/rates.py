"""
Remote Support tower — rate card.

ILLUSTRATIVE DATA ONLY. Synthetic rates for demonstration. Not NSC pricing.

This tower prices everything resolved without anyone travelling: second and
third line engineering, monitoring and event management, and the automation
that closes incidents before a human sees them.

It sits between two other lots. Escalations arrive from `service-desk`, and
whatever this tower fails to close becomes a dispatch in `field-service`. Both
directions are priced here explicitly rather than assumed.
"""

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

# --- Intake ------------------------------------------------------------------
# When the desk is not lotted separately, escalation volume is derived from the
# estate instead. Deliberately conservative — a stated desk figure always wins.
ESCALATIONS_PER_USER_PA = 1.6
ESCALATIONS_PER_DEVICE_PA = 0.24

# --- Handling ----------------------------------------------------------------
L2_AHT_MINUTES = 38.0
L3_AHT_MINUTES = 95.0
L3_SHARE_OF_ESCALATIONS = 0.22
OCCUPANCY = 0.72
PRODUCTIVE_HOURS_PA = 1_450
WORKING_DAYS_PA = 220

# --- Capability ---------------------------------------------------------------
# What this tower can close without a site visit. The complement becomes field
# dispatch volume, so this is the number the two lots must agree on.
CAPABILITY = {
    "basic":    {"remote_fix": 0.42, "automation": 0.00, "tooling_pa": 480.0},
    "standard": {"remote_fix": 0.61, "automation": 0.08, "tooling_pa": 1_150.0},
    "advanced": {"remote_fix": 0.74, "automation": 0.21, "tooling_pa": 2_400.0},
}
CAPABILITY_LABEL = {
    "basic": "Scripted triage and remote control",
    "standard": "Tooling, automation and experienced second line",
    "advanced": "Proactive monitoring, self-heal and deep automation",
}
# Effort multiplier: closing more remotely means harder cases handled, longer.
CAPABILITY_EFFORT = {"basic": 1.00, "standard": 1.12, "advanced": 1.30}

# --- Third line in scope ------------------------------------------------------
TIERS = ("l2", "l2_l3")
TIER_LABEL = {"l2": "Second line only", "l2_l3": "Second and third line"}

# --- Monitoring / event management -------------------------------------------
# Estate under monitoring, per engineer, before the coverage factor.
APS_PER_NOC_FTE = 2_600
SWITCHES_PER_NOC_FTE = 900
DEVICES_PER_NOC_FTE = 14_000
MONITORING_LEVEL = {"none": 0.0, "reactive": 0.6, "proactive": 1.0}
MONITORING_LABEL = {"none": "No monitoring in scope",
                    "reactive": "Alarm handling only",
                    "proactive": "Proactive monitoring and event correlation"}

# --- Coverage -----------------------------------------------------------------
# A remote function is centralised, so the floor is per *hub*, not per country
# or per language — which is exactly why this lot is cheaper to run 24x7 than
# field service is, and worth saying when a tender prices them together.
PRESENCE_FTE_PER_ROLE = {"8x5": 1.15, "12x5": 1.70, "24x7": 4.80}
COVERAGE_LABEL = {"8x5": "8×5 business hours", "12x5": "12×5 extended day",
                  "24x7": "24×7 continuous"}
FOLLOW_THE_SUN_SPLIT = [("PL", 0.65), ("UK", 0.35)]

# --- Tooling ------------------------------------------------------------------
MONITORING_PER_NODE_PA = 26.0
REMOTE_CONTROL_PER_ENGINEER_PA = 890.0
AUTOMATION_PLATFORM_PA = 74_000.0        # only at advanced capability

# --- Onboarding (one-off) -----------------------------------------------------
RUNBOOK_DAYS_PER_SERVICE = 4.5
TOOLING_INTEGRATION_DAYS = 28.0
AUTOMATION_BUILD_DAYS = {"basic": 0.0, "standard": 22.0, "advanced": 65.0}
PM_OVERHEAD_PCT = 0.15
DEFAULT_ONBOARDING_MONTHS = 3

# --- Country rate card (loaded day rates, GBP) -------------------------------
COUNTRY_RATES = {
    "UK": {"l2": 415, "l3": 615, "noc": 470, "lead": 520, "sdm": 720},
    "DE": {"l2": 445, "l3": 660, "noc": 495, "lead": 555, "sdm": 760},
    "FR": {"l2": 420, "l3": 620, "noc": 460, "lead": 525, "sdm": 700},
    "NL": {"l2": 435, "l3": 645, "noc": 485, "lead": 545, "sdm": 740},
    "PL": {"l2": 232, "l3": 355, "noc": 260, "lead": 295, "sdm": 430},
}
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)
HUB_PRIMARY = "PL"

ENGINEERS_PER_LEAD = 10
SDM_BANDS = [(1_000_000, 0.4), (3_000_000, 0.9), (7_000_000, 1.6),
             (float("inf"), 2.2)]

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.12
DEFAULT_MARGIN_PCT = 0.22
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
