#!/usr/bin/env python3
"""
Engagement settings — persistence, precedence and refusal.

The rule that matters is precedence: a parameter stated for this deal must beat
a saved setting, every time. Get it backwards and the skill quietly prices the
wrong contract length or the wrong margin, with no flag raised, because from the
model's point of view nothing is missing.

Run:  python tests/test_settings.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import registry, settings                                  # noqa: E402

PASS = FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"    PASS  {label}")
    else:
        FAIL += 1
        print(f"    FAIL  {label}" + (f"  — {detail}" if detail else ""))


def main() -> int:
    print("=" * 68)
    print("  Engagement settings")
    print("=" * 68)

    tmp = Path(tempfile.mkdtemp(prefix="gp20_settings_"))

    # --- round trip ---------------------------------------------------------
    print("\n  Persistence")
    check("no settings reads as None", settings.load(tmp) is None)

    settings.save({"margin_pct": 0.25, "term_years": 7}, tmp, label="Test team")
    loaded = settings.load(tmp)
    check("saved settings load back", loaded is not None)
    check("values survive the round trip",
          loaded["params"]["margin_pct"] == 0.25
          and loaded["params"]["term_years"] == 7)
    check("label survives", loaded.get("label") == "Test team")

    settings.save({"indexation_pct": 0.04}, tmp)
    loaded = settings.load(tmp)
    check("a later save merges rather than replaces",
          loaded["params"].get("margin_pct") == 0.25
          and loaded["params"].get("indexation_pct") == 0.04)
    check("label is kept across a merging save", loaded.get("label") == "Test team")

    # --- validation ---------------------------------------------------------
    print("\n  Refusal")
    for bad, why in [({"margin_pct": 1.4}, "margin above 95%"),
                     ({"margin_pct": -0.2}, "negative margin"),
                     ({"term_years": 0}, "zero term"),
                     ({"nonsense_key": 1}, "unknown key"),
                     ({"margin_pct": "lots"}, "non-numeric margin")]:
        try:
            settings.save(bad, tmp)
            check(f"rejects {why}", False, "save accepted it")
        except settings.SettingsError:
            check(f"rejects {why}", True)

    (tmp / settings.FILENAME).write_text("{ not json", encoding="utf-8")
    try:
        settings.load(tmp)
        check("malformed file raises rather than defaulting", False)
    except settings.SettingsError:
        check("malformed file raises rather than defaulting", True)

    # --- precedence ---------------------------------------------------------
    print("\n  Precedence")
    settings.save({"margin_pct": 0.25, "term_years": 7}, tmp,
                  label="Test team", merge=False)
    saved = settings.load(tmp)
    man = registry.load("managed-lan").MANIFEST

    merged, used = settings.apply({"sites": {"small": 4}}, saved, man)
    check("settings fill an unstated parameter",
          merged["margin_pct"] == 0.25 and "margin_pct" in used)
    check("filled parameters are tagged as user-supplied",
          merged["_sources"]["margin_pct"] == "user")

    merged, used = settings.apply(
        {"sites": {"small": 4}, "margin_pct": 0.11,
         "_sources": {"margin_pct": "rfp"}}, saved, man)
    check("a stated parameter beats the saved setting",
          merged["margin_pct"] == 0.11)
    check("its provenance is not overwritten",
          merged["_sources"]["margin_pct"] == "rfp")
    check("the overridden key is not reported as applied",
          "margin_pct" not in used)

    merged, _ = settings.apply({"sites": {"small": 4}, "term_years": 3}, saved, man)
    check("a term stated in the tender beats the saved default",
          merged["term_years"] == 3)

    # --- pack scoping -------------------------------------------------------
    print("\n  Pack scoping")
    settings.save({"delivery_country": "PL"}, tmp)
    saved = settings.load(tmp)
    merged, _ = settings.apply({"sites": {"small": 4}}, saved,
                               registry.load("managed-lan").MANIFEST)
    check("a setting a pack does not consume is not injected",
          "delivery_country" not in merged,
          "managed-lan sizes by country_mix, not a single hub")
    merged, _ = settings.apply({}, saved, registry.load("service-desk").MANIFEST)
    check("a setting a pack does consume is injected",
          merged.get("delivery_country") == "PL")

    for entry in registry.catalogue():
        man = registry.load(entry["key"]).MANIFEST
        declared = settings.applicable(man)
        check(f"{entry['key']} declares usable settings",
              set(declared) <= set(settings.FIELDS) and len(declared) >= 4,
              f"declared {declared}")

    # --- end to end, through the documented command line --------------------
    print("\n  Applied by the estimator")
    work = Path(tempfile.mkdtemp(prefix="gp20_settings_cli_"))
    cases = __import__("models.managed_lan.cases", fromlist=["CASES"]).CASES
    params = dict(cases[0][1])
    params.pop("margin_pct", None)
    (work / "params.json").write_text(json.dumps(params), encoding="utf-8")

    def run(extra: list[str]) -> dict:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "core" / "run_estimate.py"),
             "--pack", "managed-lan", "params.json", "--json", *extra],
            cwd=work, capture_output=True, text=True, timeout=120)
        return json.loads(proc.stdout)

    baseline = run([])
    settings.save({"margin_pct": 0.31}, work, merge=False)
    with_settings = run([])
    without = run(["--no-settings"])

    check("the estimator applies saved settings unprompted",
          abs(with_settings["summary"]["margin_pct_effective"] - 0.31) < 1e-6)
    check("--no-settings ignores the file",
          abs(without["summary"]["margin_pct_effective"]
              - baseline["summary"]["margin_pct_effective"]) < 1e-6)
    check("applying a setting clears the review flag it was raising",
          "margin_pct" not in {f["parameter"]
                               for f in with_settings["review_flags"]}
          and "margin_pct" in {f["parameter"] for f in baseline["review_flags"]})

    # Written by hand, because save() would rightly refuse to produce this.
    (work / settings.FILENAME).write_text(
        json.dumps({"params": {"margin_pct": 1.4}}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "core" / "run_estimate.py"),
         "--pack", "managed-lan", "params.json"],
        cwd=work, capture_output=True, text=True, timeout=120)
    check("an unusable settings file stops the run rather than defaulting",
          proc.returncode == 6, f"exit {proc.returncode}")

    print("\n" + "=" * 68)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 68)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
