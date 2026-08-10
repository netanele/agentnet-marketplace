# BMAD Autopilot — Execution Loop

## Status Dashboard

The trace file has a **Status Dashboard** section between the header and the Execution Log — a compact, at-a-glance view of all epics, stories, and step-by-step status.

### Dashboard Format

Columns and the presence of the `Epic Test Design` line depend on `{quality_mode}` (set in initialization Step 1.5).

**TEA mode (10 step columns + Epic Test Design line):**

```markdown
## Status Dashboard

**Last updated:** [TIMESTAMP]

### Epic 1: [epic-key]  — [STATUS]

**Epic Test Design:** [STATUS]

| Story | create | validate | atdd | dev | review | automate | test-review | nfr | trace | commit |
|-------|--------|----------|------|-----|--------|----------|-------------|-----|-------|--------|
| [story-key] | DONE | DONE | DONE | >> | - | - | - | - | - | - |
| [story-key] | - | - | - | - | - | - | - | - | - | - |

**Retrospective:** [STATUS]

### Epic 2: [epic-key]  — [STATUS]
...
```

**QA mode (6 step columns, no Epic Test Design line):**

```markdown
## Status Dashboard

**Last updated:** [TIMESTAMP]

### Epic 1: [epic-key]  — [STATUS]

| Story | create | validate | dev | review | qa-e2e | commit |
|-------|--------|----------|-----|--------|--------|--------|
| [story-key] | DONE | DONE | >> | - | - | - |
| [story-key] | - | - | - | - | - | - |

**Retrospective:** [STATUS]
```

### Status Markers

| Marker | Meaning |
|--------|---------|
| `-` | Not started |
| `>>` | Currently executing |
| `DONE` | Completed successfully |
| `FAIL` | Failed (not retrying) |
| `HANG` | Teammate hung, will retry |

Epic-level status matches sprint-status.yaml values: `backlog`, `in-progress`, `done`.
Epic Test Design: `pending`, `>>`, `DONE`, `FAIL`, `HANG`. Retrospective: same, plus `SKIPPED` (when `epic-N-retrospective: optional`).

### Dashboard Rules

1. **Create on initialization** — populated in Step 3 from sprint-status.yaml. All stories, every step set to `-`.
2. **Update after every step** — after logging a step outcome, also update the corresponding dashboard cell.
3. **Mark active step** — when spawning a teammate, set the cell to `>>`. When the step completes, replace `>>` with `DONE` / `FAIL` / `HANG`.
4. **Update timestamp** — every time you edit the dashboard, update `**Last updated:**`.
5. **On resume** — check if the dashboard exists; create it if missing. Read it to quickly assess state. Any `>>` cell → that step needs retry.
6. **Quick status check** — whenever you need to know current state mid-run, read just the Status Dashboard section rather than the entire trace.

---

## Execution Loop

Follow this EXACTLY. Do NOT deviate or exit early.

