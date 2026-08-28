"""
Model pack — Managed LAN / WLAN rollout with an attached field-support wrap.

Owns: the parameters, the rate card (rates.py) and the arithmetic.
Owns nothing else. Reading, clarification, artefacts and governance belong to
the skill and are identical for every offering.

ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.contract import (Gap, GapOption, Manifest, ValidationError, assumption,
                           bom_line, build_result, cost_line, deployment_block,
                           kv, resource, run_block, scope_item)

from . import rates as R

# ---------------------------------------------------------------------------

MANIFEST = Manifest(
    key="managed-lan",
    name="Managed LAN / WLAN with field support",
    summary="Wired and wireless access-layer refresh plus an ongoing managed "
            "service with on-site engineering attendance.",
    detect=[
        "wireless", "wlan", "access point", "local area network", "lan refresh",
        "managed lan", "naas", "network as a service", "switching",
        "access layer", "wi-fi", "wifi", "structured cabling", "site survey",
    ],
    material=["sla_tier", "coverage", "spares_strategy", "margin_pct", "term_years"],
    notes="Sizing is driven by two independent forces: incident volume, and the "
          "standing presence a committed on-site response time requires. Where "
          "the second exceeds the first, coverage — not workload — sets the price.",
    gaps=[
        Gap(
            param="coverage",
            question="What coverage window should the field and service-desk "
                     "resource be sized for?",
            rfp_hint="Tenders often state 24×7 for monitoring while expressing "
                     "response targets in business hours. Those are different "
                     "commitments; check which one governs field attendance.",
            options=[
                GapOption("8x5", "8×5 — business hours",
                          "Single shift. Cheapest, and adequate where the SLA "
                          "targets are themselves expressed in business hours."),
                GapOption("12x5", "12×5 — extended business day",
                          "Roughly 1.7 FTE per staffed post. Covers early and "
                          "late shifts without weekend cover."),
                GapOption("24x7", "24×7 — follow the sun",
                          "Roughly 4.8 FTE per staffed post, in every country "
                          "with a committed on-site response. The single largest "
                          "cost lever in this offering."),
            ],
        ),
        Gap(
            param="spares_strategy",
            question="What spares model should be priced?",
            rfp_hint="Rarely stated. A committed on-site fix time usually implies "
                     "at least regional stockholding.",
            options=[
                GapOption("none", "No spares held",
                          "Zero carrying cost; on-site fix times depend entirely "
                          "on vendor RMA and cannot be committed."),
                GapOption("central", "Central stock",
                          "2.5% of hardware value. One hub, next-day dispatch."),
                GapOption("regional", "Regional stockholding",
                          "4.5% of hardware value. Supports same-day fix across "
                          "multiple countries."),
                GapOption("onsite", "On-site spares at every location",
                          "8.5% of hardware value. Fastest restoration, highest "
                          "carrying cost — usually only justified at Campus sites."),
            ],
        ),
        Gap(
            param="install_window",
            question="What install window should the deployment be priced at?",
            rfp_hint="Look for language about minimising disruption, or sites "
                     "running extended shift patterns.",
            options=[
                GapOption("business_hours", "Business hours",
                          "No uplift. Assumes locations tolerate daytime works."),
                GapOption("out_of_hours", "Out of hours",
                          "×1.35 on installation labour. Only the one-off charge "
                          "moves; the run rate is unaffected."),
            ],
        ),
        Gap(
            param="survey_type",
            question="What survey approach should be priced?",
            rfp_hint="If the RFP says access-point counts are unsurveyed and "
                     "leaves design standards to the supplier, the quantities you "
                     "state become a commitment.",
            options=[
                GapOption("predictive", "Predictive only",
                          "0.020 days per AP. Cheapest; carries the most design "
                          "risk against a committed AP count."),
                GapOption("hybrid", "Predictive plus on-site sample",
                          "0.035 days per AP. Validates the large and campus "
                          "sites, designs the small ones predictively."),
                GapOption("onsite", "Full on-site survey",
                          "0.055 days per AP. Lowest design risk, highest "
                          "mobilisation cost."),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------
# Input normalisation
# ---------------------------------------------------------------------------

def _normalise(params: dict) -> tuple[dict, list[dict]]:
    src = params.get("_sources", {})
    reg: list[dict] = []
    p: dict[str, Any] = {}

    def take(key, default, note=""):
        if params.get(key) is not None:
            reg.append(assumption(key, params[key], src.get(key, "user"), note))
            return params[key]
        reg.append(assumption(key, default, "default", note))
        return default

    p["client_name"] = take("client_name", "Unnamed Client")
    p["rfp_ref"] = take("rfp_ref", "n/a")
    p["term_years"] = int(take("term_years", R.DEFAULT_TERM_YEARS))
    p["rollout_months"] = int(take("rollout_months", R.DEFAULT_ROLLOUT_MONTHS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")

    sites_in = params.get("sites") or {}
    sites = {b: int(sites_in.get(b, 0) or 0) for b in R.SITE_BANDS}
    if sum(sites.values()) == 0:
        raise ValidationError("At least one site must be specified.")
    for b in R.SITE_BANDS:
        if sites[b]:
            reg.append(assumption(f"sites.{b}", sites[b], src.get("sites", "user")))
    p["sites"] = sites
    p["sites_total"] = sum(sites.values())

    override = params.get("aps_per_site_override") or {}
    aps = 0
    for b, n in sites.items():
        per_site = override.get(b, R.APS_PER_SITE_BAND[b])
        if b in override:
            reg.append(assumption(f"aps_per_site.{b}", per_site,
                                  src.get("aps_per_site_override", "user")))
        aps += n * per_site
    if not override:
        reg.append(assumption("aps_per_site", R.APS_PER_SITE_BAND, "default",
                              "Design standard per band; the RFP states no survey."))
    p["aps_total"] = aps

    if params.get("user_count"):
        p["user_count"] = int(params["user_count"])
        reg.append(assumption("user_count", p["user_count"], src.get("user_count", "user")))
    else:
        p["user_count"] = sum(n * R.USERS_PER_SITE_BAND[b] for b, n in sites.items())
        reg.append(assumption("user_count", p["user_count"], "derived",
                              "Derived from site bands."))

    if params.get("switch_count"):
        p["switch_count"] = int(params["switch_count"])
        reg.append(assumption("switch_count", p["switch_count"],
                              src.get("switch_count", "user")))
    else:
        ports = p["user_count"] * R.USERS_PER_PORT
        p["switch_count"] = max(p["sites_total"],
                                math.ceil(ports / R.PORTS_PER_SWITCH))
        reg.append(assumption("switch_count", p["switch_count"], "derived",
                              f"{R.PORTS_PER_SWITCH} ports/switch, "
                              f"{R.USERS_PER_PORT} ports/user (wireless-first)."))

    mix = params.get("country_mix") or {"UK": 1.0}
    unknown = set(mix) - set(R.SUPPORTED_COUNTRIES)
    if unknown:
        raise ValidationError(
            f"Unsupported country/countries {sorted(unknown)}. "
            f"Rate card covers: {R.SUPPORTED_COUNTRIES}")
    total = sum(mix.values())
    if total <= 0:
        raise ValidationError("country_mix shares must be positive.")
    if abs(total - 1.0) > 0.01:
        mix = {k: v / total for k, v in mix.items()}
        reg.append(assumption("country_mix", mix, "derived", "Shares normalised."))
    else:
        reg.append(assumption("country_mix", mix, src.get("country_mix", "user")))
    p["country_mix"] = mix

    p["survey_type"] = take("survey_type", "hybrid")
    if p["survey_type"] not in R.SURVEY_DAYS_PER_AP:
        raise ValidationError(f"survey_type must be one of {list(R.SURVEY_DAYS_PER_AP)}")
    p["install_window"] = take("install_window", "business_hours")
    p["reuse_cabling"] = take("reuse_cabling", True)

    p["sla_tier"] = take("sla_tier", "silver", "Drives the coverage floor.")
    if p["sla_tier"] not in R.SLA_MULTIPLIER:
        raise ValidationError(f"sla_tier must be one of {list(R.SLA_MULTIPLIER)}")
    p["coverage"] = take("coverage", "8x5", "Largest single cost lever.")
    if p["coverage"] not in R.COVERAGE_MULTIPLIER:
        raise ValidationError(f"coverage must be one of {list(R.COVERAGE_MULTIPLIER)}")
    p["spares_strategy"] = take("spares_strategy", "regional")
    if p["spares_strategy"] not in R.SPARES_PCT:
        raise ValidationError(f"spares_strategy must be one of {list(R.SPARES_PCT)}")
    p["monitoring"] = take("monitoring", True)
    p["service_desk"] = take("service_desk", True)

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")

    return p, reg


# ---------------------------------------------------------------------------

def _deployment(p: dict) -> dict:
    aps, switches, sites = p["aps_total"], p["switch_count"], p["sites_total"]
    survey = aps * R.SURVEY_DAYS_PER_AP[p["survey_type"]]
    install = (aps * R.AP_INSTALL_DAYS + switches * R.SWITCH_INSTALL_DAYS
               + sites * R.MOBILISATION_DAYS_PER_SITE)
    if p["install_window"] == "out_of_hours":
        install *= R.OOH_UPLIFT
    design = R.DESIGN_DAYS_FIXED + sites * R.DESIGN_DAYS_PER_SITE
    pm = (survey + install + design) * R.PM_OVERHEAD_PCT

    blended_field = sum(R.COUNTRY_RATES[c]["field"] * s for c, s in p["country_mix"].items())
    blended_sdm = sum(R.COUNTRY_RATES[c]["sdm"] * s for c, s in p["country_mix"].items())

    labour = (survey + install) * blended_field + (design + pm) * blended_sdm
    hardware = aps * R.AP_UNIT_COST + switches * R.SWITCH_UNIT_COST
    tooling = sites * R.TOOLING_PER_SITE
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + hardware + tooling + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"survey": survey, "install": install, "design": design,
                      "project_management": pm,
                      "total": survey + install + design + pm},
        cost_lines=[cost_line("Labour", labour), cost_line("Hardware", hardware),
                    cost_line("Tooling and consumables", tooling),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["rollout_months"])


def _run(p: dict) -> tuple[dict, str]:
    aps, switches = p["aps_total"], p["switch_count"]
    incidents = aps * R.AP_INCIDENT_RATE_PA + switches * R.SWITCH_INCIDENT_RATE_PA
    demand_total = (incidents * R.HOURS_PER_INCIDENT / R.PRODUCTIVE_HOURS_PA
                    * R.SLA_MULTIPLIER[p["sla_tier"]]
                    * R.COVERAGE_MULTIPLIER[p["coverage"]])

    # Coverage floor: a committed on-site response cannot be served from a
    # central travelling pool. Each country needs standing presence sized for a
    # shift rota, whatever the incident volume says.
    enforce = p["sla_tier"] in R.ON_SITE_RESPONSE_TIERS
    by_country: dict[str, dict] = {}
    for c, share in p["country_mix"].items():
        demand = demand_total * share
        posts = (max(1, math.ceil(p["sites_total"] * share / R.SITES_PER_POST))
                 if enforce else 0)
        floor = posts * R.PRESENCE_FTE_PER_POST[p["coverage"]] if enforce else 0.0
        by_country[c] = {"fte": max(demand, floor), "demand": demand,
                         "floor": floor, "posts": posts,
                         "driver": "coverage floor" if floor > demand else "incident volume"}
    field_fte = sum(v["fte"] for v in by_country.values())

    noc = aps / R.APS_PER_NOC_FTE * R.COVERAGE_MULTIPLIER[p["coverage"]] \
        if p["monitoring"] else 0.0
    sd = 0.0
    if p["service_desk"]:
        hours = p["user_count"] * R.SD_CONTACTS_PER_USER_PA * R.SD_MINUTES_PER_CONTACT / 60
        sd = hours / R.PRODUCTIVE_HOURS_PA

    hubs = ([(R.HUB_PRIMARY, 0.65), (R.HUB_SECONDARY, 0.35)]
            if p["coverage"] == "24x7" else [(R.HUB_PRIMARY, 1.0)])

    resources = [resource(c, "Field Engineer", v["fte"], v["driver"])
                 for c, v in sorted(by_country.items(), key=lambda kv_: -kv_[1]["fte"])
                 if v["fte"] >= 0.01]
    for hub, share in hubs:
        if noc:
            resources.append(resource(hub, "NOC Engineer", noc * share, "central"))
        if sd:
            resources.append(resource(hub, "Service Desk", sd * share, "central"))

    labour = sum(v["fte"] * R.COUNTRY_RATES[c]["field"] * R.WORKING_DAYS_PA
                 for c, v in by_country.items())
    for hub, share in hubs:
        labour += noc * share * R.COUNTRY_RATES[hub]["noc"] * R.WORKING_DAYS_PA
        labour += sd * share * R.COUNTRY_RATES[hub]["service_desk"] * R.WORKING_DAYS_PA

    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    blended_sdm = sum(R.COUNTRY_RATES[c]["sdm"] * s for c, s in p["country_mix"].items())
    labour += sdm * blended_sdm * R.WORKING_DAYS_PA
    resources.append(resource(max(p["country_mix"], key=p["country_mix"].get),
                              "Service Delivery Manager", sdm, "contract band"))

    travel = sum(incidents * s * R.COUNTRY_RATES[c]["travel"]
                 for c, s in p["country_mix"].items())
    hardware = aps * R.AP_UNIT_COST + switches * R.SWITCH_UNIT_COST
    spares = hardware * R.SPARES_PCT[p["spares_strategy"]]
    tooling = p["sites_total"] * R.TOOLING_PER_SITE * 0.25
    overhead = (labour + travel) * R.OVERHEAD_PCT
    subtotal = labour + travel + spares + tooling + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    floor_driven = [c for c, v in by_country.items() if v["driver"] == "coverage floor"]
    surplus = sum(v["fte"] - v["demand"] for v in by_country.values()
                  if v["driver"] == "coverage floor")
    insight = ""
    if floor_driven:
        insight = (
            f"{', '.join(floor_driven)} are sized by the SLA coverage floor, not "
            f"incident volume — {surplus:.1f} FTE of standing presence exceeds the "
            f"actual workload of {incidents:.0f} incidents a year. A regional "
            f"pooling model, or a relaxed tier in the low-density countries, would "
            f"reduce cost without breaching the committed response time.")

    block = run_block(
        resources=resources,
        cost_lines=[cost_line("Labour", labour),
                    cost_line("Travel and subsistence", travel),
                    cost_line("Spares and logistics", spares),
                    cost_line("Tooling and consumables", tooling),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost_pa=cost, price_pa=cost / (1 - p["margin_pct"]),
        drivers={"incidents_pa": round(incidents, 1),
                 "floor_driven_countries": floor_driven,
                 "surplus_fte": round(surplus, 2)})
    return block, insight


def _bom(p: dict) -> list[dict]:
    """The physical estate, priced at cost.

    Computed independently of the cost blocks above, from the same rate card.
    `verify()` then checks the two agree. Deriving the BoM from the cost lines
    would make that check vacuous — the point is that two routes to the same
    number have to meet.
    """
    aps, switches, sites = p["aps_total"], p["switch_count"], p["sites_total"]
    spares_pct = R.SPARES_PCT[p["spares_strategy"]]

    lines = [
        bom_line("Wireless access point", aps, "each", R.AP_UNIT_COST,
                 rolls_into="Hardware", phase="one-off", category="Network hardware",
                 note="Design standard per site band"),
        bom_line("Access switch", switches, "each", R.SWITCH_UNIT_COST,
                 rolls_into="Hardware", phase="one-off", category="Network hardware",
                 note=f"{R.PORTS_PER_SWITCH} ports each"),
        bom_line("Site installation kit", sites, "site", R.TOOLING_PER_SITE,
                 rolls_into="Tooling and consumables", phase="one-off",
                 category="Consumables"),
        bom_line("Site consumables", sites, "site per annum",
                 R.TOOLING_PER_SITE * 0.25,
                 rolls_into="Tooling and consumables", phase="recurring",
                 category="Consumables"),
    ]
    if spares_pct:
        lines += [
            bom_line("Spare access points", aps, "each covered",
                     R.AP_UNIT_COST * spares_pct,
                     rolls_into="Spares and logistics", phase="recurring",
                     category="Spares",
                     note=f"{p['spares_strategy']} holding at "
                          f"{spares_pct:.1%} of unit value"),
            bom_line("Spare access switches", switches, "each covered",
                     R.SWITCH_UNIT_COST * spares_pct,
                     rolls_into="Spares and logistics", phase="recurring",
                     category="Spares"),
        ]
    return lines


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight = _run(p)

    return build_result(
        manifest=MANIFEST,
        client_name=p["client_name"], rfp_ref=p["rfp_ref"],
        scope_headline=[
            scope_item("Locations in scope", p["sites_total"]),
            scope_item("Wireless access points", p["aps_total"]),
            scope_item("Access switches", p["switch_count"]),
            scope_item("End users supported", p["user_count"]),
        ],
        service=[
            kv("Service level", f"{p['sla_tier'].title()} — "
                                f"{R.SLA_RESPONSE[p['sla_tier']]} on-site"),
            kv("Coverage window", p["coverage"]),
            kv("Spares strategy", p["spares_strategy"].title()),
            kv("Survey approach", p["survey_type"].title()),
            kv("Deployment duration", f"{p['rollout_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per site per month",
             "value": round(run["price_pa"] / 12 / p["sites_total"], 2)},
        ],
        scope_detail={"sites_by_band": p["sites"], "country_mix": p["country_mix"]},
        bom=_bom(p),
    )
