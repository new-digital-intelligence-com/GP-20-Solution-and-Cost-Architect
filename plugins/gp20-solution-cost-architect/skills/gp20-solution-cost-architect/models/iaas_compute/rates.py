"""
Rate card — IaaS Compute.
ILLUSTRATIVE DATA ONLY. Synthetic. Not NSC pricing.

Consumption-shaped: the price follows what runs, not who is employed. Two things
make this offering behave unlike the others — consumption ramps as workloads
migrate, so year one is not year three; and a reserved commitment trades
discount against flexibility before the ramp has proved the shape.
"""

CURRENCY = "GBP"
SYMBOL = "£"

# --- Instance catalogue ------------------------------------------------------
INSTANCE_CLASSES = ["small", "medium", "large", "xlarge", "gpu"]
INSTANCE_LABEL = {
    "small": "Small (2 vCPU / 8 GB)", "medium": "Medium (4 vCPU / 16 GB)",
    "large": "Large (8 vCPU / 32 GB)", "xlarge": "XLarge (16 vCPU / 64 GB)",
    "gpu": "GPU accelerated",
}
INSTANCE_HOURLY = {"small": 0.086, "medium": 0.172, "large": 0.344,
                   "xlarge": 0.688, "gpu": 2.450}
INSTANCE_VCPU = {"small": 2, "medium": 4, "large": 8, "xlarge": 16, "gpu": 8}
HOURS_PA = 8_760

# --- Commitment --------------------------------------------------------------
COMMITMENT = ["on_demand", "reserved_1yr", "reserved_3yr"]
COMMITMENT_DISCOUNT = {"on_demand": 1.00, "reserved_1yr": 0.72, "reserved_3yr": 0.59}
COMMITMENT_LABEL = {"on_demand": "On demand",
                    "reserved_1yr": "One-year reserved",
                    "reserved_3yr": "Three-year reserved"}

# --- Resilience --------------------------------------------------------------
AVAILABILITY = ["single_az", "multi_az", "multi_region"]
AVAILABILITY_MULT = {"single_az": 1.00, "multi_az": 1.90, "multi_region": 2.60}
AVAILABILITY_LABEL = {"single_az": "Single availability zone",
                      "multi_az": "Multi-AZ", "multi_region": "Multi-region"}

# Non-production can be powered down outside working hours.
NONPROD_RUNTIME_FACTOR = 0.42

# --- Storage and network -----------------------------------------------------
STORAGE_TIERS = ["performance", "standard", "archive"]
STORAGE_PER_TB_PM = {"performance": 118.0, "standard": 21.0, "archive": 4.2}
EGRESS_PER_TB = 78.0
BACKUP_PER_TB_PM = 9.5
BACKUP_RETENTION_ALLOWED = (7, 30, 90, 365)

# --- Management --------------------------------------------------------------
MANAGED_LEVELS = ["unmanaged", "monitored", "fully_managed"]
MANAGED_LABEL = {"unmanaged": "Client managed",
                 "monitored": "Monitored and patched",
                 "fully_managed": "Fully managed"}
INSTANCES_PER_ENGINEER = {"unmanaged": 0, "monitored": 180, "fully_managed": 65}
TOOLING_PER_INSTANCE_PA = {"unmanaged": 0.0, "monitored": 74.0, "fully_managed": 168.0}

# --- Migration ---------------------------------------------------------------
LANDING_ZONE_DAYS = 35.0
PER_WORKLOAD_DAYS = {"assess": 1.2, "migrate": 3.5, "test": 1.8, "cutover": 0.6}
PM_OVERHEAD_PCT = 0.15
DEFAULT_RAMP_MONTHS = 12

# --- Labour ------------------------------------------------------------------
PRODUCTIVE_HOURS_PA = 1_450
WORKING_DAYS_PA = 220
COUNTRY_RATES = {
    "UK": {"engineer": 610, "architect": 780, "sdm": 720},
    "DE": {"engineer": 640, "architect": 815, "sdm": 760},
    "FR": {"engineer": 595, "architect": 755, "sdm": 700},
    "NL": {"engineer": 625, "architect": 795, "sdm": 740},
    "PL": {"engineer": 340, "architect": 445, "sdm": 430},
}
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)
HUB_PRIMARY = "PL"
SDM_BANDS = [(1_200_000, 0.4), (3_500_000, 0.9), (8_000_000, 1.6), (float("inf"), 2.4)]

# --- Commercial defaults -----------------------------------------------------
OVERHEAD_PCT = 0.09
DEFAULT_MARGIN_PCT = 0.16
DEFAULT_CONTINGENCY_PCT = 0.04
DEFAULT_INDEXATION_PCT = 0.02
DEFAULT_TERM_YEARS = 3
