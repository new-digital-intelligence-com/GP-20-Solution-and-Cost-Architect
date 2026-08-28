"""
Rate card — Service Desk and Remote Support.
ILLUSTRATIVE DATA ONLY. Synthetic. Not NSC pricing.

Shaped by two forces that pull in different directions: contact volume, and the
minimum staffing each supported language needs to hold a coverage window. Where
the second exceeds the first, language commitments — not demand — set the price.
"""

CURRENCY = "GBP"
SYMBOL = "£"

# --- Demand ------------------------------------------------------------------
CONTACTS_PER_USER_PA = 6.4
# A device-heavy estate generates more than a user count alone implies.
CONTACTS_PER_DEVICE_PA = 0.9

CHANNELS = ["phone", "email", "chat", "portal", "walk_up"]
CHANNEL_AHT_MINUTES = {          # average handling time, first line
    "phone": 11.5, "email": 9.0, "chat": 13.5, "portal": 6.0, "walk_up": 15.0,
}
DEFAULT_CHANNEL_MIX = {"phone": 0.42, "email": 0.24, "chat": 0.18,
                       "portal": 0.14, "walk_up": 0.02}

# Share of contacts never reaching an agent.
DEFLECTION = {"none": 0.00, "knowledge_base": 0.12, "ai_assistant": 0.31}

# --- Escalation --------------------------------------------------------------
ESCALATION_RATE = {"l1_only": 0.00, "l1_l2": 0.18, "l1_l2_l3": 0.18}
L3_SHARE_OF_L2 = 0.22            # of escalated contacts, share reaching third line
L2_AHT_MINUTES = 38.0
L3_AHT_MINUTES = 95.0
TIER_LABEL = {"l1_only": "First line only",
              "l1_l2": "First and second line",
              "l1_l2_l3": "First, second and third line"}

# --- Coverage ----------------------------------------------------------------
COVERAGE_HOURS_PW = {"8x5": 40, "12x5": 60, "24x7": 168, "24x7x365": 168}
# FTE needed to hold one seat continuously, allowing leave and training.
PRESENCE_FTE_PER_SEAT = {"8x5": 1.15, "12x5": 1.70, "24x7": 4.80, "24x7x365": 5.20}
COVERAGE_LABEL = {"8x5": "8×5 business hours", "12x5": "12×5 extended day",
                  "24x7": "24×7", "24x7x365": "24×7×365 including public holidays"}

# --- Language ----------------------------------------------------------------
# Each supported language needs at least one staffed seat across the coverage
# window — you cannot answer German with a fraction of a person.
LANGUAGES_SUPPORTED = ["EN", "DE", "FR", "NL", "PL", "ES", "IT"]
LANGUAGE_HOME = {"EN": "UK", "DE": "DE", "FR": "FR", "NL": "NL",
                 "PL": "PL", "ES": "PL", "IT": "PL"}
# Premium on the agent rate for a language delivered outside its home country.
NEARSHORE_LANGUAGE_PREMIUM = 0.18

# --- Quality -----------------------------------------------------------------
FCR_TARGET_UPLIFT = {0.65: 1.00, 0.75: 1.09, 0.85: 1.22}
FCR_ALLOWED = (0.65, 0.75, 0.85)

# --- Productivity ------------------------------------------------------------
PRODUCTIVE_HOURS_PA = 1_380      # lower than field roles: shrinkage, breaks, training
OCCUPANCY = 0.72                 # agents cannot be on contacts 100% of the time
WORKING_DAYS_PA = 220

# --- Labour ------------------------------------------------------------------
COUNTRY_RATES = {
    #        L1 agent  L2 analyst  L3 engineer  team lead  sdm
    "UK": {"l1": 300, "l2": 415, "l3": 560, "lead": 470, "sdm": 720},
    "DE": {"l1": 325, "l2": 445, "l3": 590, "lead": 500, "sdm": 760},
    "FR": {"l1": 305, "l2": 420, "l3": 545, "lead": 465, "sdm": 700},
    "NL": {"l1": 320, "l2": 435, "l3": 575, "lead": 490, "sdm": 740},
    "PL": {"l1": 168, "l2": 245, "l3": 310, "lead": 275, "sdm": 430},
}
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)
HUB_PRIMARY = "PL"

AGENTS_PER_TEAM_LEAD = 12
SDM_BANDS = [(900_000, 0.4), (2_500_000, 0.8), (6_000_000, 1.5), (float("inf"), 2.2)]

# --- Tooling -----------------------------------------------------------------
ITSM_PER_AGENT_PA = 1_150.0
TELEPHONY_PER_AGENT_PA = 640.0
KNOWLEDGE_PLATFORM_PA = 18_000.0
AI_ASSISTANT_PA = 46_000.0       # only when deflection = ai_assistant

# --- Transition --------------------------------------------------------------
KNOWLEDGE_CAPTURE_DAYS = 22.0
RUNBOOK_DAYS_PER_LANGUAGE = 6.0
TRAINING_DAYS_PER_AGENT = 7.0
PARALLEL_RUN_WEEKS = {"none": 0, "knowledge_base": 2, "ai_assistant": 4}
PM_OVERHEAD_PCT = 0.16

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.13
DEFAULT_MARGIN_PCT = 0.24
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
DEFAULT_ONBOARDING_MONTHS = 3
