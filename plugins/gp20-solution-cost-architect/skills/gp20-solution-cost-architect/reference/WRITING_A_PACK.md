# Writing a model pack

Adding an offering means writing one folder. Nothing else in the skill changes —
no registry to edit, no writer to extend, no prompt to touch.

```
models/<offering>/
├── __init__.py      empty
├── pack.py          MANIFEST + estimate()
├── rates.py         every constant, nothing else
├── cases.py         CASES = [(label, params), ...] for the conformance suite
└── schema.md        the parameters, in prose, for humans
```

---

## The whole contract

```python
MANIFEST: Manifest
def estimate(params: dict) -> dict
```

That is it. `estimate` builds its return value with the helpers in
`core/contract.py`, which is what keeps every pack consumable by the same
artefact writers.

---

## 1 · rates.py

Every number that could ever be argued about goes here and nowhere else. When
Finance hands over the real rate card, this is the only file that changes.

```python
CURRENCY = "GBP"
SYMBOL = "£"
UNIT_COST = {"laptop": 950.0, ...}
FAILURE_RATE_PA = {"laptop": 0.11, ...}
DEFAULT_MARGIN_PCT = 0.19
```

No arithmetic in this file. No arithmetic constants buried in `pack.py`.

## 2 · MANIFEST

```python
MANIFEST = Manifest(
    key="service-desk",                    # slug, unique, stable
    name="Service Desk and Remote Support",
    summary="One line shown when choosing a pack.",
    detect=["service desk", "helpdesk", "ticket", "first line", ...],
    material=["coverage", "language_count", "margin_pct", "term_years"],
    gaps=[...],
    notes="What a reader should understand about how this offering prices.",
)
```

**`detect`** — phrases that appear in a tender for this offering. Keep them
specific enough not to collide with another pack; the conformance suite fails on
a signal claimed by two packs.

**`material`** — parameters whose defaults materially move the price. These get
flagged for review in every artefact. Be honest: over-flagging trains people to
ignore the flags.

**`settings`** — parameters a team sets once and reuses across deals. Every pack
inherits `COMMON_SETTINGS` (margin, contingency, indexation, default term). Add
to the list only if your pack consumes something else in that category:

```python
settings=[*COMMON_SETTINGS, "delivery_country"],
```

Only declare what `_normalise` actually reads. A setting a pack ignores is worse
than one it does not offer — the user sets it, sees it accepted, and it silently
does nothing.

**`gaps`** — the parameters tenders routinely fail to state. Each option must
carry a `consequence` explaining the commercial effect:

```python
GapOption("24x7", "24×7 — follow the sun",
          "Roughly 4.8 FTE per staffed post, in every country with a "
          "committed on-site response. The largest cost lever here."),
```

`"24×7 coverage"` is a label. `"4.8 FTE per post per country"` is a
consequence. The conformance suite rejects options without one.

## 3 · estimate()

```python
def estimate(params: dict) -> dict:
    p, register = _normalise(params)      # defaults + provenance + validation
    dep = _deployment(p)                  # one-off
    run, insight = _run(p)                # recurring
    return build_result(
        manifest=MANIFEST,
        client_name=p["client_name"], rfp_ref=p["rfp_ref"],
        scope_headline=[scope_item("Devices in scope", p["device_total"]), ...],
        service=[kv("Break-fix commitment", "8 business hours"), ...],
        deployment=dep, run=run,
        term_years=p["term_years"], indexation_pct=p["indexation_pct"],
        assumptions=register, insight=insight,
        unit_metrics=[{"label": "Per device per month", "value": 33.71}],
    )
```

`build_result` handles the term schedule, indexation, TCV and review flags. Do
not reimplement those.

### Three things every `_normalise` must do

1. **Record provenance for every value.** `assumption(key, value, source)` where
   source is `rfp` / `user` / `derived` / `default`. Callers pass a `_sources`
   map; honour it.
2. **Raise `ValidationError` on input that cannot produce a meaningful
   estimate** — no scope, an unsupported country, an unknown enum. Rejecting is
   always better than guessing.
3. **Never silently substitute.** A default is fine; an *unrecorded* default is
   not.

### The insight

`run.insight` is where a pack earns its place. It is not a summary of the
numbers — the artefacts already show those. It is the structural observation a
good architect makes on the third read:

> Every country is sized by the SLA coverage floor, not incident volume. 18 FTE
> of standing presence exceeds the actual workload.

> Hardware amortisation is 67% of the annual cost. This is a capital-shaped
> deal; squeezing the service model cannot move the price much.

If a pack has nothing to say here, the model is probably too shallow.

### The bill of materials

Every pack returns one, via `bom=_bom(p)`. Even a service desk buys something —
ITSM seats and telephony. Each line is a quantity, a unit and a **unit cost**;
never a price, because the BoM is what finance reads before any commercial
adjustment.

```python
bom_line("Wireless access point", aps, "each", R.AP_UNIT_COST,
         rolls_into="Hardware", phase="one-off", category="Network hardware")
```

`rolls_into` names the cost line the item belongs to, and this is the part that
matters: `verify()` sums every line carrying a given label and checks it equals
that cost line. A tagged group must cover its cost line **in full**.

Build the BoM from the rate card independently, not by decomposing the cost
lines you already computed. Deriving one from the other makes the check vacuous.
The point is that two routes to the same number have to meet — the same reason
the managed-LAN workbook is recalculated against the Python rather than trusted.

Two traps worth knowing before you hit them:

- **Do not round quantities.** `bom_line` stores `qty` at full precision for the
  same reason `resource()` stores FTE unrounded. 34.80004975845411 agent seats
  rounds to 34.8, and 34.8 × the licence rate no longer equals the cost line.
- **Match the phase to the cost block.** `one-off` reconciles against
  `deployment.cost_lines`, `recurring` against `run.cost_lines`. If the pack
  ramps, recurring cost lines are *year one*, so the BoM must be year one too —
  quote steady state and the same workbook contradicts itself two sheets apart.

Leave `rolls_into` empty for a line that is genuinely informational. Do not
leave it empty to dodge a failing check.

## 4 · cases.py

Three or four scenarios spanning the parameter space — the realistic one, a
small one, and one that exercises the edges (a different tier, an option turned
off). All must be valid input; the suite tests rejection separately.

## 5 · Run the gate

```bash
python tests/test_contract.py     # every pack, every case, all three writers
python tests/test_cost_model.py   # workbook formulas recalculated vs Python
python tests/test_settings.py     # settings precedence, including your pack's
```

The first discovers every installed pack, runs each through identical
assertions, and drives all three artefact writers with the output. The second
renders each pack's cost model, recalculates it headlessly in LibreOffice and
compares the formula results against the pack — because a spreadsheet formula
that disagrees with the Python is a wrong number in a document with our name on
it, and no amount of Python testing would ever see it.

The third proves that a parameter stated for the deal still beats a saved
setting once your pack is in the mix.

A pack that passes all three can be consumed by the whole skill.

---

## What a pack must never do

- **Format currency or dates.** Return numbers; the writers format.
- **Know about artefacts.** No pack imports a writer.
- **Import another pack.** Shared logic belongs in `core/`.
- **Reimplement indexation or TCV.** `build_result` owns those.
- **Recommend a bid position.** Produce a cost and show the working.

---

## Sizing the work

The first pack costs a day because the interface is being discovered with it.
Subsequent packs are half a day of modelling and an hour of plumbing — and the
plumbing is mostly copying `_normalise` and changing the fields.

The expensive part is never the code. It is agreeing the cost drivers with the
people who own the real rate card.
