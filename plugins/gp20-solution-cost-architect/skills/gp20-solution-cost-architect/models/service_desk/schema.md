# Service Desk — parameter schema

**Currency:** GBP · **Default term:** 3 years
**Status:** ILLUSTRATIVE — synthetic rates, not NSC pricing

## Inputs

### Population
| Param | Type | Notes |
|---|---|---|
| `user_count` | int | **Required.** Supported user population |
| `device_count` | int | Optional. Devices generate contacts beyond the user count |

### Service
| Param | Values | Default |
|---|---|---|
| `languages` | list or comma string from `EN DE FR NL PL ES IT` | `["EN"]` |
| `coverage` | `8x5` / `12x5` / `24x7` / `24x7x365` | `8x5` |
| `tiers` | `l1_only` / `l1_l2` / `l1_l2_l3` | `l1_l2` |
| `self_service` | `none` / `knowledge_base` / `ai_assistant` | `knowledge_base` |
| `fcr_target` | 0.65 / 0.75 / 0.85 | 0.65 |
| `channel_mix` | dict over `phone email chat portal walk_up` | 42/24/18/14/2 |
| `delivery_country` | `UK DE FR NL PL` | `PL` |

### Commercials
`margin_pct` 0.24 · `contingency_pct` 0.05 · `indexation_pct` 0.03 · `onboarding_months` 3

## Model

```
contacts_pa = users × 6.4 + devices × 0.9, less deflection
agent_hours = contacts × blended AHT × FCR uplift ÷ occupancy (0.72)
demand_fte  = agent_hours ÷ productive hours (1,380)

per language:
  floor = PRESENCE_FTE_PER_SEAT[coverage]      # 1.15 / 1.70 / 4.80 / 5.20
  fte   = max(demand share, floor)             # ← the language coverage floor
```

Escalation adds second line at 18% of contacts (38 min) and, where in scope,
third line at 22% of those (95 min). Team leads at 1 per 12 agents; SDM banded
on labour. Tooling is ITSM and telephony per agent, plus the self-service
platform.

**The structural point:** contact volume sets how many agents the work needs;
every language needs a staffed seat across the coverage window regardless. At
24×7 that is 4.8 FTE per language before anyone calls.

## Outputs

Standard contract shape. `unit_metrics` carries **per user per month** and
**per contact**.

## Overlap with other packs

`managed-lan` and `daas` include a simplified service desk. If this pack prices
the desk, set `service_desk: false` on the other, or it is counted twice.
