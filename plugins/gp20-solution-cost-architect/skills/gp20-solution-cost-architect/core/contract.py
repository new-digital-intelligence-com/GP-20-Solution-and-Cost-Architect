"""
The model-pack contract.

Every offering — managed LAN, DaaS, service desk, IaaS — is a *pack*. A pack
owns its parameters, its rate card and its arithmetic, and nothing else. The
skill owns reading, extraction, clarification, artefacts and governance, and is
identical for every offering.

This module defines the boundary between the two. It is deliberately small: the
narrower this contract, the cheaper each new pack is.

--------------------------------------------------------------------------------
A pack module must expose:

    MANIFEST : Manifest
    estimate(params: dict) -> dict          # returns a result dict

That is all. `estimate` builds its result with the helpers below so every pack
produces the same shape, which is what lets one set of artefact writers serve
all of them.
--------------------------------------------------------------------------------
"""

from __future__ import annotations

# --- Windows console safety -------------------------------------------------
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        if _s and getattr(_s, "encoding", "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Any, Callable

DISCLAIMER = "ILLUSTRATIVE MODEL — synthetic rates, not NSC pricing."


class ValidationError(ValueError):
    """Inputs cannot produce a meaningful estimate. Packs raise this."""


class ContractError(AssertionError):
    """A pack returned something the writers cannot consume."""


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

@dataclass
class GapOption:
    """One answer to a clarification question."""
    value: str
    label: str
    consequence: str            # the commercial effect, not a restatement of the label


@dataclass
class Gap:
    """A price-material parameter the RFP often fails to state.

    The skill turns these into AskUserQuestion calls. `rfp_hint` tells the user
    what the document does say, so the question reads as informed rather than
    mechanical.
    """
    param: str
    question: str
    options: list[GapOption]
    rfp_hint: str = ""


# Commercial parameters that outlive a single deal. Every pack takes these, so
# they are the default; a pack adds to the list only if it consumes something
# else that a team would set once and reuse.
COMMON_SETTINGS = ("margin_pct", "contingency_pct", "indexation_pct", "term_years")


# A pack is either a *tower* — one lot of a lotted tender, priced on its own —
# or an *offering*, a whole outcome that internally consumes several towers.
# Real tenders arrive both ways, sometimes in the same document, so both kinds
# coexist. The kind decides how the skill composes them, not how they compute.
PACK_KINDS = ("tower", "offering")


@dataclass
class Manifest:
    key: str                    # stable id, e.g. "managed-lan"
    name: str                   # human name
    summary: str                # one line, shown when choosing a pack
    detect: list[str]           # phrases in an RFP that point at this offering
    kind: str = "offering"      # tower | offering
    gaps: list[Gap] = field(default_factory=list)
    material: list[str] = field(default_factory=list)   # defaults worth flagging
    settings: list[str] = field(
        default_factory=lambda: list(COMMON_SETTINGS))  # saved between runs
    currency: str = "GBP"
    symbol: str = "£"
    notes: str = ""


# ---------------------------------------------------------------------------
# Result builders — every pack uses these
# ---------------------------------------------------------------------------

def scope_item(label: str, value: Any, fmt: str = "int") -> dict:
    """A headline figure describing the shape of the solution.

    fmt: int | float1 | float2 | money | text
    """
    return {"label": label, "value": value, "format": fmt}


def kv(label: str, value: Any) -> dict:
    """A service-commitment line: label plus already-formatted value."""
    return {"label": label, "value": value}


def cost_line(label: str, amount: float) -> dict:
    return {"label": label, "amount": round(float(amount), 2)}


BOM_PHASES = ("one-off", "recurring")


def bom_line(item: str, qty: float, unit: str, unit_cost: float,
             *, rolls_into: str = "", phase: str = "one-off",
             category: str = "", note: str = "") -> dict:
    """One line of the bill of materials. Carries COST, never price.

    Finance reads the BoM to see what is being bought before any commercial
    adjustment, so margin has no place here. It is applied once, at the cost
    block, and shown separately.

    `rolls_into` names the cost line this item belongs to. When set, `verify()`
    checks that every BoM line carrying that label sums to the cost line
    itself. That is what stops the BoM becoming a decorative sidecar that
    quietly drifts from the model it claims to describe — the same class of
    defect as a workbook that no longer agrees with the Python.

    Leave `rolls_into` empty for a purely informational line. A tagged group
    must cover its cost line in full, or the check fails — which is the point.
    """
    if phase not in BOM_PHASES:
        raise ContractError(f"bom phase must be one of {BOM_PHASES}, got {phase!r}")
    # qty and unit_cost are stored at full precision, for the same reason
    # `resource()` stores FTE unrounded: a quantity like 34.80004975845411
    # agent-seats rounds to 34.8, and 34.8 x the licence rate no longer equals
    # the cost line it has to reconcile against. The writers round for display.
    return {
        "item": item,
        "qty": float(qty),
        "unit": unit,
        "unit_cost": float(unit_cost),
        "extended_cost": round(float(qty) * float(unit_cost), 2),
        "rolls_into": rolls_into,
        "phase": phase,
        "category": category,
        "note": note,
    }


def resource(location: str, role: str, fte: float, driver: str = "") -> dict:
    """One line of the resource model. `driver` explains what set the number —
    the difference between a headcount and an architectural observation.

    `fte` is stored at full precision deliberately. Rounding here and then
    summing rounds N times instead of once, which drifts the total by up to
    0.005 × N — visible against a small headcount and enough to fail parity
    against the workbook.  The writers round for display.
    """
    return {"location": location, "role": role,
            "fte": float(fte), "driver": driver}


def assumption(parameter: str, value: Any, source: str, note: str = "") -> dict:
    """source: rfp | user | derived | default"""
    if source not in ("rfp", "user", "derived", "default"):
        raise ContractError(f"bad provenance tag {source!r} on {parameter}")
    return {"parameter": parameter, "value": value, "source": source, "note": note}


def build_result(
    *,
    manifest: Manifest,
    client_name: str,
    rfp_ref: str,
    scope_headline: list[dict],
    service: list[dict],
    deployment: dict,
    run: dict,
    term_years: int,
    indexation_pct: float,
    assumptions: list[dict],
    insight: str = "",
    unit_metrics: list[dict] | None = None,
    scope_detail: dict | None = None,
    bom: list[dict] | None = None,
) -> dict:
    """Assemble the common result. Handles the term schedule and TCV so no pack
    reimplements indexation."""
    profile = run.get("year_profile") or [1.0] * term_years
    if len(profile) < term_years:                 # hold the last year flat
        profile = list(profile) + [profile[-1]] * (term_years - len(profile))

    yearly, tcv = [], deployment["price"]
    tcc = deployment["cost"]                      # the same schedule, pre-margin
    for yr in range(1, term_years + 1):
        factor = profile[yr - 1] * ((1 + indexation_pct) ** (yr - 1))
        amount = run["price_pa"] * factor
        yearly.append({"year": yr, "price": round(amount, 2),
                       "cost": round(run["cost_pa"] * factor, 2)})
        tcv += amount
        tcc += run["cost_pa"] * factor

    flags = [a for a in assumptions
             if a["source"] == "default" and a["parameter"] in manifest.material]

    return {
        "meta": {
            "offering": manifest.key,
            "offering_name": manifest.name,
            "kind": manifest.kind,
            "client_name": client_name,
            "rfp_ref": rfp_ref,
            "currency": manifest.currency,
            "symbol": manifest.symbol,
            "disclaimer": DISCLAIMER,
        },
        "scope": {"headline": scope_headline, "detail": scope_detail or {}},
        "service": service,
        "deployment": deployment,
        "run": {**run, "insight": insight},
        "bom": bom or [],
        "summary": {
            "term_years": term_years,
            "indexation_pct": indexation_pct,
            "year_profile": [round(float(x), 6) for x in profile],
            "one_off_price": deployment["price"],
            "annual_price_year1": run["price_pa"],
            "monthly_price_year1": run["price_pm"],
            "yearly": yearly,
            "tcv": round(tcv, 2),
            "unit_metrics": unit_metrics or [],
            # Cost before pricing adjustment — what finance signs off on, and
            # what the margin is actually being taken on. Same schedule, same
            # indexation, margin removed.
            "one_off_cost": deployment["cost"],
            "annual_cost_year1": run["cost_pa"],
            "total_cost": round(tcc, 2),
            "margin_value": round(tcv - tcc, 2),
            "margin_pct_effective": round((tcv - tcc) / tcv, 4) if tcv else 0.0,
        },
        "assumptions": assumptions,
        "review_flags": flags,
    }


def deployment_block(*, days_by_role: dict, cost_lines: list[dict],
                     price: float, cost: float, duration_months: int) -> dict:
    return {
        "days_by_role": {k: round(float(v), 1) for k, v in days_by_role.items()},
        "cost_lines": cost_lines,
        "cost": round(float(cost), 2),
        "price": round(float(price), 2),
        "duration_months": duration_months,
    }


def run_block(*, resources: list[dict], cost_lines: list[dict],
              cost_pa: float, price_pa: float, drivers: dict | None = None,
              year_profile: list[float] | None = None) -> dict:
    """`price_pa` is always the YEAR ONE price.

    `year_profile` lets an offering whose consumption changes over the term say
    so: multipliers relative to year one, before indexation. A migration ramp is
    [1.0, 1.6, 1.8, 1.8]; a flat managed service omits it entirely. Without this
    an offering that ramps has to lie about either year one or the TCV.
    """
    total_fte = round(sum(r["fte"] for r in resources), 2)
    block = {
        "resources": resources,
        "total_fte": total_fte,
        "cost_lines": cost_lines,
        "cost_pa": round(float(cost_pa), 2),
        "price_pa": round(float(price_pa), 2),
        "price_pm": round(float(price_pa) / 12, 2),
        "drivers": drivers or {},
    }
    if year_profile:
        block["year_profile"] = [round(float(x), 4) for x in year_profile]
    return block


# ---------------------------------------------------------------------------
# Conformance — the gate every pack must pass
# ---------------------------------------------------------------------------

REQUIRED_TOP = ("meta", "scope", "service", "deployment", "run",
                "summary", "assumptions", "review_flags", "bom")
VALID_FORMATS = ("int", "float1", "float2", "money", "text")
BOM_KEYS = {"item", "qty", "unit", "unit_cost", "extended_cost",
            "rolls_into", "phase", "category", "note"}


def _check_bom(result: dict) -> list[str]:
    """The BoM must be arithmetically honest and must agree with the cost model.

    Two separate failures are possible and both have bitten this project before
    in other guises: a line whose extension does not equal qty x unit cost, and
    a set of lines that no longer sums to the cost line they claim to explain.
    """
    p: list[str] = []
    bom = result.get("bom") or []
    if not bom:
        return p                       # a BoM is optional; a wrong one is not

    for i, b in enumerate(bom):
        missing = BOM_KEYS - set(b)
        if missing:
            p.append(f"bom[{i}] missing {sorted(missing)}")
            continue
        if b["phase"] not in BOM_PHASES:
            p.append(f"bom[{i}].phase {b['phase']!r} is not a valid phase")
        expected = round(float(b["qty"]) * float(b["unit_cost"]), 2)
        if abs(expected - float(b["extended_cost"])) > 0.05:
            p.append(f"bom[{i}] {b['item']!r}: extended_cost {b['extended_cost']} "
                     f"!= qty x unit_cost {expected}")
        if float(b["qty"]) < 0 and float(b["unit_cost"]) < 0:
            p.append(f"bom[{i}] {b['item']!r}: negative qty and negative unit "
                     f"cost multiply to a positive — state the credit once")

    lines = {"one-off": {c["label"]: c["amount"]
                         for c in result["deployment"].get("cost_lines", [])},
             "recurring": {c["label"]: c["amount"]
                           for c in result["run"].get("cost_lines", [])}}

    grouped: dict[tuple, float] = {}
    for b in bom:
        if not b.get("rolls_into"):
            continue                   # informational line, nothing to reconcile
        grouped.setdefault((b["phase"], b["rolls_into"]), 0.0)
        grouped[(b["phase"], b["rolls_into"])] += float(b["extended_cost"])

    for (phase, label), total in grouped.items():
        if label not in lines[phase]:
            p.append(f"bom rolls_into {label!r} ({phase}) matches no cost line")
            continue
        amount = lines[phase][label]
        if abs(total - amount) > max(1.0, abs(amount) * 0.001):
            p.append(f"bom lines for {label!r} ({phase}) sum to {total:,.2f} "
                     f"but the cost line is {amount:,.2f}")
    return p


def verify(result: dict, manifest: Manifest) -> list[str]:
    """Return a list of contract violations. Empty means the pack conforms.

    Run against every pack in CI. A pack that passes this can be consumed by
    every artefact writer without the writers knowing what offering it is.
    """
    p: list[str] = []

    for key in REQUIRED_TOP:
        if key not in result:
            p.append(f"missing top-level key: {key}")
    if p:
        return p

    if manifest.kind not in PACK_KINDS:
        p.append(f"manifest.kind {manifest.kind!r} must be one of {PACK_KINDS}")

    m = result["meta"]
    for key in ("offering", "client_name", "rfp_ref", "currency", "symbol", "disclaimer"):
        if not m.get(key) and m.get(key) != 0:
            p.append(f"meta.{key} is empty")
    if m.get("offering") != manifest.key:
        p.append(f"meta.offering {m.get('offering')!r} != manifest key {manifest.key!r}")
    if m.get("disclaimer") != DISCLAIMER:
        p.append("meta.disclaimer must be the standard illustrative-model text")

    head = result["scope"].get("headline")
    if not head:
        p.append("scope.headline is empty — writers have nothing to lead with")
    else:
        for i, item in enumerate(head):
            if set(item) != {"label", "value", "format"}:
                p.append(f"scope.headline[{i}] must have exactly label/value/format")
            elif item["format"] not in VALID_FORMATS:
                p.append(f"scope.headline[{i}].format {item['format']!r} not recognised")

    for i, item in enumerate(result["service"]):
        if set(item) != {"label", "value"}:
            p.append(f"service[{i}] must have exactly label/value")

    dep = result["deployment"]
    for key in ("days_by_role", "cost_lines", "cost", "price", "duration_months"):
        if key not in dep:
            p.append(f"deployment.{key} missing")
    run = result["run"]
    for key in ("resources", "total_fte", "cost_lines", "cost_pa",
                "price_pa", "price_pm"):
        if key not in run:
            p.append(f"run.{key} missing")
    for i, r in enumerate(run.get("resources", [])):
        if not {"location", "role", "fte"} <= set(r):
            p.append(f"run.resources[{i}] needs location/role/fte")

    s = result["summary"]
    for key in ("term_years", "one_off_price", "annual_price_year1",
                "monthly_price_year1", "yearly", "tcv", "unit_metrics",
                "one_off_cost", "annual_cost_year1", "total_cost",
                "margin_value", "margin_pct_effective"):
        if key not in s:
            p.append(f"summary.{key} missing")

    # Cost must sit below price everywhere, or margin has been applied twice,
    # or subtracted. Cheap to check, expensive to discover in a bid review.
    if s.get("total_cost") is not None and s.get("tcv") is not None:
        if s["total_cost"] > s["tcv"] + 0.01:
            p.append(f"summary.total_cost {s['total_cost']} exceeds tcv {s['tcv']}")
        expected_margin = round(s["tcv"] - s["total_cost"], 2)
        if abs(expected_margin - s.get("margin_value", 0)) > 1.0:
            p.append(f"summary.margin_value {s.get('margin_value')} "
                     f"!= tcv - total_cost {expected_margin}")

    prof = result["run"].get("year_profile")
    if prof is not None:
        if not prof or any(float(x) <= 0 for x in prof):
            p.append("run.year_profile must be non-empty and strictly positive")
        elif abs(float(prof[0]) - 1.0) > 1e-6:
            p.append("run.year_profile[0] must be 1.0 — price_pa is the year-one price")

    if s.get("yearly") and s.get("term_years"):
        if len(s["yearly"]) != s["term_years"]:
            p.append(f"summary.yearly has {len(s['yearly'])} entries "
                     f"for a {s['term_years']}-year term")
        expected = dep.get("price", 0) + sum(y["price"] for y in s["yearly"])
        if abs(expected - s.get("tcv", 0)) > 1.0:
            p.append(f"summary.tcv {s.get('tcv')} != one-off + sum(yearly) {expected:.2f}")

    if not result["assumptions"]:
        p.append("assumptions is empty — every result must carry provenance")
    for i, a in enumerate(result["assumptions"]):
        if not {"parameter", "value", "source"} <= set(a):
            p.append(f"assumptions[{i}] needs parameter/value/source")
        elif a["source"] not in ("rfp", "user", "derived", "default"):
            p.append(f"assumptions[{i}].source {a['source']!r} is not a valid tag")

    flagged = {f["parameter"] for f in result["review_flags"]}
    defaults = {a["parameter"] for a in result["assumptions"] if a["source"] == "default"}
    missed = (defaults & set(manifest.material)) - flagged
    if missed:
        p.append(f"price-material defaults not flagged for review: {sorted(missed)}")

    for gap in manifest.gaps:
        if not gap.options:
            p.append(f"gap {gap.param!r} declares no options")
        for o in gap.options:
            if not o.consequence:
                p.append(f"gap {gap.param!r} option {o.value!r} has no stated consequence")

    p.extend(_check_bom(result))

    return p
