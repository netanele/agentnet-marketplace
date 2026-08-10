---
name: planex
disable-model-invocation: true
argument-hint: "[describe what to plan & build | provide a plan.md to execute]"
description: >
  Plan-then-execute engine for large engineering efforts (migrations, rewrites,
  big features) using an agent team. Explicit invocation only. Two modes,
  detected from the argument: `/planex <project description>` runs PLANNING
  mode — research the codebase, interview the user in guided rounds
  (surfacing aspects they haven't considered and recommending decisions), and
  write three linked documents under docs/implementations/<slug>/ — plan.md
  (the what), execution-plan.md (the how: team roster, model assignments, review
  gates), and tasks.md (the tracker the team lead marks done incrementally). `/planex <path/to/plan.md>` runs EXECUTION
  mode — skip planning and orchestrate the agent team: sonnet worker subagents
  in isolated worktrees (lead on the invoking model), every merge gated by a
  sonnet task reviewer (with a security checklist on security-tagged tasks),
  a sonnet security-review sweep at each milestone, and one final opus
  full-branch code-review + security-review pass before cutover — tracker
  updated by the lead as tasks complete. Safe to run for several efforts concurrently in one repo: every
  effort is namespaced by its slug (branches, tags, lead worktree, tracker).
---

# Planex — plan and execute large efforts with an agent team

One skill, two modes. Detect the mode first:

- **EXECUTION mode** — the argument is a path to an existing file or folder
  under `docs/implementations/<slug>/` (or a slug that resolves there). Resolve
  it to the effort's `plan.md`: given `execution-plan.md`, `tasks.md`, or the
  folder itself, use the `plan.md` beside/inside it. Confirm it really is a
  planex plan — it has a "Companion documents" section; if it doesn't, say so
  and offer planning mode instead. If the argument looks like a planex path or
  slug but no file exists in the checkout, check the effort branch before
  concluding — `git show planex/<slug>:docs/implementations/<slug>/plan.md` —
  a hit means resume execution from the branch copy. A planex-shaped plan
  living outside `docs/implementations/`: ask whether to execute it in place
  or move it into the canonical folder first — never silently fall back to
  planning. Then go straight to
  [Execution](#execution-mode). Do NOT re-plan, do not regenerate the three
  documents; the planning phase already happened.
- **PLANNING mode** — the argument describes a project to plan. Produce the
  three documents below and stop for approval before executing.
- **Bare `/planex` with no argument** — ask whether they want to plan something
  new (and what) or execute an existing plan (list any under
  `docs/implementations/`). Don't guess.

The three documents are a set. The Plan is the *what*, the Execution Plan is the
*how*, the Task Tracker is the *state*. They live together in **their own folder
named after the effort's slug — `docs/implementations/<slug>/`** — as `plan.md`,
`execution-plan.md`, and `tasks.md`, and the Plan links to the other two — that
link is what lets a future session execute from nothing but the plan's path.

---

## Planning mode

Do NOT use plan mode (no EnterPlanMode/ExitPlanMode) — the approval gate here is
your own, at the end. Until the three documents are written, stay read-only
toward the project by discipline: research and interview only, no code changes,
no scaffolding. The flow:

### 1. Research until the plan can be grounded

A plan for a large effort is only as good as its inventory. Launch Explore
subagents in parallel (up to 3) to build ground truth: every module and its
responsibilities, the full API/protocol surface, persistent state schemas,
spawned processes, security mechanisms, packaging/build pipelines, and the
existing test suite (count the files — the plan will commit to migrating them).
Also record the branch currently checked out — **the integration branch is
always based on the branch the skill was invoked from**; capture its name now
so the execution plan can lock it.
For a rewrite, also split "pure UI / presentation" from "business logic" per
module. Capture load-bearing invariants and documented gotchas verbatim — these
become review checklists later.

### 2. Think it through WITH the user

You are not just collecting requirements — you are the experienced counterpart
who helps the user discover what they haven't thought about yet. A user asking
for "a rewrite in X" has usually pictured the happy path; the plan's quality
comes from the aspects they *didn't* mention. Read
`references/discovery-checklist.md` and walk its dimensions against both the
user's request and your research findings.

Work in rounds, not one interrogation:

- **Gap-driven, not questionnaire-driven.** Compare what the user asked for
  against what the research uncovered. Every subsystem, platform behavior, or
  invariant the research found that the user's request is silent about is either
  a question or a stated assumption in the plan — never a silent decision.
  ("You didn't mention the packaged installer — the current app has a signed
  bundle with OS-permission anchoring. Should the rewrite preserve that?")
- **Guide decisions, don't just pose them.** Use AskUserQuestion (batch up to 4
  per round) with concrete options, a recommended choice first with
  "(Recommended)", and the trade-off named in each description — the user should
  be able to decide in one read. If they pick something with a consequence they
  may not see, say the consequence and confirm.
- **Only ask what research can't settle.** Decisions the codebase, its
  conventions, or its documented history already answer, make yourself and state
  in the plan as locked decisions. Asking the user to re-decide what their own
  repo already decided wastes their attention on the questions that matter.
  The integration branch is one of these and is never a question: a fresh
  `planex/<slug>` cut from **the branch the skill was invoked from** — that
  base is a standing rule, not a choice. Record name + base in the execution
  plan as a locked decision.
- **Stop when the plan writes itself.** Two to three rounds is typical. When
  every checklist dimension is either user-decided, research-settled, or
  explicitly deferred to a named plan section (e.g. "risks"), move on.

Record every answer as a **locked decision** in the plan ("Owner decisions
locked in: …") so execution never re-litigates them.

### 3. Write the three documents

**First, check whether the effort already exists** — any of: the folder
`docs/implementations/<slug>/` in the checkout, the branch `planex/<slug>`, or
the tag `planex/<slug>/start`. A branch or tag hit means the effort is live or
paused **regardless of what the checkout copies say** — once execution starts,
the checkout `tasks.md` is a frozen all-`todo` artifact and proves nothing. If
any exists, stop and ask: resume via execution mode, revise the existing
documents, or pick a new slug. Never overwrite an existing effort's documents
without explicit confirmation.

Use the templates in `references/` of this skill — read the relevant template
before writing each file. All three go in one folder named after the effort:
`docs/implementations/<slug>/plan.md`, `docs/implementations/<slug>/execution-plan.md`, `docs/implementations/<slug>/tasks.md`.
**Create any missing directories on this path** (`docs/`, `docs/implementations/`,
the `<slug>/` folder) — a project that has never used this skill won't have them
yet, and their absence is never a reason to write the files anywhere else.

- **The Plan (`plan.md`)** — `references/plan-template.md`. Context and goal,
  locked decisions, target architecture, invariants to port verbatim, success
  criteria, verification, ranked risks, out-of-scope. **Its "Companion
  documents" section must link to `./execution-plan.md` and `./tasks.md`** —
  execution mode resolves both files from these references, so a plan without
  them is incomplete by definition.
- **The Execution Plan (`execution-plan.md`)** — `references/execution-plan-template.md`.
  Ground rules, integration branch (name + base), team roster (a named worker
  per lane, each owning task IDs), task lifecycle with its review layers
  (per-task gate, milestone sweeps, final full review), model assignments,
  milestones, standing risks.
- **The Task Tracker (`tasks.md`)** — `references/tasks-template.md`. Every task
  as a table row: ID, description, owner, deps, status, CR/SR columns, notes.
  One task ≈ one focused agent-session; the Deps column is the scheduler.
  **Shape the dependency graph so several lanes have ready tasks at any given
  time** — a long single-lane chain serializes the whole effort no matter how
  many workers exist.
  **Tag every task's SR column now**: `PT` if it touches a security surface
  (untrusted input, paths, subprocess args, sanitization, network/auth,
  credentials, packaging) — when in doubt, `PT` — else `MS` (covered by the
  next security sweep: its milestone's, or the final review's security pass).
  Header states: **only the team lead edits this file.**

### 4. Approval gate, then execute

With the three files written, present the plan for approval: a short summary in
the conversation (goal, locked decisions, team size, task count, milestones,
the three file paths), then AskUserQuestion with options like **"Approve —
start execution"** / **"I have changes"** / **"Stop here (keep the files)"**.
Do not start executing without this explicit approval, and don't bury the
question in prose — the files being on disk is not consent to run a fleet of
agents against the repo.

- **Approve** → immediately enter [Execution mode](#execution-mode) with the
  plan file you just wrote — become the team lead and run the protocol. Do not
  start implementing tasks yourself in the main session; workers implement,
  you orchestrate.
- **Changes** → revise the three files in place and re-present.
- **Stop** → the documents remain; execution can start any time later via
  `/planex docs/implementations/<slug>/plan.md`.

---

## Execution mode

You are the **team lead**. Read, in order: the plan file the user referenced,
then the execution plan and task tracker it links to (if the links are missing
or dead, stop and tell the user — offer to generate the missing pieces via
planning mode rather than improvising an execution structure). Then run the
protocol below, which the execution plan may refine but not contradict.

### Setup — before spawning anything

Every step here is idempotent; on a resumed session, rerun them and reuse what
already exists.

1. **Integration branch.** Take name + base from the execution plan. If the
   branch doesn't exist, create it: `git branch <integration> <base>`.
2. **Your own worktree.** If `git worktree list` already shows
   `.planex/<effort-slug>` with an intact directory, reuse it as-is — do not
   `worktree add` again (it fails on an existing path). Otherwise
   `git worktree add .planex/<effort-slug> <integration>` (if the directory is
   gone but git still registers it, `git worktree prune` first). Ensure `.planex/` is listed in `.git/info/exclude` — append it if
   missing; never edit the user's `.gitignore` for this. A fresh worktree has
   no installed dependencies — run the project's install/bootstrap command
   (named in the execution plan) before the first test run; and if tooling run
   from the main checkout ever recurses into `.planex/`, add it to that
   tooling's ignore config too. **All merges,
   post-merge test runs, and tracker edits happen in this worktree — never in
   the user's main checkout.** That checkout is shared ground: the user works
   there, and other planex leads may too; two sessions merging in one working
   tree race on `index.lock` and run each other's tests against the wrong
   files.
3. **Commit the documents — first run only.** If `docs/implementations/<slug>/`
   does not yet exist **on the integration branch**, copy the three documents
   into the worktree (same path) and commit. **On any rerun, never copy** —
   from the first commit onward the integration-branch copy of `tasks.md`
   **is** the tracker (edit it only there, commit after every update), and the
   copies in the user's checkout are dead planning artifacts, frozen at
   all-`todo`; copying them again would regress every status, ✅, and note.
   Leave them alone either way.
4. **Tag the start:** `git tag planex/<effort-slug>/start <integration>` (if
   absent) — the first milestone sweep and the final full review measure from
   here.

### Ground rules

- The tracker is the single source of truth. **Only you edit it**, in your
  integration worktree, committing every update. A task becomes `done` only
  after: the worker reported completion with passing tests, the task-reviewer
  gate passed — its security checklist included where the task is tagged `PT`
  (an `MS` task's SR ✅ arrives later, from its milestone's security sweep —
  or from the final review's security pass, for tasks merged after the last
  swept milestone), and you merged the branch. Mark it immediately after the merge — `done(<date>)` plus
  a one-line outcome note — not in batches at the end.
- **Branch namespace.** Every task branch is
  `task/<effort-slug>/<id>-<task-slug>`. The effort-slug segment is what keeps
  concurrent efforts in one repo from colliding — scope every listing to
  `git branch --list 'task/<effort-slug>/*'`, and branches outside your
  namespace are never yours to touch, adopt, or clean up.
- Every task runs on its own branch, cut from the integration tip. Every
  **lane worker** gets its own git worktree (spawn with
  `isolation: "worktree"`) and keeps it for the life of the lane — the lead
  removes it only at lane retirement, never after an individual merge. Only you
  touch the integration branch. The user's live/running instances, real data
  dirs, and production ports are off-limits to everyone; every test server
  binds a **unique** port — ephemeral (bind port 0) by default, or the
  per-effort fixed scheme recorded in the execution plan — with a throwaway
  data dir.
- Definition of done per task: code + tests meeting the project's coverage bar +
  formatter/linter clean + the task's own verification step + the review gates
  that apply to its tier.

### Model assignments

- **Team lead (you)**: whatever model the skill was invoked with — no override.
- **Worker agents**: `model: "sonnet"` by default; the roster may deliberately
  override a genuinely subtle lane to a stronger model — an exception it must
  justify, not a default.
- **Reviewer agents**: the per-task task reviewer and the milestone security
  sweeps run on `model: "sonnet"`; only the two final full-review agents run
  on `model: "opus"` — one deep, expensive pass, at the point where a whole
  branch exists to judge.

### Running the team

- Spawn one **named, persistent worker agent per lane** from the roster (e.g.
  `Agent(name: "term", model: "sonnet", isolation: "worktree", ...)`), and
  continue the same agent across its lane's tasks with SendMessage — lane
  context (contracts it built, decisions it made) is valuable and shouldn't be
  re-derived per task.
- Keep **up to min(4, lanes with ready tasks)** workers active in parallel,
  chosen as: any task whose dependencies are all `done`, preferring the
  critical path. **Exception — the final cutover task is never picked by this
  rule**: even with every dependency `done`, hold it until the final full
  review has run and its fix tasks are merged; only then assign it. Spawn
  them in one message when independent. Flip status to
  `assigned` on spawn. **A lane's worktree is single-occupancy**: never assign
  a lane its next task while a previous task of that lane is still in
  `review` — review fixes happen in that worktree, and a new task's
  start-point checkout would sweep the tree out from under the reviewer. The
  lane idles until its review clears (merging is the lead's job and doesn't
  block the lane).
- Each assignment message contains: the task row verbatim, the relevant plan
  sections, the source files that serve as the spec, the full branch name, the
  integration branch name, and these standing instructions:
  1. **First action, before any code:**
     `git checkout -b task/<effort-slug>/<id>-<task-slug> <integration-branch>`
     — the start-point form both names the branch AND resets the worktree to
     the current integration tip. Never omit the start point: on every task
     after the lane's first, the worktree is sitting on the previous task's
     branch, and without it the new branch inherits those commits (polluting
     its review diff) and misses everything other lanes merged since.
  2. **Immediately after creating the branch — before implementing — message
     the lead** with the branch name and the worktree path. (This report is
     what makes the work findable after a crash; don't defer it to the end.)
  3. **Commit incrementally** — small commits with real messages at each
     coherent step, never one giant commit at the end; after each, message the
     lead a one-line progress checkpoint. Agent memory dies with the process
     and worktree directories are disposable, but a named branch with commits
     survives anything short of deleting the repo.
  4. **`docs/implementations/**` is the lead's — read-only for workers**, the
     tracker above all.
  5. A fresh worktree has no installed dependencies — run the project's
     install/bootstrap command (named in the execution plan) before the first
     test run. Before the completion report, run the full local check suite
     and include its output; **never mark your own task done**; report
     `blocked(<reason>)` rather than guessing through an ambiguity.
- On the worker's branch report, flip status to `in-progress` AND record the
  branch in the row's **Branch column** in the same tracker commit — from that
  moment the tracker, not the naming convention, is the authoritative
  task↔branch registry.
- On each checkpoint message, append a one-line note to that task's Notes in
  the tracker ("checkpoint: parser done, fixtures failing on CRLF"). Cheap now;
  after a crash it's the difference between resuming and re-deriving.
- **Every notes-append is compressed by the lead, never pasted verbatim.**
  A worker's completion report, a reviewer's findings, a merge summary — none
  of it goes into the tracker as-is. A Notes cell is a pointer for resuming or
  auditing, not an archive of the conversation: **2-4 sentences per event** —
  what shipped or was found, its resolution, the commit SHA. The full detail
  already lives in the agent messages; copying it into the one file every
  future read loads in full is how a cell grows past what any editor can
  safely re-edit. If a finding needs more than that to explain, put the extra
  detail in the commit message, not the tracker.
- **Any text landing in a tracker table cell — checkpoint notes, review
  findings, anything copied from a worker report — is Markdown table
  content: backslash-escape every literal `|` first (`\|`), including ones
  inside code fragments (closures like `|e|`, `||`, regex alternation,
  shell pipes). Wrap short code fragments in backticks too, but backticks
  alone don't exempt a cell from needing the pipe escaped — an unescaped `|`
  anywhere in the cell splits the row and breaks the table.**
- Cross-cutting contracts (shared types, protocol vocabularies, schemas) have
  one owning lane named in the execution plan. Route change requests through
  yourself to that lane so the contract never forks.
- **Lane retirement.** A persistent worker's context grows with every task —
  cards, suite outputs, review-fix exchanges — until late tasks pay for the
  whole lane history on every call. Retire a lane worker roughly every 5 tasks,
  or sooner if its responses degrade: have it write a lane summary (contracts
  built, decisions made, gotchas hit), spawn a successor seeded with that
  summary, and remove the old worktree only after its last task merged. A
  worker that hits context death mid-task is handled like any dead worker
  (see [Stalls](#when-things-stall)).

### The review gate — light per task, deep at the end

Two layers: a cheap purpose-built reviewer on every merge, and the expensive
skill-driven pass exactly once, when there is a whole branch to judge.

- **Per-task review: every task, by the task reviewer.** A plain sonnet
  subagent whose instructions live in this skill —
  `references/task-reviewer.md` — NOT the `code-review` skill: one task's
  diff is small and well-scoped, and a purpose-built prompt beats general
  review machinery on cost. It reads the task's diff against the task card
  and the plan's "invariants to port verbatim" checklists; on tasks tagged
  `PT` in the SR column (security surface: untrusted input, paths, subprocess
  args, sanitization/rendering, network/auth, credentials,
  packaging/signing — **when in doubt, tag `PT`**) it additionally applies
  the security checklist in its instructions. Scale the reviewer's *effort*
  to the task: deep for complex/subtle lanes, a quick pass for mechanical
  ports — the tracker's notes and the plan's risk ranking tell you which is
  which.
- **Milestone security sweep: at each milestone.** One sonnet subagent
  invoking the `security-review` skill in your integration worktree over
  everything merged since the previous milestone tag
  (`planex/<effort-slug>/M<n-1>..HEAD`; first milestone:
  `planex/<effort-slug>/start..HEAD` — the tags are ancestors of HEAD, so
  these ranges are correct as written). This is the early net for `MS` tasks —
  which merge with no security look of their own — and for mistagged rows.
  There is no milestone *code* sweep: every diff already had a correctness
  review before it merged, so a per-milestone code pass would re-buy coverage
  already paid for. The **last** milestone has no sweep of its own either —
  the final full review's opus security pass covers its range at greater
  depth and replaces it.
- **Final full review: once, after every task except the final cutover task
  is merged.** Two **opus**
  subagents in parallel in your integration worktree — one invoking the
  `code-review` skill, one invoking the `security-review` skill — both over
  the whole effort, `planex/<effort-slug>/start..HEAD`. This is the one deep,
  expensive pass, and the only place opus appears: it hunts what the cheap
  layers structurally cannot see — cross-task and cross-milestone composition
  (two individually safe changes forming a hole together). Cutover happens
  only after its findings are resolved.

Mechanics, per task: when a worker reports done, set status `review` and note
the branch's current SHA in the row. Spawn the **task reviewer** — `model:
"sonnet"`, its prompt built from the template in
`references/task-reviewer.md` with every placeholder filled: the task card,
the worktree path, the branch and integration branch names, the diff commands
(the template carries the three-dot merge-base form — keep it verbatim), the
task's invariant checklists, the project's coverage bar, the success-criteria
rows the plan's SC table maps to this task (by the "Verified by" column — or
"none maps to this task"), the effort level, and the security-checklist item
included only when the task is `PT`.

The reviewer reports its findings back to you; you triage (drop anything not
confirmed), send confirmed findings to the owning worker via SendMessage, the
worker fixes in the same worktree on the same branch, and you re-run the gate
with a fresh reviewer — scoped to the fix commits
(`<the SHA you noted at the last round>..HEAD`) and carrying the previous
round's findings and their resolutions, so rounds converge instead of
re-opening the whole diff. Note each round's number and SHA in the row's
Notes — the cap must survive a crash. **Hard cap: 3 rounds per task**
(initial + 2 re-runs). If confirmed findings remain after round 3, stop that task and
escalate to the user with the outstanding list — don't loop reviewers
indefinitely. The gate passes when no confirmed findings remain. Record ✅ in
the tracker: CR on every task when its reviewer passes; SR on `PT` tasks from
the same review (its security checklist ran), and on `MS` tasks when their
covering sweep — the next milestone's, or the final review's security pass —
comes back clean. The verdict is always yours — reviewers recommend, the
lead decides.

### Merge and close

In **your integration worktree**, one merge at a time: check
`git diff --stat <integration>...<branch> -- docs/implementations/` first — a
worker edit to the documents is stripped or sent back, never merged over the
live tracker (strip: merge with `--no-commit`, then
`git restore --source=HEAD --staged --worktree docs/implementations/`, then
commit the merge). Merge the task branch, re-run the project's test suite on the
merge result, update the tracker row to `done(<date>)` with its note, and
commit the tracker. Do **not** remove the worker's worktree — it is the lane's
home until the lane retires. Keep merged task branches until cutover (they are
cheap, and they are the audit trail and recovery net); at cutover, **you**
delete all `task/<effort-slug>/*` branches, after every lane — including
qa — has retired: a branch checked out in a surviving worktree can't be
deleted. Then record a `cutover complete` row in the milestone log — the
durable marker resume checks. If the merge
exposes a cross-lane conflict, you own the resolution and record it in the row.

At each milestone in the execution plan — **except the last, whose sweep the
final full review replaces**: stop assigning new tasks and let
in-flight tasks land. Run the **milestone security sweep** — the sonnet
`security-review` subagent from the review-gate section over
`planex/<effort-slug>/M<n-1>..HEAD` (first:
`planex/<effort-slug>/start..HEAD`). **Persist the report before triaging
it**: commit the reviewer's confirmed-findings list verbatim into the
tracker, under the milestone's entry in the milestone log — one commit,
before any triage. The report otherwise exists only in agent-message space:
a crash mid-triage would silently drop every finding not yet converted to a
fix-task row. Then triage; confirmed findings become **fix tasks appended to
the tracker** — fresh IDs continuing the sequence, tagged `PT`, on fresh
branches off the integration tip, normal lifecycle; their per-task gates
cover the fixes. SR ✅ back-fills immediately onto the `MS` rows the sweep
cleared — a finding blocks only the rows it implicates. The milestone
completes when its fix tasks are done: tag it
(`git tag planex/<effort-slug>/M<n>`, if absent), record tag + date in the
tracker's milestone log, then stop and demo the checkpoint to the user before
continuing. A crash mid-milestone leaves it untagged: on resume, compare the
persisted findings list against the fix-task rows and append any missing
ones; re-run the sweep only if no persisted list exists.

When **every task except the final cutover task is merged**, run the **final
full review**: the two **opus** subagents from the review-gate section —
`code-review` and `security-review`, in parallel — in your integration
worktree over `planex/<effort-slug>/start..HEAD`. Persist BOTH reports into
the tracker before triaging either — if one agent died before reporting,
re-run that agent; never proceed on one report alone. Confirmed findings
become fix tasks exactly as at milestones (fresh IDs, tagged `PT`, normal
lifecycle). Re-run the full pass **at most once**, and only if the findings
were systemic; if the re-run still looks systemic, stop and escalate to the
user. The security pass **replaces the last milestone's sweep** and
back-fills SR ✅ onto every `MS` row an earlier milestone sweep didn't
clear. Only after the fix tasks merge do you assign the cutover task;
cutover completes when it merges. A crash mid-final-review recovers by the
persisted reports: both on disk → resume triage from them (findings vs fix
rows, never row-existence alone); a missing report → re-run that agent.

### When things stall

`blocked` tasks get their reason recorded in the tracker; resolve the contract,
reorder the schedule, or escalate to the user — don't let a worker idle-spin.

If a worker dies, drifts off-spec, or hits context death, the respawn mechanics
matter. First **salvage uncommitted work**: if the dead worktree survives,
`git -C <worktree> add -A && git -C <worktree> commit -m "wip: salvage (<task id>)"`
on the task branch, and note it in the row — crashes land exactly between the
worker's "coherent step" commits, and force-removing the worktree would discard
that work. Then — git refuses to check out a branch that another worktree still
holds — `git worktree remove --force <dead worktree>` (or `git worktree prune`
if the directory is already gone), then spawn a fresh worker with the task card,
the previous agent's report and checkpoints, and this flag in the card: **"the
branch `task/<effort-slug>/<id>-<task-slug>` already exists — first action is
`git checkout <branch>` (no `-b`), then read the diff against
`<integration-branch>` before writing anything."**

### Resuming after a crash or in a new session

Subagents are in-process: a shutdown kills the lead and every worker, and their
contexts are not reattachable — do not SendMessage old agent names hoping they
survived. The durable state is on disk by design: the integration branch (the
three documents, the committed tracker, every merged task, the milestone tags),
every task branch, and any surviving worktrees (including uncommitted files).
To resume, invoke this skill with the plan file
(`/planex docs/implementations/<slug>/plan.md`) and reconcile BEFORE spawning
anything:

1. **Rerun [Setup](#setup--before-spawning-anything)** — it is idempotent
   (step 3 copies documents on the first run only — never on a resume):
   reattach (or recreate — `git worktree prune` first if the directory is
   gone) the `.planex/<effort-slug>` worktree, and read the tracker **from the
   integration branch** — the copies in the user's checkout stopped being
   authoritative the moment execution first started. Then, before anything
   else, `git status` in the integration worktree: if a merge is in progress,
   `git merge --abort` — a later tracker commit would silently complete the
   half-resolved merge, conflict markers and all; the un-merged task's gates
   already passed, so redo the merge cleanly. If `tasks.md` itself is dirty,
   those are interrupted tracker edits — the committed HEAD copy is the
   authoritative baseline; reconcile the dirty edits against reality in steps
   2–3 rather than committing or discarding them blindly. The worktree must
   be clean before any tracker edit.
2. Audit reality, scoped to your namespace. The **Branch column is the primary
   task↔branch registry** — read it first. Fall back to
   `git branch --list 'task/<effort-slug>/*'` for rows whose Branch cell is
   empty — a worker that died between spawn and its branch report — and to
   catch branches the tracker never learned about. **Never adopt a branch
   outside your `task/<effort-slug>/` namespace** — it belongs to a concurrent
   effort. `git worktree list` shows which branches still have working
   directories. For each non-`done` task inspect its branch (`git log` vs the
   integration branch, `git status` where a worktree survives). **The branch is
   ground truth for partial work; the tracker is ground truth for what passed
   review.**
3. Correct the tracker to match reality: an `assigned` task with an untouched
   branch goes back to `todo` — and delete that untouched branch in the same
   breath (it's in your namespace with no unique commits, and leaving it makes
   the next assignment's `checkout -b` fail); note salvageable uncommitted
   work. Delete crash litter: auto-named worktree branches (created at spawn,
   before the rename) with no tracker row, no unique commits, **and no
   registered worktree**. If a branch or worktree cannot be positively
   attributed to this effort, leave it — a concurrent effort's just-spawned
   worker looks identical to your litter, and auto-named branches are cheap.
4. For each `in-progress` task: first check whether the work is already
   finished — the crash may have hit between the worker's completion report
   and the tracker commit. If the branch's diff covers the task and the local
   suite passes on it, skip the respawn and go straight to the review gate.
   Otherwise respawn per the [Stalls](#when-things-stall) mechanics — prune
   the dead worktree first, fresh lane worker, existing-branch card
   ("`git checkout`, no `-b`"), the checkpoint notes, and "resume from the
   current branch state — read the diff before writing anything."
5. For each task that was in `review`: first check
   `git branch --merged <integration>` — an already-merged branch means the
   crash hit between merge and tracker update; mark it `done` directly (its
   gates necessarily passed first). A row whose applicable gate ✅s are all
   recorded skips straight to merge — the tracker is the ground truth for what
   passed review. Only rows with gates genuinely unfinished re-run them from
   scratch — full task range, fresh reviewers, round counter reset — review
   context died with the reviewers, and a half-finished review protects
   nothing.
6. Resume normal scheduling. `done` tasks need nothing: done is done, that is
   what the merge + gates bought. One exception: if every task is `done` but
   the milestone log has no `cutover complete` row, finish the cutover
   cleanup — retire the lanes, delete the `task/<effort-slug>/*` branches,
   record the row.
