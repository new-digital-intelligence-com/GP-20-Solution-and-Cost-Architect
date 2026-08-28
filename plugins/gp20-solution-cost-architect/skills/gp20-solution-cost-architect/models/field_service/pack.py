"""
Model pack — Field Service tower.

One lot of a lotted tender: engineers attending sites. Break-fix dispatch, IMAC
work, smart hands. It consumes the shared estate and prices only attendance.

Two forces set the size, and they are independent:

  * **dispatch volume** — how often somebody has to travel, which is the estate's
    incident rate less whatever remote support closes without a visit;
  * **the coverage floor** — a committed on-site response time requires standing
    presence in every country, whatever the volume says.

Where the second exceeds the first, coverage sets the price and the estate is
almost irrelevant. Saying so is the point of this pack.

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
    key="field-service",
    name="Field Service",
    kind="tower",
    summary="On-site engineering attendance across the estate — break-fix "
            "dispatch, IMAC and smart hands, to a committed response time.",
    detect=[
        "field service", "field services", "on-site support", "onsite support",
        "engineer attendance", "smart hands", "deskside", "desk-side",
        "break-fix", "break fix", "imac", "installs moves adds",
        "site attendance", "on-site response", "dispatch",
    ],
    material=["sla_tier", "coverage", "remote_capability", "margin_pct",
              "term_years"],
    settings=[*COMMON_SETTINGS],
    notes="Sized by whichever is larger: dispatch volume, or the standing "
          "presence a committed on-site response requires in each country. "
          "When the floor binds, incident volume stops mattering and the price "
          "is set by geography and the clock.",
    gaps=[
        Gap(
            param="coverage",
            question="What coverage window should field attendance be sized "
                     "for?",
            rfp_hint="Tenders often state 24×7 for monitoring while expressing "
                     "on-site response targets in business hours. Those are "
                     "different commitments — check which governs attendance.",
            options=[
                GapOption("8x5", "8×5 — business hours",
                          "One shift per post. Cheapest, and adequate where the "
                          "response targets are themselves in business hours."),
                GapOption("12x5", "12×5 — extended day",
                          "1.70 FTE per staffed post. Early and late shifts, no "
                          "weekend cover."),
                GapOption("24x7", "24×7 — continuous",
                          "4.80 FTE per staffed post, in every country with a "
                          "committed response. The single largest lever in "
                          "this lot."),
            ],
        ),
        Gap(
            param="sla_tier",
            question="What on-site response time is being committed to?",
            rfp_hint="Anything at 4 hours or better forces standing presence in "
                     "each country; 8 hours or next-day can be served from a "
                     "travelling pool.",
            options=[
                GapOption("bronze", "Next business day",
                          "No coverage floor. Sized purely by dispatch volume, "
                          "which is much cheaper across a dispersed estate."),
                GapOption("silver", "8 business hours",
                          "×1.15 on volume-driven effort, still no standing "
                          "presence required."),
                GapOption("gold", "4 business hours",
                          "×1.40, and triggers the coverage floor — a staffed "
                          "post in every country regardless of volume."),
                GapOption("platinum", "2 business hours",
                          "×1.90 and the floor, with tighter post density. "
                          "Rarely justified outside campus estates."),
            ],
        ),
        Gap(
            param="remote_capability",
            question="What remote support capability sits in front of this lot?",
            rfp_hint="If the tender lots remote support separately, its "
                     "capability decides how many incidents become dispatches "
                     "here. Price the two together or this lot is guesswork.",
            options=[
                GapOption("none", "No remote tower",
                          "Every incident becomes a visit. Roughly triples "
                          "dispatch volume against a standard desk."),
                GapOption("basic", "Scripted triage and remote control",
                          "Closes 42% remotely."),
                GapOption("standard", "Tooling, automation, experienced 2nd line",
                          "Closes 61% remotely — the usual assumption."),
                GapOption("advanced", "Proactive monitoring and self-heal",
                          "Closes 74% remotely, but only pays back where the "
                          "floor is not already binding."),
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

    if not estate["sites_total"]:
        raise ValidationError(
            "Field service prices attendance at sites — state the site estate.")

    p["term_years"] = int(take("term_years", R.DEFAULT_TERM_YEARS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")
    p["mobilisation_months"] = int(
        take("mobilisation_months", R.DEFAULT_MOBILISATION_MONTHS))

    p["sla_tier"] = take("sla_tier", "silver", "Drives the coverage floor.")
    if p["sla_tier"] not in R.SLA_MULTIPLIER:
        raise ValidationError(f"sla_tier must be one of {list(R.SLA_MULTIPLIER)}")

    p["coverage"] = take("coverage", "8x5", "Largest single cost lever.")
    if p["coverage"] not in R.COVERAGE_EFFICIENCY:
        raise ValidationError(
            f"coverage must be one of {list(R.COVERAGE_EFFICIENCY)}")

    p["remote_capability"] = take(
        "remote_capability", "standard",
        "Sets how many incidents become dispatches in this lot.")
    if p["remote_capability"] not in R.REMOTE_FIX_RATE:
        raise ValidationError(
            f"remote_capability must be one of {list(R.REMOTE_FIX_RATE)}")

    p["imac_included"] = take("imac_included", True)

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(
        take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(
        take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")
    return p, reg


def _incidents(p: dict) -> dict:
    e = p["estate"]
    parts = {
        "access points": e["aps_total"] * R.AP_INCIDENT_RATE_PA,
        "switches": e["switch_count"] * R.SWITCH_INCIDENT_RATE_PA,
        "end-user devices": e["device_total"] * R.DEVICE_INCIDENT_RATE_PA,
        "site infrastructure": e["sites_total"] * R.SITE_INFRA_INCIDENT_RATE_PA,
    }
    return {k: v for k, v in parts.items() if v}


def _deployment(p: dict) -> dict:
    e = p["estate"]
    days = (R.MOBILISATION_FIXED_DAYS
            + e["sites_total"] * R.MOBILISATION_DAYS_PER_SITE)
    blended_field = sum(R.COUNTRY_RATES[c]["field"] * s
                        for c, s in e["country_mix"].items())
    labour = days * blended_field

    # Tooling is bought per engineer, so it cannot be costed until the run
    # model has sized the team. _run() reports the headcount; mobilisation
    # follows it rather than guessing.
    tooling = p["_engineers"] * R.TOOLING_PER_ENGINEER
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + tooling + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"site_mobilisation": e["sites_total"]
                      * R.MOBILISATION_DAYS_PER_SITE,
                      "programme_setup": R.MOBILISATION_FIXED_DAYS,
                      "total": days},
        cost_lines=[cost_line("Mobilisation labour", labour),
                    cost_line("Engineer tooling and test equipment", tooling),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["mobilisation_months"])


def _run(p: dict) -> tuple[dict, str, dict]:
    e = p["estate"]
    incidents = sum(_incidents(p).values())
    remote_rate = R.REMOTE_FIX_RATE[p["remote_capability"]]
    dispatches = incidents * (1 - remote_rate)

    hours = dispatches * R.HOURS_PER_DISPATCH
    if p["imac_included"]:
        hours += e["user_count"] * R.IMAC_PER_USER_PA * R.IMAC_HOURS

    demand_total = (hours / R.PRODUCTIVE_HOURS_PA
                    * R.SLA_MULTIPLIER[p["sla_tier"]]
                    * R.COVERAGE_EFFICIENCY[p["coverage"]])

    enforce = p["sla_tier"] in R.ON_SITE_RESPONSE_TIERS
    by_country: dict[str, dict] = {}
    for c, share in e["country_mix"].items():
        demand = demand_total * share
        posts = (max(1, math.ceil(e["sites_total"] * share / R.SITES_PER_POST))
                 if enforce else 0)
        floor = posts * R.PRESENCE_FTE_PER_POST[p["coverage"]] if enforce else 0.0
        by_country[c] = {
            "fte": max(demand, floor), "demand": demand, "floor": floor,
            "posts": posts,
            "driver": "coverage floor" if floor > demand else "dispatch volume"}

    field_fte = sum(v["fte"] for v in by_country.values())

    resources = [resource(c, "Field Engineer", v["fte"], v["driver"])
                 for c, v in sorted(by_country.items(), key=lambda kv_: -kv_[1]["fte"])
                 if v["fte"] >= 0.01]

    labour = sum(v["fte"] * R.COUNTRY_RATES[c]["field"] * R.WORKING_DAYS_PA
                 for c, v in by_country.items())
    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    blended_sdm = sum(R.COUNTRY_RATES[c]["sdm"] * s
                      for c, s in e["country_mix"].items())
    labour += sdm * blended_sdm * R.WORKING_DAYS_PA
    resources.append(resource(max(e["country_mix"], key=e["country_mix"].get),
                              "Field Service Manager", sdm, "contract band"))

    travel = sum(dispatches * s * R.COUNTRY_RATES[c]["travel"]
                 for c, s in e["country_mix"].items())
    vehicles = field_fte * R.VEHICLE_PER_ENGINEER_PA
    overhead = (labour + travel) * R.OVERHEAD_PCT
    subtotal = labour + travel + vehicles + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    floor_driven = [c for c, v in by_country.items()
                    if v["driver"] == "coverage floor"]
    surplus = sum(v["fte"] - v["demand"] for v in by_country.values()
                  if v["driver"] == "coverage floor")

    if floor_driven:
        insight = (
            f"{', '.join(floor_driven)} are sized by the on-site response "
            f"commitment, not by workload — {surplus:.1f} FTE of standing "
            f"presence exceeds the {dispatches:,.0f} dispatches a year those "
            f"countries actually generate. While the floor binds, improving "
            f"remote support does not reduce this lot at all: the engineers "
            f"are there for the clock, not the queue. Relaxing the tier in the "
            f"low-density countries, or pooling regionally, is the only lever "
            f"that moves it.")
    else:
        headroom = incidents * (R.REMOTE_FIX_RATE["advanced"] - remote_rate)
        if remote_rate == 0:
            insight = (
                f"No remote support tower is assumed, so all "
                f"{incidents:,.0f} incidents a year become site visits and this "
                f"lot carries the entire estate. Standing up even basic remote "
                f"triage would remove roughly "
                f"{incidents * R.REMOTE_FIX_RATE['basic']:,.0f} of them. If the "
                f"tender lots remote support separately, this lot is being "
                f"priced for work another lot is meant to absorb — worth "
                f"confirming before the bid goes in.")
        else:
            insight = (
                f"This lot is sized by dispatch volume, not by the response "
                f"commitment, so remote capability is the lever: "
                f"{p['remote_capability']} support already avoids "
                f"{incidents * remote_rate:,.0f} visits a year out of "
                f"{incidents:,.0f} incidents. Moving to advanced would remove "
                f"about {headroom:,.0f} more — a saving that has to be bought "
                f"in the remote lot and shows up here, which is exactly the "
                f"trade a lotted tender makes easy to miss.")

    block = run_block(
        resources=resources,
        cost_lines=[cost_line("Field labour", labour),
                    cost_line("Travel and subsistence", travel),
                    cost_line("Vehicles and field overhead", vehicles),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost_pa=cost, price_pa=cost / (1 - p["margin_pct"]),
        drivers={"incidents_pa": round(incidents, 1),
                 "dispatches_pa": round(dispatches, 1),
                 "remote_fix_rate": remote_rate,
                 "floor_driven_countries": floor_driven,
                 "surplus_fte": round(surplus, 2)})
    return block, insight, {"field_fte": field_fte, "dispatches": dispatches}


def _bom(p: dict, engineers: float) -> list[dict]:
    return [
        bom_line("Engineer tooling and test equipment", engineers, "engineer",
                 R.TOOLING_PER_ENGINEER,
                 rolls_into="Engineer tooling and test equipment",
                 phase="one-off", category="Field equipment",
                 note="Issued once per engineer at mobilisation"),
        bom_line("Vehicle and field overhead", engineers, "engineer per annum",
                 R.VEHICLE_PER_ENGINEER_PA,
                 rolls_into="Vehicles and field overhead", phase="recurring",
                 category="Field equipment"),
    ]


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)

    # The run model sizes the team; mobilisation then equips it. Running them
    # in this order avoids two different headcounts in one lot.
    run, insight, d = _run(p)
    p["_engineers"] = d["field_fte"]
    dep = _deployment(p)

    e = p["estate"]
    return build_result(
        manifest=MANIFEST,
        client_name=e["client_name"], rfp_ref=e["rfp_ref"],
        scope_headline=[
            scope_item("Sites attended", e["sites_total"]),
            scope_item("Countries", len(e["country_mix"])),
            scope_item("Dispatches per annum", round(d["dispatches"])),
            scope_item("Field engineers", round(d["field_fte"], 1), "float1"),
        ],
        service=[
            kv("On-site response", R.SLA_RESPONSE[p["sla_tier"]]),
            kv("Coverage window", R.COVERAGE_LABEL[p["coverage"]]),
            kv("Remote support assumed",
               f"{p['remote_capability']} — closes "
               f"{R.REMOTE_FIX_RATE[p['remote_capability']]:.0%} without a visit"),
            kv("IMAC included", "Yes" if p["imac_included"] else "No"),
            kv("Mobilisation", f"{p['mobilisation_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per site per month",
             "value": round(run["price_pa"] / 12 / e["sites_total"], 2)},
            {"label": "Per dispatch",
             "value": round(run["price_pa"] / d["dispatches"], 2)
             if d["dispatches"] else 0.0},
        ],
        scope_detail=EST.scope_detail(e),
        bom=_bom(p, d["field_fte"]),
    )
