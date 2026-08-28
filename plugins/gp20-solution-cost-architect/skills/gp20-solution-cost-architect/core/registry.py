"""
Pack discovery and loading.

Packs live in `models/<name>/pack.py`. Dropping a conforming folder there is
the entire installation procedure for a new offering — there is no register to
edit, which is the point.

CLI:
    python registry.py list                 every pack, one line each
    python registry.py describe <key>       manifest detail, gaps and options
    python registry.py detect <text-file>   rank packs against an RFP's text
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

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType

SKILL_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = SKILL_ROOT / "models"

if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


class UnknownPack(KeyError):
    """No model pack exists for the requested offering.

    Raised rather than guessing. An RFP for something we have no model for must
    stop here — an improvised price is worse than an honest gap.
    """


def pack_keys() -> list[str]:
    if not MODELS_DIR.is_dir():
        return []
    return sorted(
        d.name for d in MODELS_DIR.iterdir()
        if d.is_dir() and (d / "pack.py").is_file() and not d.name.startswith("_")
    )


def load(key: str) -> ModuleType:
    """Load a pack by manifest key or by folder name."""
    wanted = key.strip().lower().replace("-", "_")
    candidates = pack_keys()

    if wanted in candidates:
        return importlib.import_module(f"models.{wanted}.pack")

    for name in candidates:                       # fall back to manifest key
        mod = importlib.import_module(f"models.{name}.pack")
        if mod.MANIFEST.key.lower() == key.strip().lower():
            return mod

    raise UnknownPack(
        f"No model pack for {key!r}. Available: {', '.join(available_keys()) or 'none'}. "
        "Do not improvise a price — say that no model exists and describe what a "
        "pack would need."
    )


def all_packs() -> list[ModuleType]:
    return [importlib.import_module(f"models.{n}.pack") for n in pack_keys()]


def available_keys() -> list[str]:
    return [p.MANIFEST.key for p in all_packs()]


def catalogue() -> list[dict]:
    out = []
    for p in all_packs():
        m = p.MANIFEST
        out.append({
            "key": m.key, "name": m.name, "summary": m.summary,
            "detect": m.detect, "currency": m.currency,
            "kind": getattr(m, "kind", "offering"),
            "gaps": [g.param for g in m.gaps],
            "settings": list(getattr(m, "settings", [])),
        })
    return out


def detect(text: str) -> list[dict]:
    """Rank packs by how strongly an RFP's text matches their signals.

    A blunt keyword count on purpose. It proposes; the skill confirms with the
    user. Silent auto-selection of a cost model is not a thing worth building.
    """
    low = text.lower()
    scored = []
    for p in all_packs():
        m = p.MANIFEST
        hits = [s for s in m.detect if s.lower() in low]
        scored.append({"key": m.key, "name": m.name,
                       "kind": getattr(m, "kind", "offering"),
                       "score": len(hits), "matched": hits})
    scored.sort(key=lambda r: -r["score"])
    return scored


KIND_HEADING = {
    "tower": ("Towers — lots of a lotted tender, priced separately",
              "Run the lots the tender actually asks for."),
    "offering": ("Offerings — whole outcomes, internally spanning several towers",
                 "Use when a tender buys a result rather than a set of lots."),
}


def _cmd_list() -> int:
    packs = catalogue()
    if not packs:
        print("No model packs installed.")
        return 1
    width = max(len(p["key"]) for p in packs)
    print(f"{len(packs)} model pack(s):")
    for kind, (heading, note) in KIND_HEADING.items():
        members = [p for p in packs if p.get("kind", "offering") == kind]
        if not members:
            continue
        print(f"\n  {heading}")
        print(f"  {note}\n")
        for p in members:
            print(f"    {p['key']:<{width}}  {p['summary']}")
    return 0


def _cmd_describe(key: str) -> int:
    m = load(key).MANIFEST
    print(f"{m.name}  [{m.key}]   ({getattr(m, 'kind', 'offering')})")
    print(f"{m.summary}\n")
    print(f"Currency        : {m.currency}")
    print(f"Detect signals  : {', '.join(m.detect)}")
    print(f"Flagged defaults: {', '.join(m.material)}")
    print(f"Saved settings  : {', '.join(getattr(m, 'settings', [])) or 'none'}"
          f"   (see core/settings.py)")
    if m.notes:
        print(f"\n{m.notes}")
    print(f"\nClarification gaps ({len(m.gaps)}):")
    for g in m.gaps:
        print(f"\n  {g.param}")
        print(f"    {g.question}")
        if g.rfp_hint:
            print(f"    RFP hint: {g.rfp_hint}")
        for o in g.options:
            print(f"      · {o.value:<16} {o.label}")
            print(f"        {o.consequence}")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = args[0]
    if cmd == "list":
        return _cmd_list()
    if cmd == "describe" and len(args) > 1:
        return _cmd_describe(args[1])
    if cmd == "detect" and len(args) > 1:
        text = Path(args[1]).read_text(encoding="utf-8", errors="replace")
        print(json.dumps(detect(text), indent=2))
        return 0
    if cmd == "json":
        print(json.dumps(catalogue(), indent=2))
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
