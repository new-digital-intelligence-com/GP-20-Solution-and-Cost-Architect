"""Exercise cases for the conformance suite. Every case must be valid input."""

CASES = [
    ("Aurelian — data centre exit, 3yr reserved, 18-month ramp", {
        "client_name": "Aurelian Global Holdings plc",
        "rfp_ref": "AG/2026/IAAS/402",
        "term_years": 5,
        "instances": {"small": 240, "medium": 180, "large": 95,
                      "xlarge": 28, "gpu": 6},
        "nonprod_ratio": 0.6,
        "storage_tb": {"performance": 180, "standard": 640, "archive": 2100},
        "egress_tb_pm": 42,
        "commitment": "reserved_3yr", "availability": "multi_az",
        "managed_level": "fully_managed", "backup_retention_days": 90,
        "workloads": 210, "ramp_months": 18, "delivery_country": "PL",
        "_sources": {"instances": "rfp", "storage_tb": "rfp", "term_years": "rfp",
                     "workloads": "rfp"},
    }),
    ("Small on-demand estate, single AZ, unmanaged", {
        "client_name": "Test B", "term_years": 3,
        "instances": {"small": 40, "medium": 12},
        "storage_tb": {"standard": 25},
        "commitment": "on_demand", "availability": "single_az",
        "managed_level": "unmanaged", "backup_retention_days": 30,
        "ramp_months": 6,
    }),
    ("Multi-region, 1yr reserved, long retention", {
        "client_name": "Test C", "term_years": 4,
        "instances": {"large": 60, "xlarge": 40, "gpu": 14},
        "nonprod_ratio": 0.35,
        "storage_tb": {"performance": 90, "standard": 300},
        "egress_tb_pm": 110,
        "commitment": "reserved_1yr", "availability": "multi_region",
        "managed_level": "monitored", "backup_retention_days": 365,
        "workloads": 85, "ramp_months": 24, "delivery_country": "UK",
    }),
]
