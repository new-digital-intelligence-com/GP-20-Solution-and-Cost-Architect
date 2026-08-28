# GP-20 · Demo Script

**Runtime:** 8–10 minutes · **Audience:** NSC Solution & Sales leadership

---

## Before you start

- [ ] Skill loaded; `/gp20-solution-cost-architect` resolves
- [ ] `samples/RFP_Aurelian_Global_Managed_LAN.docx` to hand
- [ ] `assets/WLAN_Cost_Estimator.xlsx` open in a second window — you will switch to it
- [ ] `python3 scripts/test_end_to_end.py` run once today (24 checks, all green)
- [ ] Python available; `openpyxl` and `python-pptx` importable (preflight checks both)

**Open with the disclaimer, not with the tool.** One sentence, in the first
fifteen seconds:

> The rate card behind this is synthetic. What I'm showing is the workflow from
> RFP to costed solution — not a price, and not NSC's numbers.

Say it once, properly, and the room will stop litigating the rates and start
watching the process. Skip it and you will spend the whole demo defending
£540 a day.

---

## The six beats

### 1 · An RFP lands  ·  ~40s

Invoke the skill, upload the sample RFP. Say what it is: a real-shaped tender
for a managed LAN and WLAN refresh across 101 European sites, five countries,
five-year term.

> This is the document a Solution Shaper gets on a Monday morning.

### 2 · It reads the document  ·  ~90s

Let the extraction table land. Do not talk over it.

Then point at the **Source** column — that is the whole argument:

> Every number traces back. Site counts come from Annex A, and it preferred the
> annex over the body text, which says "approximately 100". Access-point counts
> aren't in the RFP at all, so they're marked derived, from our design standard
> per size band. Nothing here is invented and nothing is silent.

### 3 · It knows what it's missing  ·  ~90s

Four parameters are absent from the RFP. Let the clarification dialogue run and
answer as the Solution Shaper would: **24×7, regional spares, out-of-hours
install, hybrid survey.**

Call out *why* it is asking rather than assuming:

> The RFP commits to a four-hour on-site response but never states the coverage
> window for field engineering — only for monitoring. That single gap is worth
> more than twenty million pounds over the term, so it asks rather than guesses.

### 4 · It sizes and costs the solution  ·  ~90s

Roughly £2.14m one-off, £4.87m a year, £28.0m TCV, 31 FTE across five countries.

Move quickly. The numbers are not the point — the next beat is.

### 5 · It tells you something you didn't ask for  ·  ~2 min

**This is the demo.** Slow down here.

> Look at the resource model. Every one of those five countries is sized by the
> SLA coverage floor, not by incident volume. Eighteen FTE of standing presence
> exceeds the actual workload — because you cannot deliver a four-hour on-site
> response in the Netherlands from a pool in Warsaw. You need people standing
> by, and a 24×7 rota costs about 4.8 heads per post.
>
> No calculator tells you that. It's the observation a good Solution Architect
> makes on the third read.

Then land the consequence:

> So the recommendation writes itself: pool regionally, or relax the tier in the
> low-density countries. Same committed response time, materially less cost.

### 6 · Change one thing  ·  ~90s

Ask for the sensitivity run: **Silver, 8×5.**

| | Gold / 24×7 | Silver / 8×5 |
|---|---|---|
| Total FTE | 30.98 | 6.89 |
| Annual | £4,871,464 | £836,505 |
| **5-year TCV** | **£28,008,002** | **£6,586,061** |

> Twenty-one million pounds of difference, in about ten seconds, with the
> reasoning attached. That is the conversation a Solution Shaper wants to be
> having with a client — and today it takes a week.

Close by generating the pricing form and the deck.

---

## If you have another two minutes

Switch to `WLAN_Cost_Estimator.xlsx`. Change the SLA tier on the **Input** sheet
and let them watch **Output** recalculate.

> The model isn't inside the AI. It's a workbook Solution and Finance own, and
> the skill drives it. If your rates change, you edit the Rates sheet — nobody
> touches a prompt.

That answers the governance question before it is asked.

---

## Questions you will get

**"Where did these rates come from?"**
They're synthetic, and deliberately so. The structure is what's on trial today.
Swapping in the real rate card is one sheet and no logic changes.

**"Our field engineering doesn't work like that."**
Good — that's the conversation worth having. The coverage floor, the incident
rates and the shift ratios are all assumptions in one file. Tell us the real
ones and it re-costs in minutes.

**"Could it read our actual RFPs?"**
That's exactly what we want next. Three or four past tenders — ideally one won,
one lost — plus the pricing sheets that went with them.

**"Does it decide the price?"**
No. It produces a cost and shows its working. Margin, bid position and
commercial strategy stay with the humans — the skill is explicitly barred from
recommending them.

**"How long did this take?"**
Days. Which is the point: the same pattern applies to any offering with a
definable cost model. Managed LAN is the first, not the only one.

---

## Do not

- **Do not defend the numbers.** They are illustrative. Say so and move on.
- **Do not let the estimator become the demo.** The workbook is a supporting
  actor; the extraction, the clarification and the observation are the show.
- **Do not skip beat 5** for time. Cut beat 4 instead — the cost breakdown is
  the least interesting minute in the demo.
- **Do not promise a production date.** Bring the questions in
  `reference/OPEN_QUESTIONS.md` instead.
