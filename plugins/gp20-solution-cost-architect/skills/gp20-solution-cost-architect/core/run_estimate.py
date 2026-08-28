"""
Single entry point for every offering.

    python run_estimate.py --pack <key> params.json > result.json

JSON goes to stdout; the human-readable summary goes to stderr, so the redirect
above yields a file the artefact writers can parse. `--json` silences the
summary entirely.

If `--pack` is omitted, the pack key is read from `params.json`'s `_pack` field.
An unknown pack is an error, never a guess.

Saved engagement settings (`gp20_settings.json` in the working directory) are
applied automatically to any commercial parameter this deal has not stated —
margin, contingency, indexation, default term. Anything in params.json wins;
settings only fill gaps. `--no-settings` ignores the file entirely.
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import registry, settings as settings_mod
from core.contract import ValidationError, verify


def summarise(result: dict) -> str:
    meta, summ, run, dep = (result["meta"], result["summary"],
                            result["run"], result["deployment"])
    sym = meta["symbol"]

    def m(v):
        return f"{sym}{round(float(v)):,}"

    head = " · ".join(
        f"{i['label']}: {i['value']:,}" if isinstance(i["value"], (int, float))
        else f"{i['label']}: {i['value']}"
        for i in result["scope"]["headline"][:4])

    lines = [
        f"{meta['client_name']} — {meta['offering_name']}",
        head,
        " · ".join(f"{s['label']}: {s['value']}" for s in result["service"][:3]),
        "",
        f"Transition ({dep['duration_months']} months): "
        f"{dep['days_by_role'].get('total', 0):,.0f} days → {m(dep['price'])} one-off",
        f"Run: {run['total_fte']} FTE → {m(run['price_pa'])}/yr ({m(run['price_pm'])}/mo)",
    ]
    for u in summ.get("unit_metrics", []):
        lines.append(f"     {u['label']}: {sym}{u['value']:,.2f}")
    lines.append(f"TCV over {summ['term_years']} years: {m(summ['tcv'])}")

    if run.get("insight"):
        lines += ["", f"◆ {run['insight']}"]
    if result["review_flags"]:
        flagged = ", ".join(f["parameter"] for f in result["review_flags"])
        lines += ["", f"⚠ Model defaults in force for: {flagged} — confirm before issuing."]
    return "\n".join(lines)


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    quiet = "--json" in args or "-q" in args
    use_settings = "--no-settings" not in args
    pack_key = None
    if "--pack" in args:
        i = args.index("--pack")
        if i + 1 >= len(args):
            print("--pack needs a value", file=sys.stderr)
            return 2
        pack_key = args[i + 1]
        del args[i:i + 2]
    positional = [a for a in args if not a.startswith("-")]

    if positional:
        params = json.loads(Path(positional[0]).read_text(encoding="utf-8"))
    else:
        params = json.load(sys.stdin)

    pack_key = pack_key or params.get("_pack")
    if not pack_key:
        print("No pack specified. Use --pack <key> or set _pack in params.json.\n"
              f"Available: {', '.join(registry.available_keys())}", file=sys.stderr)
        return 2

    try:
        pack = registry.load(pack_key)
    except registry.UnknownPack as exc:
        print(str(exc), file=sys.stderr)
        return 3

    applied: list[str] = []
    if use_settings:
        try:
            saved = settings_mod.load()
        except settings_mod.SettingsError as exc:
            # Refuse rather than fall back to defaults. A settings file the user
            # believes is in force, silently ignored, is the worst outcome here.
            print(f"Saved settings could not be read: {exc}", file=sys.stderr)
            print("Fix the file, or re-run with --no-settings.", file=sys.stderr)
            return 6
        params, applied = settings_mod.apply(params, saved, pack.MANIFEST)

    try:
        result = pack.estimate(params)
    except ValidationError as exc:
        print(f"Input rejected: {exc}", file=sys.stderr)
        return 4

    problems = verify(result, pack.MANIFEST)
    if problems:
        print("Pack returned a non-conforming result:", file=sys.stderr)
        for p in problems:
            print(f"  · {p}", file=sys.stderr)
        return 5

    if not quiet:
        print(summarise(result), file=sys.stderr)
        if applied:
            shown = ", ".join(
                f"{settings_mod.FIELDS[k][0].lower()} "
                f"{settings_mod.fmt(k, params[k])}" for k in applied)
            print(f"\n⚙ From saved settings: {shown}", file=sys.stderr)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
