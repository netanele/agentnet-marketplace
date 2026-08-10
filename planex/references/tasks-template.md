# Task tracker template — (the STATE)

Path: `docs/implementations/<slug>/tasks.md`. The one file that changes during
execution — and once execution starts, the authoritative copy lives **on the
integration branch**, edited and committed by the lead in its integration
worktree; the copy in the user's checkout is a planning artifact.
Sizing guidance: one task ≈ one focused agent-session (a subsystem slice with
its tests). Every task gets explicit deps — the Deps column IS the scheduler —
so shape the graph so several lanes have ready tasks at any given time: a long
single-lane chain serializes the whole effort. Give every task a verification
note where the plan defines one.

**Notes-column hygiene**: every cell is Markdown table content. Before
writing a checkpoint note, review finding, or anything else into a cell,
backslash-escape any literal `|` — including ones inside code fragments
(`|e|`, `||`, regex alternation) — or it silently splits the row and breaks
the table. Keep each addition to **2-4 sentences** — what shipped or was
found, its resolution, the commit SHA — compressed by the lead, never a
worker/reviewer report pasted verbatim; a cell is a pointer for resuming or
auditing, not a transcript, and an ever-growing one is both what breaks the
table (harder to edit correctly) and what makes the tracker unreadable as
an actual table.

```markdown
# <Project> — Task Tracker

> **Edited by the team lead ONLY** (workers: `docs/implementations/**` is
> read-only). Workers report completion to the lead; the lead flips status
> after the task-reviewer gate passes (security checklist included for `PT`
> tasks) and the branch is merged into `<integration-branch>`.
>
> Status values: `todo` · `assigned` · `in-progress` · `review` ·
> `blocked(<reason>)` · `done(<date>)`
> Every task's branch: `task/<slug>/<id>-<task-slug>`, cut from the
> integration tip (the `<slug>/` namespace separates concurrent efforts). The
> **Branch** column is the authoritative task↔branch registry: the worker
> reports its branch + worktree path immediately after creating the branch —
> before implementing — and the lead fills the cell then; the naming
> convention is only the fallback for rows where it's empty.
> Deps: task IDs, `—` for none, or `all` = every other task in this tracker.
> The cutover task is additionally held by the lead until the final full
> review's fix tasks merge — the ready-task rule never auto-assigns it.
> CR = task-reviewer gate — every task, ✅ before `done`. SR = security tier:
> `PT` = the task reviewer applies its security checklist in the same review,
> ✅ before `done`; `MS` = covered by the next security sweep — the next
> milestone's, or the final full review's security pass for rows merged after
> the last swept milestone — ✅ back-filled when that sweep clears the row
> (`done` does not wait for it).

## P0 — <Phase name>

| ID | Task | Owner | Deps | Status | Branch | CR (code review) | SR (security tier) | Notes |
|---|---|---|---|---|---|---|---|---|
| T01 | <deliverable + what tests it ports/adds> | <lane> | — | todo | | | PT | <invariant / gotcha / verification> |
| T02 | … | <lane> | T01 | todo | | | MS | |

## P1 — <Phase name>

| ID | Task | Owner | Deps | Status | Branch | CR (code review) | SR (security tier) | Notes |
|---|---|---|---|---|---|---|---|---|
| T0x | …; **M1: <milestone demo>** | <lane> | T02, T03 | todo | | | PT | |

<!-- …one section per phase, through the final task: -->

## P<last> — <Final phase>

| ID | Task | Owner | Deps | Status | Branch | CR (code review) | SR (security tier) | Notes |
|---|---|---|---|---|---|---|---|---|
| T<n> | Parity sweep + cutover: <side-by-side checks>, docs; **M<last>** | qa | all | todo | | | PT | runs after the final full review's fix tasks merge; owner sign-off; after this merge the lead retires all lanes, then deletes `task/<slug>/*` branches |

## Milestone log

<!-- The lead appends a row when each milestone completes; the tag is the next
sweep's diff base, and `start..HEAD` is the final full review's range. Sweep
and final-review findings lists are committed here verbatim BEFORE triage
(crash-safety); their fix tasks get fresh IDs appended to the phase tables
above. The last row is `cutover complete` — the marker resume checks. -->

| Milestone | Reached | Tag | Notes |
|---|---|---|---|
| start | <date> | `planex/<slug>/start` | integration branch created |
```
