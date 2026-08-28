"""
Model pack — IaaS Compute.

The third cost shape. Managed LAN is labour-shaped, DaaS is capital-shaped;
this one is consumption-shaped, and it is the first offering whose run cost
genuinely changes year to year for a reason other than inflation. Workloads
migrate over a ramp, so year one is not year three — which is what
`run_block(year_profile=...)` exists for.

The architectural tension here is commitment against evidence: a three-year
reserved discount is large, and buying it before the ramp has proved the shape
means paying for capacity the migration cannot yet fill.

ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.contract import (COMMON_SETTINGS, Gap, GapOption, Manifest,
                           ValidationError, assumption, bom_line, build_result,
                           cost_line, deployment_block, kv, resource, run_block,
                           scope_item)

from . import rates as R

# ---------------------------------------------------------------------------

MANIFEST = Manifest(
    key="iaas-compute",
    name="IaaS Compute",
    summary="Migrated and hosted compute, storage and network capacity, "
            "consumed monthly with an optional managed wrap.",
    detect=[
        "iaas", "infrastructure as a service", "compute", "vcpu", "virtual machine",
        "cloud migration", "workload migration", "hosting", "landing zone",
        "availability zone", "reserved instance", "egress", "hypervisor",
        "data centre exit", "lift and shift", "capacity",
    ],
    material=["commitment", "availability", "managed_level", "margin_pct",
              "term_years"],
    settings=[*COMMON_SETTINGS, "delivery_country"],
    notes="Consumption ramps as workloads migrate, so the year-one charge is "
          "materially below steady state. Reserved commitments are the largest "
          "discount available and the largest way to overpay — they are bought "
          "on day one against a shape the migration has not yet proved.",
    gaps=[
        Gap(
            param="commitment",
            question="What commitment model should be priced?",
            rfp_hint="Tenders ask for the lowest price without saying whether "
                     "they will accept the lock-in that produces it.",
            options=[
                GapOption("on_demand", "On demand",
                          "No discount, no lock-in. Right while the target "
                          "footprint is still uncertain."),
                GapOption("reserved_1yr", "One-year reserved",
                          "28% off compute. Renewable annually, so the "
                          "commitment can follow the ramp rather than precede it."),
                GapOption("reserved_3yr", "Three-year reserved",
                          "41% off compute — the largest single saving here, but "
                          "it commits capacity from day one, including through a "
                          "migration ramp during which much of it is idle."),
            ],
        ),
        Gap(
            param="availability",
            question="What resilience posture should be priced?",
            rfp_hint="An availability percentage in the SLA implies a posture "
                     "even when the architecture is not stated.",
            options=[
                GapOption("single_az", "Single availability zone",
                          "Baseline cost. No infrastructure resilience — "
                          "recovery depends entirely on backups."),
                GapOption("multi_az", "Multi-AZ",
                          "×1.9 on compute and storage. The usual answer for a "
                          "99.9%+ commitment."),
                GapOption("multi_region", "Multi-region",
                          "×2.6. Only justified by a genuine regional-outage "
                          "requirement; it roughly doubles the largest cost line."),
            ],
        ),
        Gap(
            param="managed_level",
            question="How much of the operational wrap is in scope?",
            rfp_hint="Check whether the client retains platform operations.",
            options=[
                GapOption("unmanaged", "Client managed",
                          "Consumption only. No engineering labour priced."),
                GapOption("monitored", "Monitored and patched",
                          "One engineer per 180 instances plus tooling."),
                GapOption("fully_managed", "Fully managed",
                          "One engineer per 65 instances. Roughly triples the "
                          "labour line but is still a minority of the total."),
            ],
        ),
        Gap(
            param="ramp_months",
            question="Over how many months will workloads migrate?",
            rfp_hint="The programme timetable usually implies this even when the "
                     "commercial section does not state it.",
            options=[
                GapOption("6", "6 months — aggressive",
                          "Consumption reaches steady state inside year one, so "
                          "a reserved commitment is used almost immediately."),
                GapOption("12", "12 months — typical",
                          "Year one averages roughly half of steady-state "
                          "consumption."),
                GapOption("24", "24 months — phased",
                          "Two years below steady state. A three-year reserved "
                          "commitment bought on day one is substantially idle "
                          "for the first of them."),
            ],
        ),
        Gap(
            param="backup_retention_days",
            question="What backup retention is required?",
            rfp_hint="Often stated in a compliance annex rather than the "
                     "technical requirements.",
            options=[
                GapOption("30", "30 days",
                          "Standard operational recovery."),
                GapOption("90", "90 days",
                          "Adds roughly 27% to the backup line."),
                GapOption("365", "365 days",
                          "Adds roughly 160% to the backup line; usually driven "
                          "by regulation rather than recovery need."),
            ],
        ),
    ],
)


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
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")

    inst_in = params.get("instances") or {}
    unknown = set(inst_in) - set(R.INSTANCE_CLASSES)
    if unknown:
        raise ValidationError(f"Unknown instance class(es) {sorted(unknown)}. "
                              f"Catalogue: {R.INSTANCE_CLASSES}")
    inst = {c: int(inst_in.get(c, 0) or 0) for c in R.INSTANCE_CLASSES}
    if sum(inst.values()) == 0:
        raise ValidationError("At least one instance must be specified.")
    for c, n in inst.items():
        if n:
            reg.append(assumption(f"instances.{c}", n, src.get("instances", "user")))
    p["instances"] = inst
    p["instance_total"] = sum(inst.values())
    p["vcpu_total"] = sum(n * R.INSTANCE_VCPU[c] for c, n in inst.items())

    p["nonprod_ratio"] = float(take("nonprod_ratio", 0.6,
                                    "Non-production instances as a multiple of "
                                    "production; powered down out of hours."))
    if p["nonprod_ratio"] < 0:
        raise ValidationError("nonprod_ratio cannot be negative")

    st_in = params.get("storage_tb") or {}
    unknown = set(st_in) - set(R.STORAGE_TIERS)
    if unknown:
        raise ValidationError(f"Unknown storage tier(s) {sorted(unknown)}. "
                              f"Tiers: {R.STORAGE_TIERS}")
    storage = {t: float(st_in.get(t, 0) or 0) for t in R.STORAGE_TIERS}
    p["storage_tb"] = storage
    p["storage_total_tb"] = sum(storage.values())
    if any(storage.values()):
        reg.append(assumption("storage_tb", storage, src.get("storage_tb", "user")))
    else:
        reg.append(assumption("storage_tb", storage, "default", "No storage stated."))

    p["egress_tb_pm"] = float(take("egress_tb_pm", 0.0))

    p["commitment"] = take("commitment", "on_demand",
                           "Largest discount available, and the largest lock-in.")
    if p["commitment"] not in R.COMMITMENT_DISCOUNT:
        raise ValidationError(f"commitment must be one of {R.COMMITMENT}")

    p["availability"] = take("availability", "single_az")
    if p["availability"] not in R.AVAILABILITY_MULT:
        raise ValidationError(f"availability must be one of {R.AVAILABILITY}")

    p["managed_level"] = take("managed_level", "monitored")
    if p["managed_level"] not in R.MANAGED_LEVELS:
        raise ValidationError(f"managed_level must be one of {R.MANAGED_LEVELS}")

    p["backup_retention_days"] = int(take("backup_retention_days", 30))
    if p["backup_retention_days"] not in R.BACKUP_RETENTION_ALLOWED:
        raise ValidationError(
            f"backup_retention_days must be one of {list(R.BACKUP_RETENTION_ALLOWED)}")

    p["workloads"] = int(take("workloads", max(1, p["instance_total"] // 3),
                              "Migration units; derived from instance count "
                              "if not stated."))
    if p["workloads"] < 1:
        raise ValidationError("workloads must be at least 1")

    p["ramp_months"] = int(take("ramp_months", R.DEFAULT_RAMP_MONTHS,
                                "Months until full consumption."))
    if p["ramp_months"] < 1:
        raise ValidationError("ramp_months must be at least 1")

    p["delivery_country"] = take("delivery_country", R.HUB_PRIMARY)
    if p["delivery_country"] not in R.SUPPORTED_COUNTRIES:
        raise ValidationError(
            f"delivery_country must be one of {R.SUPPORTED_COUNTRIES}")

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")

    return p, reg


def _ramp_fractions(ramp_months: int, term_years: int) -> list[float]:
    """Average consumption in each contract year, as a share of steady state.

    Workloads land evenly across the ramp, so consumption in month m is
    min(1, m / ramp_months). Averaging over each year gives the year's share.
    """
    out = []
    for yr in range(term_years):
        months = range(yr * 12 + 1, yr * 12 + 13)
        out.append(sum(min(1.0, m / ramp_months) for m in months) / 12)
    return out


def _steady_consumption(p: dict) -> dict:
    """Annual consumption cost at full steady state, before margin."""
    avail = R.AVAILABILITY_MULT[p["availability"]]
    discount = R.COMMITMENT_DISCOUNT[p["commitment"]]

    prod = sum(n * R.INSTANCE_HOURLY[c] for c, n in p["instances"].items()) * R.HOURS_PA
    nonprod = prod * p["nonprod_ratio"] * R.NONPROD_RUNTIME_FACTOR
    compute = (prod + nonprod) * discount * avail

    storage = sum(tb * R.STORAGE_PER_TB_PM[t] for t, tb in p["storage_tb"].items()) * 12
    storage *= avail

    egress = p["egress_tb_pm"] * 12 * R.EGRESS_PER_TB

    retention_factor = 1 + (p["backup_retention_days"] / 90) * 0.4
    backup = p["storage_total_tb"] * R.BACKUP_PER_TB_PM * 12 * retention_factor

    tooling = p["instance_total"] * R.TOOLING_PER_INSTANCE_PA[p["managed_level"]]

    return {"compute": compute, "storage": storage, "egress": egress,
            "backup": backup, "tooling": tooling}


def _deployment(p: dict) -> dict:
    w = p["workloads"]
    days = {k: w * v for k, v in R.PER_WORKLOAD_DAYS.items()}
    days["landing_zone"] = R.LANDING_ZONE_DAYS
    subtotal_days = sum(days.values())
    days["project_management"] = subtotal_days * R.PM_OVERHEAD_PCT
    days["total"] = subtotal_days + days["project_management"]

    rates = R.COUNTRY_RATES[p["delivery_country"]]
    labour = ((days["landing_zone"] + days["assess"]) * rates["architect"]
              + (days["migrate"] + days["test"] + days["cutover"]) * rates["engineer"]
              + days["project_management"] * rates["sdm"])
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role=days,
        cost_lines=[cost_line("Migration labour", labour),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["ramp_months"])


def _run(p: dict) -> tuple[dict, str]:
    steady = _steady_consumption(p)
    fractions = _ramp_fractions(p["ramp_months"], p["term_years"])
    y1 = fractions[0]

    per_eng = R.INSTANCES_PER_ENGINEER[p["managed_level"]]
    eng_fte = p["instance_total"] / per_eng if per_eng else 0.0

    resources: list[dict] = []
    labour = 0.0
    country = p["delivery_country"]
    if eng_fte:
        resources.append(resource(country, "Cloud Engineer", eng_fte,
                                  f"1 per {per_eng} instances"))
        labour += eng_fte * R.COUNTRY_RATES[country]["engineer"] * R.WORKING_DAYS_PA

    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    if p["managed_level"] != "unmanaged":
        resources.append(resource(country, "Service Delivery Manager", sdm,
                                  "contract band"))
        labour += sdm * R.COUNTRY_RATES[country]["sdm"] * R.WORKING_DAYS_PA

    # Year-one consumption, not steady state — the ramp is the point.
    consumption_y1 = {k: v * y1 for k, v in steady.items()}
    overhead = (sum(consumption_y1.values()) + labour) * R.OVERHEAD_PCT
    subtotal = sum(consumption_y1.values()) + labour + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency
    price = cost / (1 - p["margin_pct"])

    profile = [f / y1 for f in fractions]

    steady_annual = sum(steady.values())
    idle_years = sum(1 for f in fractions if f < 0.97)
    insight = ""
    if p["commitment"] == "reserved_3yr" and p["ramp_months"] > 9:
        wasted = sum(steady["compute"] * (1 - f) for f in fractions[:min(3, len(fractions))])
        insight = (
            f"A three-year reserved commitment is the largest discount available "
            f"— 41% off compute — but it is bought on day one against a "
            f"{p['ramp_months']}-month migration ramp. Roughly "
            f"£{wasted:,.0f} of committed compute goes unconsumed across the "
            f"first three years because the workloads have not landed yet. A "
            f"one-year commitment renewed as the ramp completes captures most of "
            f"the discount without paying for capacity the programme cannot fill.")
    elif p["commitment"] == "on_demand":
        saving = steady["compute"] * (1 - R.COMMITMENT_DISCOUNT["reserved_1yr"])
        insight = (
            f"Everything is priced on demand. Moving to a one-year reserved "
            f"commitment once the footprint stabilises would save roughly "
            f"£{saving:,.0f} a year at steady state — worth revisiting at the "
            f"end of the ramp rather than committing now.")
    elif idle_years:
        insight = (
            f"Consumption reaches steady state in month {p['ramp_months']}; year "
            f"one averages {y1:.0%} of the full run rate. The year-one charge "
            f"below is therefore not the ongoing charge — the schedule shows the "
            f"ramp explicitly, and steady state is roughly "
            f"£{price / y1:,.0f} a year.")

    lines = [cost_line("Compute", consumption_y1["compute"]),
             cost_line("Storage", consumption_y1["storage"])]
    if consumption_y1["egress"]:
        lines.append(cost_line("Network egress", consumption_y1["egress"]))
    lines.append(cost_line("Backup", consumption_y1["backup"]))
    if consumption_y1["tooling"]:
        lines.append(cost_line("Monitoring and tooling", consumption_y1["tooling"]))
    if labour:
        lines.append(cost_line("Managed service labour", labour))
    lines += [cost_line("Delivery overhead", overhead),
              cost_line("Contingency", contingency)]

    block = run_block(
        resources=resources, cost_lines=lines,
        cost_pa=cost, price_pa=price,
        year_profile=profile,
        drivers={"steady_state_annual_cost": round(steady_annual, 2),
                 "year_one_fraction": round(y1, 3),
                 "ramp_months": p["ramp_months"],
                 "vcpu_total": p["vcpu_total"]})
    return block, insight


def _bom(p: dict) -> list[dict]:
    """Consumption, priced at year-one volume rather than steady state.

    Every line here is scaled by the year-one ramp fraction, because the cost
    lines it reconciles against are year-one figures. Quoting steady-state
    consumption in the BoM while the cost model shows year one is the single
    easiest way to make this offering look wrong on two pages of the same
    document — the note on each line states the fraction explicitly.
    """
    fractions = _ramp_fractions(p["ramp_months"], p["term_years"])
    y1 = fractions[0]
    avail = R.AVAILABILITY_MULT[p["availability"]]
    discount = R.COMMITMENT_DISCOUNT[p["commitment"]]
    ramp_note = f"year one at {y1:.0%} of steady state"

    lines: list[dict] = []
    for cls, n in sorted(p["instances"].items(), key=lambda kv_: -kv_[1]):
        if not n:
            continue
        lines.append(bom_line(
            f"{cls.replace('_', ' ')} instance — production", n, "instance",
            R.INSTANCE_HOURLY[cls] * R.HOURS_PA * discount * avail * y1,
            rolls_into="Compute", phase="recurring", category="Compute",
            note=f"{R.COMMITMENT_LABEL[p['commitment']]}, {ramp_note}"))

    prod = sum(n * R.INSTANCE_HOURLY[c] for c, n in p["instances"].items()) * R.HOURS_PA
    nonprod = prod * p["nonprod_ratio"] * R.NONPROD_RUNTIME_FACTOR
    if nonprod:
        lines.append(bom_line(
            "Non-production environments", 1, "environment set",
            nonprod * discount * avail * y1,
            rolls_into="Compute", phase="recurring", category="Compute",
            note=f"{p['nonprod_ratio']:.0%} of production at "
                 f"{R.NONPROD_RUNTIME_FACTOR:.0%} runtime, {ramp_note}"))

    for tier, tb in sorted(p["storage_tb"].items(), key=lambda kv_: -kv_[1]):
        if not tb:
            continue
        lines.append(bom_line(
            f"{tier.title()} storage", tb, "TB",
            R.STORAGE_PER_TB_PM[tier] * 12 * avail * y1,
            rolls_into="Storage", phase="recurring", category="Storage",
            note=ramp_note))

    if p["egress_tb_pm"]:
        lines.append(bom_line(
            "Network egress", p["egress_tb_pm"] * 12, "TB per annum",
            R.EGRESS_PER_TB * y1, rolls_into="Network egress",
            phase="recurring", category="Network", note=ramp_note))

    retention_factor = 1 + (p["backup_retention_days"] / 90) * 0.4
    lines.append(bom_line(
        "Backup and retention", p["storage_total_tb"], "TB protected",
        R.BACKUP_PER_TB_PM * 12 * retention_factor * y1,
        rolls_into="Backup", phase="recurring", category="Storage",
        note=f"{p['backup_retention_days']}-day retention, {ramp_note}"))

    tooling_unit = R.TOOLING_PER_INSTANCE_PA[p["managed_level"]]
    if tooling_unit:
        lines.append(bom_line(
            "Monitoring and management tooling", p["instance_total"],
            "instance per annum", tooling_unit * y1,
            rolls_into="Monitoring and tooling", phase="recurring",
            category="Software", note=ramp_note))
    return lines


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight = _run(p)

    # Steady state is the year-one price scaled up by the ramp, so it
    # reconciles with the schedule. Deriving it from consumption alone would
    # omit labour and overhead and contradict the final year on the same page.
    y1 = run["drivers"]["year_one_fraction"]
    steady_price = run["price_pa"] / y1 if y1 else run["price_pa"]
    per_vcpu_pm = steady_price / 12 / p["vcpu_total"] if p["vcpu_total"] else 0.0

    return build_result(
        manifest=MANIFEST,
        client_name=p["client_name"], rfp_ref=p["rfp_ref"],
        scope_headline=[
            scope_item("Instances", p["instance_total"]),
            scope_item("vCPU total", p["vcpu_total"]),
            scope_item("Storage (TB)", round(p["storage_total_tb"], 1), "float1"),
            scope_item("Workloads to migrate", p["workloads"]),
        ],
        service=[
            kv("Commitment", R.COMMITMENT_LABEL[p["commitment"]]),
            kv("Resilience", R.AVAILABILITY_LABEL[p["availability"]]),
            kv("Management", R.MANAGED_LABEL[p["managed_level"]]),
            kv("Backup retention", f"{p['backup_retention_days']} days"),
            kv("Migration ramp", f"{p['ramp_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per vCPU per month at steady state",
             "value": round(per_vcpu_pm, 2)},
            {"label": "Steady-state annual charge", "value": round(steady_price, 2)},
        ],
        scope_detail={"instances": p["instances"], "storage_tb": p["storage_tb"]},
        bom=_bom(p),
    )
