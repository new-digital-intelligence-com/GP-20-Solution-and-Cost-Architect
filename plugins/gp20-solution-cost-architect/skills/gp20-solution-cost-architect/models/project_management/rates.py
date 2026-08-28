"""
Project Management tower — rate card.

ILLUSTRATIVE DATA ONLY. Synthetic rates for demonstration. Not NSC pricing.

This tower prices the **programme**: transition into service, cross-lot
governance, the service management office that runs the contract after go-live.

It does not price the delivery management inside each lot. Every other tower
already carries its own Service Delivery Manager, and pricing that person twice
is the single easiest mistake to make when governance becomes a lot of its own.
The boundary is deliberate and stated in the pack docstring.
"""

CURRENCY = "GBP"
CURRENCY_SYMBOL = "£"

# --- Transition (one-off) ----------------------------------------------------
BASE_TRANSITION_DAYS = 85.0            # any transition at all costs this much
DAYS_PER_LOT = 34.0                    # before the shared-effort discount
DAYS_PER_COUNTRY = 12.0
DAYS_PER_100_SITES = 26.0
DAYS_PER_1K_USERS = 4.5

# Governance does not scale linearly with lots. The second lot reuses the
# programme, the governance model, the reporting pack and the client
# relationship built for the first. Effort per lot decays; the *total* still
# rises, which is the point — but a bid that charges full programme effort per
# lot is uncompetitive and wrong.
LOT_SCALING_EXPONENT = 0.62            # effort ∝ lots ** this

COMPLEXITY = {
    "low":      {"factor": 0.85, "label": "Single-vendor, stable scope"},
    "standard": {"factor": 1.00, "label": "Multi-vendor, defined scope"},
    "high":     {"factor": 1.35, "label": "Incumbent transition, TUPE or "
                                          "regulated environment"},
}

# --- Transition role mix ------------------------------------------------------
ROLE_SHARE = {"programme_manager": 0.22, "transition_manager": 0.30,
              "pmo_analyst": 0.28, "service_architect": 0.20}

# --- Run phase: the service management office ---------------------------------
# Continuing governance once the service is live: reporting, service review,
# CSI, contract management.
SMO_BASE_FTE = 0.8
SMO_FTE_PER_LOT = 0.35
SMO_LOT_SCALING_EXPONENT = 0.70
SMO_FTE_PER_COUNTRY = 0.10
REPORTING_LEVEL = {
    "standard": {"factor": 1.00, "label": "Monthly service review and SLA pack"},
    "enhanced": {"factor": 1.40, "label": "Weekly operational plus monthly "
                                          "board reporting"},
    "regulated": {"factor": 1.85, "label": "Audited reporting with evidence "
                                           "retention"},
}
SMO_ROLE_SHARE = {"service_manager": 0.45, "pmo_analyst": 0.35,
                  "contract_manager": 0.20}

# --- Tooling ------------------------------------------------------------------
PPM_TOOLING_PA = 18_500.0              # programme and portfolio management
REPORTING_PLATFORM_PA = 26_000.0       # only at enhanced or regulated

# --- Country rate card (loaded day rates, GBP) -------------------------------
COUNTRY_RATES = {
    "UK": {"programme_manager": 905, "transition_manager": 780,
           "pmo_analyst": 470, "service_architect": 850,
           "service_manager": 700, "contract_manager": 645},
    "DE": {"programme_manager": 950, "transition_manager": 820,
           "pmo_analyst": 495, "service_architect": 890,
           "service_manager": 740, "contract_manager": 680},
    "FR": {"programme_manager": 880, "transition_manager": 760,
           "pmo_analyst": 455, "service_architect": 830,
           "service_manager": 685, "contract_manager": 625},
    "NL": {"programme_manager": 925, "transition_manager": 795,
           "pmo_analyst": 480, "service_architect": 865,
           "service_manager": 715, "contract_manager": 660},
    "PL": {"programme_manager": 545, "transition_manager": 460,
           "pmo_analyst": 275, "service_architect": 520,
           "service_manager": 410, "contract_manager": 380},
}
SUPPORTED_COUNTRIES = list(COUNTRY_RATES)
HUB_PRIMARY = "UK"                     # governance sits with the client, not offshore

WORKING_DAYS_PA = 220

# --- Commercial defaults ------------------------------------------------------
OVERHEAD_PCT = 0.12
DEFAULT_MARGIN_PCT = 0.22
DEFAULT_CONTINGENCY_PCT = 0.05
DEFAULT_INDEXATION_PCT = 0.03
DEFAULT_TERM_YEARS = 3
DEFAULT_TRANSITION_MONTHS = 6
