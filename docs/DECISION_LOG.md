# Decision Log - Monday.com Business Intelligence Agent

## 1) Key assumptions

1. monday.com is the system of record; agent must query live boards, not hardcoded CSV.
2. Two boards exist and are mapped via env vars:
   - `MONDAY_DEALS_BOARD_ID`
   - `MONDAY_WORK_ORDERS_BOARD_ID`
3. Founder questions will mostly fall into pipeline, revenue/collections, and operations.
4. Data is messy enough that every answer should include caveats and missing-field percentages.
5. Read-only integration is sufficient for this assignment; no writes/backfills to monday are needed.

## 2) Trade-offs and rationale

### Trade-off A: monday API over MCP

- Choice: monday GraphQL API directly.
- Why: simpler deployment, fewer moving parts, and easier to explain in 6-hour scope.
- Cost: no generic tool abstraction layer as MCP can offer.

### Trade-off B: hybrid intent understanding (heuristics + optional LLM)

- Choice: deterministic keyword parser by default, optional OpenAI JSON intent parsing.
- Why: keeps core behavior reliable even without LLM key; still demonstrates AI-driven interpretation when key exists.
- Cost: heuristic parsing is less flexible on unusual phrasings.

### Trade-off C: normalization by alias mapping vs learned schema inference

- Choice: explicit alias maps for known messy columns.
- Why: predictable behavior, transparent debugging, and robust handling of real-world CSV/monday inconsistencies.
- Cost: requires minor maintenance if board column names change significantly.

### Trade-off D: speed to deploy over deep forecasting

- Choice: focused on descriptive BI (pipeline/revenue/ops snapshots), not advanced forecasting.
- Why: assignment asks for quick, accurate answers under a short timebox.
- Cost: fewer predictive insights.

## 3) Data resilience strategy

1. Null-safe parsing for text/number/date fields with explicit null tokens.
2. Date coercion with tolerant parsing; invalid dates become null, not failures.
3. Numeric coercion with `errors='coerce'` to avoid crash-on-bad-value.
4. Sector/status normalization to lowercase canonical forms for filtering.
5. Data quality report attached to every answer:
   - rows loaded
   - missing percentage on critical fields
6. User-facing caveats when data is incomplete.

## 4) Interpretation of optional requirement: "prepare data for leadership updates"

Implemented as a **leadership update mode** that generates a concise quarterly summary with three blocks:

1. Pipeline health: open deals, total value, stage concentration
2. Revenue/collections: billed, collected, receivable, collection efficiency
3. Operations: execution and billing status distribution

Reasoning: this mirrors what leadership typically needs in weekly/monthly executive updates.

## 5) What I would do with more time

1. Add semantic layer for natural-language metrics (e.g., "slipping deals", "at-risk accounts").
2. Add stronger schema discovery from monday board metadata to reduce alias maintenance.
3. Add unit/integration tests and snapshot tests for messy datasets.
4. Add caching + incremental refresh to reduce API calls and improve latency.
5. Add charted executive dashboard export (PDF/slides) for leadership packs.
6. Add confidence scoring and explanation traces per answer.

## 6) Risks / limitations

1. If board schema changes heavily, alias mapping may miss fields until updated.
2. Deterministic parsing may ask for clarification less intelligently than a fully agentic planner.
3. "This quarter" uses server date context; timezone differences may slightly shift boundaries.
