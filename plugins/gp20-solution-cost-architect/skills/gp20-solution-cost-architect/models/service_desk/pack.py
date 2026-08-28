"""
Model pack — Service Desk tower (first line).

One lot of a lotted tender: the desk that answers. Multi-channel first contact,
across a defined language set and coverage window. Second and third line are a
separate lot — see `remote-support`.

The defining behaviour is a coverage floor driven by **language**. Contact
volume sets how many agents the work needs; every supported language needs at
least one staffed seat across the window regardless. Where the second exceeds
the first, the language commitment is setting the price, not demand.

What leaves this lot matters as much as what stays. Contacts the desk cannot
resolve become escalations into `remote-support`, and the FCR target this lot is
priced to is what sets that volume. Raising FCR makes this lot more expensive
and the next one cheaper — a trade invisible if the lots are priced by different
people, which in a lotted tender they usually are.

Note on overlap: managed-lan and daas each include a simplified service-desk
line. Where a tender wants a full desk *alongside* one of those, run this pack
and set `service_desk: false` on the other, or the desk is priced twice.

ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.contract import (COMMON_SETTINGS, Gap, GapOption, Manifest,
                           ValidationError, assumption, bom_line, build_result,
                           cost_line, deployment_block, kv, resource, run_block,
                           scope_item)
from core import estate as EST

from . import rates as R

# ---------------------------------------------------------------------------

MANIFEST = Manifest(
    key="service-desk",
    name="Service Desk (first line)",
    kind="tower",
    summary="Multi-channel first-contact support across a defined language set "
            "and coverage window. Second and third line are a separate lot.",
    detect=[
        "service desk", "helpdesk", "help desk", "first line", "1st line",
        "single point of contact", "spoc", "contact centre", "call centre",
        "ticket volume", "first contact resolution", "fcr", "user support",
        "service management", "itsm",
    ],
    material=["coverage", "languages", "fcr_target", "margin_pct", "term_years"],
    settings=[*COMMON_SETTINGS, "delivery_country"],
    notes="Two forces size this lot and they pull apart: contact volume, and "
          "the minimum presence each language needs to hold the coverage "
          "window. A tender asking for six languages 24×7 is buying language "
          "capability, not support capacity. Escalations out of this lot are "
          "priced in remote-support and are set by the FCR target here.",
    gaps=[
        Gap(
            param="coverage",
            question="What coverage window should the desk be staffed for?",
            rfp_hint="Check whether the window applies to every language or only "
                     "to the primary one — tenders often leave that implicit.",
            options=[
                GapOption("8x5", "8×5 business hours",
                          "1.15 FTE per seat. Cheapest, and adequate where the "
                          "population is single-timezone office-based."),
                GapOption("12x5", "12×5 extended day",
                          "1.70 FTE per seat. Covers early and late shifts "
                          "without weekend staffing."),
                GapOption("24x7", "24×7",
                          "4.80 FTE per seat — per language. This is where a "
                          "multilingual requirement becomes expensive."),
                GapOption("24x7x365", "24×7 including public holidays",
                          "5.20 FTE per seat plus holiday premia. Only justified "
                          "where the population genuinely works continuously."),
            ],
        ),
        Gap(
            param="languages",
            question="Which languages must be answered natively?",
            rfp_hint="A list of countries is not a list of languages. Ask whether "
                     "English is acceptable for some populations.",
            options=[
                GapOption("EN", "English only",
                          "One seat per shift. Every additional language "
                          "multiplies the coverage floor, not the workload."),
                GapOption("EN,DE,FR", "English, German, French",
                          "Three staffed seats per shift. At 24×7 that is "
                          "roughly 14 FTE before contact volume is considered."),
                GapOption("EN,DE,FR,NL,PL", "Five European languages",
                          "Five staffed seats per shift. Usually the single "
                          "largest driver in a multilingual tender."),
            ],
        ),
        Gap(
            param="self_service",
            question="What deflection capability should be priced?",
            rfp_hint="Tenders often ask for 'self-service' without saying whether "
                     "they expect a knowledge base or a conversational assistant.",
            options=[
                GapOption("none", "No self-service",
                          "Every contact reaches an agent."),
                GapOption("knowledge_base", "Knowledge base and portal",
                          "Deflects roughly 12% of contacts for an £18k annual "
                          "platform cost — usually pays for itself quickly."),
                GapOption("ai_assistant", "AI assistant",
                          "Deflects roughly 31% at £46k a year. Worth it above "
                          "about 60,000 contacts a year; below that the platform "
                          "costs more than the agents it saves."),
            ],
        ),
        Gap(
            param="fcr_target",
            question="What first-contact resolution target should be priced?",
            rfp_hint="A stated FCR percentage changes the skill mix, not just "
                     "the reporting.",
            options=[
                GapOption("0.65", "65% — standard",
                          "No uplift. Typical for a general first line."),
                GapOption("0.75", "75% — enhanced",
                          "9% uplift on first-line effort: longer handling times "
                          "and a more experienced agent profile."),
                GapOption("0.85", "85% — high",
                          "22% uplift. Requires near-second-line capability at "
                          "first contact; rarely achievable on a broad estate."),
            ],
        ),
    ],
)


# ---------------------------------------------------------------------------

def _normalise(params: dict) -> tuple[dict, list[dict]]:
    # The desk counts the same estate every other lot counts. Normalising it
    # here rather than locally is what lets a bid-level check prove the lots
    # priced the same deal.
    estate, reg = EST.normalise(params)
    src = params.get("_sources", {})
    p: dict[str, Any] = {"estate": estate}

    def take(key, default, note=""):
        if params.get(key) is not None:
            reg.append(assumption(key, params[key], src.get(key, "user"), note))
            return params[key]
        reg.append(assumption(key, default, "default", note))
        return default

    p["client_name"] = estate["client_name"]
    p["rfp_ref"] = estate["rfp_ref"]
    p["term_years"] = int(take("term_years", R.DEFAULT_TERM_YEARS))
    p["onboarding_months"] = int(take("onboarding_months", R.DEFAULT_ONBOARDING_MONTHS))
    if p["term_years"] < 1:
        raise ValidationError("term_years must be at least 1")

    p["user_count"] = estate["user_count"]
    if p["user_count"] <= 0:
        raise ValidationError(
            "user_count must be a positive number of supported users.")
    # Devices generate contacts beyond the user count. `device_count` is
    # accepted for a desk priced on its own; the shared estate wins when both
    # are present, because the other lots are counting that one.
    p["device_count"] = estate["device_total"] or int(
        take("device_count", 0,
             "Devices generate contacts beyond the user count."))

    langs = params.get("languages") or ["EN"]
    if isinstance(langs, str):
        langs = [x.strip().upper() for x in langs.split(",") if x.strip()]
    langs = [x.upper() for x in langs]
    unknown = set(langs) - set(R.LANGUAGES_SUPPORTED)
    if unknown:
        raise ValidationError(
            f"Unsupported language(s) {sorted(unknown)}. "
            f"Rate card covers: {R.LANGUAGES_SUPPORTED}")
    if not langs:
        raise ValidationError("At least one supported language is required.")
    p["languages"] = langs
    reg.append(assumption("languages", ",".join(langs), src.get("languages", "user")))

    p["coverage"] = take("coverage", "8x5", "Multiplies with every language.")
    if p["coverage"] not in R.PRESENCE_FTE_PER_SEAT:
        raise ValidationError(f"coverage must be one of {list(R.PRESENCE_FTE_PER_SEAT)}")

    p["self_service"] = take("self_service", "knowledge_base")
    if p["self_service"] not in R.DEFLECTION:
        raise ValidationError(f"self_service must be one of {list(R.DEFLECTION)}")

    p["fcr_target"] = float(take("fcr_target", 0.65))
    if p["fcr_target"] not in R.FCR_ALLOWED:
        raise ValidationError(f"fcr_target must be one of {list(R.FCR_ALLOWED)}")

    mix = params.get("channel_mix") or R.DEFAULT_CHANNEL_MIX
    unknown = set(mix) - set(R.CHANNELS)
    if unknown:
        raise ValidationError(f"Unknown channel(s) {sorted(unknown)}. "
                              f"Supported: {R.CHANNELS}")
    total = sum(mix.values())
    if total <= 0:
        raise ValidationError("channel_mix shares must be positive.")
    if abs(total - 1.0) > 0.01:
        mix = {k: v / total for k, v in mix.items()}
        reg.append(assumption("channel_mix", mix, "derived", "Shares normalised."))
    else:
        reg.append(assumption("channel_mix", mix,
                              src.get("channel_mix", "user")
                              if params.get("channel_mix") else "default"))
    p["channel_mix"] = mix

    p["delivery_country"] = take("delivery_country", R.HUB_PRIMARY,
                                 "Where non-native-language seats are staffed.")
    if p["delivery_country"] not in R.SUPPORTED_COUNTRIES:
        raise ValidationError(
            f"delivery_country must be one of {R.SUPPORTED_COUNTRIES}")

    p["margin_pct"] = float(take("margin_pct", R.DEFAULT_MARGIN_PCT))
    p["contingency_pct"] = float(take("contingency_pct", R.DEFAULT_CONTINGENCY_PCT))
    p["indexation_pct"] = float(take("indexation_pct", R.DEFAULT_INDEXATION_PCT))
    if not 0 <= p["margin_pct"] < 0.95:
        raise ValidationError("margin_pct must be between 0 and 0.95")

    return p, reg


def _seat_country(lang: str, p: dict) -> tuple[str, float]:
    """Where a language is staffed, and any premium for delivering it away from
    its home country."""
    home = R.LANGUAGE_HOME.get(lang, R.HUB_PRIMARY)
    if home == p["delivery_country"]:
        return home, 1.0
    # Nearshore delivery is cheaper even with the language premium; take it
    # where the rate card says so.
    near = p["delivery_country"]
    if R.COUNTRY_RATES[near]["l1"] * (1 + R.NEARSHORE_LANGUAGE_PREMIUM) \
            < R.COUNTRY_RATES[home]["l1"]:
        return near, 1 + R.NEARSHORE_LANGUAGE_PREMIUM
    return home, 1.0


def _demand(p: dict) -> tuple[float, float]:
    """Contacts a year, and the first-line agent-hours they consume."""
    contacts = (p["user_count"] * R.CONTACTS_PER_USER_PA
                + p["device_count"] * R.CONTACTS_PER_DEVICE_PA)
    contacts *= (1 - R.DEFLECTION[p["self_service"]])
    aht = sum(R.CHANNEL_AHT_MINUTES[c] * s for c, s in p["channel_mix"].items())
    aht *= R.FCR_TARGET_UPLIFT[p["fcr_target"]]
    hours = contacts * aht / 60 / R.OCCUPANCY
    return contacts, hours


def _deployment(p: dict) -> dict:
    n_lang = len(p["languages"])
    _, l1_hours = _demand(p)
    agents_est = max(1.0, l1_hours / R.PRODUCTIVE_HOURS_PA)

    knowledge = R.KNOWLEDGE_CAPTURE_DAYS
    runbooks = n_lang * R.RUNBOOK_DAYS_PER_LANGUAGE
    training = agents_est * R.TRAINING_DAYS_PER_AGENT
    parallel = R.PARALLEL_RUN_WEEKS[p["self_service"]] * 5 * min(agents_est, 6)
    pm = (knowledge + runbooks + training + parallel) * R.PM_OVERHEAD_PCT

    rates = R.COUNTRY_RATES[p["delivery_country"]]
    labour = ((knowledge + runbooks) * rates["l2"]
              + (training + parallel) * rates["l1"]
              + pm * rates["sdm"])
    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency

    return deployment_block(
        days_by_role={"knowledge_capture": knowledge, "runbook_build": runbooks,
                      "agent_training": training, "parallel_run": parallel,
                      "project_management": pm,
                      "total": knowledge + runbooks + training + parallel + pm},
        cost_lines=[cost_line("Labour", labour),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost=cost, price=cost / (1 - p["margin_pct"]),
        duration_months=p["onboarding_months"])


def _run(p: dict) -> tuple[dict, str, dict]:
    contacts, l1_hours = _demand(p)
    demand_fte = l1_hours / R.PRODUCTIVE_HOURS_PA
    per_seat = R.PRESENCE_FTE_PER_SEAT[p["coverage"]]

    # Demand is shared across languages in proportion to the population each
    # serves; the floor is one staffed seat per language regardless.
    share = 1.0 / len(p["languages"])
    by_lang: dict[str, dict] = {}
    for lang in p["languages"]:
        country, premium = _seat_country(lang, p)
        demand = demand_fte * share
        floor = per_seat
        by_lang[lang] = {
            "fte": max(demand, floor), "demand": demand, "floor": floor,
            "country": country, "premium": premium,
            "driver": "language coverage floor" if floor > demand else "contact volume",
        }
    l1_fte = sum(v["fte"] for v in by_lang.values())

    # What this lot cannot close leaves it. The volume is the remote-support
    # lot's entire intake, so it is reported rather than absorbed.
    escalations = contacts * (1 - p["fcr_target"])

    resources: list[dict] = []
    labour = 0.0
    for lang, v in sorted(by_lang.items(), key=lambda kv_: -kv_[1]["fte"]):
        resources.append(resource(v["country"], f"First Line — {lang}",
                                  v["fte"], v["driver"]))
        labour += (v["fte"] * R.COUNTRY_RATES[v["country"]]["l1"]
                   * v["premium"] * R.WORKING_DAYS_PA)

    hub = p["delivery_country"]
    agents = l1_fte
    leads = math.ceil(agents / R.AGENTS_PER_TEAM_LEAD) if agents else 0
    if leads:
        resources.append(resource(hub, "Team Lead", leads, "span of control"))
        labour += leads * R.COUNTRY_RATES[hub]["lead"] * R.WORKING_DAYS_PA

    sdm = next(f for cap, f in R.SDM_BANDS if labour < cap)
    resources.append(resource(hub, "Service Delivery Manager", sdm, "contract band"))
    labour += sdm * R.COUNTRY_RATES[hub]["sdm"] * R.WORKING_DAYS_PA

    itsm = agents * R.ITSM_PER_AGENT_PA
    telephony = agents * R.TELEPHONY_PER_AGENT_PA
    platform = 0.0
    if p["self_service"] == "knowledge_base":
        platform = R.KNOWLEDGE_PLATFORM_PA
    elif p["self_service"] == "ai_assistant":
        platform = R.AI_ASSISTANT_PA + R.KNOWLEDGE_PLATFORM_PA

    overhead = labour * R.OVERHEAD_PCT
    subtotal = labour + itsm + telephony + platform + overhead
    contingency = subtotal * p["contingency_pct"]
    cost = subtotal + contingency
    price = cost / (1 - p["margin_pct"])

    floor_langs = [l for l, v in by_lang.items() if v["driver"] == "language coverage floor"]
    surplus = sum(v["fte"] - v["demand"] for v in by_lang.values()
                  if v["driver"] == "language coverage floor")

    insight = ""
    if floor_langs:
        insight = (
            f"{', '.join(floor_langs)} are sized by the language coverage floor, "
            f"not contact volume — {surplus:.1f} FTE of standing language "
            f"capability exceeds the {contacts:,.0f} contacts a year the desk "
            f"actually handles. At {R.COVERAGE_LABEL[p['coverage']]} each language "
            f"costs {per_seat:.2f} FTE whether or not anyone calls in it. "
            f"Consolidating the low-volume languages to English with a translation "
            f"layer, or narrowing their coverage window, would cut cost without "
            f"reducing the service the majority receives.")
    elif p["self_service"] == "ai_assistant" and contacts < 60_000:
        insight = (
            f"At {contacts:,.0f} contacts a year the AI assistant costs more "
            f"than the agent time it deflects. It becomes economic above roughly "
            f"60,000 contacts — worth revisiting if the estate grows.")
    else:
        insight = (
            f"Sized by contact volume rather than the language floor. The "
            f"{p['fcr_target']:.0%} first-contact resolution target is then the "
            f"lever that matters most, and it points outward: it sends "
            f"{escalations:,.0f} contacts a year into the remote-support lot. "
            f"Every point of FCR bought here removes roughly "
            f"{contacts / 100:,.0f} escalations from that lot.")

    block = run_block(
        resources=resources,
        cost_lines=[cost_line("Labour", labour),
                    cost_line("ITSM tooling", itsm),
                    cost_line("Telephony", telephony),
                    cost_line("Self-service platform", platform),
                    cost_line("Delivery overhead", overhead),
                    cost_line("Contingency", contingency)],
        cost_pa=cost, price_pa=price,
        drivers={"contacts_pa": round(contacts, 0),
                 # The remote-support lot's entire intake. Published here so the
                 # two lots can be reconciled rather than independently guessed.
                 "escalations_pa": round(escalations, 0),
                 "fcr_target": p["fcr_target"],
                 "floor_driven_languages": floor_langs,
                 "surplus_fte": round(surplus, 2),
                 "deflection_pct": R.DEFLECTION[p["self_service"]]})
    return block, insight, {"contacts": contacts, "agents": agents,
                            "escalations": escalations}


def _bom(p: dict, agents: float) -> list[dict]:
    """A service desk buys very little that you can touch.

    The bill of materials is per-seat tooling and platform licences, and it is
    deliberately short — which is itself the finding. If a desk looks expensive
    the answer is never in this table; it is in the labour the language
    coverage floor drives.
    """
    lines = [
        bom_line("ITSM platform licence", agents, "agent seat per annum",
                 R.ITSM_PER_AGENT_PA, rolls_into="ITSM tooling",
                 phase="recurring", category="Software"),
        bom_line("Contact-centre telephony", agents, "agent seat per annum",
                 R.TELEPHONY_PER_AGENT_PA, rolls_into="Telephony",
                 phase="recurring", category="Software"),
    ]
    if p["self_service"] == "knowledge_base":
        lines.append(bom_line("Knowledge management platform", 1,
                              "tenant per annum", R.KNOWLEDGE_PLATFORM_PA,
                              rolls_into="Self-service platform",
                              phase="recurring", category="Software"))
    elif p["self_service"] == "ai_assistant":
        lines += [
            bom_line("Knowledge management platform", 1, "tenant per annum",
                     R.KNOWLEDGE_PLATFORM_PA, rolls_into="Self-service platform",
                     phase="recurring", category="Software"),
            bom_line("AI assistant and deflection", 1, "tenant per annum",
                     R.AI_ASSISTANT_PA, rolls_into="Self-service platform",
                     phase="recurring", category="Software",
                     note=f"{R.DEFLECTION[p['self_service']]:.0%} assumed deflection"),
        ]
    return lines


def estimate(params: dict) -> dict:
    p, reg = _normalise(params)
    dep = _deployment(p)
    run, insight, d = _run(p)

    per_user_pm = run["price_pa"] / 12 / p["user_count"]
    per_contact = run["price_pa"] / d["contacts"] if d["contacts"] else 0.0

    return build_result(
        manifest=MANIFEST,
        client_name=p["client_name"], rfp_ref=p["rfp_ref"],
        scope_headline=[
            scope_item("Users supported", p["user_count"]),
            scope_item("Contacts per annum", round(d["contacts"])),
            scope_item("Languages", len(p["languages"])),
            scope_item("Agents", d["agents"], "float1"),
            scope_item("Escalations out per annum", round(d["escalations"])),
        ],
        service=[
            kv("Coverage window", R.COVERAGE_LABEL[p["coverage"]]),
            kv("Languages", ", ".join(p["languages"])),
            kv("Scope", "First line only — escalations pass to remote support"),
            kv("Self-service", p["self_service"].replace("_", " ").title()),
            kv("First-contact resolution", f"{p['fcr_target']:.0%}"),
            kv("Onboarding", f"{p['onboarding_months']} months"),
        ],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=reg, insight=insight,
        unit_metrics=[
            {"label": "Per user per month", "value": round(per_user_pm, 2)},
            {"label": "Per contact", "value": round(per_contact, 2)},
        ],
        scope_detail={**EST.scope_detail(p["estate"]),
                      "languages": p["languages"],
                      "channel_mix": p["channel_mix"]},
        bom=_bom(p, d["agents"]),
    )
