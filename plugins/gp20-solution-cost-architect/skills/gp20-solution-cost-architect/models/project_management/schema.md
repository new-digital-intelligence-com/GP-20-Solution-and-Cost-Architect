# Programme and Service Governance tower — parameter schema

**Lot:** transition into service, cross-lot governance, service management office
**Currency:** GBP (£) · **Default term:** 3 years
**Status:** ILLUSTRATIVE MODEL — rates are synthetic, not NSC pricing

**Excludes the per-lot delivery managers.** Every other tower already carries its
own Service Delivery Manager. This lot prices the layer above them. Pricing that
person here as well is the easiest mistake to make once governance is a lot of
its own, and no single lot's numbers reveal it.

---

## 1 · Inputs

| Param | Key | Type | Default |
|---|---|---|---|
| Delivery lots governed | `lots` | int | 1 |
| Transition complexity | `complexity` | `low` \| `standard` \| `high` | `standard` |
| Reporting | `reporting` | `standard` \| `enhanced` \| `regulated` | `standard` |
| Transition duration (months) | `transition_months` | int | 6 |
| Delivery country | `delivery_country` | UK/DE/FR/NL/PL | `UK` |

**`lots` excludes this lot.** A programme does not govern itself: a five-tower
award has four delivery lots plus this one, so `lots` is 4. `core/bid.py` checks
the figure against the lots actually present in the bid.

Estate fields (`sites`, `country_mix`, `user_count`) size the discovery effort.

---

## 2 · Model

### 2.1 Transition (one-off)

```
scope_days = 12 × countries + 26 × sites/100 + 4.5 × users/1000
lot_days   = 34 × lots ** 0.62
total      = (85 + lot_days + scope_days) × complexity_factor
```

The exponent is the whole point: **governance scales sub-linearly with lots.**
The second lot reuses the programme, the governance model, the reporting pack
and the client relationship built for the first.

Role split: programme manager 22% · transition manager 30% · PMO analyst 28% ·
service architect 20%.

### 2.2 Service management office (run)

```
smo_fte = (0.8 + 0.35 × lots ** 0.70 + 0.10 × countries)
        × reporting_factor          # 1.00 / 1.40 / 1.85
```

---

## 3 · The observation this lot exists to make

One programme governing four delivery lots takes far fewer transition days than
four separately-run programmes over the same estate, because each of those would
repeat the base mobilisation and its own discovery of the sites and countries.

State the comparison precisely in a response: it is against separate
*programmes*, not against a single supplier discounting. Framed loosely it reads
as padding; framed correctly it is the commercial argument for awarding the
whole stack to one supplier, and a competitor bidding two lots cannot match it.
