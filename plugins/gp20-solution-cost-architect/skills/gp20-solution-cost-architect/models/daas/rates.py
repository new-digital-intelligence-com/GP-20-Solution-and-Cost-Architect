"""
Rate card — Device as a Service.
ILLUSTRATIVE DATA ONLY. Synthetic. Not NSC pricing.

Structurally unlike managed LAN: the dominant cost is hardware amortised over a
refresh cycle, not standing labour. Labour is a minority of the price, and the
buying metric is £ per device per month.
"""

CURRENCY = "GBP"
SYMBOL = "£"

# --- Device catalogue --------------------------------------------------------
DEVICE_TYPES = ["laptop_standard", "laptop_performance", "desktop", "tablet", "phone"]

DEVICE_LABEL = {
    "laptop_standard": "Standard laptop",
    "laptop_performance": "Performance laptop",
    "desktop": "Desktop",
    "tablet": "Tablet",
    "phone": "Smartphone",
}
DEVICE_UNIT_COST = {
    "laptop_standard": 950.0, "laptop_performance": 1_650.0,
    "desktop": 780.0, "tablet": 620.0, "phone": 540.0,
}
# Annual probability a device needs a swap or on-site intervention.
FAILURE_RATE_PA = {
    "laptop_standard": 0.11, "laptop_performance": 0.13,
    "desktop": 0.06, "tablet": 0.09, "phone": 0.14,
}
# Residual value recovered at refresh, as a share of original unit cost.
BUYBACK_PCT = {
    "laptop_standard": 0.14, "laptop_performance": 0.18,
    "desktop": 0.06, "tablet": 0.11, "phone": 0.16,
}

REFRESH_YEARS_ALLOWED = (3, 4, 5)
DEFAULT_REFRESH_YEARS = 4

# --- Accessories -------------------------------------------------------------
ACCESSORY_LEVEL = {"none": 0.0, "basic": 95.0, "standard": 190.0, "premium": 340.0}
ACCESSORY_REFRESH_YEARS = 5

# --- Software / management ---------------------------------------------------
MDM_PER_DEVICE_PA = 42.0
ASSET_MGMT_FIXED_PA = 25_000.0
ASSET_MGMT_PER_DEVICE_PA = 3.5

# --- Deployment --------------------------------------------------------------
IMAGE_BUILD_DAYS_PER_VARIANT = 12.0
IMAGE_VARIANTS = {"standard": 1, "custom": 3, "per_persona": 6}

ENROLMENT_MINUTES_PER_DEVICE = 18.0
DEPLOY_MINUTES_PER_DEVICE = {"desk_side": 45.0, "ship_to_user": 12.0, "depot_collect": 25.0}
SHIPPING_COST_PER_DEVICE = {"desk_side": 0.0, "ship_to_user": 24.0, "depot_collect": 11.0}
DATA_MIGRATION_MINUTES_PER_USER = 35.0
LEGACY_COLLECTION_PER_DEVICE = 8.5
PM_OVERHEAD_PCT = 0.14

# --- Break-fix ---------------------------------------------------------------
SWAP_MINUTES = {"next_business_day": 40.0, "8h": 55.0, "4h": 75.0}
SWAP_RESPONSE = {
    "next_business_day": "Next business day swap",
    "8h": "8 business hour swap",
    "4h": "4 business hour swap",
}
SWAP_SLA_MULTIPLIER = {"next_business_day": 1.00, "8h": 1.25, "4h": 1.65}
SWAP_LOGISTICS_COST = {"next_business_day": 18.0, "8h": 31.0, "4h": 58.0}
# Spare pool held as a share of fleet, to make the committed swap time deliverable.
SPARE_POOL_PCT = {"next_business_day": 0.02, "8h": 0.04, "4h": 0.07}

# --- Service desk ------------------------------------------------------------
SD_CONTACTS_PER_DEVICE_PA = 1.8
SD_MINUTES_PER_CONTACT = 13.0

# --- Labour ------------------------------------------------------------------
PRODUCTIVE_HOURS_PA = 1_450
WORKING_DAYS_PA = 220

COUNTRY_RATES = {
    #            field tech  service desk  engineer (build)  sdm
    "UK": {"tech": 420, "service_desk": 330, "engineer": 560, "sdm": 720},
    "DE": {"tech": 445, "service_desk": 355, "engineer": 590, "sdm": 760},
    "FR": {"tech": 410, "service_desk": 335, "engineer": 545, "sdm": 700},
    "NL": {"tech": 435, "service_desk": 350, "engineer": 575, "sdm": 740},
    "PL": {"tech": 235, "service_desk": 185, "engineer": 310, "sdm": 430},
}
HUB_PRIMARY = "PL"
HUB_SECONDARY = "UK"
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)

SDM_BANDS = [(1_500_000, 0.5), (4_000_000, 1.0), (9_000_000, 1.8), (float("inf"), 2.5)]

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.11
DEFAULT_MARGIN_PCT = 0.19
DEFAULT_CONTINGENCY_PCT = 0.04
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 4
DEFAULT_ROLLOUT_MONTHS = 6
