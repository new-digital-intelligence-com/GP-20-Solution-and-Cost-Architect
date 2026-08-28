# GP-20 — Solution & Cost Architect

NDI's GP-20 is a Claude plugin that turns a customer RFP into a costed solution. It reads the
tender, extracts every sizing parameter with a citation to the clause it came from, asks for
what only the bidder knows, runs the cost model for the relevant offering, and produces the
pricing form and the proposal deck.

> **Illustrative model.** Every rate card in this repository is synthetic. No output may be
> presented as NSC pricing.

## Command syntax

```
/gp20-solution-cost-architect Sample Input/RFP_Aurelian_Global_Managed_LAN.docx
```

Or without arguments — attach the tender and a rate card, and say what you want:

```
Run cost analysis for the attached RFP
```

## Installation

```
/plugin marketplace add new-digital-intelligence-com/GP-20-Solution-and-Cost-Architect
/plugin install gp20-solution-cost-architect@ndi-ai-employees
```

**Auto-update is off by default** for a third-party marketplace like this one — it defaults on
only for Anthropic's own. Until someone enables it, changes pushed here do not reach installed
copies. Turn it on in Customize → Plugins, or pull manually:

```
/plugin marketplace update ndi-ai-employees
```

## Repository structure

```
.
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   └── gp20-solution-cost-architect/
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── gp20-solution-cost-architect/
│               ├── SKILL.md
│               ├── core/            [workflow: read, estimate, write artefacts]
│               ├── models/          [one pack per offering — the arithmetic]
│               ├── assets/          [workbook + example artefacts]
│               ├── reference/        [process flow, demo script, open questions]
│               ├── samples/          [synthetic RFPs and rate card]
│               ├── tests/            [parity and contract tests]
│               └── tools/
├── Sample Input/                     [synthetic RFPs, site schedule]
├── Sample Output/                    [example pricing forms and proposal decks]
└── Templates/                        [rate card template, WLAN estimator]
```

The skill lives inside the plugin because Claude's loader blocks path traversal outside the
plugin root.

## How the model packs work

One workflow, pluggable arithmetic. Reading the RFP, citing the source, clarifying the gaps and
producing the artefacts is identical for every offering; each offering's numbers live in its own
pack under `models/`. Eight packs ship today: managed LAN, service desk, DaaS, IaaS compute,
field service, remote support, logistics, project management.

Adding an offering means adding a pack, not editing the workflow. See
`plugins/gp20-solution-cost-architect/skills/gp20-solution-cost-architect/reference/WRITING_A_PACK.md`.

## Skill updates

Edit `SKILL.md` (or a model pack) directly, then commit and push. `plugin.json` carries no
`version` field, so the plugin is versioned by commit SHA — **every push updates installations
that have auto-update enabled.** Add a `version` field if you want releases to be deliberate
rather than continuous.

## Tests

```bash
cd plugins/gp20-solution-cost-architect/skills/gp20-solution-cost-architect
python3 -m pytest tests/
```

`test_parity.py` is the one that matters: it checks the Python model and the generated Excel
workbook agree, so the two cannot drift.

## What it will not do

- **Invent a rate, a volume or a service level.** Anything the tender does not state is asked
  for, and anything derived says what it was derived from.
- **Absorb a non-compliant price.** If the priced solution does not meet a commitment the tender
  states, that is reported as an exposure, not smoothed over.
- **Present a figure as NSC pricing.** Every rate card here is illustrative.

## Demo

A 2-minute narrated walkthrough is on NDI's YouTube channel. The recording it was cut from and
the narration script live in `reference/DEMO_SCRIPT.md`.
