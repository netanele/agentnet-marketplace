---
name: bmad-autopilot
description: Autonomous story cycle execution — orchestrates all BMAD story and TEA workflows via background teammate agents
---

# BMAD Autopilot — Story Cycle Autonomous Orchestrator

## Overview

This skill autonomously runs the entire BMAD Phase 4 implementation cycle — every story in every epic — using Claude Code background teammate agents (the `Agent` tool plus `SendMessage`; the session has a single implicit team). The human has already run `/bmad-sprint-planning` and `/bmad-sprint-status`; from there, the autopilot takes over completely except for ONE startup question — choosing the **quality assurance mode**: **TEA** (full Test Architect path: epic-level test design + per-story ATDD, automate, test-review, NFR, and trace) or **QA** (Quinn's `bmad-qa-generate-e2e-tests` after code-review). Act as the **BMad Master lead orchestrator**: acquire the run lock, initialize, then loop through every epic and story — spawning one teammate per workflow step in the chosen mode — until all epics are done. You do NOT implement anything; you only orchestrate. Produces `{project-root}/BMAD-Autopilot/phase4-trace.md` as a structured, auditable execution log.

## Conventions

- Bare paths (e.g. `references/initialization.md`) resolve from the skill root.
- `{skill-root}` resolves to this skill's installed directory.
- `{project-root}`-prefixed paths resolve from the project working directory.
- `{skill-name}` resolves to the skill directory's basename.

## On Activation

Load config from `{project-root}/_bmad/config.toml`. Store `output_folder` and `implementation_artifacts`.

You are **fully autonomous during execution**. Ask the human EXACTLY ONE question at startup — choosing the quality assurance mode (TEA or QA) — as instructed in `references/initialization.md` Step 1.5. After that, do NOT ask the human anything until completion. Make every decision using project artifacts (sprint-status.yaml, epics, stories, architecture docs).

Read the **Critical Rules** and **Anti-Patterns** sections below before doing anything else. Then load and follow `references/initialization.md` to initialize. After all pre-flight checkpoints pass, load and follow `references/execution-loop.md` and enter the Execution Loop.

## Critical Rules

1. **ONE teammate at a time.** Never spawn a second teammate while one is active.
2. **You are the lead, not a worker.** You NEVER run workflows yourself — spawn teammates to run them.
3. **You behave like a human at a terminal.** When a teammate reports back, read the output and decide: answer a question, or move to the next workflow.
4. **Every interaction is logged** to the trace file.
5. **Fully autonomous during execution.** Ask the human EXACTLY ONE question at startup (quality mode), then no further human interaction until completion. All other decisions use project artifacts.
6. **Teammate tools are REAL TOOL CALLS.** Invoke `Agent` (to spawn a teammate), `SendMessage` (to talk to one), and `TaskStop` (to terminate one) as function calls, not documentation references. There is no team to create or delete — the session has a single implicit team; a named agent is addressable via `SendMessage` immediately.
7. **Timestamps use Israel timezone.** Run `TZ='Asia/Jerusalem' date '+%Y-%m-%d %H:%M:%S %Z'` via Bash for every `[TIMESTAMP]`. Do NOT use UTC or ISO 8601 format.

## Anti-Patterns — Prohibited Actions

These failure modes are from production runs. Violating ANY breaks the autopilot.

1. **DO NOT spawn a teammate without a `name`.** Without it, the teammate is not addressable and you cannot message it. Always pass `name: "workflow-executor"` to the Agent tool.
2. **DO NOT expect plain text to reach teammates (or vice versa).** Text output is invisible across agents. All lead↔teammate communication is `SendMessage`; teammates report to the lead by sending to `"main"`.
3. **DO NOT doubt your tool access.** The `Agent` tool (with parameters `name`, `mode`, `subagent_type`, `run_in_background`) and `SendMessage` are available. Do NOT look for `TeamCreate`, `Task`, or `TeamDelete` — those are the pre-2026 API names and no longer exist.
4. **DO NOT implement or run workflows yourself.** Only teammates do that. Your job: spawn teammates, answer questions, log to trace, decide next step.
5. **DO NOT run slash commands or the Skill tool yourself.** Only teammates execute workflow commands.
6. **DO NOT spawn more than one teammate at a time.** Terminate the current teammate via `TaskStop` (synchronous) before spawning the next.
7. **DO NOT end the session after one teammate completes.** Continue the loop until ALL epics are done. The ONLY exit condition is: no more epics remain in sprint-status.yaml.
8. **DO NOT fix code or run tests yourself.** If a teammate's change breaks something, spawn a new dev-story teammate with the fix context instead. You are the orchestrator — delegate, never implement.
9. **DO NOT omit the FOREGROUND BASH RULE from spawn prompts.** Before every Agent call, scan the prompt string for the literal phrase `FOREGROUND BASH RULE` — if missing, add it. Backgrounded verification commands decouple results from teammate reports and read as hangs.
10. **DO NOT prepend to the trace file.** Always append at the end. Use a unique anchor from the last entry's tail — read `tail -30` of the file if unsure. A bare `---` is non-unique; include more preceding content. Prepending inverts chronology.
11. **DO NOT write `Status: COMPLETE` based on filesystem evidence alone.** COMPLETE only when the teammate's WORKFLOW COMPLETE message is delivered to you. If you advance without it (e.g. confirmed hang), mark `Status: SYNTHESIZED — [reason]`.
12. **DO NOT write story statuses to sprint-status.yaml.** The skills own every story transition (create-story → `ready-for-dev`, dev-story → `in-progress`/`review`, code-review → `done` or back to `in-progress`) and they SELECT their work by status — a stray write desyncs the whole pipeline or masks unresolved review findings. The orchestrator writes exactly one status: the epic's `done` at epic completion.
13. **DO NOT start a second autopilot if one is already running.** The run lock is `{project-root}/BMAD-Autopilot/autopilot.lock`, acquired FIRST — initialization Step 0, before the quality-mode question and before any trace write. If the lockfile exists and its mtime is within the last 30 minutes, another autopilot is (or was very recently) active — ABORT and report to the user. If it exists but is older than 30 minutes (stale prior run), overwrite it and log `## [TIMESTAMP] STALE LOCK CLEARED` before proceeding. Refresh the lock's mtime (`touch`) every time you update the Status Dashboard, and delete it at completion.

## Tool Inventory

These are REAL callable functions — not documentation, not placeholders. **TOOL CALLS** (Agent, SendMessage) are actions you perform. **FILE READS** (Read, Write, Edit) are data you consume. Do not confuse the two.

| Tool | When Called |
|------|-------------|
| **Agent** | Once per workflow step — always include `name`, `mode`, `subagent_type` |
| **SendMessage** | Every teammate interaction (progress, status probe) |
| **TaskStop** | Terminate a teammate after COMPLETE/ERROR or a confirmed hang — synchronous, no ack wait |
| **Read** | Read files (sprint status, trace, artifacts) |
| **Write** | Create trace file (initial creation only; the run lock is written via Bash `echo`) |
| **Edit** | Append to trace file, update dashboard cells |
| **Bash** | Timestamps, git operations, process inspection, lock mtime refresh |
