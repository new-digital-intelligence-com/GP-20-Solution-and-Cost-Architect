"""
Model pack — Logistics tower.

One lot of a lotted tender: parts and their movement. Spares holding, forward
stock, shipping, RMA and repair, staging, end-of-life disposal.

The reason this is its own lot rather than a line in someone else's: a committed
fix time is a **stock** commitment before it is a labour commitment. An engineer
standing next to a broken switch with no spare has not met a four-hour fix, and
no amount of field headcount changes that. Priced separately, the two lots can
be checked against each other — which is the only way anyone notices that the
tender has committed to four hours on central stock.

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
    key="logistics",
    name="Logistics and Spares",
    kind="tower",
    summary="Spares holding, forward stock, shipping, RMA and repair, staging "
            "and end-of-life disposal across the estate.",
    detect=[
        "logistics", "spares", "spare parts", "stock", "stockholding",
        "forward stock", "warehouse", "warehousing", "rma", "return material",
        "repair", "depot", "staging", "asset disposal", "weee", "end of life",
        "supply chain", "shipping", "courier",
    ],
    material=["stock_strategy", "disposal", "margin_pct", "term_years"],
    settings=[*COMMON_SETTINGS, "delivery_country"],
    notes="Stock strategy is chosen by the fix time the bid commits to, not by "
          "preference. Where the field lot promises four hours and this lot "
          "holds central stock, the commitment cannot be met — and neither "
          "lot's own numbers will show it.",
    gaps=[
        Gap(
            param="stock_strategy",
            question="What spares model should be priced?",
            rfp_hint="Rarely stated directly. Read it off the committed fix "
                     "time instead — that is what decides it.",
            options=[
                GapOption("central", "Central stock — one hub",
                          "2.5% of estate value. Supports next business day and "
                          "nothing faster."),
                GapOption("regional", "Regional stock — two hubs",
                          "4.5%. Same-day within region; still cannot commit to "
                          "a four-hour fix across borders."),
                GapOption("forward", "Forward stock in every country",
                          "7.0% plus a small warehouse per country. The minimum "
                          "that supports a four-hour in-country fix."),
                GapOption("onsite", "On-site stock at large sites",
                          "11.5%. Supports a one-hour fix where stocked, and "
                          "carries the most obsolescence risk."),
            ],
        ),
        Gap(
            param="disposal",
            question="What end-of-life treatment is in scope?",
            rfp_hint="Look for WEEE, data destruction or certificate "
                     "requirements — they change the unit cost materially.",
            options=[
                GapOption("none", "Client retains disposal",
                          "No cost in this lot; the obligation stays with the "
                          "client and should be stated in the response."),
                GapOption("recycle", "Certified recycling",
                          "£8.50 a device. Meets WEEE without data guarantees."),
                GapOption("secure_erase", "Secure erasure and certified disposal",
                          "£16.15 a device with certificates. Assume this "
                          "wherever the estate holds regulated data."),
            ],
        ),
        Gap(
            param="staging_included",
            question="Is device staging and build in scope for this lot?",
            rfp_hint="Often assumed into a deployment lot instead — check it is "
                     "priced exactly once across the bid.",
            options=[
                GapOption("true", "Staging in this lot",
                          "£22 a device to build, asset-tag and kit before "
                          "dispatch."),
                GapOption("false", "Staging elsewhere",
                          "Assumes another lot owns build. Confirm it does, or "
                          "the bid has a gap rather than a saving."),
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

    if not estate["hardware_value"]:
        raise ValidationError(
            "Logistics prices parts — the estate holds no hardware to stock.")

    p["term_years"] = int(take("term_years", R.DEFAULT_TERM_YEARS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")
    p["mobilisation_months"] = int(
        take("mobilisation_months", R.DEFAULT_MOBILISATION_MONTHS))

    p["stock_strategy"] = take("stock_strategy", "central",
                               "Decides what fix time the bid can support.")
    if p["stock_strategy"] not in R.STOCK_STRATEGY:
        raise ValidationError(
            f"stock_strategy must be one of {list(R.STOCK_STRATEGY)}")

    # The field lot's commitment, when there is one. Not used to override the
    # strategy — the point is to report the mismatch, not to silently fix it.
    p["fix_tier"] = take("fix_tier", "", "The field lot's committed response "
                                         "tier, for coherence checking.")
    if p["fix_tier"] and p["fix_tier"] not in R.TIER_MIN_STRATEGY:
        raise ValidationError(
            f"fix_tier must be one of {list(R.TIER_MIN_STRATEGY)} or empty")

    # Part consumption follows dispatches. A figure from the field lot wins.
    if params.get("dispatches_pa"):
        p["dispatches_pa"] = float(params["dispatches_pa"])
        reg.append(assumption("dispatches_pa", round(p["dispatches_pa"]),
                              src.get("dispatches_pa", "user"),
                              "Taken from the field service lot."))
    else:
        p["dispatches_pa"] = (estate["device_total"] * 0.16
                              + estate["aps_total"] * 0.12
                              + estate["switch_count"] * 0.22)
        reg.append(assumption("dispatches_pa", round(p["dispatches_pa"]),
                              "derived",
                              "No field service lot supplied a figure; derived "
                              "from the estate."))

    p["disposal"] = take("disposal", "recycle")
    if p["disposal"] not in R.DISPOSAL_MODE:
        raise ValidationError(f"disposal must be one of {list(R.DISPOSAL_MODE)}")

    p["staging_included"] = bool(take("staging_included", True))
    p["staging_devices_pa"] = float(take(
        "staging_devices_pa", estate["device_total"] / 4.0,
        "Devices staged per annum; a quarter of the fleet on a four-year cycle."))

    p["delivery_country"] = take("delivery_country", R.HUB_PRIMARY,
                                 "Where the central function is staffed.")
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


def _locations(p: dict) -> int:
    e, strat = p["estate"], p["stock_strategy"]
    spec = R.STOCK_STRATEGY[strat]
    if strat == "forward":
        return len(e["country_mix"])
    if strat == "onsite":
        return sum(e["sites"].get(b, 0) for b in R.ONSITE_BANDS) or 1
    return spec["locations"]


def _deployment(p: dict) -> dict:
    locations = _locations(p)
    setup = locations * R.SETUP_DAYS_PER_LOCATION
    integration = R.SYSTEM_INTEGRATION_DAYS
    pm = (setup + integration) * R.PM_OVERHEAD_PCT

    rates = R.COUNTRY_RATES[p["delivery_country"]]
    labour = (setup * rates["store"] + integration * rates["planner"]
              + pm * rates["sdm"])

    # The pool is bought at mobilisation and replaced on its own cycle.
    pool_value = p["estate"]["hardware_value"] * \
        R.STOCK_STRATEGY[p["stock_strategy"]]["pool_pct"]
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + pool_value + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"location_setup": setup,
                      "system_integration": integration,
                      "project_management": pm,
                      "total": setup + integration + pm},
        cost_lines=[cost_line("Mobilisation labour", labour),
                    cost_line("Initial spares pool", pool_value),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["mobilisation_months"])


def _run(p: dict) -> tuple[dict, str, dict]:
    e = p["estate"]
    strat = p["stock_strategy"]
    spec = R.STOCK_STRATEGY[strat]
    locations = _locations(p)

    pool_value = e["hardware_value"] * spec["pool_pct"]
    carrying = pool_value * R.CARRYING_PCT_PA
    pool_refresh = pool_value / R.STOCK_REFRESH_YEARS

    units = max(1.0, e["aps_total"] + e["switch_count"] + e["device_total"])
    sqm = units / 1000 * R.SQM_PER_1K_UNITS
    warehouse = 0.0
    if locations:
        fixed = R.WAREHOUSE_FIXED_PA[strat] * locations
        warehouse = fixed + sqm * R.WAREHOUSE_PER_SQM_PA

    parts = p["dispatches_pa"] * R.PARTS_PER_DISPATCH
    shipping = parts * R.SHIPMENT_COST[R.SHIPMENT_TIER[strat]]

    returned = parts * R.RETURN_RATE
    rma_handling = returned * R.RMA_HANDLING_COST
    unit_value = e["hardware_value"] / units
    repaired = returned * R.REPAIRABLE_SHARE * (1 - R.WARRANTY_RECOVERY_PCT)
    repair = repaired * unit_value * R.REPAIR_COST_PCT

    staging = (p["staging_devices_pa"] * R.STAGING_COST_PER_DEVICE
               if p["staging_included"] else 0.0)
    disposal = (p["staging_devices_pa"] * R.DISPOSAL_COST_PER_DEVICE
                * R.DISPOSAL_MODE[p["disposal"]])

    storekeepers = max(0.5, units / R.UNITS_PER_STOREKEEPER_PA)
    planners = max(0.4, locations * R.PLANNER_PER_LOCATION)
    rates = R.COUNTRY_RATES[p["delivery_country"]]
    labour = (storekeepers * rates["store"] + planners * rates["planner"]) \
        * R.WORKING_DAYS_PA
    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    labour += sdm * rates["sdm"] * R.WORKING_DAYS_PA

    hub = p["delivery_country"]
    resources = [resource(hub, "Storekeeper", storekeepers, "units under stock"),
                 resource(hub, "Supply Planner", planners, "stocking locations"),
                 resource(hub, "Logistics Manager", sdm, "contract band")]

    overhead = labour * R.OVERHEAD_PCT
    subtotal = (labour + carrying + pool_refresh + warehouse + shipping
                + rma_handling + repair + staging + disposal + overhead)
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    lines = [cost_line("Labour", labour),
             cost_line("Stock carrying cost", carrying),
             cost_line("Spares pool replenishment", pool_refresh)]
    if warehouse:
        lines.append(cost_line("Warehousing", warehouse))
    lines += [cost_line("Shipping and courier", shipping),
              cost_line("RMA handling", rma_handling),
              cost_line("Repair", repair)]
    if staging:
        lines.append(cost_line("Device staging", staging))
    if disposal:
        lines.append(cost_line("End-of-life disposal", disposal))
    lines += [cost_line("Delivery overhead", overhead),
              cost_line("Contingency", contingency)]

    # The observation. A fix commitment the supply chain cannot support is the
    # single most expensive thing a lotted bid can get wrong, because it is not
    # discovered until service commences.
    required = R.TIER_MIN_STRATEGY.get(p["fix_tier"], "")
    if required and R.STRATEGY_RANK[strat] < R.STRATEGY_RANK[required]:
        insight = (
            f"The field lot commits to a {p['fix_tier']} on-site fix, which "
            f"needs {required} stock — this lot is priced for {strat}, which "
            f"supports {R.FIX_TIME_SUPPORTED[strat]}. The commitment cannot be "
            f"met as priced. Moving to {required} adds stock, and neither lot's "
            f"own figures show the gap: the field lot has its engineers, this "
            f"lot has its warehouse, and the part is not in the van.")
    elif spec["pool_pct"] >= 0.07:
        share = (carrying + pool_refresh) / cost
        insight = (
            f"{share:.0%} of this lot is the spares pool — £{pool_value:,.0f} of "
            f"stock held to support {R.FIX_TIME_SUPPORTED[strat]}. That is "
            f"capital sitting on shelves against {parts:,.0f} parts a year "
            f"actually consumed. Relaxing the fix commitment in the low-density "
            f"countries would release most of it, and is a conversation for the "
            f"field lot rather than this one.")
    else:
        insight = (
            f"Priced on {strat} stock, supporting {R.FIX_TIME_SUPPORTED[strat]}. "
            f"Movement rather than holding dominates: £{shipping:,.0f} of "
            f"shipping against £{carrying:,.0f} of carrying cost. If the bid "
            f"later tightens the fix commitment, this lot changes shape "
            f"entirely — it is not a percentage adjustment.")

    block = run_block(
        resources=resources,
        cost_lines=lines,
        cost_pa=cost, price_pa=cost / (1 - p["margin_pct"]),
        drivers={"pool_value": round(pool_value, 2),
                 "stocking_locations": locations,
                 "parts_consumed_pa": round(parts, 1),
                 "supports_fix_time": R.FIX_TIME_SUPPORTED[strat],
                 "stock_strategy": strat})
    return block, insight, {"pool_value": pool_value, "locations": locations,
                            "parts": parts, "units": units}


def _bom(p: dict, d: dict) -> list[dict]:
    e = p["estate"]
    lines = EST.hardware_bom(e, rolls_into="Initial spares pool",
                             phase="one-off")
    pct = R.STOCK_STRATEGY[p["stock_strategy"]]["pool_pct"]
    # The pool is a fraction of the estate, so each estate line is scaled.
    scaled = []
    for line in lines:
        scaled.append(bom_line(
            f"{line['item']} — spares pool", line["qty"], line["unit"],
            line["unit_cost"] * pct, rolls_into="Initial spares pool",
            phase="one-off", category="Spares",
            note=f"{pct:.1%} pool for {p['stock_strategy']} stock"))
    if d["parts"]:
        scaled.append(bom_line(
            "Pool replenishment", d["parts"], "part consumed per annum",
            d["pool_value"] / R.STOCK_REFRESH_YEARS / d["parts"],
            rolls_into="Spares pool replenishment", phase="recurring",
            category="Spares",
            note=f"Pool replaced on a {R.STOCK_REFRESH_YEARS}-year cycle"))
    return scaled


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight, d = _run(p)
    e = p["estate"]

    return build_result(
        manifest=MANIFEST,
        client_name=e["client_name"], rfp_ref=e["rfp_ref"],
        scope_headline=[
            scope_item("Units under stock", round(d["units"])),
            scope_item("Stocking locations", d["locations"]),
            scope_item("Spares pool value", round(d["pool_value"]), "money"),
            scope_item("Parts consumed per annum", round(d["parts"])),
        ],
        service=[
            kv("Stock strategy", R.STOCK_STRATEGY[p["stock_strategy"]]["label"]),
            kv("Supports fix time", R.FIX_TIME_SUPPORTED[p["stock_strategy"]]),
            kv("Disposal", R.DISPOSAL_LABEL[p["disposal"]]),
            kv("Staging", "In scope" if p["staging_included"] else "Elsewhere"),
            kv("Mobilisation", f"{p['mobilisation_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per unit under stock per annum",
             "value": round(run["price_pa"] / d["units"], 2)},
            {"label": "Per part consumed",
             "value": round(run["price_pa"] / d["parts"], 2) if d["parts"] else 0.0},
        ],
        scope_detail=EST.scope_detail(e),
        bom=_bom(p, d),
    )
