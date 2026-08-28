# Logistics tower — parameter schema

**Lot:** spares, stock, shipping, RMA and repair, staging, disposal
**Currency:** GBP (£) · **Default term:** 3 years
**Status:** ILLUSTRATIVE MODEL — rates are synthetic, not NSC pricing

Not in this lot: the engineer who fits the part (→ `field-service`), or the
diagnosis that decided one was needed (→ `remote-support`).

---

## 1 · Inputs

### 1.1 The estate — shared, see `core/estate.py`

`aps_total`, `switch_count` and `devices` give the hardware value the pool is
sized against. `country_mix` and `sites` decide how many stocking locations a
strategy implies.

### 1.2 Service

| Param | Key | Type | Default |
|---|---|---|---|
| Stock strategy | `stock_strategy` | `none` \| `central` \| `regional` \| `forward` \| `onsite` | `central` |
| Field lot's fix tier | `fix_tier` | `bronze` \| `silver` \| `gold` \| `platinum` | — |
| Dispatches per annum | `dispatches_pa` | float | Derived from estate |
| Disposal | `disposal` | `none` \| `recycle` \| `secure_erase` | `recycle` |
| Staging in scope | `staging_included` | bool | true |
| Devices staged per annum | `staging_devices_pa` | float | fleet ÷ 4 |

`fix_tier` and `dispatches_pa` both come from the **field service lot**. Neither
is used to change this lot's arithmetic — `fix_tier` exists so the pack can
report an incoherent commitment rather than silently price around it.

---

## 2 · Model

### 2.1 Stock

```
pool_value = hardware_value × pool_pct[stock_strategy]
carrying   = pool_value × 0.185          # capital, insurance, obsolescence
refresh    = pool_value ÷ 5              # the pool is itself replaced
locations  = 1 (central) · 2 (regional)
           · one per country (forward) · one per large/campus site (onsite)
```

### 2.2 Movement and repair

```
parts        = dispatches_pa × 0.62      # not every visit consumes a part
shipping     = parts × shipment_cost[tier implied by strategy]
returned     = parts × 0.86
rma_handling = returned × 31
repaired     = returned × 0.58 × (1 − 0.41 warranty recovery)
repair       = repaired × unit_value × 0.34
```

### 2.3 What each strategy can actually support

| Strategy | Supports |
|---|---|
| `none` | Best endeavours, vendor RMA only |
| `central` | Next business day |
| `regional` | Same day in region |
| `forward` | 4 hours in country |
| `onsite` | 1 hour at stocked sites |

---

## 3 · Cross-lot dependency

A committed fix time is a **stock** commitment before it is a labour one. Where
`field-service` commits to gold (4h) and this lot holds central stock, the
commitment cannot be met — and neither lot's own numbers show it. `core/bid.py`
enforces the minimum: bronze/silver → `central`, gold → `forward`, platinum →
`onsite`.
