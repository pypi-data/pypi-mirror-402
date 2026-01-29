---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys']
inputDocuments: ['agent-instructions.md', '_bmad-output/analysis/brainstorming-session-2026-01-15.md', '_bmad-output/planning-artifacts/architecture.md', '_bmad-output/planning-artifacts/data-models.md']
workflowType: 'prd'
project_name: 'belt'
user_name: 'Mr Wizard'
date: '2026-01-19'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 1
  architecture: 1
  dataModels: 1
  agentInstructions: 1
classification:
  projectType: cli_tool
  domain: scientific
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - BELT Model Enhancements

**Author:** Mr Wizard
**Date:** 2026-01-19

## Success Criteria

### User Success

**Core "Aha!" Moment:**
> *"I can see exactly why Scenario B beats Scenario A — the transport carbon saved by drying outweighs the drying energy cost beyond 75km."*

**Specific User Outcomes:**
- Run 5-10 scenario variants and compare them meaningfully
- See OPEX broken down by category (labor, energy, materials, rent) — not one opaque number
- Understand transport costs ($ and carbon) as a function of distance, weight, and mode
- Compare scenarios across different time scales (annual vs. per-batch) without restructuring YAML
- Answer "what if I change X?" without creating a whole new scenario file

**Success Signals:**
- User can create a new scenario variant in < 5 minutes
- User can identify which variable drives the viability decision
- User trusts the output enough to share with investors/partners

### Business Success

**For Brine & Ember:**
- Confidently decide facility location based on transport/processing tradeoffs
- Build investor-ready analysis showing sensitivity to key variables
- Reduce "analysis paralysis" — know which modeling depth is sufficient

