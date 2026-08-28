"""
Preflight — run before any demo.

Verifies dependencies, discovers every installed model pack, and exercises the
full chain for each one. A missing package or a broken pack surfaces here rather
than in front of an audience.

Run:  python preflight.py
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
import shutil
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL))

OK, WARN, BAD = "  OK  ", " WARN ", " FAIL "
results: list[tuple[str, str, str]] = []


def record(status, label, detail=""):
    results.append((status, label, detail))
    print(f"[{status}] {label}" + (f"  —  {detail}" if detail else ""))


def check_module(mod, install, required=True):
    try:
        m = importlib.import_module(mod)
        record(OK, f"Python package: {mod}", getattr(m, "__version__", ""))
    except ImportError:
        record(BAD if required else WARN, f"Python package: {mod}",
               f"missing — pip install {install}")


def main() -> int:
    print("=" * 68)
    print("  GP-20 Solution & Cost Architect — preflight")
    print(f"  Skill folder: {SKILL}")
    print("=" * 68)

    print("\nEnvironment")
    v = sys.version_info
    record(OK if v >= (3, 10) else BAD, "Python",
           f"{v.major}.{v.minor}.{v.micro} at {sys.executable}")
    check_module("openpyxl", "openpyxl")
    check_module("pptx", "python-pptx")
    check_module("docx", "python-docx", required=False)
    exe = shutil.which("soffice") or shutil.which("soffice.exe")
    record(OK if exe else WARN, "LibreOffice",
           exe or "not found — only needed for workbook parity, not the demo")

    print("\nCore files")
    for rel in ["SKILL.md", "core/run_estimate.py", "core/registry.py",
                "core/contract.py", "core/read_docx.py", "core/settings.py",
                "core/estate.py", "core/bid.py",
                "core/write_pricing_form.py", "core/write_deck.py",
                "core/write_cost_model.py"]:
        p = SKILL / rel
        record(OK if p.exists() else BAD, rel, "" if p.exists() else "missing")

    print("\nModel packs")
    try:
        from core import registry
        from core.contract import verify
    except Exception as exc:                                    # noqa: BLE001
        record(BAD, "core import", f"{type(exc).__name__}: {exc}")
        return 1

    folders = registry.pack_keys()
    if not folders:
        record(BAD, "pack discovery", "no packs found under models/")
        return 1
    record(OK, "pack discovery", f"{len(folders)} pack(s): {', '.join(folders)}")

    print("\nEngagement settings")
    try:
        from core import settings as settings_mod
        saved = settings_mod.load()
        if saved:
            record(OK, "saved settings",
                   ", ".join(f"{k}={settings_mod.fmt(k, v)}"
                             for k, v in saved["params"].items()))
        else:
            record(OK, "saved settings",
                   "none in this folder — packs will use their own defaults")
    except Exception as exc:                                    # noqa: BLE001
        record(BAD, "saved settings", f"{type(exc).__name__}: {exc}")

    tmp = Path(tempfile.mkdtemp(prefix="gp20_preflight_"))
    from core.write_cost_model import build as build_model
    from core.write_deck import build as build_deck
    from core.write_pricing_form import build as build_form

    for folder in folders:
        try:
            pack = importlib.import_module(f"models.{folder}.pack")
            cases = importlib.import_module(f"models.{folder}.cases").CASES
            result = pack.estimate(cases[0][1])
            problems = verify(result, pack.MANIFEST)
            if problems:
                record(BAD, f"pack {pack.MANIFEST.key}", problems[0])
                continue
            sym = result["meta"]["symbol"]
            record(OK, f"pack {pack.MANIFEST.key}",
                   f"TCV {sym}{result['summary']['tcv']:,.0f}")
            build_form(result, str(tmp / f"{folder}.xlsx"))
            build_deck(result, str(tmp / f"{folder}.pptx"))
            build_model(result, str(tmp / f"{folder}_model.xlsx"))
            record(OK, f"  artefacts for {pack.MANIFEST.key}",
                   f"{len(result.get('bom') or [])} BoM lines")
        except Exception as exc:                                # noqa: BLE001
            record(BAD, f"pack {folder}", f"{type(exc).__name__}: {exc}")

    shutil.rmtree(tmp, ignore_errors=True)

    bad = [r for r in results if r[0] == BAD]
    warn = [r for r in results if r[0] == WARN]
    print("\n" + "=" * 68)
    if bad:
        print(f"  NOT READY — {len(bad)} blocking issue(s):")
        for _, label, detail in bad:
            print(f"    · {label}: {detail}")
    else:
        print("  READY FOR DEMO" + (f"  ({len(warn)} warning(s))" if warn else ""))
    print("=" * 68)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
