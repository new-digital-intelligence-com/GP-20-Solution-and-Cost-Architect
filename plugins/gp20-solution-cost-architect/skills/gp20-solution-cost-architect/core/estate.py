"""
The shared estate.

A lotted tender asks several towers to service one estate. Field service,
logistics and remote support are priced separately, but they are all counting
the same sites, the same devices, the same people. Before this module each pack
normalised its own scope, which was harmless while one pack saw the whole deal
and is not harmless now: if the field-service lot prices 101 sites and the
logistics lot prices 98, nobody notices until the client adds the lots up.

So the estate is described once, normalised once, and handed to every tower.
`fingerprint()` then makes disagreement detectable rather than merely unlikely.

Hardware lives here rather than in a tower because none of the five towers is a
hardware tower — they are all services. The estate says what exists; the towers
price servicing it. Whether the provider also *supplies* the hardware is a
separate commercial question, answered by `hardware_supplied_by`.

    from core.estate import normalise, fingerprint
    estate, register = normalise(params)
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

import hashlib
import json
import math
from typing import Any

from core.contract import ValidationError, assumption, bom_line
from core import estate_rates as E

HARDWARE_SUPPLY = ("client", "provider")


# ---------------------------------------------------------------------------

def normalise(params: dict) -> tuple[dict, list[dict]]:
    """Turn a described estate into counted things, with provenance.

    Every tower calls this with the same `params`, so every tower gets the same
    numbers. Returns the estate and the assumption register entries it
    generated; the tower appends its own service parameters to that register.
    """
    src = params.get("_sources", {})
    reg: list[dict] = []
    e: dict[str, Any] = {}

    def take(key, default, note=""):
        if params.get(key) is not None:
            reg.append(assumption(key, params[key], src.get(key, "user"), note))
            return params[key]
        reg.append(assumption(key, default, "default", note))
        return default

    e["client_name"] = take("client_name", "Unnamed Client")
    e["rfp_ref"] = take("rfp_ref", "n/a")

    # --- sites ------------------------------------------------------------
    sites_in = params.get("sites") or {}
    unknown = set(sites_in) - set(E.SITE_BANDS)
    if unknown:
        raise ValidationError(
            f"Unknown site band(s) {sorted(unknown)}. "
            f"Bands are: {', '.join(E.SITE_BANDS)}")
    sites = {b: int(sites_in.get(b, 0) or 0) for b in E.SITE_BANDS}
    if any(v < 0 for v in sites.values()):
        raise ValidationError("Site counts cannot be negative.")
    e["sites"] = sites
    e["sites_total"] = sum(sites.values())
    for b, n in sites.items():
        if n:
            reg.append(assumption(f"sites.{b}", n, src.get("sites", "user")))

    # --- geography --------------------------------------------------------
    mix = params.get("country_mix") or {"UK": 1.0}
    unknown = set(mix) - set(E.SUPPORTED_COUNTRIES)
    if unknown:
        raise ValidationError(
            f"Unsupported country/countries {sorted(unknown)}. "
            f"Rate cards cover: {', '.join(E.SUPPORTED_COUNTRIES)}")
    total = sum(float(v) for v in mix.values())
    if total <= 0:
        raise ValidationError("country_mix shares must be positive.")
    if abs(total - 1.0) > 0.01:
        mix = {k: float(v) / total for k, v in mix.items()}
        reg.append(assumption("country_mix", mix, "derived", "Shares normalised."))
    else:
        reg.append(assumption("country_mix", mix, src.get("country_mix", "user")))
    e["country_mix"] = mix

    # --- people -----------------------------------------------------------
    if params.get("user_count"):
        e["user_count"] = int(params["user_count"])
        reg.append(assumption("user_count", e["user_count"],
                              src.get("user_count", "user")))
    elif e["sites_total"]:
        e["user_count"] = sum(n * E.USERS_PER_SITE_BAND[b]
                              for b, n in sites.items())
        reg.append(assumption("user_count", e["user_count"], "derived",
                              "Derived from site bands."))
    else:
        raise ValidationError(
            "The estate is empty — state either sites or a user count.")

    # --- network ----------------------------------------------------------
    if params.get("aps_total"):
        e["aps_total"] = int(params["aps_total"])
        reg.append(assumption("aps_total", e["aps_total"],
                              src.get("aps_total", "user")))
    else:
        e["aps_total"] = sum(n * E.APS_PER_SITE_BAND[b] for b, n in sites.items())
        if e["aps_total"]:
            reg.append(assumption("aps_total", e["aps_total"], "derived",
                                  "Design standard per site band; no survey stated."))

    if params.get("switch_count"):
        e["switch_count"] = int(params["switch_count"])
        reg.append(assumption("switch_count", e["switch_count"],
                              src.get("switch_count", "user")))
    elif e["aps_total"]:
        ports = e["user_count"] * E.USERS_PER_PORT
        e["switch_count"] = max(e["sites_total"],
                                math.ceil(ports / E.PORTS_PER_SWITCH))
        reg.append(assumption("switch_count", e["switch_count"], "derived",
                              f"{E.PORTS_PER_SWITCH} ports/switch, "
                              f"{E.USERS_PER_PORT} ports/user (wireless-first)."))
    else:
        e["switch_count"] = 0

    # --- devices ----------------------------------------------------------
    devices_in = params.get("devices")
    if devices_in:
        unknown = set(devices_in) - set(E.DEVICE_TYPES)
        if unknown:
            raise ValidationError(
                f"Unknown device type(s) {sorted(unknown)}. "
                f"Types are: {', '.join(E.DEVICE_TYPES)}")
        devices = {t: int(devices_in.get(t, 0) or 0) for t in E.DEVICE_TYPES}
        reg.append(assumption("devices", devices, src.get("devices", "user")))
    elif params.get("device_total"):
        n = int(params["device_total"])
        reg.append(assumption("device_total", n, src.get("device_total", "user")))
        devices = {t: round(n * share)
                   for t, share in E.DEFAULT_DEVICE_MIX.items()}
        reg.append(assumption("devices", devices, "derived",
                              "Split by the standard mix; the tender states a "
                              "total only."))
    else:
        devices = {t: 0 for t in E.DEVICE_TYPES}
    e["devices"] = devices
    e["device_total"] = sum(devices.values())

    # --- languages --------------------------------------------------------
    langs = params.get("languages")
    if isinstance(langs, str):
        langs = [x.strip() for x in langs.split(",") if x.strip()]
    if langs:
        langs = [str(x).upper() for x in langs]
        unknown = set(langs) - set(E.SUPPORTED_LANGUAGES)
        if unknown:
            raise ValidationError(
                f"Unsupported language(s) {sorted(unknown)}. "
                f"Supported: {', '.join(E.SUPPORTED_LANGUAGES)}")
        e["languages"] = list(dict.fromkeys(langs))
        reg.append(assumption("languages", e["languages"],
                              src.get("languages", "user")))
    else:
        e["languages"] = list(dict.fromkeys(
            E.COUNTRY_LANGUAGE[c] for c in mix if c in E.COUNTRY_LANGUAGE))
        reg.append(assumption("languages", e["languages"], "derived",
                              "One language per country in the estate."))

    # --- hardware supply --------------------------------------------------
    e["hardware_supplied_by"] = take(
        "hardware_supplied_by", "client",
        "Whether the provider supplies the hardware or services what is there.")
    if e["hardware_supplied_by"] not in HARDWARE_SUPPLY:
        raise ValidationError(
            f"hardware_supplied_by must be one of {HARDWARE_SUPPLY}")

    e["hardware_value"] = hardware_value(e)
    return e, reg


# ---------------------------------------------------------------------------

def hardware_value(estate: dict) -> float:
    """Replacement value of the estate, whoever owns it.

    Logistics needs this even when the client supplies the kit — a spares pool
    is sized against what is deployed, not against what was invoiced.
    """
    total = (estate.get("aps_total", 0) * E.AP_UNIT_COST
             + estate.get("switch_count", 0) * E.SWITCH_UNIT_COST)
    for t, n in (estate.get("devices") or {}).items():
        total += n * E.DEVICE_UNIT_COST[t]
    return round(total, 2)


def hardware_bom(estate: dict, *, rolls_into: str, phase: str = "one-off") -> list[dict]:
    """The estate as a bill of materials, at cost.

    Only meaningful when the provider supplies the hardware; when the client
    does, this is the deployed base, useful for context but not for charging.
    """
    lines = []
    if estate.get("aps_total"):
        lines.append(bom_line("Wireless access point", estate["aps_total"],
                              "each", E.AP_UNIT_COST, rolls_into=rolls_into,
                              phase=phase, category="Network hardware"))
    if estate.get("switch_count"):
        lines.append(bom_line("Access switch", estate["switch_count"], "each",
                              E.SWITCH_UNIT_COST, rolls_into=rolls_into,
                              phase=phase, category="Network hardware"))
    for t, n in sorted((estate.get("devices") or {}).items(),
                       key=lambda kv: -kv[1]):
        if n:
            lines.append(bom_line(E.DEVICE_LABEL[t], n, "each",
                                  E.DEVICE_UNIT_COST[t], rolls_into=rolls_into,
                                  phase=phase, category="End-user hardware"))
    return lines


# ---------------------------------------------------------------------------

MATERIAL = ("sites", "country_mix", "user_count", "aps_total", "switch_count",
            "devices", "hardware_supplied_by")


def fingerprint(estate: dict) -> str:
    """A short hash of the scope every lot must agree on.

    Two lots in one bid that disagree here are pricing different deals. The
    hash exists so that becomes a failed check rather than a client's
    discovery — `languages` is excluded deliberately, because a desk lot may
    legitimately cover fewer languages than the estate speaks.
    """
    canon = {}
    for key in MATERIAL:
        value = estate.get(key)
        if isinstance(value, dict):
            canon[key] = {k: (round(v, 6) if isinstance(v, float) else v)
                          for k, v in sorted(value.items())}
        else:
            canon[key] = value
    blob = json.dumps(canon, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def describe(estate: dict) -> str:
    """One line, for confirming the estate before pricing any lot."""
    bits = []
    if estate.get("sites_total"):
        bits.append(f"{estate['sites_total']:,} sites")
    if estate.get("user_count"):
        bits.append(f"{estate['user_count']:,} users")
    if estate.get("device_total"):
        bits.append(f"{estate['device_total']:,} devices")
    if estate.get("aps_total"):
        bits.append(f"{estate['aps_total']:,} APs")
    if estate.get("country_mix"):
        bits.append("/".join(sorted(estate["country_mix"])))
    return " · ".join(bits)


def scope_detail(estate: dict) -> dict:
    """The estate block every tower puts in `scope.detail`.

    Identical across lots by construction, which is what lets a reviewer
    compare two lots' artefacts side by side and see at a glance that they
    priced the same thing.
    """
    return {
        "estate_fingerprint": fingerprint(estate),
        "sites_by_band": estate["sites"],
        "country_mix": estate["country_mix"],
        "user_count": estate["user_count"],
        "devices": {k: v for k, v in estate["devices"].items() if v},
        "aps_total": estate["aps_total"],
        "switch_count": estate["switch_count"],
        "hardware_supplied_by": estate["hardware_supplied_by"],
    }