```
RUN PRELUDE — FRAMEWORK BOOTSTRAP (once per run):  [TEA MODE ONLY]
  The TEA skills hard-HALT without a test framework: atdd and automate refuse
  to run if no framework config exists ("Run `framework` workflow first").
  Before the OUTER LOOP:
    1. Check for a test framework config via Bash:
       ls playwright.config.* cypress.config.* 2>/dev/null
    2. Found → log "Framework bootstrap: skipped (config present)" to trace; continue.
    3. Not found → spawn a teammate for testarch-framework (standard spawn pattern,
       command file `.claude/skills/bmad-testarch-framework/SKILL.md`), communication
       loop until COMPLETE/ERROR, shutdown, log outcome to trace. On ERROR: STOP the
       autopilot and report — every TEA story cycle would HALT at atdd without it.
  QA mode: skip this prelude entirely.

OUTER LOOP — EPICS:
  while epics remain in sprint-status.yaml:

    EPIC PRELUDE — STEP 0 (epic-test-design):  [TEA MODE ONLY]
      if {quality_mode} == "qa":
        skip — no epic prelude in QA mode; go straight to INNER LOOP.

      Otherwise (TEA mode), before the first story of this epic begins:
        - If resuming and `**Epic Test Design:**` is DONE → skip
        - If any story in this epic already has progress → skip
        - Otherwise:
          1. Update dashboard: set `**Epic Test Design:** >>` and timestamp
          2. Spawn teammate for testarch-test-design (Epic-Level mode)
             ADDITIONAL CONTEXT: "Run in Epic-Level mode for epic [epic-key].
             Produce the epic-level test plan covering all stories in this epic."
          3. Communication loop until COMPLETE or ERROR
          4. Shutdown teammate
          5. Log outcome to trace
          6. Update dashboard: `**Epic Test Design:** DONE` (or FAIL/HANG)

    INNER LOOP — STORIES:
      while stories remain in current epic:

        STORY CYCLE — step list depends on {quality_mode}:
          TEA mode (10 steps):
            create-story → validate-story → testarch-atdd → dev-story → code-review
            → testarch-automate → testarch-test-review → testarch-nfr → testarch-trace
            → commit-and-push

          QA mode (6 steps):
            create-story → validate-story → dev-story → code-review
            → qa-generate-e2e-tests → commit-and-push

          for each step from starting step:
            Workflow steps (every step except the final commit-and-push):
              1. Look up the command file in the Skill Name Reference table
              1a. Update dashboard: set current story+step cell to `>>` and timestamp
              2. Spawn teammate (see Spawn Teammate section)
              3. Communication loop: handle messages until COMPLETE or ERROR
              4. Shutdown teammate
              5. Post-step evaluation (code review retry if needed)
              6. Log outcome to trace
              6a. Update dashboard: replace `>>` with DONE / FAIL / HANG and timestamp
              7. Advance to next step — CONTINUE the loop
            Final step (commit-and-push):
              Orchestrator handles directly — see Commit-and-Push Logic.
              After commit, update dashboard: set commit cell to DONE and timestamp.

        Story cycle complete (all steps for the mode done).
        Verify story status in sprint-status.yaml — do NOT write it yourself:
          code-review OWNS the story-status write (`done` when clean,
          `in-progress` when unresolved findings remain). If the story is not
          `done` (5-cycle retry limit hit), log `**Status:** INCOMPLETE` to the
          trace, leave sprint-status.yaml untouched, and treat the story as
          exhausted — never re-enter it this run.
        Continue INNER LOOP → next story in epic (next story still in `backlog`).

      All stories in epic complete.

    EPIC COMPLETION:  [both modes — same logic]
      Update sprint-status.yaml: mark epic as done. (This is the ONE status the
      orchestrator writes — no skill sets epic `done`, and the retrospective
      expects the epic already marked complete when it runs.)
      If epic-N-retrospective is `optional` → skip retrospective (log + dashboard SKIPPED).
      Otherwise spawn teammate for retrospective (see Handle Epic Completion).
      Log retrospective to trace. Update dashboard.
      Orchestrator runs commit-and-push directly.
      Continue OUTER LOOP → next epic.

  All epics complete → proceed to Completion section.
```

**CRITICAL:** Do NOT exit the loop early. The ONLY exit condition is: no more epics remain in sprint-status.yaml.

---

## Spawn Teammate

For each workflow step, call the `Agent` tool with these EXACT parameters:

```
Agent:
  subagent_type: "general-purpose"
  name: "workflow-executor"
  mode: "bypassPermissions"
  description: "[step-name] for [story-id]"
  prompt: [use the template below]
```

Teammates run in the background by default — the Agent call returns immediately, the teammate's `SendMessage` reports are delivered to you automatically, and you are notified when it completes. Do NOT pass `run_in_background: false`. Note: reusing the name `workflow-executor` for each spawn is intentional — the latest spawn owns the name.

