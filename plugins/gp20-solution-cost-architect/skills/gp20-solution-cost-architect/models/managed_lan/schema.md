# GP-20 Solution & Cost Architect — Parameter Schema

**Scope:** Managed LAN / WLAN rollout with attached field-support wrap
**Currency:** GBP (£) · **Default term:** 3 years
**Status:** ILLUSTRATIVE MODEL — rates are synthetic, not NSC pricing

---

## 1 · Inputs

### 1.1 Engagement
| Param | Key | Type | Default | Source in RFP |
|---|---|---|---|---|
| Client name | `client_name` | str | — | Cover page |
| RFP reference | `rfp_ref` | str | — | Cover page |
| Contract term (years) | `term_years` | int | 3 | Commercial section |
| Start date | `start_date` | date | — | Timetable |

### 1.2 Estate
| Param | Key | Type | Default | Notes |
|---|---|---|---|---|
| Sites by band | `sites.{small,medium,large,campus}` | int | — | Small ≤50 users, Medium 51–250, Large 251–1000, Campus >1000 |
| APs per site override | `aps_per_site_override` | dict\|null | null | Else derived from band |
| Access switches total | `switch_count` | int | derived | Derived at 1 per 24 ports if absent |
| Total end users | `user_count` | int | derived | Drives service-desk sizing |
| Country mix | `country_mix` | dict[str,float] | — | Shares must sum to 1.0. Supported: `UK, DE, FR, NL, PL` |

**Derived AP counts per site band** (when no override): small 4, medium 14, large 45, campus 140.

### 1.3 Deployment
| Param | Key | Type | Default |
|---|---|---|---|
| Survey type | `survey_type` | `predictive` \| `onsite` \| `hybrid` | `hybrid` |
| Install window | `install_window` | `business_hours` \| `out_of_hours` | `business_hours` |
| Rollout duration (months) | `rollout_months` | int | 9 |
| Existing cabling reused | `reuse_cabling` | bool | true |

### 1.4 Service (the field-support wrap)
| Param | Key | Type | Default |
|---|---|---|---|
| SLA tier | `sla_tier` | `bronze` \| `silver` \| `gold` \| `platinum` | `silver` |
| Coverage | `coverage` | `8x5` \| `12x5` \| `24x7` | `8x5` |
| Spares strategy | `spares_strategy` | `none` \| `central` \| `regional` \| `onsite` | `regional` |
| Monitoring included | `monitoring` | bool | true |
| Service desk included | `service_desk` | bool | true |

**SLA tier → on-site response:** bronze = next business day · silver = 8h · gold = 4h · platinum = 2h

### 1.5 Commercials
| Param | Key | Type | Default |
|---|---|---|---|
| Target margin % | `margin_pct` | float | 0.22 |
| Contingency % | `contingency_pct` | float | 0.05 |
| Annual indexation % | `indexation_pct` | float | 0.03 |

---

## 2 · Model

### 2.1 Deployment effort (one-off)
```
aps_total        = Σ (sites_band × aps_per_site_band)
survey_days      = aps_total × survey_rate[survey_type]
install_days     = aps_total × ap_install_rate
                 + switch_count × switch_install_rate
                 + sites_total × mobilisation_days_per_site
design_days      = design_fixed + sites_total × design_per_site
pm_days          = (survey + install + design) × pm_overhead_pct
ooh_uplift       = ×1.35 if install_window = out_of_hours
```

### 2.2 Run-rate sizing (per annum)
```
incidents_pa     = aps_total × ap_incident_rate + switch_count × switch_incident_rate
field_fte        = incidents_pa × hours_per_incident
                   ÷ productive_hours_pa
                   × sla_multiplier[sla_tier]
                   × coverage_multiplier[coverage]
noc_fte          = f(aps_total, coverage)              if monitoring
sd_fte           = user_count × sd_contact_rate ÷ productive_hours_pa   if service_desk
sdm_fte          = banded by contract value
```

**SLA multiplier:** bronze 1.00 · silver 1.15 · gold 1.40 · platinum 1.90
**Coverage multiplier:** 8x5 1.00 · 12x5 1.35 · 24x7 3.20

### 2.3 Resource location
- **Field FTE** distributed by `country_mix` (on-site presence must follow the estate)
- **NOC / service desk** centralised to the lowest-cost supported hub, unless `coverage = 24x7`, which splits across two hubs for follow-the-sun

### 2.4 Cost build
```
labour       = Σ (role_fte × loaded_day_rate[country,role] × working_days_pa)
travel       = incidents_pa × travel_cost[country]
hardware     = aps_total × ap_unit + switch_count × switch_unit
spares       = hardware × spares_pct[spares_strategy]
tooling      = sites_total × tooling_per_site
overhead     = (labour + travel) × overhead_pct
subtotal     = labour + travel + hardware + spares + tooling + overhead
contingency  = subtotal × contingency_pct
cost         = subtotal + contingency
price        = cost ÷ (1 − margin_pct)
```

---

## 3 · Outputs

| Output | Key | Notes |
|---|---|---|
| Deployment effort | `deployment.days_by_role` | Survey, install, design, PM |
| One-off price | `deployment.price` | Deployment + hardware |
| Run FTE by role | `run.fte_by_role` | Field, NOC, service desk, SDM |
| Resource locations | `run.locations[]` | country × role × FTE |
| Annual cost breakdown | `run.cost_breakdown` | Labour, travel, spares, tooling, overhead, contingency |
| Annual price | `run.price_pa` | Year 1, indexed thereafter |
| Monthly price | `run.price_pm` | |
| TCV | `summary.tcv` | One-off + Σ indexed annual over term |
| Assumption register | `assumptions[]` | Every value with `source`: `rfp` \| `user` \| `default` |

---

## 4 · Provenance rule

Every input carries a `source` tag:

- **`rfp`** — extracted from the document, with page/section citation
- **`user`** — supplied via the clarification dialogue
- **`default`** — model default, never silently applied; always surfaced in the assumption register

Any parameter that is `default` **and** materially affects price is flagged in the output for review.
