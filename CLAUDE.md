# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`agentnet-marketplace` is a **Claude Code plugin marketplace** — not an application. It has no
build, lint, or test tooling; its "source code" is Markdown skill definitions consumed by Claude
Code itself. The repo currently registers three plugins in the marketplace manifest: `planex`, which
orchestrates multi-agent work via the `Agent`/`SendMessage`/`TaskStop` tools rather than executing
anything itself; `session-terminal-replay`, which renders a session transcript as an HTML replay;
and `tech-deep-dive-artifact`, which writes deep technical explainer pages as local HTML files. A
fourth plugin, `bmad-autopilot`, still lives in the repo but is unregistered from the marketplace
(see below).

## Structure

- `.claude-plugin/marketplace.json` — the marketplace manifest. Every plugin must be registered
  here with `name`, `source` (relative path), `description`, `category`, `tags`. This is the file
  Claude Code reads to discover what's installable from this marketplace.
- `<plugin-name>/SKILL.md` — each plugin's entry point (YAML frontmatter with `name`,
  `description`, optionally `disable-model-invocation` and `argument-hint`, followed by the
  instructions Claude follows when the skill is invoked).
- `<plugin-name>/references/*.md` — detailed instructions loaded on demand by the SKILL.md (kept
  out of the main file to save context until actually needed).
- `<plugin-name>/scripts/` — helper scripts a skill runs (e.g. Python stdlib).
- `<plugin-name>/evals/` — skill-creator eval definitions (not loaded at runtime).
- `<plugin-name>/assets/` — non-Markdown supporting files shipped with a plugin (e.g. a
  standalone HTML dashboard).

There is no shared code between plugins; each is self-contained under its own top-level directory.

## The plugins

### `bmad-autopilot` (unregistered — not currently in the marketplace)

Removed from `.claude-plugin/marketplace.json` because it's not currently relevant; the plugin
directory and its instructions are left intact in case it's re-registered later. Do not treat it
as installable via this marketplace unless its entry is restored.

Autonomous orchestrator for the BMAD Phase-4 story-implementation cycle. Assumes
`/bmad-sprint-planning` and `/bmad-sprint-status` already ran. Acts as a lead agent that asks
exactly one startup question (TEA vs QA quality-assurance mode), then loops through every
epic/story, spawning **one teammate at a time** (never more) via `Agent`, communicating over
`SendMessage`, and logging every step to `{project-root}/BMAD-Autopilot/phase4-trace.md`. The lead
never implements or runs workflows itself — only teammates do.

- `references/initialization.md` — run-lock acquisition, quality-mode question, trace log
  bootstrap, sprint-status resume logic.
- `references/execution-loop.md` — the epic/story loop, teammate spawn/report/shutdown protocol,
  hang detection (10/5/kill), code-review retry loop, commit/push logic, completion summary.
- `assets/autopilot-dashboard.html` — a standalone HTML viewer copied into the project's
  `BMAD-Autopilot/` folder on first run; the human drops `phase4-trace.md` onto it for a visual
  dashboard.
- Critical invariants (see the skill's "Critical Rules" / "Anti-Patterns" sections before editing
  this plugin): one teammate at a time, lead never does implementation work, all lead↔teammate
  communication is `SendMessage` (plain text does not cross agents), trace file is append-only,
  the run lock (`BMAD-Autopilot/autopilot.lock`) prevents concurrent autopilot runs, timestamps
  are Israel time via `TZ='Asia/Jerusalem' date ...`.

### `planex`

Plan-then-execute engine for large engineering efforts (migrations, rewrites, big features), with
explicit invocation only (`disable-model-invocation: true`). Mode is detected from the argument:

- **Planning mode** (`/planex <description>`) — research via parallel `Explore` subagents,
  interview the user in rounds using `AskUserQuestion`, then write three linked documents to
  `docs/implementations/<slug>/`: `plan.md` (the what), `execution-plan.md` (the how — team
  roster, model assignments, review gates), `tasks.md` (the tracker). Stops for explicit approval
  before executing.
- **Execution mode** (`/planex <path/to/plan.md>`) — becomes the team lead: creates the
  `planex/<slug>` integration branch and a `.planex/<effort-slug>` worktree, spawns one named,
  persistent **sonnet** worker per lane in its own worktree (`isolation: "worktree"`), gates every
  merge with a sonnet task-reviewer (`references/task-reviewer.md`, with a security checklist on
  `PT`-tagged tasks), runs a sonnet `security-review` sweep at each milestone, and finishes with
  one **opus** `code-review` + one **opus** `security-review` pass over the whole effort before
  cutover. The task tracker (`tasks.md`, committed on the integration branch) is the single
  source of truth and only the lead edits it.
- `references/discovery-checklist.md` — dimensions to walk with the user during planning
  (sequencing, platforms, data/continuity, interfaces, security, performance, quality, packaging,
  operations, people/process).
- `references/plan-template.md`, `references/execution-plan-template.md`,
  `references/tasks-template.md` — the three document templates; read the relevant one before
  writing that file.
- `references/task-reviewer.md` — the per-task merge-gate reviewer prompt template.
- Effort isolation: everything is namespaced by the effort's slug — branch
  `task/<effort-slug>/<id>-<task-slug>`, integration branch `planex/<slug>`, milestone tags
  `planex/<slug>/M<n>`, worktree `.planex/<slug>` — so several efforts can run concurrently in one
  repo without colliding. Never touch a branch/worktree outside the current effort's namespace.

### `session-terminal-replay`

Model-invocable skill that reads the current session's JSONL transcript (plus each subagent's
`agent-<id>.jsonl`) from `~/.claude/projects/<slug>/` and writes an animated terminal replay into a
`session-replay/` folder in the project root. It shows only what the real terminal shows (no raw
tool JSON or harness plumbing).

- `scripts/build_replay.py` — stdlib-only Python: finds, parses, and renders the transcript.
- `assets/replay-template.html` — the player template the script fills in.

### `tech-deep-dive-artifact`

Model-invocable skill that explains a list of technical topics at engineering depth (real fields,
payloads, configs, limits, traps) as a local, RavTech-themed HTML file written to the project root.

- `assets/ravtech-base.html` — the themed page shell the file is built on.
- `references/components.md` — the component patterns to use inside that shell.
- `evals/evals.json` — skill-creator evals for the skill.

## Working on this repo

- Changes here are prompt-engineering changes, not code changes: there's nothing to compile, and
  validation means re-reading the instructions for internal consistency and, where feasible,
  actually invoking the skill against a scratch project to see how Claude follows it.
- Adding a new plugin means: create `<plugin-name>/SKILL.md` (+ `references/`/`assets/` as
  needed), then register it in `.claude-plugin/marketplace.json`.
- Keep `SKILL.md` lean and push detail into `references/*.md` — the whole point of the split is
  that references only load into context when the skill actually needs them.
