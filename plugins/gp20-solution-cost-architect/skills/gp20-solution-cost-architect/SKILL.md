---
name: gp20-solution-cost-architect
description: Turns an RFP into a costed solution with a pricing form and proposal deck. Reads the tender, extracts sizing parameters with source citations, clarifies what is missing through a structured dialogue, runs the cost model for the relevant offering, and produces the artefacts. Use when a customer RFP, ITT or tender needs sizing, resourcing or pricing — network, LAN, WLAN, managed connectivity, field support, device as a service, end-user computing, device refresh, service desk, helpdesk, IaaS, compute, cloud migration, hosting — or when the user asks for a solution cost, BoM, bill of services, TCV, or asks to "cost this RFP" or "size this deal".
argument-hint: "[path to RFP document]"
allowed-tools: Read Write AskUserQuestion Bash(python ${CLAUDE_SKILL_DIR}/core/*) Bash(python3 ${CLAUDE_SKILL_DIR}/core/*)
---

# GP-20 · Solution & Cost Architect

One workflow, many offerings. The skill owns reading, extraction, clarification,
artefacts and governance. Each offering's arithmetic lives in a **model pack**
under `models/`, owned by Solution and Finance.

> **Illustrative model.** Every rate card here is synthetic. Each artefact must
> carry the disclaimer and no output may be presented as real NSC pricing.

## Locating the scripts

Resolve the skill folder **once** and reuse it — the working directory is the
user's project, not the skill:

- **Claude Code:** `${CLAUDE_SKILL_DIR}`
- **Anywhere else** (chat, Cowork, Office add-ins): find the directory holding
  `core/run_estimate.py` — it sits beside this SKILL.md.

Call it `SKILL_DIR` below. Everything is Python; `openpyxl` and `python-pptx`
are the only dependencies and both are preinstalled where code execution runs.

---

## Opening move

Say what this does in two sentences, then ask for the RFP. Do not open with a
list of questions — the document answers most of them.

> I turn an RFP into a costed solution: I read the tender, pull out the sizing
> parameters, check with you on anything missing, then produce the resource
> model, the cost breakdown and a pricing form you can issue.
>
> Share the RFP and I'll start. A site schedule, asset list or rate card is
> welcome too.

If the user has no document, offer the samples in `samples/`.

---

## Workflow

### 1 · Settle the commercial settings

Margin, contingency, indexation and default term are not in the tender. They
belong to the business, they are the same across deals, and they are stored in
`gp20_settings.json` in the working directory.

```bash
python "$SKILL_DIR/core/settings.py" show
```

**If settings exist**, show them and ask — one **AskUserQuestion**, before
anything else — whether to reuse or change them. Reuse is almost always the
answer, so lead with it; the question exists so that the one time it is wrong,
it is caught before a price is issued rather than after.

**If there are none**, say nothing yet. Do not interrogate someone about margin
before they have shown you a document. Fold the missing settings into the
clarification round at step 5, where you are already asking questions, and offer
to save them at step 9.

```bash
python "$SKILL_DIR/core/settings.py" save '{"margin_pct": 0.25, "indexation_pct": 0.03}' "NSC bid team"
```

`run_estimate.py` applies saved settings on its own. You do not need to copy them
into `params.json`, and you should not: anything stated for this deal takes
precedence, so writing them in by hand only creates a way to override the tender
by accident. The run reports which settings it used.

### 2 · Read every input

Read the RFP in full before extracting anything, plus any annex, schedule or
rate card. Annexes usually override prose — a table totalling 101 beats a
paragraph saying "approximately 100".

```bash
python "$SKILL_DIR/core/read_docx.py" <file.docx>
```

Stdlib only. Do not reach for `python-docx` to read — it is often absent and pip
frequently cannot reach PyPI. Do not improvise a zip parser; the bundled reader
already handles tables, tabs and breaks. For `.xlsx` use `openpyxl` directly.

### 3 · Choose the model pack

The offering determines the cost model. See what is installed:

```bash
python "$SKILL_DIR/core/registry.py" list
python "$SKILL_DIR/core/registry.py" describe <key>     # params, gaps, options
```

Pick the pack the RFP is asking for and **state your choice and why** before
proceeding. If the tender is ambiguous, or spans more than one offering, ask.

**First ask whether the tender is lotted.** `registry.py list` groups packs into
two kinds and the answer decides which you use:

- **Lotted** — "Lot 1: field services, Lot 2: service desk" → use **towers**.
  Run the lots the tender asks for, then reconcile them:

  ```bash
  python "$SKILL_DIR/core/bid.py" lot1.json lot2.json lot3.json
  ```

  That check is not optional. Each lot passes its own contract check while the
  bid still fails to add up — different estates, contradictory hand-offs,
  different terms. None of it is visible one lot at a time.

- **Outcome** — "a managed LAN for 101 sites" → use an **offering** pack, which
  spans several towers internally.

**Describe the estate once.** Every tower consumes the same estate block —
sites, countries, users, devices. Write it once and reuse it verbatim across
lots; `core/estate.py` fingerprints it and `bid.py` fails if two lots disagree.

**Towers hand work to each other, and the tender hides it.** The service desk's
FCR target sets remote support's intake; remote support's capability sets field
service's dispatch volume. Price them against the same assumptions or one lot is
carrying work another has not costed. State the hand-off explicitly when you
present either side.

**A tender may also cover several offerings.** Devices *and* the network is two
packs, not one. Run them separately and present both, plus a combined TCV — do
not force one model to cover both.

**Watch for double-counting.** Some offerings contain others. `managed-lan` and
`daas` each include a simplified service-desk line, because a managed service
without one is not a service. If the tender also wants a full service desk —
multilingual, tiered, its own coverage window — then:

1. price the desk with the `service-desk` pack, **and**
2. set `service_desk: false` on the other pack,

or the desk is in the price twice. Say explicitly which pack owns the desk when
you present the result. The same rule applies to any future pack that embeds a
component another pack models in full.

**If no pack fits, stop.** Say plainly that no cost model exists for this
offering and describe what a pack would need. An improvised price is worse than
an honest gap.

### 4 · Extract parameters, with provenance

Read the pack's parameter schema (`models/<pack>/schema.md`) and build the
parameter set. Tag **every** value:

| Tag | Meaning |
|---|---|
| `rfp` | Stated in the document — cite the section |
| `user` | Supplied in conversation |
| `derived` | Computed from other stated values |
| `default` | Model default — nothing in the document supports it |

Show an extraction table before going further. Never silently fill a gap — a
number the client cannot trace is worse than a question.

### 5 · Clarify what is missing

The pack declares its own gaps. Read them:

```bash
python "$SKILL_DIR/core/registry.py" describe <key>
```

Each gap comes with options and, for every option, the commercial consequence.
Use **AskUserQuestion**, put the consequence in the option description, and lead
with whatever the RFP hints at. Batch related questions into one call.

Ask only about the pack's declared gaps and material parameters. Everything else
takes a documented default and is flagged later.

### 6 · Run the estimator

```bash
python "$SKILL_DIR/core/run_estimate.py" --pack <key> params.json > result.json
```

JSON goes to stdout, the human summary to stderr, so the redirect yields a clean
`result.json`. `--json` silences the summary. Include a `_sources` map so
provenance survives:

```json
{
  "client_name": "Aurelian Global Holdings plc",
  "term_years": 5,
  "sites": {"small": 62, "medium": 28, "large": 9, "campus": 2},
  "sla_tier": "gold",
  "coverage": "24x7",
  "_sources": {"sites": "rfp", "sla_tier": "rfp", "coverage": "user"}
}
```

Never compute costs yourself. The pack is the single source of truth, and a
figure reasoned out in prose will not match the artefacts. If the result fails
its contract check the tool says so — report that, do not patch around it.

### 7 · Present the result

Lead with shape, then money:

- **Scope** — `scope.headline`, whatever the pack put there
- **Service** — `service`
- **Transition** — effort and one-off price
- **Run** — resources by role and location, annual and monthly
- **TCV**, plus any `summary.unit_metrics` (per device per month, per site per
  month — usually the metric the client actually buys on)

Give the cost-to-price bridge alongside the TCV, not buried: `summary.total_cost`
is what delivery costs, `summary.margin_value` is what sits on top, `summary.tcv`
is what the client pays. Anyone reviewing a bid asks what the margin is being
taken on, and the three numbers together answer it before they ask.

Then surface **`run.insight`** verbatim if present. That is the pack's
architectural observation and it is usually the most valuable line on the page —
it is what separates an architect from a calculator.

Finish with `review_flags`: anything still resting on a model default.

### 8 · Offer a sensitivity run

Offer to re-run with one parameter changed before generating documents. The
client always asks "what if we relaxed X?", and answering in seconds with a full
delta is the point of the tool. The pack's material parameters are the obvious
candidates.

### 9 · Generate artefacts

**If more than one scenario has been run, ask which to price.** Never assume the
baseline — issuing a pricing form for a rejected scenario is invisible until a
client queries it. Name scenarios by their configuration, not "baseline" and
"alternative", and put the scenario in the filename.

```bash
python "$SKILL_DIR/core/write_pricing_form.py" result.json output/Pricing_Form_<scenario>.xlsx
python "$SKILL_DIR/core/write_cost_model.py"   result.json output/Cost_Model_<scenario>.xlsx
python "$SKILL_DIR/core/write_deck.py"         result.json output/Proposal_Deck_<scenario>.pptx
```

All three writers are offering-agnostic — they consume the contract shape, so
they work for every pack. Write into the user's working directory, never the
skill folder.

**Then offer to save the commercial settings**, if this run established any that
were not already stored:

```bash
python "$SKILL_DIR/core/settings.py" save '{"margin_pct": 0.25}' "NSC bid team"
```

Offer once, and only for parameters the user actually decided — not for values
the pack defaulted. Saving a default as though it were a decision is how a
number nobody chose ends up in force on every future deal.

**What each one is for**, because they are read by different people:

| Artefact | Reader | Contains |
|---|---|---|
| Pricing form | Commercial, and the client | Bill of services and **bill of materials** (two sheets), at price |
| Cost model | Finance, bid review | The audit trail — inputs, drivers, cost build, margin, schedule |
| Proposal deck | The client | The story: scope, insight, price |

The cost model is a **live workbook**. Costs are values, because the pack owns
the arithmetic. Margin, price, indexation, the schedule and contract value are
Excel formulas reading from amber input cells, so finance can flex a lever and
watch the schedule move without a rerun. Say so when you hand it over — a
reviewer who thinks it is a static dump will not use the thing that makes it
useful.

---

## Files

Relative to `SKILL_DIR`.

```
core/run_estimate.py       single entry point — always call this
core/registry.py           list / describe / detect packs
core/read_docx.py          stdlib .docx reader
core/settings.py           engagement settings — show / save / clear
core/estate.py             the shared estate every tower counts
core/bid.py                reconcile lots — run before issuing a lotted bid
core/write_pricing_form.py generic pricing form + bill of materials
core/write_cost_model.py   generic per-deal cost model (live formulas)
core/write_deck.py         generic proposal deck
core/contract.py           the pack interface
core/preflight.py          environment check — run when a script fails
models/<pack>/schema.md    that offering's parameters
tests/test_contract.py     conformance — every pack must pass
tests/test_cost_model.py   workbook formulas vs Python, recalculated headlessly
tests/test_settings.py     settings persistence and precedence
tests/test_bid.py          cross-lot reconciliation
samples/                   sample tenders and supporting data
reference/process_flow.puml  this workflow as a diagram (render_diagram.sh)
```

Every script forces UTF-8 output; `python -X utf8` is never needed. A
`UnicodeEncodeError` means you are running your own script, not a bundled one.

---

## Rules

1. **Cite or ask.** Every parameter traces to the RFP, the user, or a flagged default.
   A saved setting counts as the user — they did decide it, in an earlier session.
2. **Never invent scope.** Derive from a documented standard and label it `derived`.
3. **The pack owns the arithmetic.** Do not restate or adjust its numbers.
4. **Flag the defaults that move money**, every time.
5. **No pack, no price.** An unsupported offering stops the workflow.
6. **One estate per bid.** Lots that disagree on scope are not a bid.
7. **Disclaimer on everything.**
8. **Stop at the price.** Producing a cost is in scope; recommending a bid
   position, discount or commercial strategy is not.
