# Execution plan template — (the HOW)

Path: `docs/implementations/<slug>/execution-plan.md`. Companion to the plan; encodes how the
agent team runs so execution mode follows it instead of improvising.

```markdown
# <Project> — Execution Plan (Agent Team)

Companion to [`plan.md`](./plan.md) (the *what*). This document is the *how*: a team
of subagents, each owning its own tasks, orchestrated by a team lead, with a
per-task review gate, milestone security sweeps, a final full-branch
code-review + security-review pass, and a single tracking file.

## Integration branch

- **Branch**: `planex/<slug>`, created from **`<base branch>`** — always the
  branch the skill was invoked from at planning time (standing rule) — at
  execution start if it doesn't exist. Locked decision — execution never
  re-derives it.
- The lead works in its own dedicated worktree (`.planex/<slug>`) — all merges,
  post-merge test runs, and tracker edits happen there, never in the shared
  main checkout. Start and each milestone are tagged
  `planex/<slug>/start`, `planex/<slug>/M1`, …

## Ground rules

- **Tracking file**: `docs/implementations/<slug>/tasks.md` **on the
  integration branch** is the single source of truth for task status. **Only
  the team lead edits it**, in the lead's integration worktree, committing
  every update. A task is marked `done` only after (1) the owning subagent
  reports completion with passing tests, (2) the task-reviewer gate passes —
  its security checklist included for `PT` tasks; an `MS` task's SR ✅
  back-fills from the next security sweep (its milestone's, or the final
  review's security pass for tasks merged after the last swept milestone) —
  and (3) the lead has merged the branch.
- **Isolation**: every task runs on its own branch
  `task/<slug>/<id>-<task-slug>`, cut from the integration tip. The
  `<slug>/` namespace keeps concurrent efforts in the same repo apart — all
  branch listings scope to it. Each lane worker keeps one worktree for the
  life of its lane. Nobody touches the integration branch except the lead.
  <Live systems / production branches> stay untouched until cutover.
- **The live system is sacred**: name the ports, data dirs, and branches no
  agent may touch; all test instances run isolated — **bind port 0
  (ephemeral) by default**; a fixed scheme is the exception and needs a
  per-effort base recorded here (e.g. <base + task number>), chosen after
  checking every other effort's `docs/implementations/*/execution-plan.md`
  for its recorded base — and a throwaway data dir.
- **Bootstrap**: fresh worktrees have no installed dependencies — the first
  command in any new worktree (the lead's and every worker's) is
  `<install/bootstrap command>`, before any test run.
- **Definition of done per task**: code + tests (<coverage bar> on new lines) +
  <formatter/linter> clean + the task's verification step from the plan + the
  review gates that apply to its tier.
- **Durability**: workers commit incrementally in their worktrees (small, real
  commits — the branch is the only resumable record if a session dies); the
  worker reports its branch + worktree path immediately after creating the
  branch (before implementing), and the lead records the branch in the
  tracker's Branch column; a one-line checkpoint lands in Notes after each worker
  commit. The tracker itself is committed on the integration branch with
  every update. Recovery = re-invoke the skill with the plan file; setup is
  idempotent; audit branches vs tracker scoped to `task/<slug>/*`; respawn
  fresh workers on the existing branches (prune dead worktrees first).

## Team roster

One **team lead** (the orchestrating session) + <N> worker agents, each a named
subagent persisting across its lane (continued via SendMessage, retired and
re-seeded with a lane summary roughly every 5 tasks). Lead keeps up to
min(4, lanes with ready tasks) active in parallel, scheduled by the dependency
column.

**Model assignments**: the lead runs on whatever model the session was invoked
with; workers are spawned with `model: "sonnet"` unless the Model column
deliberately overrides a subtle lane; the per-task task reviewer and the
milestone security sweeps are spawned with `model: "sonnet"`; the two final
full-review agents with `model: "opus"`.

| Agent name | Lane | Owns tasks | Model |
|---|---|---|---|
| `lead` | Assigns, merges, runs review gates, updates the tracker, resolves cross-lane contracts | — | (invoking) |
| `<lane-1>` | <scope> | T01–T0x | sonnet |
| `<lane-2>` | <scope> | T0x–T0y | sonnet |
| … | … | … | … |

Cross-cutting contracts (<shared types / protocol / schema>) are owned by
`<lane>`; changes route through the lead so the contract never forks.

## Task lifecycle protocol

todo → assigned → in-progress → review → done   (or → blocked, with reason)

1. **Assign** — lead picks a task whose deps are all done; spawns/continues the
   lane agent with the task card, the relevant plan sections, the spec source
   files, the full branch name, and the integration branch name.
2. **Implement** — worker's first action:
   `git checkout -b task/<slug>/<id>-<task-slug> <integration-branch>` (the
   start point is mandatory — it resets the worktree to the integration tip so
   the branch doesn't inherit the previous task's commits); worker immediately
   reports branch + worktree path, then builds, committing incrementally with
   a one-line checkpoint to the lead per commit. `docs/implementations/**` is
   read-only for workers. Before reporting done, worker runs the full local
   check suite and includes output.
3. **Report** — worker messages the lead. A worker never marks its own task done.
4. **Review gate** — lead notes the branch SHA and spawns the **task
   reviewer**: a **sonnet** subagent built from the planex skill's
   `references/task-reviewer.md` template (NOT the code-review skill), told
   to run in the task's worktree and review exactly the task's own work
   (`git log <integration-branch>..<branch>` for the commit list;
   `git diff <integration-branch>...<branch>` — three-dot merge-base form —
   for the diff), with effort scaled to the task's complexity (the plan's
   "ported verbatim" lists are checklists). The reviewer also verifies the
   task's verification step, the success-criteria rows the plan maps to it,
   and the coverage bar on new/changed lines. On tasks tagged **`PT`** in the
   tracker's SR column (security surface: untrusted input, paths, subprocess
   args, sanitization, network/auth, credentials, packaging — when in doubt,
   `PT`) the reviewer also applies its security checklist. Lead triages;
   confirmed findings go back to the worker via SendMessage; re-run the gate
   with a fresh reviewer scoped to the fix commits and carrying the prior
   round's findings + resolutions. **Cap: 3 rounds**, then escalate to the
   owner. Reviewers recommend, the lead decides.
5. **Merge & mark** — in the lead's integration worktree, one merge at a time:
   verify the branch touches nothing under `docs/implementations/`, merge,
   re-run the suite on the merge result, update the tracker
   (`done(<date>)` + one-line note) and commit it. Task branches stay until
   cutover; the worker's worktree stays until its lane retires.
6. **Milestone security sweep** — at every milestone the lead stops assigning,
   lets in-flight tasks land, then spawns a **sonnet** subagent running one
   `/security-review` in the integration worktree over exactly
   `planex/<slug>/M<n-1>..HEAD` (first: `planex/<slug>/start..HEAD`): the
   early net for `MS` tasks and mistagged rows. Confirmed findings become new
   fix tasks (fresh IDs, `PT`, normal lifecycle); SR ✅ back-fills onto the
   `MS` rows the sweep cleared. When fix tasks close: tag `planex/<slug>/M<n>`,
   record it in the tracker's milestone log, demo to the owner. No milestone
   code sweep — every diff was already reviewed pre-merge — and no sweep at
   the last milestone: the final review's security pass replaces it.
7. **Final full review** — once all tasks **except the cutover task** are
   merged (the ready-task rule never auto-assigns the cutover task; the lead
   holds it until this review's fix tasks merge), the lead spawns two
   **opus** subagents in parallel in the integration worktree — one running
   `/code-review`, one `/security-review` — over exactly
   `planex/<slug>/start..HEAD`: the deep pass for cross-task composition
   issues the cheap layers can't see. Both reports are persisted to the
   tracker before triage; findings become fix tasks as at milestones (fresh
   IDs, `PT`); the full pass re-runs at most once, then escalates. Its
   security pass replaces the last milestone's sweep and back-fills SR ✅ on
   every `MS` row an earlier sweep didn't clear. Then the cutover task runs;
   cutover completes when it merges.
8. **Blocked** — reason recorded; lead resolves, reorders, or escalates.

## Milestones (checkpoints the lead demos to the owner)

Each milestone, when reached, is tagged `planex/<slug>/M<n>` and recorded in
the tracker's milestone log — the tag is the next sweep's diff base.

- **M1** after T0x: <earliest end-to-end demo>
- **M2** after T0y: <…>
- …

## Standing risks the lead watches

- <hardware-gated / environment-gated tasks and when they must resolve>
- <fixtures that must be recorded from the live system before ports start>
- <platform runners needed and when>
```
