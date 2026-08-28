"""
Regenerate the sample tenders — one per model pack.

Dev tooling; the tenders ship pre-built. Use this to produce variants, or to
reshape a sample to resemble a real NSC document.

Each tender follows the same design so the skill is exercised the same way for
every offering:

  · the authoritative figures live in an ANNEX, and the prose states them loosely
    ("approximately 100", "circa 14,000") — provenance handling is visible
  · roughly 70% of the pack's parameters are present
  · the pack's declared gaps are deliberately ABSENT, so the clarification
    dialogue has real work to do
  · nothing names the offering in a way that makes pack selection trivial —
    detection has to come from the substance

Usage:  python tools/build_samples.py [output_dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _docgen import render

OUT = Path(__file__).resolve().parent.parent / "samples"


# ===========================================================================
# Managed LAN — gaps: coverage, spares_strategy, install_window, survey_type
# ===========================================================================
MANAGED_LAN = {
    "ref": "AG/2026/NET/114",
    "title": "Managed Local Area Network and Wireless Infrastructure Services",
    "control": [
        ["RFP reference", "AG/2026/NET/114"],
        ["Issue date", "4 August 2026"],
        ["Clarification deadline", "21 August 2026"],
        ["Response deadline", "11 September 2026, 17:00 CET"],
        ["Contract commencement", "1 January 2027"],
        ["Issuing entity", "Aurelian Global Holdings plc"],
    ],
    "sections": [
        {"heading": "1.  Introduction and background", "body": [
            ("p", "Aurelian Global Holdings plc (\"Aurelian\") is a diversified "
                  "industrial and logistics group headquartered in London, operating "
                  "across five European markets. The Group employs circa 14,000 staff "
                  "across approximately 100 locations, comprising regional offices, "
                  "distribution centres, manufacturing facilities and two campus "
                  "headquarters."),
            ("p", "Aurelian's existing local area network estate has reached end of "
                  "vendor support. The Board has approved a Group-wide programme to "
                  "replace both the wired access layer and the wireless infrastructure, "
                  "and to transfer ongoing support of that estate to a single managed "
                  "service provider."),
        ]},
        {"heading": "2.  Scope of services", "body": [
            ("p", "The successful supplier will be responsible for the following:"),
            ("b", ["Design of the target wired and wireless network architecture "
                   "across all in-scope locations.",
                   "Supply, configuration and installation of wireless access points "
                   "and access-layer switching at every location listed in Annex A.",
                   "Decommissioning and environmentally compliant disposal of the "
                   "legacy estate.",
                   "An ongoing managed service covering incident resolution, proactive "
                   "monitoring and end-user support for the duration of the contract.",
                   "On-site engineering attendance where an incident cannot be resolved "
                   "remotely."]),
            ("p", "Structured cabling within each location was renewed in 2024 and is "
                  "considered fit for purpose. Suppliers should assume existing cabling "
                  "is reusable and should not price for recabling."),
        ]},
        {"heading": "3.  Estate", "body": [
            ("p", "The in-scope estate is set out in full in Annex A. Annex A is the "
                  "authoritative statement of the estate for pricing purposes; any "
                  "figures given elsewhere in this document are indicative only."),
            ("p", "Locations are categorised by user population as follows: Small (up "
                  "to 50 users), Medium (51 to 250 users), Large (251 to 1,000 users) "
                  "and Campus (in excess of 1,000 users)."),
            ("p", "Aurelian operates a wireless-first workplace policy. The substantial "
                  "majority of employees connect over wireless; wired ports are required "
                  "principally for access points, printing, building systems and a "
                  "limited number of fixed engineering workstations."),
        ]},
        {"heading": "4.  Service level requirements", "body": [
            ("p", "The following service levels shall apply from the date each location "
                  "is accepted into service:"),
            ("t", [["Ref", "Requirement", "Target"],
                   ["SL-01", "Priority 1 incident — on-site engineer attendance",
                    "4 business hours"],
                   ["SL-02", "Priority 2 incident — remote response", "2 business hours"],
                   ["SL-03", "Proactive infrastructure monitoring",
                    "24 hours a day, 7 days a week"],
                   ["SL-04", "End-user service desk", "Required — multilingual"],
                   ["SL-05", "Network availability at Campus locations", "99.95%"],
                   ["SL-06", "Monthly service reporting",
                    "Within 5 business days of month end"]],
             [1.9, 9.1, 5.0]),
            ("p", "SL-01 applies to all locations irrespective of country or size band. "
                  "Aurelian regards on-site attendance within the stated target as a "
                  "material requirement and not an aspiration.", "i"),
        ]},
        {"heading": "5.  Programme", "body": [
            ("p", "Deployment shall be completed within 9 months of contract "
                  "commencement. Aurelian expects the supplier to sequence the rollout "
                  "so that no single country is disrupted concurrently across more than "
                  "30% of its locations."),
            ("p", "The supplier is required to minimise disruption to Aurelian's "
                  "operations throughout the deployment. Distribution centres in "
                  "particular operate extended shift patterns."),
        ]},
        {"heading": "6.  Commercial requirements", "body": [
            ("p", "The contract will be awarded for an initial term of 5 years. Aurelian "
                  "reserves the right to extend by two further periods of 12 months on "
                  "the same commercial terms."),
            ("p", "Pricing shall be submitted in pounds sterling as a one-off charge "
                  "covering design, supply, installation and transition, and a recurring "
                  "annual charge for the managed service."),
            ("p", "Suppliers shall state clearly any assumptions made in arriving at "
                  "their price, and shall identify any element of the requirement for "
                  "which they consider the information provided to be insufficient."),
        ]},
    ],
    "annex": {
        "heading": "Annex A  —  Site schedule",
        "intro": "The following is the authoritative statement of the in-scope estate.",
        "rows": [["Country", "Small", "Medium", "Large", "Campus", "Total"],
                 ["United Kingdom", 28, 12, 4, 1, 45],
                 ["Germany", 16, 7, 2, 0, 25],
                 ["France", 10, 4, 1, 0, 15],
                 ["Netherlands", 6, 4, 1, 0, 11],
                 ["Poland", 2, 1, 1, 1, 5],
                 ["Total", 62, 28, 9, 2, 101]],
        "widths": [4.4, 2.3, 2.3, 2.3, 2.3, 2.4],
        "notes": [
            "Note: access point counts per location have not been surveyed. Suppliers "
            "should apply their own design standards for coverage and density "
            "appropriate to each size band, and state the resulting quantities.",
            "Total end-user population across the estate is 14,330 as at 1 July 2026.",
        ],
    },
}

# ===========================================================================
# DaaS — gaps: refresh_years, swap_sla, deployment_method,
#              image_strategy, disposal
# ===========================================================================
DAAS = {
    "ref": "AG/2026/EUC/207",
    "title": "End-User Device Provision, Support and Lifecycle Services",
    "control": [
        ["RFP reference", "AG/2026/EUC/207"],
        ["Issue date", "6 August 2026"],
        ["Clarification deadline", "27 August 2026"],
        ["Response deadline", "18 September 2026, 17:00 CET"],
        ["Contract commencement", "1 February 2027"],
        ["Issuing entity", "Aurelian Global Holdings plc"],
    ],
    "sections": [
        {"heading": "1.  Introduction", "body": [
            ("p", "Aurelian Global Holdings plc wishes to move from its current capital "
                  "purchase model for end-user computing to a consumption-based service. "
                  "The Group currently owns and manages roughly seventeen thousand "
                  "devices across five European markets, procured piecemeal over the "
                  "last six years and supported by a mixture of internal teams and "
                  "regional resellers."),
            ("p", "The intent is to transfer supply, imaging, deployment, support and "
                  "end-of-life handling of the entire fleet to a single provider, charged "
                  "on a per-device basis."),
        ]},
        {"heading": "2.  Scope of services", "body": [
            ("b", ["Supply of end-user devices and associated peripherals across the "
                   "device types listed in Annex A.",
                   "Standard operating environment build, testing and maintenance.",
                   "Enrolment, configuration and delivery of devices to end users.",
                   "Migration of user data and settings from the outgoing estate.",
                   "Break-fix support including replacement of failed devices.",
                   "Asset register maintenance and monthly reporting.",
                   "Collection, data destruction and end-of-life handling of the "
                   "outgoing fleet."]),
            ("p", "Mobile telephony airtime and connectivity are out of scope and are "
                  "contracted separately."),
        ]},
        {"heading": "3.  The estate", "body": [
            ("p", "The device fleet in scope is set out in Annex A, which is the "
                  "authoritative statement for pricing purposes. Approximate figures "
                  "given elsewhere in this document are indicative only."),
            ("p", "Aurelian's device policy states that hardware is \"typically "
                  "refreshed every four years\", although in practice the current estate "
                  "contains devices between two and seven years old. Suppliers should "
                  "state the refresh cycle on which their price is based."),
            ("p", "Approximately 14,000 staff are supported. A proportion of employees "
                  "hold both a primary computing device and a smartphone; a small "
                  "number of field-based roles hold a tablet in addition."),
        ]},
        {"heading": "4.  Service requirements", "body": [
            ("t", [["Ref", "Requirement", "Target"],
                   ["EU-01", "Replacement device provided following hardware failure",
                    "Promptly — see note"],
                   ["EU-02", "Service desk response for device incidents",
                    "2 business hours"],
                   ["EU-03", "Asset register accuracy", "99% at quarterly audit"],
                   ["EU-04", "Standard build applied to all delivered devices",
                    "100%"],
                   ["EU-05", "Data destruction certification on collected devices",
                    "Required"],
                   ["EU-06", "Monthly fleet and lifecycle reporting",
                    "Within 5 business days of month end"]],
             [1.9, 9.1, 5.0]),
            ("p", "Note on EU-01: Aurelian has not fixed a replacement time. Suppliers "
                  "should propose a commitment appropriate to a distributed European "
                  "estate and price accordingly, stating clearly what their proposal "
                  "assumes.", "i"),
        ]},
        {"heading": "5.  Deployment", "body": [
            ("p", "The outgoing estate must be replaced within 6 months of contract "
                  "commencement. Aurelian's locations range from single-floor sales "
                  "offices to distribution centres operating extended shifts."),
            ("p", "Aurelian has no fixed position on how devices should reach users and "
                  "invites suppliers to propose an approach. Suppliers should note that "
                  "approximately 18% of the workforce is field-based and attends a "
                  "company location infrequently."),
            ("p", "The Group currently maintains a single standard build. Several "
                  "business units have requested role-specific configurations; no "
                  "decision has been taken."),
        ]},
        {"heading": "6.  Commercial requirements", "body": [
            ("p", "The contract will be awarded for an initial term of 4 years."),
            ("p", "Pricing shall be expressed as a charge per device per month, with "
                  "transition costs shown separately. Suppliers should also state the "
                  "total contract value over the initial term."),
            ("p", "Aurelian holds no position on the treatment of the outgoing fleet. "
                  "Suppliers may propose retention, recycling or a buyback arrangement, "
                  "and should show the effect of their proposal on the monthly charge."),
        ]},
    ],
    "annex": {
        "heading": "Annex A  —  Device schedule",
        "intro": "The following is the authoritative statement of the in-scope fleet.",
        "rows": [["Device type", "UK", "DE", "FR", "NL", "PL", "Total"],
                 ["Standard laptop", 4410, 2450, 1470, 980, 490, 9800],
                 ["Performance laptop", 630, 350, 210, 140, 70, 1400],
                 ["Desktop", 405, 225, 135, 90, 45, 900],
                 ["Tablet", 293, 162, 98, 65, 32, 650],
                 ["Smartphone", 1890, 1050, 630, 420, 210, 4200],
                 ["Total", 7628, 4237, 2543, 1695, 847, 16950]],
        "widths": [4.0, 2.1, 2.1, 2.1, 2.1, 2.1, 2.3],
        "notes": [
            "Total supported user population is 14,330 as at 1 July 2026.",
            "Note: peripheral and accessory requirements have not been specified. "
            "Suppliers should state what their price includes.",
        ],
    },
}

# ===========================================================================
# Service Desk — gaps: coverage, languages, tiers, self_service, fcr_target
# ===========================================================================
SERVICE_DESK = {
    "ref": "AG/2026/SD/311",
    "title": "Single Point of Contact — User Support Services",
    "control": [
        ["RFP reference", "AG/2026/SD/311"],
        ["Issue date", "8 August 2026"],
        ["Clarification deadline", "29 August 2026"],
        ["Response deadline", "22 September 2026, 17:00 CET"],
        ["Contract commencement", "1 March 2027"],
        ["Issuing entity", "Aurelian Global Holdings plc"],
    ],
    "sections": [
        {"heading": "1.  Introduction", "body": [
            ("p", "Aurelian Global Holdings plc currently operates four separate user "
                  "support functions, inherited through acquisition and organised by "
                  "country rather than by service. Users in different markets receive "
                  "materially different levels of service, and the Group has no "
                  "consolidated view of demand."),
            ("p", "This tender seeks a single point of contact for all user support "
                  "across the Group, replacing the existing arrangements."),
        ]},
        {"heading": "2.  Scope of services", "body": [
            ("b", ["First-line receipt, triage and resolution of user contacts across "
                   "all supported channels.",
                   "Incident and request management within the Group's ITSM platform.",
                   "Escalation to specialist resolver groups where first-line "
                   "resolution is not achieved.",
                   "Maintenance of a knowledge base and user-facing support content.",
                   "Monthly reporting on volume, resolution and satisfaction."]),
            ("p", "Aurelian retains its own specialist application-support teams. The "
                  "boundary between the supplier's responsibility and those teams has "
                  "not been fixed and forms part of the response."),
        ]},
        {"heading": "3.  Population and demand", "body": [
            ("p", "The supported population is set out in Annex A, which is the "
                  "authoritative statement for pricing purposes."),
            ("p", "The Group supports circa 14,000 staff and an estate of roughly "
                  "seventeen thousand end-user devices. Historic contact volume is not "
                  "reliably recorded across all four existing functions; suppliers "
                  "should state the volume assumption underpinning their price."),
            ("p", "Contacts arrive predominantly by telephone and email, with a growing "
                  "proportion through the self-service portal. Two campus locations "
                  "operate a walk-up technology bar."),
        ]},
        {"heading": "4.  Service requirements", "body": [
            ("t", [["Ref", "Requirement", "Target"],
                   ["SD-01", "Telephone answered", "80% within 30 seconds"],
                   ["SD-02", "Email and portal contacts acknowledged",
                    "1 business hour"],
                   ["SD-03", "Priority 1 incident response", "15 minutes"],
                   ["SD-04", "Service availability",
                    "Aligned to business hours in each market — see note"],
                   ["SD-05", "User satisfaction", "4.2 of 5 rolling quarterly"],
                   ["SD-06", "Monthly service reporting",
                    "Within 5 business days of month end"]],
             [1.9, 9.1, 5.0]),
            ("p", "Note on SD-04: Aurelian's distribution centres and two manufacturing "
                  "sites operate outside standard office hours. The Group has not "
                  "determined whether support should extend to those hours for all "
                  "users or only for those populations, and invites suppliers to "
                  "propose an approach with the cost of each shown.", "i"),
        ]},
        {"heading": "5.  Language and locations", "body": [
            ("p", "Aurelian operates in the United Kingdom, Germany, France, the "
                  "Netherlands and Poland. English is the Group's business language and "
                  "is used for all internal reporting."),
            ("p", "Employee feedback in the 2025 engagement survey identified support "
                  "in local language as a significant dissatisfier in the German and "
                  "French businesses. Aurelian has taken no decision on which languages "
                  "must be answered natively and invites suppliers to set out the "
                  "options and their cost."),
            ("p", "The supplier may deliver from any location provided data-protection "
                  "obligations are met. Aurelian has no requirement for support to be "
                  "delivered in-country."),
        ]},
        {"heading": "6.  Commercial requirements", "body": [
            ("p", "The contract will be awarded for an initial term of 3 years."),
            ("p", "Pricing shall be expressed per supported user per month, with "
                  "transition costs shown separately."),
            ("p", "Aurelian is interested in the role automation and self-service could "
                  "play in reducing contact volume, but has made no investment decision. "
                  "Suppliers should state what their price assumes."),
        ]},
    ],
    "annex": {
        "heading": "Annex A  —  Supported population",
        "intro": "The following is the authoritative statement of the population in scope.",
        "rows": [["Country", "Users", "Devices", "Locations"],
                 ["United Kingdom", 6448, 7628, 45],
                 ["Germany", 3583, 4237, 25],
                 ["France", 2150, 2543, 15],
                 ["Netherlands", 1433, 1695, 11],
                 ["Poland", 716, 847, 5],
                 ["Total", 14330, 16950, 101]],
        "widths": [4.6, 3.4, 3.4, 3.4],
        "notes": [
            "Figures as at 1 July 2026.",
            "Note: the existing functions do not record contact volume on a comparable "
            "basis. No consolidated historic volume is available.",
        ],
    },
}

# ===========================================================================
# IaaS Compute — gaps: commitment, availability, managed_level,
#                      ramp_months, backup_retention_days
# ===========================================================================
IAAS = {
    "ref": "AG/2026/IAAS/402",
    "title": "Data Centre Exit and Hosted Compute Services",
    "control": [
        ["RFP reference", "AG/2026/IAAS/402"],
        ["Issue date", "11 August 2026"],
        ["Clarification deadline", "1 September 2026"],
        ["Response deadline", "25 September 2026, 17:00 CET"],
        ["Contract commencement", "1 April 2027"],
        ["Issuing entity", "Aurelian Global Holdings plc"],
    ],
    "sections": [
        {"heading": "1.  Introduction", "body": [
            ("p", "Aurelian Global Holdings plc operates two owned data centres in the "
                  "United Kingdom and Germany. The lease on the German facility expires "
                  "in September 2028 and will not be renewed; the UK facility requires "
                  "significant mechanical and electrical investment to remain viable "
                  "beyond 2029."),
            ("p", "The Board has approved an exit from both facilities and the migration "
                  "of all workloads to hosted infrastructure."),
        ]},
        {"heading": "2.  Scope of services", "body": [
            ("b", ["Assessment and migration planning for the workloads listed in "
                   "Annex A.",
                   "Design and build of the target hosting environment.",
                   "Migration, testing and cutover of all in-scope workloads.",
                   "Provision of compute, storage and network capacity for the term.",
                   "Backup and recovery services.",
                   "Decommissioning support for the vacated facilities."]),
            ("p", "Application remediation and any re-platforming beyond a like-for-like "
                  "migration are out of scope and will be handled by Aurelian's "
                  "application teams."),
        ]},
        {"heading": "3.  The estate", "body": [
            ("p", "The current estate is set out in Annex A, which is the authoritative "
                  "statement for pricing purposes. Approximate figures elsewhere in "
                  "this document are indicative."),
            ("p", "The estate comprises roughly five hundred and fifty virtual machines "
                  "supporting around two hundred distinct workloads. Non-production "
                  "environments represent approximately 60% of the production footprint "
                  "and are not required outside working hours."),
            ("p", "Storage is tiered across performance, standard and archive classes. "
                  "Monthly outbound data transfer averages 42 TB."),
        ]},
        {"heading": "4.  Service requirements", "body": [
            ("t", [["Ref", "Requirement", "Target"],
                   ["IA-01", "Platform availability", "99.9%"],
                   ["IA-02", "Recovery time objective — tier 1 workloads", "4 hours"],
                   ["IA-03", "Recovery point objective — tier 1 workloads", "1 hour"],
                   ["IA-04", "Backup retention", "See note"],
                   ["IA-05", "Capacity reporting", "Monthly"],
                   ["IA-06", "Security patching of the hosting platform",
                    "Within vendor guidance"]],
             [1.9, 9.1, 5.0]),
            ("p", "Note on IA-04: Aurelian's records-retention policy is under review "
                  "following a regulatory change in the German business. Suppliers "
                  "should price a stated retention period and show the incremental cost "
                  "of longer alternatives.", "i"),
            ("p", "Aurelian has stated an availability target but has not specified the "
                  "resilience architecture required to achieve it. Suppliers should set "
                  "out what their proposal assumes.", "i"),
        ]},
        {"heading": "5.  Programme", "body": [
            ("p", "The German facility must be vacated by 30 September 2028. The UK "
                  "facility should follow within a further twelve months."),
            ("p", "Aurelian's application teams have limited capacity to support "
                  "concurrent migration activity, and the Group's change freeze runs "
                  "from mid-November to early January each year. Suppliers should "
                  "propose a migration profile consistent with these constraints and "
                  "state the assumptions on which their consumption forecast is based."),
        ]},
        {"heading": "6.  Commercial requirements", "body": [
            ("p", "The contract will be awarded for an initial term of 5 years."),
            ("p", "Pricing shall separate one-off migration charges from recurring "
                  "consumption. Suppliers should state clearly the basis on which "
                  "consumption is charged and how it varies across the term."),
            ("p", "Aurelian is willing to consider capacity commitments in exchange for "
                  "reduced unit rates but has taken no decision. Suppliers should "
                  "present the options available and the trade-off each involves."),
            ("p", "Aurelian's platform operations team will be retained in some form. "
                  "The division of operational responsibility between that team and the "
                  "supplier has not been determined."),
        ]},
    ],
    "annex": {
        "heading": "Annex A  —  Infrastructure inventory",
        "intro": "The following is the authoritative statement of the estate in scope.",
        "rows": [["Class", "Specification", "Production", "Non-production", "Total"],
                 ["Small", "2 vCPU / 8 GB", 150, 90, 240],
                 ["Medium", "4 vCPU / 16 GB", 113, 67, 180],
                 ["Large", "8 vCPU / 32 GB", 59, 36, 95],
                 ["XLarge", "16 vCPU / 64 GB", 18, 10, 28],
                 ["GPU", "8 vCPU / 61 GB + GPU", 6, 0, 6],
                 ["Total", "", 346, 203, 549]],
        "widths": [2.8, 4.6, 2.9, 3.1, 2.6],
        "notes": [
            "Storage: 180 TB performance, 640 TB standard, 2,100 TB archive.",
            "Outbound data transfer: 42 TB per month averaged over the last 12 months.",
            "Distinct workloads in scope: 210.",
            "Note: the non-production column is included in the totals above and is "
            "not required outside working hours.",
        ],
    },
}


SPECS = [
    ("RFP_Aurelian_Global_Managed_LAN.docx", MANAGED_LAN),
    ("RFP_Aurelian_Global_Device_Services.docx", DAAS),
    ("RFP_Aurelian_Global_Service_Desk.docx", SERVICE_DESK),
    ("RFP_Aurelian_Global_Data_Centre_Exit.docx", IAAS),
]


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    for filename, spec in SPECS:
        print("Written:", render(spec, str(out_dir / filename)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
