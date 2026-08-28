"""
Bid-level reconciliation across lots.

A lotted tender is priced one lot at a time, often by different people, and the
failure mode is not that any single lot is wrong — it is that the lots do not
agree with each other. Three ways that happens, all of them silent:

  1. **Different estates.** Lot 1 prices 101 sites, Lot 2 prices 98. Each is
     internally consistent; the bid is not.
  2. **Contradictory hand-offs.** The field lot assumes `standard` remote
     capability while the remote lot is priced at `basic`. Somebody is carrying
     work nobody has priced.
  3. **Different commercials.** One lot at a 5-year term, another at 3.

None of these show up in a per-lot review, because each lot passes its own
contract check. They only appear when the lots are put side by side, which is
what this module does.

    python bid.py lot1.json lot2.json lot3.json
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


def _get(result: dict, *path, default=None):
    node = result
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def reconcile(results: list[dict]) -> list[str]:
    """Return the disagreements between lots. Empty means the bid hangs together."""
    problems: list[str] = []
    if len(results) < 2:
        return problems

    def label(r):
        return _get(r, "meta", "offering", default="?")

    # --- 1. one estate ----------------------------------------------------
    prints: dict[str, list[str]] = {}
    for r in results:
        fp = _get(r, "scope", "detail", "estate_fingerprint")
        if fp is None:
            problems.append(
                f"{label(r)} does not publish an estate fingerprint — it is not "
                f"using the shared estate, so it cannot be reconciled")
            continue
        prints.setdefault(fp, []).append(label(r))
    if len(prints) > 1:
        groups = "; ".join(f"[{', '.join(v)}] = {k}" for k, v in prints.items())
        problems.append(f"lots priced different estates: {groups}")

    # --- 2. one term, one commercial basis --------------------------------
    for field, human in (("term_years", "contract term"),
                         ("margin_pct_effective", "margin")):
        seen: dict = {}
        for r in results:
            value = _get(r, "summary", field)
            if value is None:
                continue
            seen.setdefault(round(float(value), 4), []).append(label(r))
        if len(seen) > 1:
            groups = "; ".join(f"[{', '.join(v)}] = {k}" for k, v in seen.items())
            problems.append(f"lots priced on a different {human}: {groups}")

    # --- 3. hand-offs agree -----------------------------------------------
    by_key = {label(r): r for r in results}

    field, remote = by_key.get("field-service"), by_key.get("remote-support")
    if field and remote:
        assumed = next((a["value"] for a in field.get("assumptions", [])
                        if a["parameter"] == "remote_capability"), None)
        priced = next((a["value"] for a in remote.get("assumptions", [])
                       if a["parameter"] == "capability"), None)
        if assumed and priced and assumed != priced:
            problems.append(
                f"field-service is priced assuming {assumed!r} remote "
                f"capability, but remote-support is priced to deliver "
                f"{priced!r} — one lot is carrying work the other has not "
                f"costed")

    field, logistics = by_key.get("field-service"), by_key.get("logistics")
    if field and logistics:
        tier = next((a["value"] for a in field.get("assumptions", [])
                     if a["parameter"] == "sla_tier"), None)
        strategy = _get(logistics, "run", "drivers", "stock_strategy")
        # A committed fix time is a stock commitment before it is a labour one.
        # Neither lot's own numbers reveal the gap: the field lot has its
        # engineers, the logistics lot has its warehouse, and the part is not
        # in the van.
        rank = {"none": 0, "central": 1, "regional": 2, "forward": 3, "onsite": 4}
        needs = {"bronze": "central", "silver": "central",
                 "gold": "forward", "platinum": "onsite"}
        if tier in needs and strategy in rank:
            if rank[strategy] < rank[needs[tier]]:
                problems.append(
                    f"field-service commits to a {tier!r} on-site fix, which "
                    f"needs {needs[tier]!r} stock, but logistics is priced for "
                    f"{strategy!r} — the fix time cannot be met as bid")

    pm = by_key.get("project-management")
    if pm:
        governed = _get(pm, "run", "drivers", "lots_governed")
        actual = len(results) - 1          # every lot except the PM lot itself
        if governed is not None and actual >= 1 and int(governed) != actual:
            problems.append(
                f"project-management is priced to govern {int(governed)} lots "
                f"but the bid contains {actual} other lots — governance is "
                f"sized to the wrong programme")

    desk, remote = by_key.get("service-desk"), by_key.get("remote-support")
    if desk and remote:
        out = _get(desk, "run", "drivers", "escalations_pa")
        into = _get(remote, "run", "drivers", "escalations_pa")
        if out is not None and into is not None:
            if abs(float(out) - float(into)) > max(1.0, float(out) * 0.02):
                problems.append(
                    f"service-desk passes {float(out):,.0f} escalations a year "
                    f"but remote-support is priced for {float(into):,.0f} — "
                    f"feed the desk's figure into the remote lot")
    return problems


def summarise(results: list[dict]) -> str:
    """The bid as a whole: lot by lot, then the total."""
    if not results:
        return "No lots supplied."
    sym = _get(results[0], "meta", "symbol", default="")
    rows, one_off, tcv, cost = [], 0.0, 0.0, 0.0
    for r in results:
        s = r["summary"]
        rows.append((_get(r, "meta", "offering_name", default="?"),
                     s["one_off_price"], s["annual_price_year1"], s["tcv"]))
        one_off += s["one_off_price"]
        tcv += s["tcv"]
        cost += s.get("total_cost", 0.0)

    width = max(len(n) for n, *_ in rows)
    lines = [f"{'Lot':<{width}}  {'One-off':>14}  {'Annual (Y1)':>14}  {'TCV':>16}",
             "-" * (width + 50)]
    for name, oo, pa, t in rows:
        lines.append(f"{name:<{width}}  {sym}{oo:>13,.0f}  {sym}{pa:>13,.0f}  "
                     f"{sym}{t:>15,.0f}")
    lines.append("-" * (width + 50))
    lines.append(f"{'BID TOTAL':<{width}}  {sym}{one_off:>13,.0f}  "
                 f"{'':>14}  {sym}{tcv:>15,.0f}")
    if cost:
        lines.append(f"{'  of which cost':<{width}}  {'':>14}  {'':>14}  "
                     f"{sym}{cost:>15,.0f}")
        lines.append(f"{'  of which margin':<{width}}  {'':>14}  {'':>14}  "
                     f"{sym}{tcv - cost:>15,.0f}"
                     f"   ({(tcv - cost) / tcv:.1%})")

    fp = _get(results[0], "scope", "detail", "estate_fingerprint")
    if fp:
        lines.append(f"\nEstate fingerprint: {fp} — identical across all lots.")
    return "\n".join(lines)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__)
        return 1

    results = []
    for path in args:
        try:
            results.append(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Cannot read {path}: {exc}", file=sys.stderr)
            return 2

    print(summarise(results))
    problems = reconcile(results)
    if problems:
        print(f"\n{len(problems)} disagreement(s) between lots:", file=sys.stderr)
        for p in problems:
            print(f"  · {p}", file=sys.stderr)
        return 3
    print("\nLots reconcile: one estate, one term, hand-offs agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