**Teammate prompt template:**

```
You are a BMAD workflow executor teammate. Your lead is the main conversation — send ALL reports via SendMessage with to="main".

STEP: [step-name]
STORY: [story-id]

EXECUTE THE WORKFLOW:
1. Read the skill file at: {project-root}/[skill-file-path]
2. Follow it exactly as written: execute its "On Activation" steps in order (customization
   resolution, config load, step files), then the workflow steps themselves. The skill is
   self-contained — do NOT look for a workflow engine or workflow.xml; everything you need
   is in the SKILL.md and the files it references.
3. Save all outputs to the paths the skill specifies, as you go — not at the end.

AUTONOMY MODE:
You are fully autonomous. Do NOT ask questions — make decisions using project artifacts
(story file, architecture docs, sprint-status.yaml) and your expertise.
Auto-complete all workflow sections that request user input.

FOREGROUND BASH RULE — NON-NEGOTIABLE:
Run all bash commands in the FOREGROUND with a long `timeout` (e.g., `timeout=600000` for
10 min). DO NOT use `run_in_background=true` for ANY verification, test, build, lint, or
gate run. Reason: a foreground bash blocks until it exits, so the result and your report
to the lead land in the same turn — one command, one heartbeat, deterministic. A background
bash re-invokes you when it exits, but that decouples the result from your reporting flow
and multiplies silent-gap windows the lead may read as a hang. Background bashes are ONLY
acceptable for genuinely long-lived processes you intend to monitor across multiple turns
(dev servers, watch modes) — never for one-shot verification commands. If a one-shot
verification genuinely exceeds 10 min, split it into smaller foreground runs (e.g., run
test shards sequentially) rather than backgrounding it.

**Auto-background backstop:** if a command is auto-backgrounded by the harness:
  1. Send a HEARTBEAT WORKFLOW PROGRESS immediately with the bash id + estimated remaining time
  2. Use the Monitor tool actively to watch for completion
  3. If Monitor doesn't fire within (estimate + 5 min), kill via `pkill` and split into shorter shards

HEARTBEAT CONTRACT — NON-NEGOTIABLE:
Send a message to the lead at least every 5 minutes of wall-clock time. The lead treats
>10 minutes of total silence as a confirmed hang and will force-shut you down.

Three scenarios:
1. **Finished a section / milestone** → send WORKFLOW PROGRESS:
     SendMessage(to="main",
       summary="Progress: [step-name] - [section name]",
       message="WORKFLOW PROGRESS\nSTEP: [step-name]\nSTORY: [story-id]\nSECTION: [section name]\nSTATUS: [brief description]")
   Send one after your FIRST completed section to confirm you started.

2. **About to start a long operation (estimated >5 min)** → send PRE-FLIGHT heartbeat BEFORE starting:
     SendMessage(to="main",
       summary="Heartbeat: starting [operation]",
       message="WORKFLOW PROGRESS\nSTEP: [step-name]\nSTORY: [story-id]\nSECTION: [name]\nSTATUS: HEARTBEAT — about to run [operation], estimated [duration]; will report result")
   If the operation exceeds your estimate, kill at minute 5 of overage, send a follow-up heartbeat, then split into shorter shards.

3. **Discovered a pre-existing infra issue** → send KNOWN-GOTCHA notice:
     SendMessage(to="main",
       summary="KNOWN-GOTCHA: [title]",
       message="WORKFLOW PROGRESS\nSTEP: [step-name]\nSTORY: [story-id]\nSECTION: known-gotcha-discovery\nSTATUS: KNOWN-GOTCHA: [one-line title]\nDETAILS: [what breaks, how to avoid, workaround if any]")
   Then continue your work.

[ADDITIONAL CONTEXT — story file path, code review findings, architecture ref, KNOWN-GOTCHAS block]

--- CRITICAL: REPORT NO MATTER WHAT ---
Even if the workflow fails to load or a tool errors out — you MUST still send a
WORKFLOW ERROR message. Never stop silently.

--- MANDATORY REPORTING (DO NOT SKIP) ---
Your text output is NOT visible to the lead. You MUST use SendMessage.

When done:
  SendMessage(to="main",
    summary="[step-name] complete for [story-id]",
    message="WORKFLOW COMPLETE\nSTEP: [step-name]\nSTORY: [story-id]\nARTIFACTS: [files created/modified]\nSUMMARY: [what was done]")

On error:
  SendMessage(to="main",
    summary="[step-name] error for [story-id]",
    message="WORKFLOW ERROR\nSTEP: [step-name]\nSTORY: [story-id]\nERROR: [details]")

Legacy fallback: if you ever receive a shutdown_request message, approve it immediately
by replying SendMessage(to="main", message={type: "shutdown_response", request_id: [echo it],
approve: true}). (The lead normally terminates you via TaskStop — no action needed on your side.)
```

