# IaaS Compute — parameter schema

**Currency:** GBP · **Default term:** 3 years
**Status:** ILLUSTRATIVE — synthetic rates, not NSC pricing

## Inputs

### Estate
| Param | Type | Notes |
|---|---|---|
| `instances` | dict | `small` `medium` `large` `xlarge` `gpu` |
| `nonprod_ratio` | float | Non-prod as a multiple of prod; runs 42% of hours |
| `storage_tb` | dict | `performance` `standard` `archive` |
| `egress_tb_pm` | float | Monthly egress |
| `workloads` | int | Migration units; derived at 1 per 3 instances if absent |

### Service
| Param | Values | Default |
|---|---|---|
| `commitment` | `on_demand` / `reserved_1yr` / `reserved_3yr` | `on_demand` |
| `availability` | `single_az` / `multi_az` / `multi_region` | `single_az` |
| `managed_level` | `unmanaged` / `monitored` / `fully_managed` | `monitored` |
| `backup_retention_days` | 7 / 30 / 90 / 365 | 30 |
| `ramp_months` | int | 12 |
| `delivery_country` | `UK DE FR NL PL` | `PL` |

### Commercials
`margin_pct` 0.16 · `contingency_pct` 0.04 · `indexation_pct` 0.02

## Model

```
compute = (prod + nonprod × 0.42) × hourly × 8760
          × commitment_discount × availability_mult
storage = Σ TB × tier rate × 12 × availability_mult
egress  = TB/month × 12 × rate
backup  = TB × rate × 12 × (1 + retention_days/90 × 0.4)
labour  = instances ÷ INSTANCES_PER_ENGINEER[managed_level] + SDM
```

### The ramp

**This is the pack that made the contract grow a `year_profile`.** Workloads
land evenly across `ramp_months`, so consumption in month *m* is
`min(1, m / ramp_months)`. Averaged per contract year, that gives the year's
share of steady state.

`price_pa` is the **year-one** charge. `run.year_profile` carries the
multipliers for later years, and `build_result` applies them before indexation.
An 18-month ramp over five years produces roughly `[1.0, 2.58, 2.77, 2.77, 2.77]`
— year one is a third of steady state, and quoting it as the ongoing charge
would understate the deal by two thirds.

## Outputs

Standard contract shape. `unit_metrics` carries **per vCPU per month at steady
state** and the **steady-state annual charge** — both derived from `price_pa ÷
year-one fraction`, so they reconcile with the final year of the schedule.

## The insight this pack exists to surface

A three-year reserved commitment is the largest discount available and the
largest way to overpay. It is bought on day one against a ramp that has not
happened yet, so a portion of the committed compute is idle for the first years
of the term. The pack quantifies that and proposes the one-year alternative.
