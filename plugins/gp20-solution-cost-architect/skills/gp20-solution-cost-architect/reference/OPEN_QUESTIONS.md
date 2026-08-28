# GP-20 · Open questions

What we need from NSC to move this from mock-up to pilot. Ordered by what blocks
the most downstream work.

## Blocks everything else

1. **Three to five past RFPs** in the field-services or managed-network space —
   ideally one won, one lost, one no-bid — with the proposal and internal
   pricing sheet that went with each. Anonymised is fine. Without these we are
   designing against an invented document shape.
2. **The current pricing tool.** Excel, in-house application, third party —
   whichever it is, we need to see one deal priced end to end. This is the
   single highest-value artefact NSC can hand over.
3. **WPC.** Confirm the acronym, the format, who owns it, and how often it
   changes.

## Shapes the model

4. **Real cost drivers.** Which of these actually drive a field-services price
   at NSC: loaded day rates by country, travel, spares, tooling, coverage
   overhead, management, contingency, target margin? What are we missing?
5. **Configuration rules.** Documented constraints — "SLA tier N requires N+1
   spares", regional coverage minima, incompatible option combinations. Where do
   they live?
6. **Coverage floor.** Our model assumes a committed on-site response requires
   standing local presence (~4.8 FTE per 24×7 post). Is that how NSC actually
   resources it, or is there a pooling or subcontract model we should reflect?
7. **Service catalogue.** Format, ownership, update cadence, country variants.

## Shapes the output

8. **Canonical templates** for the pricing form and the proposal deck. The
   Phase 1 diagram says "Solution (Excel)" and "Proposal (PPT/Word)" — we need
   the real ones.
9. **Artefact granularity.** BoM at SKU level, service-line level, or both?
   Does the architecture artefact need a diagram at proposal stage?
10. **Which artefacts are internal-only** and which go to the customer.

## Governance

11. **What must stay human.** Final cost sign-off? Assumptions? Risk premium?
    Our current position: the skill produces a cost and is barred from
    recommending a bid position — confirm that is the right line.
12. **Audit expectation.** Is per-parameter provenance (which page of which
    document each value came from) a requirement or a nice-to-have?
13. **Approval step.** Who signs off a GP-20 output before it reaches the
    Proposal Writer, and against what criteria?

## Delivery

14. **NDI tenant publish access** — required by the Acceptance Criteria for any
    Claude-fronted demo. Currently blocking acceptance, not build.
15. **Aurelian Global.** The tracker notes this was "requested by NSC for fast
    go-live Aurelian Global Solution Architecture". Is there a live account
    behind this, and can we see its RFP?
16. **Pilot success criteria.** What measurable result passes the gate — e.g.
    "AI-produced cost within X% of the Solution Shaper's on N of M pilot RFPs"?