**Fill these placeholders before spawning:**
- `[step-name]` → current step (e.g., "create-story", "dev-story")
- `[story-id]` → current story identifier
- `[skill-file-path]` → the full "Command File" path from the Skill Name Reference table (e.g. `.claude/skills/bmad-create-story/SKILL.md`)
- `[ADDITIONAL CONTEXT]` → story details, code review findings, architecture ref, and KNOWN-GOTCHAS block (read registry from trace before each Agent call, inject verbatim)

**validate-story exception:** the validate-story step invokes `bmad-create-story` with the `*validate-create-story` command argument (the invocation is `/bmad-create-story *validate-create-story`, run after story creation). Replace the "EXECUTE THE WORKFLOW" block of the template with:

```
EXECUTE THE VALIDATION:
1. Read the skill file at: {project-root}/.claude/skills/bmad-create-story/SKILL.md
2. You are invoked with the argument: *validate-create-story — the story-validation
   quality check. This is a VALIDATION run, not a creation run: the target is the
   story that was just created, at [story file path from the create-story step's
   ARTIFACTS].
3. Run the validation using the skill's checklist at
   {project-root}/.claude/skills/bmad-create-story/checklist.md — you are its
   "independent quality validator in a fresh context". Apply it fully against the
   story file, cross-checking epics, architecture docs, and the codebase.
4. Fix every issue you find by editing the story file in place.
5. GUARDRAIL — NON-NEGOTIABLE: this invocation must NEVER create a new story or
   advance auto-discovery to the next backlog item. If you find yourself in the
   story-creation flow (Step "Determine target story" selecting a backlog story),
   STOP and send WORKFLOW ERROR instead.
6. Do NOT change the story's status in sprint-status.yaml — it stays ready-for-dev.
7. Report via WORKFLOW COMPLETE: issues found, fixes applied, and a PASS/FIXED verdict.
```

---

## Handle Teammate Reports

**WORKFLOW COMPLETE:**
1. Log the completion to the trace (artifacts, summary, test results)
2. Shut down the teammate
3. Determine the next step from the Execution Loop sequence
4. Continue the execution loop — spawn next teammate

**WORKFLOW ERROR:**
1. Log the error to the trace (error details, last output)
2. Evaluate retryability: missing artifact or tool failure → retryable; fundamental failure → log and skip
3. Shut down the teammate
4. Retry (spawn new teammate for same step) or proceed to next step

**WORKFLOW PROGRESS:**
1. Append a one-line progress entry to trace: `[TIMESTAMP] ⏳ [step-name] / [story-id] — [section]: [status]`
2. Update `**Last updated:**` in the Status Dashboard
3. Continue waiting — do NOT shut down or advance
4. Reset your internal hang-probe counter (this message proves the teammate is alive)

