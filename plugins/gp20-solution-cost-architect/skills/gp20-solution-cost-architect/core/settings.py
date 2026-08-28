"""
Engagement settings — the commercial parameters that outlive a single run.

Margin, contingency, indexation and default term are not in the tender. They
come from the business, they are the same for every deal a team prices, and
before this existed they were re-derived on every run and flagged for review
every time. A flag that appears on every document is a flag nobody reads.

So they are stored once, in the user's working directory, and applied
automatically. The file is deliberately plain JSON and deliberately local: it
belongs to the engagement, not to the skill, and a different client can have a
different margin without anyone editing code.

Precedence, highest first:

    1. parameters supplied for this deal   (the RFP, or the conversation)
    2. saved settings                      (this file)
    3. pack defaults                       (rates.py)

That order matters. A term stated in the tender must beat a saved default, or
the skill will quietly price the wrong contract length.

Usage:
    python settings.py show
    python settings.py save '{"margin_pct": 0.25, "indexation_pct": 0.03}'
    python settings.py clear
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

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

FILENAME = "gp20_settings.json"
VERSION = 1


class SettingsError(ValueError):
    """The settings file exists but cannot be trusted."""


# key -> (label, kind, validator, hint shown when asking)
FIELDS: dict[str, tuple] = {
    "margin_pct": (
        "Target margin", "pct",
        lambda v: 0 <= v < 0.95,
        "Applied to cost to reach price. The single most sensitive number here."),
    "contingency_pct": (
        "Contingency", "pct",
        lambda v: 0 <= v < 0.5,
        "Added to cost before margin, so it compounds with it."),
    "indexation_pct": (
        "Annual indexation", "pct",
        lambda v: -0.1 <= v < 0.25,
        "Applied from year two onwards across the term."),
    "term_years": (
        "Default contract term", "int",
        lambda v: 1 <= v <= 15,
        "Used only when the tender does not state one."),
    "delivery_country": (
        "Default delivery country", "text",
        lambda v: isinstance(v, str) and 1 < len(v) <= 24,
        "Where centralised roles are based, for packs that offer the choice."),
}

# Written alongside the parameters, but not passed to any pack.
META_FIELDS = ("output_dir", "label")


def path_for(directory: str | Path | None = None) -> Path:
    return Path(directory or Path.cwd()) / FILENAME


# ---------------------------------------------------------------------------

def load(directory: str | Path | None = None) -> dict | None:
    """Return the saved settings, or None if there are none.

    A malformed file raises rather than being silently ignored — settings move
    money, and a typo that quietly reverts everyone to a 22% default is exactly
    the failure this is meant to prevent.
    """
    p = path_for(directory)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SettingsError(f"{p} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or "params" not in data:
        raise SettingsError(f"{p} is missing a 'params' object")

    bad = validate(data["params"])
    if bad:
        raise SettingsError(f"{p} holds unusable values: " + "; ".join(bad))
    return data


def validate(params: dict) -> list[str]:
    """Return a list of problems. Empty means the values are usable."""
    problems = []
    for key, value in params.items():
        if key not in FIELDS:
            problems.append(f"{key} is not a recognised setting")
            continue
        label, kind, ok, _ = FIELDS[key]
        if kind in ("pct", "int"):
            try:
                value = float(value)
            except (TypeError, ValueError):
                problems.append(f"{label} must be a number, got {value!r}")
                continue
        if not ok(value):
            problems.append(f"{label} is out of range: {value!r}")
    return problems


def save(params: dict, directory: str | Path | None = None, *,
         label: str = "", output_dir: str = "", merge: bool = True) -> Path:
    """Write settings, merging over anything already saved unless told not to."""
    problems = validate(params)
    if problems:
        raise SettingsError("; ".join(problems))

    existing = {}
    try:
        current = load(directory)
        if current and merge:
            existing = current.get("params", {})
            label = label or current.get("label", "")
            output_dir = output_dir or current.get("output_dir", "")
    except SettingsError:
        pass                       # a broken file is replaced, not merged into

    merged = {**existing, **params}
    for key in ("margin_pct", "contingency_pct", "indexation_pct"):
        if key in merged:
            merged[key] = float(merged[key])
    if "term_years" in merged:
        merged["term_years"] = int(merged["term_years"])

    doc = {
        "version": VERSION,
        "saved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "label": label,
        "output_dir": output_dir,
        "params": merged,
        "_comment": "GP-20 engagement settings. Edit by hand if you prefer; "
                    "values are validated on load.",
    }
    p = path_for(directory)
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return p


def clear(directory: str | Path | None = None) -> bool:
    p = path_for(directory)
    if p.exists():
        p.unlink()
        return True
    return False


# ---------------------------------------------------------------------------

def fmt(key: str, value) -> str:
    label, kind, _, _ = FIELDS.get(key, (key, "text", None, ""))
    if kind == "pct":
        return f"{float(value):.2%}"
    if kind == "int":
        return f"{int(value)}"
    return str(value)


def describe(settings: dict | None) -> str:
    """A short human summary, for showing the user before they confirm."""
    if not settings or not settings.get("params"):
        return "No saved settings — commercial parameters will use pack defaults."
    lines = []
    if settings.get("label"):
        lines.append(settings["label"])
    for key, value in settings["params"].items():
        label = FIELDS.get(key, (key,))[0]
        lines.append(f"  {label}: {fmt(key, value)}")
    if settings.get("saved_utc"):
        lines.append(f"  (saved {settings['saved_utc'][:10]})")
    return "\n".join(lines)


def applicable(manifest) -> list[str]:
    """Which settings this pack actually consumes."""
    return [k for k in getattr(manifest, "settings", []) if k in FIELDS]


def apply(params: dict, settings: dict | None, manifest=None) -> tuple[dict, list[str]]:
    """Merge saved settings into params without overriding anything supplied.

    Returns the new params and the list of keys the settings actually supplied,
    so the caller can say so rather than applying them invisibly.
    """
    if not settings or not settings.get("params"):
        return params, []

    allowed = applicable(manifest) if manifest is not None else list(FIELDS)
    merged = dict(params)
    sources = dict(merged.get("_sources") or {})
    used: list[str] = []

    for key, value in settings["params"].items():
        if key not in allowed:
            continue                       # this pack does not take it
        if merged.get(key) is not None:
            continue                       # the deal already said otherwise
        merged[key] = value
        # The user did supply this — in an earlier session. `user` is the honest
        # tag, and it is what stops the same default being flagged every run.
        sources.setdefault(key, "user")
        used.append(key)

    if used:
        merged["_sources"] = sources
    return merged, used


# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    cmd = args[0]
    try:
        if cmd == "show":
            current = load()
            print(describe(current))
            if current:
                print(f"\nFile: {path_for()}")
            return 0

        if cmd == "save":
            if len(args) < 2:
                print("save needs a JSON object, e.g. "
                      "save '{\"margin_pct\": 0.25}'", file=sys.stderr)
                return 2
            incoming = json.loads(args[1])
            label = args[2] if len(args) > 2 else ""
            p = save(incoming, label=label)
            print(f"Saved: {p}")
            print(describe(load()))
            return 0

        if cmd == "clear":
            print("Removed." if clear() else "Nothing to remove.")
            return 0

    except SettingsError as exc:
        print(f"Settings problem: {exc}", file=sys.stderr)
        return 4
    except json.JSONDecodeError as exc:
        print(f"Not valid JSON: {exc}", file=sys.stderr)
        return 2

    print(f"Unknown command {cmd!r}. Use show, save or clear.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
