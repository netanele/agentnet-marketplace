# Plan template — "<Project>: <Effort> Plan" (the WHAT)

Path: `docs/implementations/<slug>/plan.md` — the three documents share the `docs/implementations/<slug>/`
folder. This is the document a future session can execute from, so it must be
self-sufficient: locked decisions, target design, and the links to its two
companions.

```markdown
# <Project> — <Effort> Plan

## Companion documents

<!-- REQUIRED. Execution mode resolves both files from these links. -->
- **Execution plan (the how — team, protocol, review gates):** [execution-plan.md](./execution-plan.md)
- **Task tracker (the state — owned by the team lead):** [tasks.md](./tasks.md)

## Context

What exists today (sizes, tech, module count), what the effort produces, and why.
State the decisions the owner has locked in ("Owner decisions locked in: …") so
execution never re-litigates them. Note any known documentation that is stale
and where the real behavior lives instead.

## Target architecture

The end-state design: component/module layout (a tree helps), old→new mapping
table, technology choices with one-line rationale for the non-obvious ones,
protocols/contracts named concretely (message types, routes, schemas), state
model, and — where behavior must not drift — "ported verbatim" invariant lists.
These lists double as review checklists during execution.

## <Cross-cutting concerns>

Sections as the effort demands: security model, config/runtime parity,
packaging/distribution per platform, deliberate non-changes documented as
decisions (so they don't read as oversights).

## Build order

Numbered phases, each ending runnable, with the early "spine" milestone called
out (the soonest point a real end-to-end demo exists).

## Success criteria

<!-- REQUIRED. "Done" must be a test run, not a judgment call. -->
A table of measurable criteria; the final cutover task requires every row green,
and this table is the owner's sign-off checklist at the last milestone. Each row:

| ID | Criterion | Measurable threshold | Verified by |
|---|---|---|---|
| SC-1 | <what must be true> | <a number, a percentage, or "repro X gets result Y" — never "works well"> | <the tests/tasks that prove it, by task ID> |

Cover at minimum: functional parity (against the product's canonical feature
list), data continuity (existing users lose nothing — field-level import
assertions), security parity (known exploit repros wired as permanent
regression tests), output fidelity (golden fixtures, with allowed drift named
explicitly), performance (baseline-relative thresholds — **record the baseline
from the live system before porting starts**), coverage, packaging per
platform, stability (soak/scale), and any standing product rules (e.g.
local-first / no-egress). Every criterion maps to concrete tests; tests with no
criterion and criteria with no tests are both findings. Give the acceptance
suite its own task in the tracker, depending on the baseline recording.

## Verification

How the whole effort is proven: test-migration commitments (map the existing
suite file-by-file, port the coverage gate), new test categories, golden
fixtures (recorded from the live system BEFORE the port starts), e2e strategy,
manual/hardware-only checks, and the final parity sweep before cutover —
closing with the success-criteria acceptance suite that turns the SC table
into executable checks.

## Risks (ranked)

Each risk with its mitigation. Include shippability risk if the effort is
big-bang.

## Out of scope

The standing rules that survive the effort unchanged.
```
