# DaaS — parameter schema

**Currency:** GBP · **Default term:** 4 years · **Default refresh:** 4 years
**Status:** ILLUSTRATIVE — synthetic rates, not NSC pricing

## Inputs

### Engagement
| Param | Type | Default |
|---|---|---|
| `client_name` | str | — |
| `rfp_ref` | str | — |
| `term_years` | int | 4 |
| `rollout_months` | int | 6 |

### Fleet
| Param | Type | Notes |
|---|---|---|
| `devices` | dict | `laptop_standard`, `laptop_performance`, `desktop`, `tablet`, `phone` |
| `user_count` | int | Derived from primary devices if absent; phones and tablets treated as secondary |
| `country_mix` | dict | Shares over `UK, DE, FR, NL, PL` |

### Service
| Param | Values | Default |
|---|---|---|
| `refresh_years` | 3 / 4 / 5 | 4 |
| `swap_sla` | `next_business_day` / `8h` / `4h` | `next_business_day` |
| `deployment_method` | `ship_to_user` / `desk_side` / `depot_collect` | `ship_to_user` |
| `image_strategy` | `standard` / `custom` / `per_persona` | `standard` |
| `accessories` | `none` / `basic` / `standard` / `premium` | `standard` |
| `disposal` | `buyback` / `recycle` / `none` | `buyback` |
| `service_desk` | bool | true |

### Commercials
`margin_pct` 0.19 · `contingency_pct` 0.04 · `indexation_pct` 0.03

## Model

**One-off:** image build (12 days per variant) + enrolment (18 min/device) +
deployment (12–45 min/device by method) + data migration (35 min/user) + PM
overhead, plus shipping and legacy collection.

**Annual:**
```
device_amortisation  = fleet hardware value / refresh_years
accessory_amort      = accessory value / 5
spare_pool           = hardware value × pool%[swap_sla] / refresh_years
break_fix            = swaps_pa × logistics cost[swap_sla]
labour               = technician FTE (swap volume) + service desk + SDM
software             = devices × MDM rate
asset_management     = fixed + per-device
buyback              = −(residual % by type) / refresh_years
```

`swaps_pa` rises with refresh age: `×(1 + 0.11 × (refresh_years − 3))`.

## Outputs

Standard contract shape, plus `summary.unit_metrics` carrying **per device per
month** — the metric DaaS is actually bought on.

## Provenance

Every input tagged `rfp` / `user` / `derived` / `default`. Price-material
defaults (`swap_sla`, `refresh_years`, `margin_pct`, `term_years`,
`deployment_method`) are flagged for review in every artefact.
