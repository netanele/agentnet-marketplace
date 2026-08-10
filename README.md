# AgentNet - Marketplace

Internal AgentNet marketplace of [Claude Code](https://code.claude.com) plugins — skills the team
ships to every repo.

## Plugins

### `planex`

Plan-then-execute engine for large engineering efforts — migrations, rewrites, big features —
run by an agent team. Explicit invocation only (it won't trigger itself).

**Usage**

Plan a new effort:
```
/planex <describe what you want to build>
```
Claude researches the codebase, interviews you in a few guided rounds (surfacing things you
probably haven't considered), and writes three linked documents to
`docs/implementations/<slug>/`:
- `plan.md` — the **what**: goal, locked decisions, target architecture, success criteria, risks.
- `execution-plan.md` — the **how**: team roster, model assignments, review gates, milestones.
- `tasks.md` — the **state**: the task tracker the team lead updates as work lands.

It stops and asks for your approval before touching any code.

Execute an approved (or previously-paused) plan:
```
/planex docs/implementations/<slug>/plan.md
```
Claude becomes the team lead: cuts an integration branch, spawns sonnet worker agents (one per
lane, each in its own isolated git worktree) to implement tasks in parallel, gates every merge
with a task-level review, runs a security sweep at each milestone, and finishes with one deep
opus code-review + security-review pass before cutover.

- Multiple efforts can run concurrently in the same repo — everything is namespaced by the
  effort's slug (branches, tags, worktree, tracker).
- Interrupted or crashed runs resume cleanly: re-run `/planex docs/implementations/<slug>/plan.md`
  and Claude reconciles the branch/worktree/tracker state before continuing.

### `bmad-autopilot`

Autonomous orchestrator for the [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) Phase-4
story-implementation cycle. Once you've run `/bmad-sprint-planning` and `/bmad-sprint-status` in a
project, this skill takes over completely: it drives every epic and every story to done using
background teammate agents, asking you only **one** question up front.

**Usage**

```
/bmad-autopilot
```

- Assumes BMAD sprint planning has already produced a `sprint-status.yaml` and story backlog.
- At startup, asks you to choose the quality-assurance mode:
  - **TEA** — full Test Architect path (epic-level test design plus per-story ATDD, automate,
    test-review, NFR, and trace).
  - **QA** — Quinn's `bmad-qa-generate-e2e-tests` run after code-review.
- After that, it runs fully autonomously — no further questions — spawning one teammate agent at
  a time to execute each workflow step, until every epic in the backlog is done.
- Produces a running, auditable log at `{project-root}/BMAD-Autopilot/phase4-trace.md`. On first
  run it also drops `BMAD-Autopilot/autopilot-dashboard.html` next to it — open that file in a
  browser and drop the trace file onto it for a visual run dashboard.
- Safe to resume: re-invoking the skill picks up from the trace log and `sprint-status.yaml`
  where it left off.

## Installing this marketplace

Inside Claude Code, add this repo as a plugin marketplace:

```
/plugin marketplace add netanele/agentnet-marketplace
```

Then install whichever plugin(s) you want:

```
/plugin install planex@agentnet-marketplace
/plugin install bmad-autopilot@agentnet-marketplace
```

Plugins normally activate immediately. If a plugin doesn't show up as available, run
`/reload-plugins`.

Useful follow-up commands:

```
/plugin                                          # browse installed/available plugins interactively
/plugin marketplace update agentnet-marketplace  # pull the latest plugin versions
/plugin disable <plugin-name>@agentnet-marketplace
/plugin enable  <plugin-name>@agentnet-marketplace
```
