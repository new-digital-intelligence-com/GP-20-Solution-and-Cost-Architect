"""
Model pack — Remote Support tower.

One lot of a lotted tender: everything resolved without anyone travelling.
Second and third line engineering, monitoring and event management, and the
automation that closes incidents before a human sees them.

This lot is defined by its two neighbours more than by itself:

  * escalations arrive from `service-desk`, at a volume its FCR target sets;
  * whatever this lot cannot close becomes a dispatch in `field-service`.

Both are explicit inputs. Priced in isolation the lot looks like a small
engineering team; priced next to the others it is the cheapest place in the bid
to remove cost, because one engineer here displaces several in the field. The
pack's job is to say so with a number attached.

ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.contract import (COMMON_SETTINGS, Gap, GapOption, Manifest,
                           ValidationError, assumption, bom_line, build_result,
                           cost_line, deployment_block, kv, resource, run_block,
                           scope_item)
from core import estate as EST

from . import rates as R

# ---------------------------------------------------------------------------

MANIFEST = Manifest(
    key="remote-support",
    name="Remote Support",
    kind="tower",
    summary="Second and third line engineering, monitoring and automation — "
            "everything resolved without a site visit.",
    detect=[
        "remote support", "second line", "2nd line", "third line", "3rd line",
        "l2", "l3", "escalation", "noc", "network operations centre",
        "monitoring", "event management", "proactive monitoring",
        "remote resolution", "remote diagnostics", "automation",
    ],
    material=["capability", "tiers", "coverage", "monitoring", "margin_pct",
              "term_years"],
    settings=[*COMMON_SETTINGS, "delivery_country"],
    notes="Sized by escalation volume and by the estate under monitoring. Its "
          "capability setting is what decides how much work lands in the field "
          "service lot, so the two must be priced against the same assumption "
          "or the bid does not reconcile.",
    gaps=[
        Gap(
            param="capability",
            question="What remote resolution capability is being bought?",
            rfp_hint="Tenders rarely state this directly. Look for language "
                     "about proactive monitoring, self-healing or automation "
                     "targets — and check what the field service lot assumes.",
            options=[
                GapOption("basic", "Scripted triage and remote control",
                          "Closes 42% without a visit. Cheapest lot in "
                          "isolation, and the most expensive bid overall "
                          "because the field lot absorbs the rest."),
                GapOption("standard", "Tooling, automation, experienced 2nd line",
                          "Closes 61%. The usual assumption, and what field "
                          "service defaults to."),
                GapOption("advanced", "Proactive monitoring and self-heal",
                          "Closes 74% and automates 21% of incidents away "
                          "entirely. Costs more here, saves more in the field — "
                          "unless the field lot is coverage-floor bound, in "
                          "which case it saves nothing."),
            ],
        ),
        Gap(
            param="tiers",
            question="Is third line in scope, or retained by the client?",
            rfp_hint="Look for whether the client keeps deep product "
                     "engineering or vendor escalation in house.",
            options=[
                GapOption("l2", "Second line only",
                          "22% of escalations pass back to the client. Cheaper, "
                          "but the client must have somewhere to put them."),
                GapOption("l2_l3", "Second and third line",
                          "Adds deep resolution at 95 minutes a case. Low "
                          "volume, high unit cost, and the tier most often "
                          "under-scoped in a tender."),
            ],
        ),
        Gap(
            param="coverage",
            question="What coverage window should the remote function hold?",
            rfp_hint="A remote function is centralised, so a wide window here "
                     "costs a fraction of the same window in the field.",
            options=[
                GapOption("8x5", "8×5 business hours",
                          "1.15 FTE per staffed role."),
                GapOption("12x5", "12×5 extended day",
                          "1.70 FTE per staffed role."),
                GapOption("24x7", "24×7 continuous",
                          "4.80 FTE per staffed role, but per *hub* rather than "
                          "per country — which is why 24×7 is far cheaper here "
                          "than in field service."),
            ],
        ),
        Gap(
            param="monitoring",
            question="What monitoring scope should be priced?",
            rfp_hint="Check whether the tender wants alarms handled or events "
                     "correlated — they are different headcounts.",
            options=[
                GapOption("none", "No monitoring in this lot",
                          "Escalation handling only. Assumes someone else "
                          "watches the estate."),
                GapOption("reactive", "Alarm handling",
                          "60% of the monitoring headcount. Responds to alerts, "
                          "does not look for them."),
                GapOption("proactive", "Proactive monitoring and correlation",
                          "Full monitoring headcount, and the only option that "
                          "makes the automation capability worth buying."),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------

def _normalise(params: dict) -> tuple[dict, list[dict]]:
    estate, reg = EST.normalise(params)
    src = params.get("_sources", {})
    p: dict = {"estate": estate}

    def take(key, default, note=""):
        if params.get(key) is not None:
            reg.append(assumption(key, params[key], src.get(key, "user"), note))
            return params[key]
        reg.append(assumption(key, default, "default", note))
        return default

    p["term_years"] = int(take("term_years", R.DEFAULT_TERM_YEARS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")
    p["onboarding_months"] = int(
        take("onboarding_months", R.DEFAULT_ONBOARDING_MONTHS))

    # Intake. A figure from the desk lot always beats one derived here — the
    # desk knows its own FCR target and this pack does not.
    if params.get("escalations_pa"):
        p["escalations_pa"] = float(params["escalations_pa"])
        reg.append(assumption("escalations_pa", round(p["escalations_pa"]),
                              src.get("escalations_pa", "user"),
                              "Taken from the service desk lot."))
    else:
        p["escalations_pa"] = (
            estate["user_count"] * R.ESCALATIONS_PER_USER_PA
            + estate["device_total"] * R.ESCALATIONS_PER_DEVICE_PA)
        reg.append(assumption("escalations_pa", round(p["escalations_pa"]),
                              "derived",
                              "No service-desk lot supplied a figure; derived "
                              "from the estate."))
    if p["escalations_pa"] <= 0:
        raise ValidationError(
            "Remote support needs an escalation volume — supply "
            "`escalations_pa` from the service desk lot, or an estate.")

    p["capability"] = take("capability", "standard",
                           "Decides how much work lands in the field lot.")
    if p["capability"] not in R.CAPABILITY:
        raise ValidationError(f"capability must be one of {list(R.CAPABILITY)}")

    p["tiers"] = take("tiers", "l2_l3")
    if p["tiers"] not in R.TIERS:
        raise ValidationError(f"tiers must be one of {list(R.TIERS)}")

    p["coverage"] = take("coverage", "8x5")
    if p["coverage"] not in R.PRESENCE_FTE_PER_ROLE:
        raise ValidationError(
            f"coverage must be one of {list(R.PRESENCE_FTE_PER_ROLE)}")

    p["monitoring"] = take("monitoring", "reactive")
    if p["monitoring"] not in R.MONITORING_LEVEL:
        raise ValidationError(
            f"monitoring must be one of {list(R.MONITORING_LEVEL)}")

    p["delivery_country"] = take("delivery_country", R.HUB_PRIMARY,
                                 "Where the remote function is staffed.")
    if p["delivery_country"] not in R.SUPPORTED_COUNTRIES:
        raise ValidationError(
            f"delivery_country must be one of {R.SUPPORTED_COUNTRIES}")

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(
        take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(
        take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")
    return p, reg


def _monitored_nodes(p: dict) -> int:
    e = p["estate"]
    return e["aps_total"] + e["switch_count"] + e["device_total"]


def _deployment(p: dict) -> dict:
    services = 3 if p["tiers"] == "l2_l3" else 2
    runbooks = services * R.RUNBOOK_DAYS_PER_SERVICE
    integration = (R.TOOLING_INTEGRATION_DAYS
                   if p["monitoring"] != "none" else 0.0)
    automation = R.AUTOMATION_BUILD_DAYS[p["capability"]]
    pm = (runbooks + integration + automation) * R.PM_OVERHEAD_PCT

    rates = R.COUNTRY_RATES[p["delivery_country"]]
    labour = ((runbooks + automation) * rates["l3"]
              + integration * rates["noc"]
              + pm * rates["sdm"])
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"runbook_build": runbooks,
                      "tooling_integration": integration,
                      "automation_build": automation,
                      "project_management": pm,
                      "total": runbooks + integration + automation + pm},
        cost_lines=[cost_line("Onboarding labour", labour),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["onboarding_months"])


def _run(p: dict) -> tuple[dict, str, dict]:
    e = p["estate"]
    cap = R.CAPABILITY[p["capability"]]

    # Automation closes incidents before an engineer sees them, so it reduces
    # the intake rather than the handling time.
    automated = p["escalations_pa"] * cap["automation"]
    handled = p["escalations_pa"] - automated

    l3_share = R.L3_SHARE_OF_ESCALATIONS if p["tiers"] == "l2_l3" else 0.0
    l2_cases = handled * (1 - l3_share)
    l3_cases = handled * l3_share

    effort = R.CAPABILITY_EFFORT[p["capability"]]
    l2_fte = (l2_cases * R.L2_AHT_MINUTES * effort
              / 60 / R.PRODUCTIVE_HOURS_PA / R.OCCUPANCY)
    l3_fte = (l3_cases * R.L3_AHT_MINUTES * effort
              / 60 / R.PRODUCTIVE_HOURS_PA / R.OCCUPANCY)

    # Monitoring headcount comes from the estate, not the queue.
    nodes = _monitored_nodes(p)
    noc_fte = 0.0
    if p["monitoring"] != "none":
        noc_fte = (e["aps_total"] / R.APS_PER_NOC_FTE
                   + e["switch_count"] / R.SWITCHES_PER_NOC_FTE
                   + e["device_total"] / R.DEVICES_PER_NOC_FTE)
        noc_fte *= R.MONITORING_LEVEL[p["monitoring"]]

    # The coverage floor here is per *hub*, not per country or language.
    per_role = R.PRESENCE_FTE_PER_ROLE[p["coverage"]]
    floor_applied = []
    if l2_fte and l2_fte < per_role:
        floor_applied.append("second line")
        l2_fte = per_role
    if noc_fte and noc_fte < per_role:
        floor_applied.append("monitoring")
        noc_fte = per_role

    hubs = (R.FOLLOW_THE_SUN_SPLIT if p["coverage"] == "24x7"
            else [(p["delivery_country"], 1.0)])

    resources: list[dict] = []
    labour = 0.0
    for hub, share in hubs:
        rates = R.COUNTRY_RATES[hub]
        if l2_fte * share >= 0.01:
            resources.append(resource(hub, "Second Line Engineer", l2_fte * share,
                                      "escalation volume" if "second line"
                                      not in floor_applied else "coverage floor"))
            labour += l2_fte * share * rates["l2"] * R.WORKING_DAYS_PA
        if l3_fte * share >= 0.01:
            resources.append(resource(hub, "Third Line Engineer", l3_fte * share,
                                      "deep resolution volume"))
            labour += l3_fte * share * rates["l3"] * R.WORKING_DAYS_PA
        if noc_fte * share >= 0.01:
            resources.append(resource(hub, "Monitoring Engineer", noc_fte * share,
                                      "estate under monitoring"))
            labour += noc_fte * share * rates["noc"] * R.WORKING_DAYS_PA

    engineers = l2_fte + l3_fte + noc_fte
    hub = p["delivery_country"]
    leads = math.ceil(engineers / R.ENGINEERS_PER_LEAD) if engineers else 0
    if leads:
        resources.append(resource(hub, "Team Lead", leads, "span of control"))
        labour += leads * R.COUNTRY_RATES[hub]["lead"] * R.WORKING_DAYS_PA
    sdm = next(f for cap_, f in R.SDM_BANDS if labour < cap_)
    resources.append(resource(hub, "Service Delivery Manager", sdm,
                              "contract band"))
    labour += sdm * R.COUNTRY_RATES[hub]["sdm"] * R.WORKING_DAYS_PA

    monitoring_tools = (nodes * R.MONITORING_PER_NODE_PA
                        if p["monitoring"] != "none" else 0.0)
    remote_tools = engineers * R.REMOTE_CONTROL_PER_ENGINEER_PA
    platform_tools = engineers * cap["tooling_pa"]
    automation_platform = (R.AUTOMATION_PLATFORM_PA
                           if p["capability"] == "advanced" else 0.0)

    overhead = labour * R.OVERHEAD_PCT
    subtotal = (labour + monitoring_tools + remote_tools + platform_tools
                + automation_platform + overhead)
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    lines = [cost_line("Labour", labour)]
    if monitoring_tools:
        lines.append(cost_line("Monitoring platform", monitoring_tools))
    lines += [cost_line("Remote control tooling", remote_tools),
              cost_line("Support platform", platform_tools)]
    if automation_platform:
        lines.append(cost_line("Automation platform", automation_platform))
    lines += [cost_line("Delivery overhead", overhead),
              cost_line("Contingency", contingency)]

    # The observation that only exists because the lots are separate.
    dispatch_now = p["escalations_pa"] * (1 - cap["remote_fix"])
    if p["capability"] != "advanced":
        adv = R.CAPABILITY["advanced"]
        dispatch_adv = p["escalations_pa"] * (1 - adv["remote_fix"])
        avoided = dispatch_now - dispatch_adv
        insight = (
            f"At {p['capability']} capability this lot closes "
            f"{cap['remote_fix']:.0%} of what reaches it and passes "
            f"{dispatch_now:,.0f} incidents a year to the field. Advanced "
            f"capability would keep a further {avoided:,.0f} of those off the "
            f"road. That trade is invisible inside this lot — it costs more "
            f"here and saves more there — so it has to be argued at bid level, "
            f"and only pays back if the field lot is sized by dispatch volume "
            f"rather than by a coverage floor.")
    else:
        insight = (
            f"Advanced capability closes {cap['remote_fix']:.0%} remotely and "
            f"automates {cap['automation']:.0%} of escalations away before an "
            f"engineer sees them, leaving {dispatch_now:,.0f} incidents a year "
            f"for the field. This is the most expensive way to run this lot and "
            f"usually the cheapest way to run the bid — but only where field "
            f"service is sized by volume. If the field lot is coverage-floor "
            f"bound, the engineers are already standing there and this buys "
            f"nothing.")

    block = run_block(
        resources=resources,
        cost_lines=lines,
        cost_pa=cost, price_pa=cost / (1 - p["margin_pct"]),
        drivers={"escalations_pa": round(p["escalations_pa"], 0),
                 "automated_away_pa": round(automated, 0),
                 "remote_fix_rate": cap["remote_fix"],
                 "passed_to_field_pa": round(dispatch_now, 0),
                 "monitored_nodes": nodes,
                 "coverage_floor_applied": floor_applied})
    return block, insight, {"engineers": engineers, "nodes": nodes,
                            "dispatch": dispatch_now}


def _bom(p: dict, d: dict) -> list[dict]:
    cap = R.CAPABILITY[p["capability"]]
    lines = []
    if p["monitoring"] != "none":
        lines.append(bom_line("Monitoring platform — per node", d["nodes"],
                              "node per annum", R.MONITORING_PER_NODE_PA,
                              rolls_into="Monitoring platform", phase="recurring",
                              category="Software",
                              note=R.MONITORING_LABEL[p["monitoring"]]))
    lines += [
        bom_line("Remote control and diagnostics", d["engineers"],
                 "engineer per annum", R.REMOTE_CONTROL_PER_ENGINEER_PA,
                 rolls_into="Remote control tooling", phase="recurring",
                 category="Software"),
        bom_line(f"Support platform — {p['capability']}", d["engineers"],
                 "engineer per annum", cap["tooling_pa"],
                 rolls_into="Support platform", phase="recurring",
                 category="Software"),
    ]
    if p["capability"] == "advanced":
        lines.append(bom_line("Automation and self-heal platform", 1,
                              "tenant per annum", R.AUTOMATION_PLATFORM_PA,
                              rolls_into="Automation platform", phase="recurring",
                              category="Software",
                              note=f"automates {cap['automation']:.0%} of "
                                   f"escalations away"))
    return lines


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight, d = _run(p)
    e = p["estate"]

    return build_result(
        manifest=MANIFEST,
        client_name=e["client_name"], rfp_ref=e["rfp_ref"],
        scope_headline=[
            scope_item("Escalations in per annum", round(p["escalations_pa"])),
            scope_item("Nodes monitored", d["nodes"]),
            scope_item("Remote engineers", round(d["engineers"], 1), "float1"),
            scope_item("Passed to field per annum", round(d["dispatch"])),
        ],
        service=[
            kv("Capability", R.CAPABILITY_LABEL[p["capability"]]),
            kv("Tiers in scope", R.TIER_LABEL[p["tiers"]]),
            kv("Coverage window", R.COVERAGE_LABEL[p["coverage"]]),
            kv("Monitoring", R.MONITORING_LABEL[p["monitoring"]]),
            kv("Remote resolution rate",
               f"{R.CAPABILITY[p['capability']]['remote_fix']:.0%}"),
            kv("Onboarding", f"{p['onboarding_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per escalation",
             "value": round(run["price_pa"] / p["escalations_pa"], 2)},
            {"label": "Per user per month",
             "value": round(run["price_pa"] / 12 / e["user_count"], 2)
             if e["user_count"] else 0.0},
        ],
        scope_detail=EST.scope_detail(e),
        bom=_bom(p, d),
    )
