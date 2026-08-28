"""
Model pack — Project Management tower.

One lot of a lotted tender: the programme. Transition into service, cross-lot
governance, and the service management office that runs the contract afterwards.

**What this lot does not include.** Every other tower already carries its own
Service Delivery Manager — the person who runs *that* service day to day. This
lot prices the layer above: the programme that transitions all the lots in, and
the office that governs them as one contract. Pricing the per-lot delivery
manager here as well is the easiest mistake to make once governance becomes a
lot of its own, and it is invisible in any single lot's numbers.

**Why the lot count matters more than the estate.** Governance scales with the
number of things being governed, not with how many sites they touch — and it
scales *sub-linearly*, because the second lot reuses the programme, the
governance model, the reporting pack and the client relationship built for the
first. A bid charging full programme effort per lot is both wrong and
uncompetitive. This pack says by how much.

ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing.
"""

from __future__ import annotations

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
    key="project-management",
    name="Programme and Service Governance",
    kind="tower",
    summary="Transition into service, cross-lot programme governance, and the "
            "service management office that runs the contract.",
    detect=[
        "project management", "programme management", "program management",
        "transition", "mobilisation", "mobilization", "pmo",
        "service management office", "smo", "governance", "service review",
        "contract management", "transformation", "onboarding programme",
    ],
    material=["lots", "complexity", "reporting", "margin_pct", "term_years"],
    settings=[*COMMON_SETTINGS, "delivery_country"],
    notes="Sized by the number of lots governed, not by the estate. Effort per "
          "lot decays as lots are added, because the programme, the governance "
          "model and the client relationship are built once. Excludes the "
          "per-lot delivery managers, which every other tower already carries.",
    gaps=[
        Gap(
            param="lots",
            question="How many delivery lots will this programme govern?",
            rfp_hint="Count the delivery lots being awarded, NOT including this "
                     "governance lot — a programme does not govern itself. "
                     "Governing two of five is a different job from all five.",
            options=[
                GapOption("1", "One lot",
                          "Base programme only. Roughly 119 transition days."),
                GapOption("3", "Three lots",
                          "About 1.9× the single-lot effort, not 3× — the "
                          "programme is built once."),
                GapOption("5", "Five lots — full tower stack",
                          "About 2.7× single-lot effort. The economy of scope "
                          "is the argument for bidding the whole stack."),
            ],
        ),
        Gap(
            param="complexity",
            question="What transition complexity should be priced?",
            rfp_hint="Look for an incumbent being displaced, staff transfer, or "
                     "a regulated environment — each changes this materially.",
            options=[
                GapOption("low", "Single-vendor, stable scope",
                          "×0.85. Greenfield or a straightforward renewal."),
                GapOption("standard", "Multi-vendor, defined scope",
                          "×1.00. The usual assumption."),
                GapOption("high", "Incumbent transition, TUPE or regulated",
                          "×1.35. Staff transfer and knowledge capture from an "
                          "unwilling incumbent is the most under-priced risk in "
                          "any transition."),
            ],
        ),
        Gap(
            param="reporting",
            question="What ongoing reporting and governance is required?",
            rfp_hint="Check the service management schedule rather than the "
                     "main body — reporting obligations hide there.",
            options=[
                GapOption("standard", "Monthly service review and SLA pack",
                          "×1.00 on the service management office."),
                GapOption("enhanced", "Weekly operational plus board reporting",
                          "×1.40, and adds a reporting platform."),
                GapOption("regulated", "Audited reporting with evidence retention",
                          "×1.85. Assume this wherever the client is regulated; "
                          "it is rarely stated as a cost driver."),
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
    p["transition_months"] = int(
        take("transition_months", R.DEFAULT_TRANSITION_MONTHS))

    # Delivery lots governed, excluding this one. A five-tower award has four
    # delivery lots plus this governance lot; `lots` is 4, not 5. bid.py checks
    # the figure against the lots actually present.
    p["lots"] = int(take("lots", 1,
                         "Delivery lots governed, excluding this lot itself."))
    if p["lots"] < 1:
        raise ValidationError("lots must be at least 1")
    if p["lots"] > 12:
        raise ValidationError(
            "lots above 12 is outside the model's calibration — split the "
            "programme rather than extrapolating it.")

    p["complexity"] = take("complexity", "standard")
    if p["complexity"] not in R.COMPLEXITY:
        raise ValidationError(f"complexity must be one of {list(R.COMPLEXITY)}")

    p["reporting"] = take("reporting", "standard")
    if p["reporting"] not in R.REPORTING_LEVEL:
        raise ValidationError(
            f"reporting must be one of {list(R.REPORTING_LEVEL)}")

    p["delivery_country"] = take("delivery_country", R.HUB_PRIMARY,
                                 "Governance is usually client-facing and local.")
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


def _transition_days(p: dict) -> tuple[float, float]:
    """Total transition days, and what a single lot would have cost."""
    e = p["estate"]
    scope_days = (R.DAYS_PER_COUNTRY * len(e["country_mix"])
                  + R.DAYS_PER_100_SITES * e["sites_total"] / 100
                  + R.DAYS_PER_1K_USERS * e["user_count"] / 1000)
    factor = R.COMPLEXITY[p["complexity"]]["factor"]

    lot_days = R.DAYS_PER_LOT * (p["lots"] ** R.LOT_SCALING_EXPONENT)
    total = (R.BASE_TRANSITION_DAYS + lot_days + scope_days) * factor
    single = (R.BASE_TRANSITION_DAYS + R.DAYS_PER_LOT + scope_days) * factor
    return total, single


def _deployment(p: dict) -> dict:
    days, _ = _transition_days(p)
    rates = R.COUNTRY_RATES[p["delivery_country"]]
    by_role = {role: days * share for role, share in R.ROLE_SHARE.items()}
    labour = sum(d * rates[role] for role, d in by_role.items())
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={**{k: round(v, 1) for k, v in by_role.items()},
                      "total": days},
        cost_lines=[cost_line("Transition labour", labour),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["transition_months"])


def _run(p: dict) -> tuple[dict, str, dict]:
    e = p["estate"]
    report = R.REPORTING_LEVEL[p["reporting"]]

    smo_fte = (R.SMO_BASE_FTE
               + R.SMO_FTE_PER_LOT * (p["lots"] ** R.SMO_LOT_SCALING_EXPONENT)
               + R.SMO_FTE_PER_COUNTRY * len(e["country_mix"]))
    smo_fte *= report["factor"]

    rates = R.COUNTRY_RATES[p["delivery_country"]]
    hub = p["delivery_country"]
    resources, labour = [], 0.0
    for role, share in R.SMO_ROLE_SHARE.items():
        fte = smo_fte * share
        resources.append(resource(hub, role.replace("_", " ").title(), fte,
                                  f"{p['lots']} lots, {len(e['country_mix'])} "
                                  f"countries"))
        labour += fte * rates[role] * R.WORKING_DAYS_PA

    ppm = R.PPM_TOOLING_PA
    platform = (R.REPORTING_PLATFORM_PA
                if p["reporting"] in ("enhanced", "regulated") else 0.0)
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + ppm + platform + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    lines = [cost_line("Labour", labour),
             cost_line("Programme tooling", ppm)]
    if platform:
        lines.append(cost_line("Reporting platform", platform))
    lines += [cost_line("Delivery overhead", overhead),
              cost_line("Contingency", contingency)]

    total_days, single_days = _transition_days(p)
    if p["lots"] > 1:
        separate = single_days * p["lots"]
        insight = (
            f"One programme governing {p['lots']} lots takes {total_days:,.0f} "
            f"transition days. {p['lots']} separately-run programmes over the "
            f"same estate would take about {separate:,.0f}, because each would "
            f"repeat the base mobilisation and its own discovery of "
            f"{e['sites_total']:,} sites across {len(e['country_mix'])} "
            f"countries — {total_days / separate:.0%} of the effort, for the "
            f"same governed scope. That is the commercial argument for awarding "
            f"the stack to one supplier rather than splitting it, and it is "
            f"worth putting in the response explicitly: a competitor bidding "
            f"two lots cannot offer it. Note the comparison is against separate "
            f"*programmes*, not against a single supplier discounting — state "
            f"it that way or it will be read as padding.")
    else:
        insight = (
            f"A single-lot programme carries the full {R.BASE_TRANSITION_DAYS:,.0f} "
            f"days of base transition with nothing to share it across. If the "
            f"client is likely to award further lots, this is the most "
            f"expensive way to buy governance — each subsequent lot added later "
            f"repeats setup that a combined award would have paid for once.")

    block = run_block(
        resources=resources,
        cost_lines=lines,
        cost_pa=cost, price_pa=cost / (1 - p["margin_pct"]),
        drivers={"lots_governed": p["lots"],
                 "transition_days": round(total_days, 1),
                 "days_as_separate_programmes": round(single_days * p["lots"], 1),
                 "smo_fte": round(smo_fte, 2)})
    return block, insight, {"smo_fte": smo_fte, "transition_days": total_days}


def _bom(p: dict) -> list[dict]:
    lines = [bom_line("Programme and portfolio management tooling", 1,
                      "programme per annum", R.PPM_TOOLING_PA,
                      rolls_into="Programme tooling", phase="recurring",
                      category="Software")]
    if p["reporting"] in ("enhanced", "regulated"):
        lines.append(bom_line(
            f"Reporting platform — {p['reporting']}", 1, "tenant per annum",
            R.REPORTING_PLATFORM_PA, rolls_into="Reporting platform",
            phase="recurring", category="Software",
            note=R.REPORTING_LEVEL[p["reporting"]]["label"]))
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
            scope_item("Lots governed", p["lots"]),
            scope_item("Countries", len(e["country_mix"])),
            scope_item("Transition effort (days)",
                       round(d["transition_days"], 1), "float1"),
            scope_item("Service management office (FTE)",
                       round(d["smo_fte"], 1), "float1"),
        ],
        service=[
            kv("Transition complexity", R.COMPLEXITY[p["complexity"]]["label"]),
            kv("Reporting", R.REPORTING_LEVEL[p["reporting"]]["label"]),
            kv("Transition duration", f"{p['transition_months']} months"),
            kv("Excludes", "Per-lot delivery managers — each tower carries its own"),
            kv("Lots governed", f"{p['lots']} delivery lots, excluding this one"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per lot governed per annum",
             "value": round(run["price_pa"] / p["lots"], 2)},
        ],
        scope_detail=EST.scope_detail(e),
        bom=_bom(p),
    )