**KNOWN-GOTCHA (embedded in WORKFLOW PROGRESS):**
1. Append a new entry to the `## KNOWN-GOTCHAS` registry in the trace
2. Update `**Last updated:**` in the registry
3. Continue waiting on the teammate

---

## Teammate Shutdown

After each teammate completes (WORKFLOW COMPLETE or terminal ERROR):

```
TaskStop:
  task_id: "workflow-executor"
```

TaskStop is synchronous — it returns a success/failure status immediately; no acknowledgment wait, no extra turn. (The older `SendMessage` `shutdown_request`/`shutdown_response` dance is a legacy protocol — do not use it.) If TaskStop reports the task is already finished, that is success. NEVER spawn a new teammate while the previous one is still active.

---

## Hang Detection and Recovery — 10/5/kill Protocol

A teammate is **non-responsive** if EITHER holds:
- 10+ wall-clock minutes since their last message of ANY type
- You receive a completion notification for the teammate AND its most recent message was not WORKFLOW COMPLETE / ERROR

**STEP 1 — KILL STUCK CHILDREN FIRST** (unblocks a stalled teammate):

The teammate can be stalled behind a deadlocked child bash. Killing the child often unblocks it and produces a delayed WORKFLOW COMPLETE/PROGRESS/ERROR.

Identify suspects:
```
ps aux | grep -E "pytest|alembic|npm|build|wait|uv run" | grep -v grep
```

Kill what's stuck:
```
pkill -f "pytest -m dbintegration"
pkill -f "alembic upgrade head"
```

Wait one turn. If a delayed message arrives → handle normally and reset. If still silent → Step 2.

**STEP 2 — PROBE ONCE:**
```
SendMessage(to="workflow-executor",
  summary="Final status probe",
  message="STATUS_REQUEST: 10+ min silence. Send WORKFLOW PROGRESS / COMPLETE / ERROR within 3 min or you will be force-shut down.")
```

Note: sending to a teammate's name resumes it from its transcript even if it already completed — a probe cannot be lost; even a finished teammate is revived to answer it.

Wait up to 3 minutes. If a message arrives → handle it. If still silent → Step 3.

**STEP 3 — FORCE-SHUTDOWN AND RETRY:**
1. Call `TaskStop` with `task_id: "workflow-executor"` (synchronous — no ack wait)
2. Log a HANG DETECTED entry:
```markdown
## [TIMESTAMP] Story [story-id] — [step-name] (HANG DETECTED)

**Status:** HANG — teammate non-responsive after 10/5/kill protocol
**Last message:** [timestamp + summary of last received message, if any]
**Stuck children killed:** [list of pids/cmds, or "none found"]
**Action:** Retrying with new teammate; carrying forward known-gotchas registry
```
3. Update dashboard: set step cell to `HANG` and timestamp
4. Spawn new teammate for same step, with ADDITIONAL CONTEXT including the last useful PROGRESS message and any KNOWN-GOTCHAS

**3-strike rule:** If the same step hangs three times:
a. Update dashboard cell to `FAIL`
b. Log a FATAL HANG entry with a summary of all three attempts
c. **STOP the autopilot entirely** — do NOT skip to the next step
d. Report to the user: which story, which step, three hang summaries, last useful output
e. Wait for human instruction before continuing

---

## Handle Code Review Retry Loop

The v6.10 `bmad-code-review` workflow triages findings itself — severity is **low / medium / high** (there is NO "Critical" tier), and each finding lands in one of: **`patch`** (clear fix), **`decision-needed`** (correct fix is ambiguous without a human call), **`defer`** (pre-existing / out of scope — auto-appended to `{implementation_artifacts}/deferred-work.md`), or dismissed as noise. At the end it presents an action menu.

If a code-review teammate applies fixes that break tests, this is still a code-review retry — NOT a reason for the lead to fix code directly. Spawn a new dev-story teammate with broken test details.

**Step 0: Spawn instructions** — every code-review teammate's ADDITIONAL CONTEXT must include:

