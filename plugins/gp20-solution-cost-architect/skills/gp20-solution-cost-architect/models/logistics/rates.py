"""
Logistics tower — rate card.

ILLUSTRATIVE DATA ONLY. Synthetic rates for demonstration. Not NSC pricing.

This tower prices parts and their movement: spares holding, forward stock,
shipping, RMA and repair, staging, and end-of-life disposal. It does not price
the engineer who fits the part (`field-service`) or the person who decided one
was needed (`remote-support`).

The tower exists because a committed fix time is a *stock* commitment before it
is a labour commitment. An engineer standing next to a broken switch with no
spare has not met a four-hour fix.
"""

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

# --- Stock strategy -----------------------------------------------------------
# Pool value as a share of the estate's replacement value, and how many stocking
# locations each strategy implies.
STOCK_STRATEGY = {
    "none":     {"pool_pct": 0.000, "locations": 0, "label": "No spares held"},
    "central":  {"pool_pct": 0.025, "locations": 1, "label": "Central stock"},
    "regional": {"pool_pct": 0.045, "locations": 2, "label": "Regional stock"},
    "forward":  {"pool_pct": 0.070, "locations": 0, "label": "Forward stock per country"},
    "onsite":   {"pool_pct": 0.115, "locations": 0, "label": "On-site stock"},
}
# `forward` stocks one location per country; `onsite` one per large/campus site.
FORWARD_PER_COUNTRY = True
ONSITE_BANDS = ("large", "campus")

# What each strategy can actually support. A tender committing to a four-hour
# fix on central stock is committing to something the supply chain cannot do.
FIX_TIME_SUPPORTED = {
    "none": "best endeavours, vendor RMA only",
    "central": "next business day",
    "regional": "same day in region",
    "forward": "4 hours in country",
    "onsite": "1 hour at stocked sites",
}
# Minimum strategy a committed on-site fix tier requires.
TIER_MIN_STRATEGY = {"bronze": "central", "silver": "central",
                     "gold": "forward", "platinum": "onsite"}
STRATEGY_RANK = {"none": 0, "central": 1, "regional": 2, "forward": 3, "onsite": 4}

# --- Holding cost -------------------------------------------------------------
# Annual cost of holding stock, as a share of pool value: capital, insurance,
# obsolescence, shrinkage.
CARRYING_PCT_PA = 0.185
STOCK_REFRESH_YEARS = 5          # the pool itself is replaced on this cycle

# --- Locations ----------------------------------------------------------------
WAREHOUSE_FIXED_PA = {"central": 96_000.0, "regional": 58_000.0,
                      "forward": 21_000.0, "onsite": 1_450.0}
WAREHOUSE_PER_SQM_PA = 132.0
SQM_PER_1K_UNITS = 14.0

# --- Movement -----------------------------------------------------------------
PARTS_PER_DISPATCH = 0.62        # not every visit consumes a part
SHIPMENT_COST = {"standard": 14.5, "next_day": 27.0, "same_day": 78.0}
SHIPMENT_TIER = {"none": "standard", "central": "next_day",
                 "regional": "next_day", "forward": "same_day",
                 "onsite": "standard"}
RETURN_RATE = 0.86               # share of swapped parts returned for triage

# --- Repair vs replace --------------------------------------------------------
RMA_HANDLING_COST = 31.0         # per unit triaged and shipped to vendor
REPAIRABLE_SHARE = 0.58
REPAIR_COST_PCT = 0.34           # of unit value, when repaired
WARRANTY_RECOVERY_PCT = 0.41     # share of failures recovered under warranty

# --- Staging and disposal -----------------------------------------------------
STAGING_COST_PER_DEVICE = 22.0   # build, asset-tag, kit for deployment
DISPOSAL_COST_PER_DEVICE = 8.5
DISPOSAL_MODE = {"none": 0.0, "recycle": 1.0, "secure_erase": 1.9}
DISPOSAL_LABEL = {"none": "Client retains disposal",
                  "recycle": "Certified recycling",
                  "secure_erase": "Secure erasure and certified disposal"}

# --- Labour -------------------------------------------------------------------
UNITS_PER_STOREKEEPER_PA = 4_200
PRODUCTIVE_HOURS_PA = 1_450
WORKING_DAYS_PA = 220
COUNTRY_RATES = {
    "UK": {"store": 280, "planner": 430, "sdm": 720},
    "DE": {"store": 305, "planner": 465, "sdm": 760},
    "FR": {"store": 285, "planner": 435, "sdm": 700},
    "NL": {"store": 295, "planner": 450, "sdm": 740},
    "PL": {"store": 165, "planner": 265, "sdm": 430},
}
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)
HUB_PRIMARY = "PL"
PLANNER_PER_LOCATION = 0.35
SDM_BANDS = [(1_000_000, 0.3), (3_000_000, 0.7), (float("inf"), 1.2)]

# --- Mobilisation (one-off) ---------------------------------------------------
SETUP_DAYS_PER_LOCATION = 6.0
SYSTEM_INTEGRATION_DAYS = 24.0
PM_OVERHEAD_PCT = 0.15
DEFAULT_MOBILISATION_MONTHS = 3

# --- Commercial defaults ------------------------------------------------------
OVERHEAD_PCT = 0.12
DEFAULT_MARGIN_PCT = 0.22
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
