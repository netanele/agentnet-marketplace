# BMAD Autopilot — Initialization

Follow these steps in order. After all pre-flight checkpoints pass, load `references/execution-loop.md`.

## Step 0: Acquire the Run Lock

Do this FIRST — before asking the human anything and before touching the trace file (SKILL.md Anti-Pattern 13). A concurrent autopilot must be detected BEFORE this run mutates shared state (the quality-mode question, resume markers, dashboard repairs all come later).

1. Run `mkdir -p {project-root}/BMAD-Autopilot` via Bash (on a first-ever run the directory does not exist yet).
2. Check `{project-root}/BMAD-Autopilot/autopilot.lock` via Bash (`stat -f %m` on macOS / `stat -c %Y` on Linux for mtime).
3. **Exists, mtime within 30 minutes** → another autopilot is (or was very recently) active. ABORT and report to the user. Do NOT proceed.
4. **Exists, mtime older than 30 minutes** → stale prior run. Overwrite it via Bash: `echo "locked at [TIMESTAMP] — BMAD Autopilot run in progress" > {project-root}/BMAD-Autopilot/autopilot.lock` (Bash, not the Write tool — Write refuses to overwrite a file it hasn't read). Remember to log `## [TIMESTAMP] STALE LOCK CLEARED` to the Execution Log once the trace is initialized in Step 2.
5. **Does not exist** → create it with the same Bash `echo`.

**Keep it fresh:** `touch` the lockfile every time you update the Status Dashboard. **Release it:** delete the lockfile in the Completion section (and if you ABORT mid-run for a fatal hang, leave it — the 30-minute staleness window handles recovery).

## Step 1: Load BMad Master Knowledge

Before anything else, load the BMad Master persona so you have full BMAD domain knowledge. Do NOT use the Skill tool or a slash command — read the files directly.

Try in order:
- `{project-root}/_bmad/_config/skill-manifest.csv` — read it to absorb the available BMAD skills, plus any agent SKILL.md files under `{project-root}/_bmad/*/agents/` for personas. (Legacy installs may instead have `agent-manifest.csv` with a `"bmad-master"` row — use it if present.)
- If neither exists, skip — per-workflow knowledge lives in each `.claude/skills/bmad-*/SKILL.md` file that teammates read directly. Adopt the BMad Master orchestrator role from SKILL.md and proceed.

Also read: `{project-root}/_bmad/config.toml` — store `output_folder` (from `[core]`) and `implementation_artifacts` (from `[modules.bmm]`; used later wherever `{implementation_artifacts}` appears, e.g. the deferred-work ledger path). For `user_name`, read `{project-root}/_bmad/config.user.yaml` (fall back to `user_name` in `{project-root}/_bmad/bmm/config.yaml`; if neither has it, omit).

Adopt the persona in **orchestrator mode**: do NOT display the BMad Master menu, do NOT greet the user, do NOT wait for input — proceed directly to Step 1.5.

## Step 1.5: Determine Quality Mode

This is the ONE point in the entire run where you interact with the human. After this, you are fully autonomous until completion.

**On fresh start** (trace file does NOT exist at `{project-root}/BMAD-Autopilot/phase4-trace.md`):

Ask the human via the AskUserQuestion tool:

- **Question:** "Which quality assurance workflow should the autopilot run for each story?"
- **Header:** "Quality mode"
- **Options (2):**
  - **TEA Mode (Test Architect)** — Full Test Architect path: epic-level test design + per-story ATDD before dev, plus automate, test-review, NFR, and trace after code-review. Best for enterprise quality bar, greenfield projects, or when test-first discipline matters.
  - **QA Mode (Quick E2E)** — Quinn's `bmad-qa-generate-e2e-tests` workflow after code-review (no TEA workflows, no epic test design). Best for small-medium projects with existing code that need fast E2E coverage.

Map the user's selection to `{quality_mode}` — either `"tea"` (TEA option) or `"qa"` (QA option). This determines the story cycle steps, the epic prelude, and the Status Dashboard columns for the entire run.

**On resume** (trace file exists): use Read with `limit=10` to grab the top of the trace file. Extract `**Quality Mode:**` from the header. Use that mode without re-asking. If the field is missing (trace predates this feature), default to `"tea"` and append a `## [TIMESTAMP] MODE INFERRED — assumed TEA (legacy trace)` entry to the Execution Log.

**No mid-run mode switching.** The chosen mode is fixed for the entire trace. To change modes, the human must delete the trace file and start over.

## Step 2: Initialize or Resume the Trace Log

Check if the trace file already exists at: `{project-root}/BMAD-Autopilot/phase4-trace.md`

**If the trace file does NOT exist (fresh start):** also copy the standalone trace viewer next to it — `cp {skill-root}/assets/autopilot-dashboard.html {project-root}/BMAD-Autopilot/` (skip if already present; the human can open it in a browser and drop `phase4-trace.md` onto it for a visual dashboard). Then create the trace file with:

```markdown
# BMAD Autopilot — Story Cycle Execution Trace

**Started:** [current datetime]
**Status:** In Progress
**Quality Mode:** [tea or qa — from Step 1.5]

---

## Status Dashboard

**Last updated:** [current datetime]

[Populated after reading sprint-status.yaml — see Step 3]

---

## KNOWN-GOTCHAS

**Last updated:** [current datetime]

_(empty — no gotchas discovered yet; populated by teammates per Step 2.5)_

---

## Execution Log
```

**If the trace file ALREADY exists (resume):** do NOT read the entire file. Instead:

1. Read just the `## Status Dashboard` section (use an offset to find it near the top).
2. Read the last ~30 lines of the Execution Log (use offset from file length).
3. Validate — confirm the last log entry's story/step/status matches the dashboard. If they disagree, trust the Execution Log and fix the dashboard.
4. If the Status Dashboard section is missing, create it (see Step 3 dashboard population).

Append a resume marker:

```markdown
---

## [TIMESTAMP] RESUMED

**Previous run ended at:** [timestamp of last entry in trace]
**Resuming from:** [determined after reading sprint status]

---
```

## Step 2.5: Maintain the KNOWN-GOTCHAS Registry

The `## KNOWN-GOTCHAS` section in the trace is cross-spawn memory for pre-existing infra issues — fixture deadlocks, missing env vars, flaky upstream services, broken migrations — that any teammate has discovered. Without it, every fresh spawn trips the same issue.

**Format:**

```markdown
## KNOWN-GOTCHAS

**Last updated:** [TIMESTAMP]

- **[Title]** — Discovered during [step]/[story] at [TIMESTAMP].
  - **Symptom:** [what breaks, how to recognize]
  - **Workaround:** [how to avoid or work around]
  - **Repro avoidance:** [bash incantation / env var / pre-existing resource future spawns should reuse]
  - **Carry-forward to:** [story or infra-fix that owns the proper fix, if any]
```

**On fresh start:** create the section empty (header + "Last updated" + placeholder line).

**On resume:** locate the section. If missing (trace predates this feature), insert it between Status Dashboard and Execution Log.

**When a teammate sends a `KNOWN-GOTCHA:` message:**
1. Append a new entry to the registry using the format above
2. Update `**Last updated:**` timestamp
3. Continue waiting on the teammate (this is a heartbeat, not a terminal message)

**Every subsequent spawn prompt MUST include the current KNOWN-GOTCHAS block** — read the registry section immediately before each Agent call and inject it verbatim under a heading:

```
KNOWN-GOTCHAS — DO NOT TRIP (carried forward from prior teammates):
[paste the current ## KNOWN-GOTCHAS section content here, minus the markdown header]

These are pre-existing issues you must work around, not new bugs to investigate.
```

If the registry is empty, omit the block.

## Step 3: Read Sprint Status and Determine Resume Point

Read: `{project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml`

Identify: the current epic, all stories in the sprint, and which story to work on.

**Story statuses are a 5-state machine** — `backlog → ready-for-dev → in-progress → review → done` — and each BMAD skill selects its work BY status (create-story picks the first `backlog` story, dev-story the first `ready-for-dev`, code-review the first `review`). Pick the story to work on and its starting step from the status:

| Story status | Meaning | Start at |
|--------------|---------|----------|
| `backlog` | Not started | create-story |
| `ready-for-dev` | Created + validated | dev-story (TEA: testarch-atdd first if not yet done per trace) |
| `in-progress` | Dev underway (or review left findings unresolved) | dev-story (check trace: if a code-review retry was in flight, resume the retry loop) |
| `review` | Dev done, awaiting review | code-review |
| `done` | Complete | skip (TEA: unless post-review steps are still `-` in the dashboard — code-review sets `done` at step 5) |

Never mutate these statuses yourself — the skills own their transitions (create-story → `ready-for-dev`, dev-story → `in-progress` then `review`, code-review → `done` or back to `in-progress`).

**If resuming:** cross-reference the dashboard and last log entry. Determine resume point: next step after the last COMPLETE step. If the last entry had ERROR or RETRYING → retry that same step. Log the resume decision:

```markdown
## [TIMESTAMP] Resume Decision

**Current story:** [story-id]
**Last completed step:** [step-name from trace]
**Resuming at:** [next step-name]
**Rationale:** [why this is the correct resume point]

---
```

**If fresh start:** start from `create-story` for the first `backlog` story (matching create-story's own auto-discovery).

**Populate the Status Dashboard** — use Edit to replace the placeholder in the trace with actual tables. Column count and presence of the `Epic Test Design` line depend on `{quality_mode}` from Step 1.5. For each epic in `development_status`:
1. Create `### Epic N: [epic-key] — [epic-status]` heading
2. **TEA mode only:** Add `**Epic Test Design:** pending` (or `DONE` if the epic is already `done` in sprint-status.yaml). **QA mode:** omit this line entirely (no epic prelude in QA mode).
3. Build a story table with the mode-appropriate columns:
   - **TEA mode (10 step columns):** `| Story | create | validate | atdd | dev | review | automate | test-review | nfr | trace | commit |`
   - **QA mode (6 step columns):** `| Story | create | validate | dev | review | qa-e2e | commit |`
4. For stories with status `done` in sprint-status.yaml, mark all cells `DONE`; otherwise `-`
5. Add `**Retrospective:** pending` (or `DONE` if `epic-N-retrospective: done`, or `SKIPPED` if its value is `optional`)

**On resume:** check if the dashboard exists. If missing, create it as above. If present, read it to quickly assess state. Any cell showing `>>` was in-flight when the previous run ended — treat as needing retry.

## Step 4: Teammate Readiness (no setup required)

No team setup is needed — the session has a single implicit team, and teammates spawned via the `Agent` tool with a `name` are immediately addressable via `SendMessage`. The concurrent-run guard was already handled in Step 0.

## Pre-Flight Checklist

Verify ALL of the following before entering the Execution Loop. If ANY fails, STOP and report which checkpoint failed and why.

- [ ] **CHECKPOINT 1:** BMad Master persona load attempted AND `{project-root}/_bmad/config.toml` read successfully
- [ ] **CHECKPOINT 2:** `{quality_mode}` set to `"tea"` or `"qa"` (asked the human on fresh start, or read from trace header on resume)
- [ ] **CHECKPOINT 3:** Trace file initialized (fresh) or resume data parsed (resume) — with `**Quality Mode:**` in the header
- [ ] **CHECKPOINT 4:** Sprint status read — you know the current epic, current story, and starting step
- [ ] **CHECKPOINT 5:** Run lock acquired — `BMAD-Autopilot/autopilot.lock` written (fresh or stale-cleared, never while an active lock exists)
- [ ] **CHECKPOINT 6:** KNOWN-GOTCHAS registry section exists in the trace

**ALL CHECKPOINTS PASSED →** Load `references/execution-loop.md` and enter the Execution Loop.

## Resume Logic

When resuming, use the ordered step list for `{quality_mode}` (read from the trace header in Step 1.5).

**Run prelude (once per run, before the first epic) — TEA mode only:**

| # | Step Name | Command |
|---|-----------|---------|
| -1 | framework-bootstrap | /bmad-testarch-framework — ONLY if no `playwright.config.*` / `cypress.config.*` exists (see execution-loop Run Prelude) |

On resume: if a framework config now exists, the bootstrap is done — skip it.

**Epic prelude (per epic, before first story) — TEA mode only:**

| # | Step Name | Command |
|---|-----------|---------|
| 0 | epic-test-design | /bmad-testarch-test-design (Epic-Level mode) |

In **QA mode**, there is no epic prelude — skip directly to the first story's create-story.

**Story cycle steps — TEA mode (10 steps):**

| # | Step Name | Command |
|---|-----------|---------|
| 1 | create-story | /bmad-create-story |
| 2 | validate-story | /bmad-create-story *validate-create-story (validation-only — see execution-loop "validate-story exception" and its guardrail) |
| 3 | testarch-atdd | /bmad-testarch-atdd |
| 4 | dev-story | /bmad-dev-story |
| 5 | code-review | /bmad-code-review |
| 6 | testarch-automate | /bmad-testarch-automate |
| 7 | testarch-test-review | /bmad-testarch-test-review |
| 8 | testarch-nfr | /bmad-testarch-nfr |
| 9 | testarch-trace | /bmad-testarch-trace |
| 10 | commit-and-push | (orchestrator handles directly) |

**Story cycle steps — QA mode (6 steps):**

| # | Step Name | Command |
|---|-----------|---------|
| 1 | create-story | /bmad-create-story |
| 2 | validate-story | /bmad-create-story *validate-create-story (validation-only — see execution-loop "validate-story exception" and its guardrail) |
| 3 | dev-story | /bmad-dev-story |
| 4 | code-review | /bmad-code-review |
| 5 | qa-generate-e2e-tests | /bmad-qa-generate-e2e-tests |
| 6 | commit-and-push | (orchestrator handles directly) |

**Epic completion steps (per epic, after all stories done) — both modes:**

| Step Name |
|-----------|
| retrospective |
| commit-and-push |

**How to determine the resume point:**

1. Read the Status Dashboard and cross-reference the last Execution Log entry.
2. Identify the last completed step from the **mode-appropriate** table above.
3. Resume point is the **next step** in that table's sequence.
4. If the last entry has `**Status:** ERROR` or `**Status:** RETRYING` → retry that same step.
5. If the last data step (TEA: `testarch-trace` / QA: `qa-generate-e2e-tests`) is COMPLETE → proceed to `commit-and-push`.
6. If `commit-and-push` for the story is COMPLETE → check for more stories, or proceed to retrospective.
7. If `retrospective` is COMPLETE (or SKIPPED — `epic-N-retrospective: optional`) → proceed to the epic's final `commit-and-push`.
8. If the epic's final `commit-and-push` is COMPLETE → epic is done; move to next epic.
9. **Epic-Test-Design check (TEA mode only):** When resuming on the first story of an epic (no story has any steps DONE), check `**Epic Test Design:**`. If `pending` or missing → run step 0 before step 1. If `DONE` → skip. If any story in the epic already has progress → treat epic-test-design as done. In **QA mode**, skip this check entirely — there's no epic prelude.
