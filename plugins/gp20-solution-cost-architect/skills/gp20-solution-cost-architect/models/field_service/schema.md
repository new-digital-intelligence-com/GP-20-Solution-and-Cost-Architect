# Field Service tower — parameter schema

**Lot:** on-site engineering attendance — break-fix dispatch, IMAC, smart hands
**Currency:** GBP (£) · **Default term:** 3 years
**Status:** ILLUSTRATIVE MODEL — rates are synthetic, not NSC pricing

Not in this lot: the parts fitted (→ `logistics`), the diagnosis that dispatched
the engineer (→ `remote-support`), the programme governing it (→
`project-management`).

---

## 1 · Inputs

### 1.1 The estate — shared, see `core/estate.py`

State once for the whole bid; every lot consumes the same values.

| Param | Key | Type | Notes |
|---|---|---|---|
| Client name | `client_name` | str | Cover page |
| RFP reference | `rfp_ref` | str | Cover page |
| Sites by band | `sites.{small,medium,large,campus}` | int | Small ≤50 users, Medium 51–250, Large 251–1000, Campus >1000 |
| Country mix | `country_mix` | dict[str,float] | Shares; `UK, DE, FR, NL, PL` |
| Total users | `user_count` | int | Derived from bands if absent |
| Devices | `devices` / `device_total` | dict / int | Generates incidents |
| Access points | `aps_total` | int | Derived from bands if absent |
| Access switches | `switch_count` | int | Derived if absent |

### 1.2 Service

| Param | Key | Type | Default |
|---|---|---|---|
| On-site response | `sla_tier` | `bronze` \| `silver` \| `gold` \| `platinum` | `silver` |
| Coverage window | `coverage` | `8x5` \| `12x5` \| `24x7` | `8x5` |
| Remote capability in front | `remote_capability` | `none` \| `basic` \| `standard` \| `advanced` | `standard` |
| IMAC in scope | `imac_included` | bool | true |
| Mobilisation (months) | `mobilisation_months` | int | 4 |

**SLA tier → on-site response:** bronze = next business day · silver = 8h ·
gold = 4h · platinum = 2h. Gold and platinum trigger the coverage floor.

### 1.3 Commercials

`margin_pct` 0.22 · `contingency_pct` 0.05 · `indexation_pct` 0.03 —
all normally supplied by saved settings.

---

## 2 · Model

### 2.1 Dispatch volume

```
incidents_pa  = aps × 0.32 + switches × 0.55
              + devices × 0.41 + sites × 1.8
dispatches_pa = incidents_pa × (1 − remote_fix_rate[remote_capability])
hours         = dispatches_pa × 3.2
              + users × 0.22 × 1.1            if imac_included
demand_fte    = hours ÷ 1450
              × sla_multiplier[sla_tier]
              × coverage_efficiency[coverage]
```

`coverage_efficiency` is 1.00 / 1.10 / 1.25 — a shift-handover and
out-of-hours productivity penalty, **not** the cost of 24×7. That lives in the
floor. Applying the floor's factor to volume as well charges twice for one
commitment.

### 2.2 The coverage floor

```
posts_c = ceil(sites × share_c ÷ 60)        if sla_tier ∈ {gold, platinum}
floor_c = posts_c × presence_fte[coverage]  # 1.15 / 1.70 / 4.80
fte_c   = max(demand × share_c, floor_c)
```

Where `floor_c` binds, the country is staffed for the clock rather than the
queue, and improving remote support does not reduce this lot at all.

### 2.3 Cost build

```
labour      = Σ fte_c × field_day_rate_c × 220  + fsm
travel      = dispatches × travel_cost_c
vehicles    = field_fte × 6400
overhead    = (labour + travel) × 0.12
contingency = subtotal × contingency_pct
cost        = subtotal + contingency
price       = cost ÷ (1 − margin_pct)
```

---

## 3 · Cross-lot dependency

This lot's volume is set by another lot's capability. `remote_capability` must
match what `remote-support` is actually being priced to deliver — if the two
lots disagree, one of them is wrong and the bid does not add up. State the
assumption explicitly when presenting either lot.
