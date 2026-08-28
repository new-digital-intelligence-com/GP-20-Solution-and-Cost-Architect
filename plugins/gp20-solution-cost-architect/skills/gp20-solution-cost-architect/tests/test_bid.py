#!/usr/bin/env python3
"""
Bid-level reconciliation across lots.

Every check here covers a failure that no single lot can detect. Each lot passes
its own contract check; the bid still does not add up. That is the whole reason
this layer exists, so the tests are all negative cases: build a bid that is
wrong in one specific way, and prove the check finds it.

Run:  python tests/test_bid.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import bid, settings                                       # noqa: E402
from core.registry import load                                       # noqa: E402

PASS = FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"    PASS  {label}")
    else:
        FAIL += 1
        print(f"    FAIL  {label}" + (f"  — {detail}" if detail else ""))


SETTINGS = {"params": {"margin_pct": 0.22, "term_years": 5}}


def price(key: str, folder: str, mutate=None) -> dict:
    """Price one lot of the Aurelian tender, optionally broken on purpose."""
    pack = load(key)
    cases = __import__(f"models.{folder}.cases", fromlist=["CASES"]).CASES
    params = dict(cases[0][1])
    if mutate:
        params = mutate(params)
    params, _ = settings.apply(params, SETTINGS, pack.MANIFEST)
    return pack.estimate(params)


def main() -> int:
    print("=" * 68)
    print("  Bid-level reconciliation")
    print("=" * 68)

    field = price("field-service", "field_service")
    desk = price("service-desk", "service_desk")
    remote = price("remote-support", "remote_support")
    logistics = price("logistics", "logistics")
    pm = price("project-management", "project_management")
    lots = [field, logistics, pm, desk, remote]

    print("\n  A bid that hangs together")
    problems = bid.reconcile(lots)
    check("five lots of one tender reconcile", not problems, "; ".join(problems))
    check("all lots share one estate fingerprint",
          len({r["scope"]["detail"]["estate_fingerprint"] for r in lots}) == 1)
    check("the summary totals every lot",
          f"{sum(r['summary']['tcv'] for r in lots):,.0f}".replace(",", "")
          in bid.summarise(lots).replace(",", ""))

    print("\n  Estates that drift apart")
    def fewer_sites(p):
        p["sites"] = {**p["sites"], "small": 59}      # 98 sites, not 101
        return p
    problems = bid.reconcile([field, desk, price("remote-support",
                                                 "remote_support", fewer_sites)])
    check("a lot priced on a different estate is caught",
          any("different estates" in p for p in problems), str(problems))

    print("\n  Hand-offs that contradict")
    def better_remote(p):
        p["remote_capability"] = "advanced"           # remote lot delivers standard
        return p
    problems = bid.reconcile([price("field-service", "field_service",
                                    better_remote), desk, remote])
    check("field assuming more remote capability than remote delivers is caught",
          any("remote capability" in p for p in problems), str(problems))

    def fewer_escalations(p):
        p["escalations_pa"] = 5000                    # desk publishes ~23,500
        return p
    problems = bid.reconcile([field, desk,
                              price("remote-support", "remote_support",
                                    fewer_escalations)])
    check("remote priced for the wrong escalation volume is caught",
          any("escalations" in p for p in problems), str(problems))

    def central_stock(p):
        p["stock_strategy"] = "central"        # field commits to gold = 4h
        return p
    problems = bid.reconcile([field, price("logistics", "logistics",
                                           central_stock), pm, desk, remote])
    check("a fix time the supply chain cannot support is caught",
          any("cannot be met" in p for p in problems), str(problems))

    def wrong_lot_count(p):
        p["lots"] = 2                          # bid actually has 4 delivery lots
        return p
    problems = bid.reconcile([field, logistics,
                              price("project-management", "project_management",
                                    wrong_lot_count), desk, remote])
    check("governance sized to the wrong number of lots is caught",
          any("govern" in p for p in problems), str(problems))

    print("\n  Commercials that diverge")
    pack = load("service-desk")
    cases = __import__("models.service_desk.cases", fromlist=["CASES"]).CASES
    # Stated on the lot, not in settings — a saved default could not do this,
    # because a value supplied for the deal rightly beats a saved one.
    short_term = {**cases[0][1], "term_years": 3}
    short_term, _ = settings.apply(short_term, SETTINGS, pack.MANIFEST)
    problems = bid.reconcile([field, pack.estimate(short_term), remote])
    check("a lot priced on a different term is caught",
          any("contract term" in p for p in problems), str(problems))

    no_settings = pack.estimate(dict(cases[0][1]))     # pack default margin 0.24
    problems = bid.reconcile([field, no_settings, remote])
    check("lots on different margins are caught",
          any("margin" in p for p in problems), str(problems))

    print("\n  Degenerate input")
    check("a single lot has nothing to disagree with",
          not bid.reconcile([field]))
    check("an empty bid does not crash", not bid.reconcile([]))
    check("a lot with no estate fingerprint is reported",
          any("fingerprint" in p for p in
              bid.reconcile([field, {"meta": {"offering": "legacy"},
                                     "scope": {"detail": {}},
                                     "summary": {}, "assumptions": []}])))

    print("\n" + "=" * 68)
    print(f"  {PASS} passed, {FAIL} failed")
    print("=" * 68)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