```
CODE REVIEW AUTONOMY RULES:
SPEC BINDING — FIRST AND NON-NEGOTIABLE: at the step-01 "spec file" prompt, bind the
story file at [story file path] as {spec_file} so the review runs in FULL mode
(review_mode = "full"). Without it the review silently degrades to no-spec mode:
no findings are written to the story file and decision-needed findings cannot exist.

The workflow stops for user input at these points. Handle each exactly as follows
(these override the general "auto-complete all user-input sections" rule):
0. Step-01 preflight stops: "what to review" → the current story's changes;
   "is there a spec file" → yes, the story file (see SPEC BINDING above);
   checkpoint HALTs → confirm and proceed.
1. Decision-needed resolution: do NOT decide these yourself and do NOT reclassify them
   as defer — the lead adjudicates them. Leave them as unchecked [Review][Decision] items
   in the story file, skip past this stop, and list each one verbatim (finding, severity,
   options) in your WORKFLOW COMPLETE message.
2. Patch action menu: choose "Apply every patch" (no per-finding walkthrough).
3. Final "What would you like to do next?" menu: choose "Done — end the workflow".
   NEVER pick "Start the next story" — the lead owns story sequencing.
Also:
- Let defer findings flow to the deferred-work ledger as the workflow specifies; do not fix them.
- The workflow itself writes the story's status to sprint-status.yaml (`done` when clean,
  `in-progress` when unresolved findings remain) — let it; never adjust that write.
- Include in your WORKFLOW COMPLETE message: counts per bucket, all high-severity findings,
  whether tests still pass after patches were applied, and the sprint-status value it wrote.
```

**Step 1: Adjudicate `decision-needed` findings.** You are the human stand-in. The teammate left them unresolved in the story file and listed them in its WORKFLOW COMPLETE message. Decide each one using project artifacts (story acceptance criteria, architecture spine, PRD) and log the decision + rationale to the trace. Never leave one undecided.

**Step 2: Classify the outcome** (after adjudication):
- **Needs a fix pass** — any of: a high-severity finding was NOT resolved by an applied patch; applied patches broke tests; an adjudicated `decision-needed` resolution requires code changes
- **Clean** — everything else (patches applied, tests green, only defer/dismissed remain)

**Step 3: Fix pass (if needed):**
1. Log findings to trace
2. Shut down the code-review teammate
3. Spawn a NEW dev-story teammate with ADDITIONAL CONTEXT:
```
ADDITIONAL CONTEXT — CODE REVIEW FINDINGS (MUST FIX):
The code review identified the following issues that MUST be fixed
(high-severity findings, broken tests from applied patches, and
adjudicated decision-needed items with the lead's chosen resolution):
[paste them here]

Focus on fixing these specific issues during the dev-story workflow.
```
4. After dev-story completes, spawn another code-review teammate (same autonomy rules)
5. Repeat until the report is Clean, up to **5 retry cycles**. If issues persist after 5 cycles, log unresolved issues and proceed — do NOT loop forever.

**Step 4: Log deferred work.** Don't duplicate the ledger — add one trace line pointing at it:
```
### Deferred Findings
- [N] findings deferred to {implementation_artifacts}/deferred-work.md (see "Deferred from: code review" heading)
```

---

## Handle Story Cycle Loop

After the mode's final data step completes for a story (TEA: `testarch-trace` / QA: `qa-generate-e2e-tests`):
1. Run commit-and-push (orchestrator handles directly)
2. Read `sprint-status.yaml` and verify the story's status. **code-review owns this write** — `done` when the review ended clean, `in-progress` when unresolved findings remain. Never set a story's status yourself: forcing `done` would mask unresolved review findings, and the downstream skills select their work BY status (create-story picks the first `backlog` story, dev-story the first `ready-for-dev`, code-review the first `review`). If the story is not `done` (retry limit exhausted), log `**Status:** INCOMPLETE` to the trace and move on — do not re-enter it this run; list it under Open Action Items at completion.
3. If stories with status `backlog` remain in the current epic → loop back to `create-story` for the next story
4. If no `backlog` stories remain → proceed to epic completion

