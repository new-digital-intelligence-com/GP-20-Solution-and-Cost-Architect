# GP-20 · Solution & Cost Architect

One skill, pluggable cost models. The workflow — read the RFP, extract with
citations, clarify the gaps, cost it, produce the artefacts — is identical for
every offering. Each offering's arithmetic lives in its own **model pack**.

> **Illustrative model.** Every rate card is synthetic. No output may be
> presented as NSC pricing.

---

## Why it is built this way

Roughly 80% of this skill does not vary by offering: reading documents,
provenance discipline, the clarification pattern, the artefact writers, the
governance rules. Only the cost model varies.

Forking the whole skill per offering would duplicate that 80% six or eight times
over and guarantee drift. Instead the skill is written once and each offering is
a folder:

```
models/
├── managed_lan/     Managed LAN / WLAN with field support   labour-shaped
├── daas/            Device as a Service                     capital-shaped
├── service_desk/    Service Desk and Remote Support         language-floor-shaped
└── iaas_compute/    IaaS Compute                            consumption-shaped
```

Four offerings, four genuinely different cost structures, one set of artefact
writers that knows about none of them.

Adding an offering is one folder. Fixing a bug is one place. A tender covering
two offerings runs two packs and sums the result.

**The AI Employee is the workflow. The cost model is data.** Solution and
Finance own the packs and version them; the skill does not change when a rate
does.

---

## Layout

```
SKILL.md                       the skill
core/
├── contract.py                the pack interface — read this first
├── registry.py                pack discovery: list / describe / detect
├── run_estimate.py            single entry point for every offering
├── read_docx.py               stdlib .docx reader (no python-docx needed)
├── write_pricing_form.py      generic pricing form
├── write_deck.py              generic proposal deck
└── preflight.py               environment + every-pack check
models/<offering>/
├── pack.py                    MANIFEST + estimate()
├── rates.py                   every constant
├── cases.py                   exercise cases for the conformance suite
└── schema.md                  the parameters, for humans
tests/
├── test_contract.py           conformance — every pack must pass
└── test_parity.py             a pack's workbook vs its Python model
tools/build_samples.py         regenerates the sample tenders (dev)
reference/WRITING_A_PACK.md    how to add the next offering
samples/                       one sample tender per pack
assets/templates/              example outputs, per pack — demo fallback
```

## Sample tenders

One per pack, all for the same fictional client so they can be compared:

| Tender | Pack it should select |
|---|---|
| `RFP_..._Managed_LAN.docx` | managed-lan |
| `RFP_..._Device_Services.docx` | daas |
| `RFP_..._Service_Desk.docx` | service-desk |
| `RFP_..._Data_Centre_Exit.docx` | iaas-compute |

Each states its authoritative figures in an annex and loosely in the prose, omits
that pack's declared gaps, and avoids naming the offering in a way that makes
selection trivial. Check detection with:

```bash
python core/read_docx.py samples/<file>.docx > /tmp/t.txt
python core/registry.py detect /tmp/t.txt
```

---

## Quick start

```bash
python core/preflight.py           # dependencies + every pack end to end
python tests/test_contract.py      # the conformance gate
python core/registry.py list       # what offerings are installed
```

Then in Claude: `/gp20-solution-cost-architect`, and give it a tender —
`samples/RFP_Aurelian_Global_Managed_LAN.docx` to start.

## Running a model directly

```bash
python core/run_estimate.py --pack managed-lan params.json > result.json
python core/write_pricing_form.py result.json output/Pricing_Form.xlsx
python core/write_deck.py         result.json output/Proposal_Deck.pptx
```

JSON to stdout, human summary to stderr — so the redirect yields a clean file
while you still see the numbers.

## Adding an offering

Read `reference/WRITING_A_PACK.md`, copy the shape of `models/daas/`, and run
`python tests/test_contract.py`. The suite discovers your pack automatically and
holds it to the same standard as the others.

## Dependencies

| Package | For | |
|---|---|---|
| `openpyxl` | pricing form | Required |
| `python-pptx` | proposal deck | Required |
| `python-docx` | regenerating sample tenders | Dev only |
| LibreOffice | workbook parity check | Optional |

No Node, no npm, no runtime package installation — so the same bundle runs in
Claude Code, Chat, Cowork and the Office add-ins.

## Scope

Produces a cost and shows its working. It does not recommend a bid position, a
discount or a commercial strategy — those stay with the humans.
