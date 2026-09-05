# ROI and Time-Saving Calculation

## Inputs
- occurrences per period;
- average manual minutes per occurrence;
- realistic automatable fraction (0–1);
- expected exception/manual-review fraction;
- loaded labor cost per hour if available;
- implementation cost range if available;
- recurring operating cost range if available.

## Core formulas
`manual_hours_month = occurrences_month * minutes_each / 60`

`gross_hours_saved = manual_hours_month * automatable_fraction`

`net_hours_saved = gross_hours_saved * (1 - exception_fraction)`

`monthly_labor_benefit = net_hours_saved * loaded_hourly_cost`

`annual_net_benefit = 12 * (monthly_labor_benefit - monthly_operating_cost)`

`roi_percent = ((annual_net_benefit - implementation_cost) / implementation_cost) * 100`

`payback_months = implementation_cost / max(monthly_labor_benefit - monthly_operating_cost, epsilon)`

## Rules
- Do not calculate monetary ROI without cost evidence.
- Show ranges when inputs are ranges.
- Keep labor savings separate from “cash savings”; freed capacity is not automatically headcount reduction.
- Show assumptions beside results.
