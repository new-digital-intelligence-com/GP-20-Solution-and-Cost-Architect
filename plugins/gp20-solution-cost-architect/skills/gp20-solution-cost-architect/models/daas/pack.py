"""
Model pack — Device as a Service.

Deliberately unlike managed LAN in structure: the dominant cost is hardware
amortised over a refresh cycle, labour is a minority of the price, and the
buying metric is £ per device per month. If the contract holds for both of
these, it will hold for the rest of the catalogue.

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
    key="daas",
    name="Device as a Service",
    summary="End-user device fleet supplied, imaged, deployed, supported and "
            "refreshed as a per-device monthly service.",
    detect=[
        "device as a service", "daas", "end user device", "end-user computing",
        "workplace", "laptop", "desktop", "notebook", "device refresh",
        "device fleet", "image build", "break-fix", "asset disposal",
        "buyback", "mdm", "device lifecycle", "byod", "workstation",
    ],
    material=["swap_sla", "refresh_years", "margin_pct", "term_years",
              "deployment_method"],
    notes="Refresh cycle is the dominant lever: it sets how much of each "
          "device's capital cost lands in every year of the contract. Swap SLA "
          "is second, because it drives both the spare pool and the technician "
          "presence.",
    gaps=[
        Gap(
            param="refresh_years",
            question="What refresh cycle should be priced?",
            rfp_hint="Often stated as a policy aspiration rather than a "
                     "contractual term. Check whether the tender fixes it.",
            options=[
                GapOption("3", "3 years",
                          "Highest monthly cost — each device's capital is "
                          "recovered over 36 months. Best residual value and "
                          "lowest failure rate in the final year."),
                GapOption("4", "4 years",
                          "The common middle. Materially cheaper per month than "
                          "3-year, with a modest rise in year-four failures."),
                GapOption("5", "5 years",
                          "Lowest monthly cost, but break-fix volume and swap "
                          "logistics rise sharply in the final two years, and "
                          "residual value is close to nil."),
            ],
        ),
        Gap(
            param="swap_sla",
            question="What break-fix commitment should be priced?",
            rfp_hint="Look for a replacement-device time, which is different "
                     "from a service-desk response time.",
            options=[
                GapOption("next_business_day", "Next business day",
                          "2% spare pool, central dispatch. Cheapest and "
                          "adequate for most office populations."),
                GapOption("8h", "8 business hours",
                          "4% spare pool plus regional technician presence."),
                GapOption("4h", "4 business hours",
                          "7% spare pool and standing local technicians. The "
                          "spare pool alone is a significant capital line."),
            ],
        ),
        Gap(
            param="deployment_method",
            question="How should devices reach users at rollout?",
            rfp_hint="Tenders often specify minimal disruption without saying "
                     "whether that means desk-side or shipped.",
            options=[
                GapOption("ship_to_user", "Ship direct to user",
                          "Cheapest labour, adds shipping. Depends on zero-touch "
                          "enrolment working reliably."),
                GapOption("desk_side", "Desk-side hand-over",
                          "Most labour-intensive at roughly 45 minutes a device, "
                          "but the highest first-time-right rate."),
                GapOption("depot_collect", "Depot collection",
                          "Middle ground. Users travel to a staffed point; needs "
                          "one per major location."),
            ],
        ),
        Gap(
            param="image_strategy",
            question="How many build images should be priced?",
            rfp_hint="Check for persona or role-based device requirements.",
            options=[
                GapOption("standard", "Single standard image",
                          "One build, 12 days. Cheapest to create and maintain."),
                GapOption("custom", "Standard plus custom variants",
                          "Three builds. Covers common role differences."),
                GapOption("per_persona", "Per-persona images",
                          "Six builds. Highest build and ongoing maintenance "
                          "cost; only justified where roles genuinely diverge."),
            ],
        ),
        Gap(
            param="disposal",
            question="What should happen to the outgoing fleet?",
            rfp_hint="Look for sustainability or data-destruction requirements.",
            options=[
                GapOption("buyback", "Buyback credit",
                          "Residual value returns 6–18% of unit cost depending "
                          "on device type, reducing the monthly charge."),
                GapOption("recycle", "Certified recycling only",
                          "No credit, but a documented disposal chain."),
                GapOption("none", "Client retains the outgoing fleet",
                          "No credit and no disposal cost."),
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
    p["rollout_months"] = int(take("rollout_months", R.DEFAULT_ROLLOUT_MONTHS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")

    fleet_in = params.get("devices") or {}
    unknown = set(fleet_in) - set(R.DEVICE_TYPES)
    if unknown:
        raise ValidationError(
            f"Unknown device type(s) {sorted(unknown)}. "
            f"Catalogue covers: {R.DEVICE_TYPES}")
    fleet = {t: int(fleet_in.get(t, 0) or 0) for t in R.DEVICE_TYPES}
    if sum(fleet.values()) == 0:
        raise ValidationError("At least one device must be specified.")
    for t, n in fleet.items():
        if n:
            reg.append(assumption(f"devices.{t}", n, src.get("devices", "user")))
    p["devices"] = fleet
    p["device_total"] = sum(fleet.values())

    if params.get("user_count"):
        p["user_count"] = int(params["user_count"])
        reg.append(assumption("user_count", p["user_count"], src.get("user_count", "user")))
    else:
        # Phones and tablets are usually second devices, not second users.
        primary = fleet["laptop_standard"] + fleet["laptop_performance"] + fleet["desktop"]
        p["user_count"] = max(1, primary)
        reg.append(assumption("user_count", p["user_count"], "derived",
                              "Derived from primary devices; phones and tablets "
                              "treated as secondary."))

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

    p["refresh_years"] = int(take("refresh_years", R.DEFAULT_REFRESH_YEARS,
                                  "Dominant cost lever."))
    if p["refresh_years"] not in R.REFRESH_YEARS_ALLOWED:
        raise ValidationError(
            f"refresh_years must be one of {list(R.REFRESH_YEARS_ALLOWED)}")

    p["swap_sla"] = take("swap_sla", "next_business_day",
                         "Drives spare pool and technician presence.")
    if p["swap_sla"] not in R.SWAP_SLA_MULTIPLIER:
        raise ValidationError(f"swap_sla must be one of {list(R.SWAP_SLA_MULTIPLIER)}")

    p["deployment_method"] = take("deployment_method", "ship_to_user")
    if p["deployment_method"] not in R.DEPLOY_MINUTES_PER_DEVICE:
        raise ValidationError(
            f"deployment_method must be one of {list(R.DEPLOY_MINUTES_PER_DEVICE)}")

    p["image_strategy"] = take("image_strategy", "standard")
    if p["image_strategy"] not in R.IMAGE_VARIANTS:
        raise ValidationError(f"image_strategy must be one of {list(R.IMAGE_VARIANTS)}")

    p["accessories"] = take("accessories", "standard")
    if p["accessories"] not in R.ACCESSORY_LEVEL:
        raise ValidationError(f"accessories must be one of {list(R.ACCESSORY_LEVEL)}")

    p["disposal"] = take("disposal", "buyback")
    if p["disposal"] not in ("buyback", "recycle", "none"):
        raise ValidationError("disposal must be buyback, recycle or none")

    p["service_desk"] = take("service_desk", True)

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")

    return p, reg


def _blended(p: dict, role: str) -> float:
    return sum(R.COUNTRY_RATES[c][role] * s for c, s in p["country_mix"].items())


def _deployment(p: dict) -> dict:
    n, users = p["device_total"], p["user_count"]
    variants = R.IMAGE_VARIANTS[p["image_strategy"]]

    image_days = variants * R.IMAGE_BUILD_DAYS_PER_VARIANT
    enrol_days = n * R.ENROLMENT_MINUTES_PER_DEVICE / 60 / 7.5
    deploy_days = n * R.DEPLOY_MINUTES_PER_DEVICE[p["deployment_method"]] / 60 / 7.5
    migrate_days = users * R.DATA_MIGRATION_MINUTES_PER_USER / 60 / 7.5
    pm_days = (image_days + enrol_days + deploy_days + migrate_days) * R.PM_OVERHEAD_PCT

    labour = (image_days * _blended(p, "engineer")
              + (enrol_days + deploy_days + migrate_days) * _blended(p, "tech")
              + pm_days * _blended(p, "sdm"))
    shipping = n * R.SHIPPING_COST_PER_DEVICE[p["deployment_method"]]
    collection = n * R.LEGACY_COLLECTION_PER_DEVICE if p["disposal"] != "none" else 0.0
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + shipping + collection + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"image_build": image_days, "enrolment": enrol_days,
                      "deployment": deploy_days, "data_migration": migrate_days,
                      "project_management": pm_days,
                      "total": image_days + enrol_days + deploy_days
                               + migrate_days + pm_days},
        cost_lines=[cost_line("Labour", labour),
                    cost_line("Shipping and logistics", shipping),
                    cost_line("Legacy collection", collection),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["rollout_months"])


def _run(p: dict) -> tuple[dict, str]:
    fleet, n = p["devices"], p["device_total"]
    refresh = p["refresh_years"]

    hardware_value = sum(q * R.DEVICE_UNIT_COST[t] for t, q in fleet.items())
    device_amort = hardware_value / refresh

    accessory_value = n * R.ACCESSORY_LEVEL[p["accessories"]]
    accessory_amort = accessory_value / R.ACCESSORY_REFRESH_YEARS

    buyback = 0.0
    if p["disposal"] == "buyback":
        buyback = sum(q * R.DEVICE_UNIT_COST[t] * R.BUYBACK_PCT[t]
                      for t, q in fleet.items()) / refresh

    # Break-fix. Devices fail more as they age, so a longer refresh raises the
    # average annual swap rate across the fleet.
    age_factor = 1.0 + 0.11 * (refresh - 3)
    swaps = sum(q * R.FAILURE_RATE_PA[t] for t, q in fleet.items()) * age_factor
    swap_logistics = swaps * R.SWAP_LOGISTICS_COST[p["swap_sla"]]
    spare_pool_value = hardware_value * R.SPARE_POOL_PCT[p["swap_sla"]]
    spare_pool_cost = spare_pool_value / refresh

    tech_hours = swaps * R.SWAP_MINUTES[p["swap_sla"]] / 60
    tech_fte_total = (tech_hours / R.PRODUCTIVE_HOURS_PA
                      * R.SWAP_SLA_MULTIPLIER[p["swap_sla"]])

    sd_fte = 0.0
    if p["service_desk"]:
        sd_hours = n * R.SD_CONTACTS_PER_DEVICE_PA * R.SD_MINUTES_PER_CONTACT / 60
        sd_fte = sd_hours / R.PRODUCTIVE_HOURS_PA

    resources: list[dict] = []
    labour = 0.0
    for c, share in sorted(p["country_mix"].items(), key=lambda kv_: -kv_[1]):
        fte = tech_fte_total * share
        if fte >= 0.01:
            resources.append(resource(c, "Device Technician", fte, "swap volume"))
        labour += fte * R.COUNTRY_RATES[c]["tech"] * R.WORKING_DAYS_PA
    if sd_fte:
        resources.append(resource(R.HUB_PRIMARY, "Service Desk", sd_fte, "central"))
        labour += sd_fte * R.COUNTRY_RATES[R.HUB_PRIMARY]["service_desk"] * R.WORKING_DAYS_PA

    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    labour += sdm * _blended(p, "sdm") * R.WORKING_DAYS_PA
    resources.append(resource(max(p["country_mix"], key=p["country_mix"].get),
                              "Service Delivery Manager", sdm, "contract band"))

    software = n * R.MDM_PER_DEVICE_PA
    asset_mgmt = R.ASSET_MGMT_FIXED_PA + n * R.ASSET_MGMT_PER_DEVICE_PA
    overhead = (labour + swap_logistics) * R.OVERHEAD_PCT
    subtotal = (device_amort + accessory_amort + spare_pool_cost + swap_logistics
                + labour + software + asset_mgmt + overhead - buyback)
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency
    price = cost / (1 - p["margin_pct"])

    lines = [cost_line("Device amortisation", device_amort)]
    if accessory_amort:
        lines.append(cost_line("Accessory amortisation", accessory_amort))
    lines += [cost_line("Spare pool", spare_pool_cost),
              cost_line("Break-fix logistics", swap_logistics),
              cost_line("Labour", labour),
              cost_line("Software and MDM", software),
              cost_line("Asset management and reporting", asset_mgmt),
              cost_line("Delivery overhead", overhead)]
    if buyback:
        lines.append(cost_line("Buyback credit", -buyback))
    lines.append(cost_line("Contingency", contingency))

    hw_share = device_amort / cost if cost else 0
    insight = (
        f"Hardware amortisation is {hw_share:.0%} of the annual cost — this is a "
        f"capital-shaped deal, not a labour-shaped one. Moving the refresh from "
        f"{refresh} to {refresh + 1} years would cut the device line by roughly "
        f"{100 / (refresh + 1):.0f}% of its current value, at the cost of higher "
        f"break-fix volume in the final year. Labour is only "
        f"{labour / cost:.0%} of the total, so squeezing the service model "
        f"cannot move this price much."
        if hw_share > 0.4 else
        f"Labour and service costs dominate at {labour / cost:.0%} of the annual "
        f"charge; the refresh cycle is not the main lever here.")

    block = run_block(
        resources=resources,
        cost_lines=lines,
        cost_pa=cost, price_pa=price,
        drivers={"swaps_pa": round(swaps, 1),
                 "hardware_value": round(hardware_value, 2),
                 "spare_pool_units": math.ceil(n * R.SPARE_POOL_PCT[p["swap_sla"]]),
                 "hardware_share_of_cost": round(hw_share, 3)})
    return block, insight


def _bom(p: dict) -> list[dict]:
    """The device fleet and everything bought per device, at cost.

    A DaaS bill of materials is mostly amortised capital rather than an
    outright purchase, so the recurring lines carry the annual charge per unit
    and the sticker price sits in the note. Finance needs both: conflating them
    is how a four-year refresh gets read as a one-off buy.
    """
    fleet, n, refresh = p["devices"], p["device_total"], p["refresh_years"]
    ordered = [(t, q) for t, q in sorted(fleet.items(), key=lambda kv_: -kv_[1]) if q]
    lines: list[dict] = []

    for t, q in ordered:
        lines.append(bom_line(
            f"{R.DEVICE_LABEL[t]} — annual amortisation", q, "device",
            R.DEVICE_UNIT_COST[t] / refresh,
            rolls_into="Device amortisation", phase="recurring",
            category="Device hardware",
            note=f"{R.DEVICE_UNIT_COST[t]:,.0f} unit cost over {refresh} years"))

    spare_pct = R.SPARE_POOL_PCT[p["swap_sla"]]
    if spare_pct:
        for t, q in ordered:
            lines.append(bom_line(
                f"{R.DEVICE_LABEL[t]} — spare pool", q, "device covered",
                R.DEVICE_UNIT_COST[t] * spare_pct / refresh,
                rolls_into="Spare pool", phase="recurring", category="Spares",
                note=f"{spare_pct:.1%} pool for a {p['swap_sla']} swap commitment"))

    accessory_unit = R.ACCESSORY_LEVEL[p["accessories"]]
    if accessory_unit:
        lines.append(bom_line(
            f"Accessory bundle — {p['accessories']}", n, "device",
            accessory_unit / R.ACCESSORY_REFRESH_YEARS,
            rolls_into="Accessory amortisation", phase="recurring",
            category="Accessories",
            note=f"{accessory_unit:,.0f} per device over "
                 f"{R.ACCESSORY_REFRESH_YEARS} years"))

    lines += [
        bom_line("MDM and endpoint software licence", n, "device per annum",
                 R.MDM_PER_DEVICE_PA, rolls_into="Software and MDM",
                 phase="recurring", category="Software"),
        bom_line("Asset management platform", 1, "tenant per annum",
                 R.ASSET_MGMT_FIXED_PA,
                 rolls_into="Asset management and reporting", phase="recurring",
                 category="Software"),
        bom_line("Asset management — per device", n, "device per annum",
                 R.ASSET_MGMT_PER_DEVICE_PA,
                 rolls_into="Asset management and reporting", phase="recurring",
                 category="Software"),
    ]

    age_factor = 1.0 + 0.11 * (refresh - 3)
    swaps = sum(q * R.FAILURE_RATE_PA[t] for t, q in fleet.items()) * age_factor
    lines.append(bom_line(
        "Break-fix swap logistics", swaps, "swap",
        R.SWAP_LOGISTICS_COST[p["swap_sla"]],
        rolls_into="Break-fix logistics", phase="recurring", category="Logistics",
        note=f"{p['swap_sla']} response, fleet age factor {age_factor:.2f}"))

    shipping_unit = R.SHIPPING_COST_PER_DEVICE[p["deployment_method"]]
    if shipping_unit:
        lines.append(bom_line(
            f"Outbound shipping — {p['deployment_method'].replace('_', ' ')}",
            n, "device", shipping_unit, rolls_into="Shipping and logistics",
            phase="one-off", category="Logistics"))

    if p["disposal"] != "none":
        lines.append(bom_line(
            "Legacy device collection", n, "device",
            R.LEGACY_COLLECTION_PER_DEVICE, rolls_into="Legacy collection",
            phase="one-off", category="Logistics"))
        if p["disposal"] == "buyback":
            for t, q in ordered:
                lines.append(bom_line(
                    f"{R.DEVICE_LABEL[t]} — buyback credit", q, "device",
                    -R.DEVICE_UNIT_COST[t] * R.BUYBACK_PCT[t] / refresh,
                    rolls_into="Buyback credit", phase="recurring",
                    category="Residual value",
                    note=f"{R.BUYBACK_PCT[t]:.0%} residual, annualised"))
    return lines


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight = _run(p)

    headline = [scope_item("Devices in scope", p["device_total"]),
                scope_item("Users supported", p["user_count"])]
    for t, q in p["devices"].items():
        if q:
            headline.append(scope_item(R.DEVICE_LABEL[t], q))

    per_device_pm = run["price_pa"] / 12 / p["device_total"]

    return build_result(
        manifest=MANIFEST,
        client_name=p["client_name"], rfp_ref=p["rfp_ref"],
        scope_headline=headline[:5],
        service=[
            kv("Break-fix commitment", R.SWAP_RESPONSE[p["swap_sla"]]),
            kv("Refresh cycle", f"{p['refresh_years']} years"),
            kv("Deployment method", p["deployment_method"].replace("_", " ").title()),
            kv("Image strategy", p["image_strategy"].replace("_", " ").title()),
            kv("Accessories", p["accessories"].title()),
            kv("End-of-life", p["disposal"].title()),
            kv("Rollout duration", f"{p['rollout_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per device per month", "value": round(per_device_pm, 2)},
            {"label": "Per device per year", "value": round(per_device_pm * 12, 2)},
        ],
        scope_detail={"devices": p["devices"], "country_mix": p["country_mix"]},
        bom=_bom(p),
    )
