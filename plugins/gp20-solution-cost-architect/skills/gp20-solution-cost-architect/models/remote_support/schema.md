# Remote Support tower — parameter schema

**Lot:** second and third line, monitoring, automation — everything closed
without a site visit
**Currency:** GBP (£) · **Default term:** 3 years
**Status:** ILLUSTRATIVE MODEL — rates are synthetic, not NSC pricing

---

## 1 · Inputs

### 1.1 The estate — shared, see `core/estate.py`

Same values as every other lot in the bid. `user_count`, `devices`, `aps_total`
and `switch_count` size the monitoring headcount.

### 1.2 Intake

| Param | Key | Type | Default |
|---|---|---|---|
| Escalations per annum | `escalations_pa` | float | Derived from estate |

**Take this from the `service-desk` lot** when one exists — its
`run.drivers.escalations_pa` is the number, and it is set by that lot's FCR
target. The fallback derivation (1.6 per user + 0.24 per device per annum) is
for a remote lot priced without a desk lot beside it, and it will not match a
desk that has been priced to a specific FCR.

### 1.3 Service

| Param | Key | Type | Default |
|---|---|---|---|
| Capability | `capability` | `basic` \| `standard` \| `advanced` | `standard` |
| Tiers | `tiers` | `l2` \| `l2_l3` | `l2_l3` |
| Coverage window | `coverage` | `8x5` \| `12x5` \| `24x7` | `8x5` |
| Monitoring | `monitoring` | `none` \| `reactive` \| `proactive` | `reactive` |
| Delivery country | `delivery_country` | `UK` \| `DE` \| `FR` \| `NL` \| `PL` | `PL` |

---

## 2 · Model

### 2.1 Handling

```
automated   = escalations_pa × automation[capability]
handled     = escalations_pa − automated
l2_cases    = handled × (1 − l3_share)
l3_cases    = handled × l3_share            # 0.22 when tiers = l2_l3
l2_fte      = l2_cases × 38min × effort[capability] ÷ 1450 ÷ 0.72
l3_fte      = l3_cases × 95min × effort[capability] ÷ 1450 ÷ 0.72
```

Automation reduces the **intake**, not the handling time — an incident closed by
a runbook never reaches an engineer. Higher capability also raises the effort
multiplier (1.00 / 1.12 / 1.30), because what remains is the harder work.

### 2.2 Monitoring

```
noc_fte = (aps ÷ 2600 + switches ÷ 900 + devices ÷ 14000)
        × monitoring_level          # none 0.0 · reactive 0.6 · proactive 1.0
```

Headcount comes from the estate, not the queue. Monitoring is a watching
function; it costs the same on a quiet night.

### 2.3 Coverage floor

The floor here is **per hub**, not per country or per language — a remote
function is centralised by definition. That is why 24×7 costs a fraction of the
same window in `field-service`, and it is worth saying out loud whenever a
tender prices the two lots together.

---

## 3 · Cross-lot dependencies

This lot sits between two others and both directions are priced explicitly.

| Direction | Field | Must agree with |
|---|---|---|
| In | `escalations_pa` | `service-desk` → `run.drivers.escalations_pa` |
| Out | `capability` | `field-service` → `remote_capability` |

`core/bid.py` checks both. A field lot priced assuming `advanced` while this lot
is priced to deliver `standard` means somebody is carrying work nobody costed —
and neither lot's own contract check can see it.

**The trade this lot exists to surface:** buying capability here costs more here
and saves more in the field. It only pays back where field service is sized by
dispatch volume. Where the field lot is coverage-floor bound, the engineers are
already standing there and better remote support saves nothing.