**TEA-mode note:** code-review runs at step 5, so sprint-status.yaml shows the story `done` while automate/test-review/nfr/trace/commit are still pending. That is expected — the trace's Status Dashboard, not sprint-status.yaml, is the authority for step-level progress within a story.

---

## Handle Epic Completion

When all stories in the current epic are complete:
1. Update sprint-status.yaml: set the epic's status to `done`. This is the one status write the orchestrator owns — no skill sets epic `done`, and the retrospective expects the epic already marked complete when it runs. (Story statuses remain the skills' writes — never touch those.)
2. Check `epic-N-retrospective` in sprint-status.yaml: if its value is `optional`, skip the retrospective — log `Retrospective: skipped (optional)` to trace, set the dashboard line to `SKIPPED`, and go to step 4.
3. Spawn teammate for retrospective (standard spawn pattern) with this ADDITIONAL CONTEXT:

```
RETROSPECTIVE AUTONOMY RULES:
- Run the retrospective for epic [epic-key] SPECIFICALLY — do not use the workflow's
  own epic auto-detection (it picks the highest epic number with a done story, which
  can diverge when several epics have partial progress).
- The workflow has many "WAIT for {user_name}" interaction points and a multi-persona
  discussion script. You are the human stand-in for ALL of them: answer from the epic's
  stories, trace outcomes, and code-review findings; simulate the persona rounds; never
  stall waiting for input.
- Let the workflow write `epic-N-retrospective: done` and append `action_items` to
  sprint-status.yaml as it specifies.
```

4. After retrospective completes, log to trace and update dashboard
5. Run commit-and-push (orchestrator handles directly)
6. Read `sprint-status.yaml` to check for remaining epics
7. If more epics remain → loop back to first story of next epic
8. If all epics complete → proceed to Completion

---

## Commit-and-Push Logic

The orchestrator handles this directly (no teammate). Execute:

1. Run `git status --porcelain` via Bash
2. If output is empty → log "No uncommitted changes, skipping commit" to trace. Done.
3. If output exists:
   a. Read `sprint-status.yaml`
   b. Find the most recently completed story; extract from its key (e.g., `1-2-payment-processing`):
      - `epic_num` = 1, `story_num` = 2, slug = `payment-processing` → humanize to `Payment Processing`
   c. If story info unavailable → use fallback: `"BMAD: uncommitted changes after story completion"`
   d. Run: `git add -A`
   e. Run: `git commit -m "E{epic_num} S{story_num}: {Title}"`
   f. Run: `git push`
   g. If push fails → log warning (non-blocking), continue
4. Log outcome to trace. Update dashboard commit cell to DONE.

---

## Trace File Format

Log every step with structured metadata. Every step gets an entry — even retries and errors.

```markdown
## [TIMESTAMP] Story [story-id] — [step-name]

**Command:** [command file used]
**Teammate:** [agent id]

### Context Sent

[Brief description of additional context provided — e.g., "Story file path, architecture ref, code review findings from previous cycle"]

### Execution

[Structured summary — key actions, decisions made, artifacts discovered. Not verbatim transcription but enough detail to reconstruct what happened.]

### Outcome

**Status:** COMPLETE / ERROR / RETRYING / SYNTHESIZED — [reason]
**Artifacts:** [files created or modified]
**Findings:** [if applicable — e.g., "2 high / 3 medium / 1 low — 4 patch (applied), 1 decision-needed (adjudicated), 1 defer"]
**Test Results:** [if applicable — e.g., "34/34 pass, BUILD SUCCESS"]
**Next action:** [what happens next]

---
```