**For BELT as a Tool:**
- Useful for the seaweed→dashi→biochar use case first
- Extensible to other circular economy scenarios later
- Foundation for AI training on usage data (from brainstorming #56)

### Technical Success

| Enhancement | Success Metric |
|-------------|----------------|
| **MaterialInput + Transport** | Transport carbon appears as separate line item in output; user can vary distance and see impact |
| **Term (time scale)** | Same scenario YAML works for annual, monthly, or per-batch analysis via single config field |
| **OPEX categories** | Output shows breakdown: labor, energy, materials, rent, maintenance, logistics, other |
| **Scenario comparison** | Support 5-10 scenarios; diff view shows only what changed between scenarios |

### Measurable Outcomes

1. **Scenario creation time**: New variant in < 5 minutes
2. **Comparison clarity**: Side-by-side output shows profit + carbon + key drivers
3. **Transport visibility**: Carbon from transport is a separate, auditable number
4. **OPEX transparency**: At least 5 categories visible in financial breakdown
5. **Time scale flexibility**: Toggle between annual/batch without YAML restructuring

## Product Scope

### MVP — Minimum Viable Product

*The model enhancements that unlock the wet vs. dry seaweed question:*

1. **MaterialInput with Transport**
   - `cost_per_unit_usd` on material inputs
   - `transport_distance_km`, `transport_mode` (truck/rail/ship/none)
   - Transport carbon calculated and shown separately

2. **Term (Time Scale)**
   - Scenario-level `term` field: `annual` | `monthly` | `daily` | `per_batch`
   - All quantities interpreted in that time frame
   - Default: `annual`

3. **OPEX Categories**
   - Replace flat `opex_usd` with structured breakdown
   - Categories: labor, energy, materials, rent, maintenance, logistics, insurance, utilities, other
   - Calculation aggregates categories into total

4. **Updated viability.py**
   - Calculate transport emissions from MaterialInput
   - Sum OPEX categories
   - Include energy carbon intensity (currently modeled but not calculated!)

### Growth Features (Post-MVP)

*From brainstorming, prioritized:*
- Scenario diff view (`belt compare a.yaml b.yaml`)
- What-if explorer (`belt explore --vary transport_distance_km`)
- Calculation trace (`--explain` flag)
- Climatiq API integration for carbon intensity lookups

### Vision (Future)

- Dual-axis scatter plot visualization (profit × carbon)
- Multi-revenue stream dashboard
- AI-assisted scenario suggestions
- Certification package generator for carbon credits

## User Journeys

### Journey 1: "The Wet vs. Dry Decision"
**Mode:** Primary analysis — transport tradeoff

**Opening Scene:**
You're planning your first facility. The seaweed harvest site is 80km from the best processing location. You know wet seaweed is heavy and expensive to move, but drying costs energy and time.

**Rising Action:**
You create two scenarios in BELT:
- `scenario-wet-80km.yaml` — wet seaweed, full weight, 80km transport
- `scenario-dry-80km.yaml` — add drying process, 5:1 weight reduction, same 80km

You run both. BELT shows transport carbon, drying energy carbon, total OPEX breakdown.

**Climax:**
The output reveals: *"Drying wins at 80km — transport carbon savings (9.6 kg) exceed drying emissions (7.2 kg). Break-even is ~52km."*

**Resolution:**
You now know: **dry first, unless the facility is within 50km of harvest.** Decision made.

---

### Journey 2: "Japan vs. US Business Model"
**Mode:** Strategic comparison — fundamentally different models

**Opening Scene:**
You're weighing two paths:
- **US Model**: Buy seaweed → make dashi → pyrolysis (full vertical integration, you control everything)
- **Japan Model**: Partner with existing dashi producers → acquire their post-dashi waste → pyrolysis only (asset-light, but dependent on partnerships)

**Rising Action:**
You build two scenario families:
- `us-model-base.yaml` — includes harvest, dashi production, pyrolysis
- `japan-model-base.yaml` — starts at pyrolysis, feedstock is "acquired" with cost but no upstream processes

You compare CAPEX, OPEX breakdown, revenue streams, and carbon footprint.

**Climax:**
BELT shows:
- US Model: Higher CAPEX, but dashi revenue covers most OPEX → profitable if dashi sells
- Japan Model: Lower CAPEX, but entirely dependent on biochar + carbon credits → profitable only at scale

**Resolution:**
You see the risk/reward tradeoff clearly. US model is higher investment but more control. Japan model is asset-light but partnership-dependent. You choose to **start US, explore Japan partnerships later.**

---

### Journey 3: "Batch Planning for Seasonal Harvest"
**Mode:** Operational planning — time scale analysis

**Opening Scene:**
Seaweed harvest is seasonal (April–August). But your pyrolysis unit runs best continuously. You need to figure out: **how much storage do I need, and what does that cost?**

**Rising Action:**
You create scenarios with different `term` settings:
- `harvest-season.yaml` — term: `per_batch`, models one harvest cycle
- `annual-operation.yaml` — term: `annual`, models full year with storage

You vary storage OPEX (rent, refrigeration) and pyrolysis utilization.

**Climax:**
BELT shows the tradeoff:
- Running pyrolysis only during harvest: lower CAPEX, but 60% utilization → higher per-unit cost
- Continuous pyrolysis with storage: higher CAPEX (storage), but 95% utilization → lower per-unit cost

**Resolution:**
You find the **storage break-even point** — below X tons/year, seasonal makes sense. Above X, invest in storage for continuous operation.

---

### Journey 4: "Quick Scenario Variant"
**Mode:** Iteration — "what if?"

**Opening Scene:**
You have a working base scenario. An investor asks: *"What if energy prices rise 20%?"*

**Rising Action:**
You duplicate the scenario, tweak `opex.energy_usd` by 20%, run again.

**Climax:**
BELT's output shows profit drops from $45k to $38k — still viable, but margin shrinks.

**Resolution:**
You tell the investor: *"We have 15% margin cushion on energy prices before viability is threatened."* Confidence earned.

---

### Journey 5: "Presenting to an Investor"
**Mode:** Output consumer — confidence building

**Opening Scene:**
You're meeting with an investor who wants to see the numbers. They're skeptical of carbon claims.

**Rising Action:**
You show them BELT output:
- OPEX breakdown by category (labor, energy, materials, transport)
- Carbon breakdown (process emissions, transport emissions, carbon locked)
- Comparison of 3 scenarios showing sensitivity to key variables

**Climax:**
The investor sees: *"Transport is only 8% of your carbon footprint, but 22% of OPEX. That's your optimization lever."*

**Resolution:**
Investor says: *"I can see where the numbers come from. This is credible."* Trust established.

---

### Journey 6: "Something's Wrong"
**Mode:** Debug — error recovery

**Opening Scene:**
You run a scenario and the profit is wildly negative. That can't be right.

**Rising Action:**
You look at BELT's output breakdown:
- Per-transformation financials show pyrolysis OPEX is 10x expected
- You check the YAML — typo: `energy_usd: 50000` instead of `5000`

**Climax:**
You fix the typo, re-run. Numbers make sense now.

**Resolution:**
You're grateful BELT shows **per-transformation breakdown**, not just totals. The bug was findable.

---

### Journey 7: "Purchase vs. Lease Pyrolysis Unit"
**Mode:** Capital strategy — CAPEX/OPEX tradeoff

**Opening Scene:**
You're deciding whether to buy a pyrolysis unit ($150k) or lease one ($2k/month). Buying means you own it, but it's a big upfront hit. Leasing is lighter, but adds ongoing OPEX forever.

**Rising Action:**
You create two scenarios:
- `pyrolysis-owned.yaml` — CAPEX: $150k, OPEX includes maintenance only
- `pyrolysis-leased.yaml` — CAPEX: $0, OPEX includes $24k/year lease + maintenance

You run both for Year 1, Year 3, Year 5 projections.

**Climax:**
BELT shows:
- Year 1: Leased is +$126k cash flow better (no upfront)
- Year 3: Break-even — cumulative costs equal
- Year 5: Owned is +$48k better (lease keeps paying, owned is "free")

**Resolution:**
You see the crossover point: **if you're confident in 3+ years of operation, buy. If testing the market, lease.** The OPEX category breakdown makes the lease cost visible month-to-month.

---

### Journey 8: "Ocean vs. Farms — Location Optimization"
**Mode:** Facility siting — two-sided transport problem

**Opening Scene:**
You need to site your processing facility. Two options:
- **Near the ocean** (close to seaweed harvest) — cheap to bring inputs in, expensive to ship biochar out to inland farms
- **Near the farms** (close to biochar buyers) — expensive to bring seaweed in, cheap to deliver biochar

**Rising Action:**
You model three scenarios:
- `facility-coastal.yaml` — 10km from harvest, 150km to farms
- `facility-inland.yaml` — 150km from harvest, 20km to farms
- `facility-midpoint.yaml` — 80km from each

For each, you specify transport on BOTH:
- `materials_input` (seaweed coming in)
- Output transport (biochar going out)

**Climax:**
BELT reveals the asymmetry:
- Seaweed is HEAVY (wet) or BULKY (dry) — transport cost/kg is high
- Biochar is LIGHT and DENSE — transport cost/kg is low
- **Input transport dominates!** Coastal facility wins on total transport cost AND carbon.

**Resolution:**
You discover: *"Biochar is 10x lighter per unit value than seaweed input. Optimize for input proximity, not output."* Facility siting decision made.

---

### Journey Requirements Summary

| Journey | Key Capabilities Revealed |
|---------|---------------------------|
| Wet vs. Dry | Transport carbon separate from process; MaterialInput with distance/weight |
| Japan vs. US | Different scenario structures; boundary flexibility; compare across models |
| Batch Planning | Term flexibility (annual vs per_batch); storage as OPEX category |
| Quick Variant | Fast iteration; clear diffs between runs |
| Investor Presentation | OPEX breakdown; carbon breakdown; credible audit trail |
| Debug | Per-transformation output; traceable calculations |
| Purchase vs. Lease | CAPEX vs OPEX modeling; multi-year projection support |
| Ocean vs. Farms | Transport on BOTH inputs AND outputs; weight/value ratio analysis |

### New Insight: Output Transport

Journey 8 reveals that transport applies to OUTPUTS too, not just inputs. Biochar delivery to farms has cost and carbon implications. This may be modeled as:
- Transport attributes on MaterialOutput (symmetric with MaterialInput)
- OR a logistics OPEX category at the scenario/transformation level