**Logging rules:**
- Every step gets an entry
- Timestamps on every entry
- List all artifacts — every file created or modified
- Capture findings and test results — critical for code review retry decisions
- Structured, not verbatim — concise enough to scan, detailed enough to debug

---

## Completion

When ALL epics are complete:

1. Collect open action items (v6.9.0+): Read `sprint-status.yaml` and parse its `action_items` list — each entry is `{ epic, action, owner, status }`, appended by the per-epic retrospectives. Keep entries whose `status` is `open` or `in-progress`. If the section is absent (older sprint-status), skip this step — it is optional.

2. Append final summary to the trace:

```markdown
## Phase 4 Autopilot Complete

**Finished:** [current datetime]
**Total Duration:** [total time]

### Summary Statistics
- **Epics completed:** [count]
- **Stories completed:** [count]
- **Retrospectives run:** [count]
- **Code review retries:** [count]
- **TEA workflows executed:** [count]
- **Total teammate spawns:** [count]
- **Total Q&A interactions:** [count]

### Epic Summaries
[Brief summary of each epic's retrospective findings]

### Open Action Items
[One line per open/in-progress item from Step 1: `- {action} — {status} (epic {epic}, owner: {owner})`. Write "none" if there are no open items.]

### Incomplete Stories
[One line per story that ended the run NOT `done` in sprint-status.yaml (code-review retry limit exhausted): `- {story-key} — left {status}, unresolved: {summary}`. Write "none" if every story completed.]
```

3. Release the run lock: delete `{project-root}/BMAD-Autopilot/autopilot.lock` via Bash. If it fails, log the error but still report completion.

4. Report that Phase 4 autonomous execution is complete — surface the **Open Action Items** list so the retrospective follow-ups aren't buried in sprint-status.yaml, and remind the human they can open `BMAD-Autopilot/autopilot-dashboard.html` and drop `phase4-trace.md` onto it for a visual run summary.

---

## Skill Name Reference

| Step | Command File | Mode | Notes |
|------|-------------|------|-------|
| framework-bootstrap | `.claude/skills/bmad-testarch-framework/SKILL.md` | TEA only | Once per run, before the first epic — ONLY if no `playwright.config.*` / `cypress.config.*` exists. See Run Prelude. |
| epic-test-design | `.claude/skills/bmad-testarch-test-design/SKILL.md` | TEA only | Runs once per epic before first story. Teammate must operate in **Epic-Level mode**. Pass current `epic-key` in ADDITIONAL CONTEXT. |
| create-story | `.claude/skills/bmad-create-story/SKILL.md` | Both | |
| validate-story | `.claude/skills/bmad-create-story/SKILL.md` | Both | Invoked with the `*validate-create-story` argument (i.e. `/bmad-create-story *validate-create-story`), run after story creation — see the validate-story exception in Spawn Teammate, including its never-create-a-story guardrail. |
| testarch-atdd | `.claude/skills/bmad-testarch-atdd/SKILL.md` | TEA only | |
| dev-story | `.claude/skills/bmad-dev-story/SKILL.md` | Both | |
| code-review | `.claude/skills/bmad-code-review/SKILL.md` | Both | |
| testarch-automate | `.claude/skills/bmad-testarch-automate/SKILL.md` | TEA only | |
| testarch-test-review | `.claude/skills/bmad-testarch-test-review/SKILL.md` | TEA only | |
| testarch-nfr | `.claude/skills/bmad-testarch-nfr/SKILL.md` | TEA only | |
| testarch-trace | `.claude/skills/bmad-testarch-trace/SKILL.md` | TEA only | |
| qa-generate-e2e-tests | `.claude/skills/bmad-qa-generate-e2e-tests/SKILL.md` | QA only | Runs after code-review, before commit |
| commit-and-push | (orchestrator handles directly) | Both | Runs after each story cycle and after retrospective |
| retrospective | `.claude/skills/bmad-retrospective/SKILL.md` | Both | Runs once per epic after all stories done |
