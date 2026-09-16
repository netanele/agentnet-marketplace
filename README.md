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

### `session-terminal-replay`

Turns the current Claude Code session's on-disk transcript into a self-contained, animated
terminal-replay HTML artifact (play/pause, speed, scrub), with a switchable pane per subagent.
Triggers on requests like "make a replay/video of this session".

### `tech-deep-dive-artifact`

Builds a published, RavTech-themed HTML artifact that explains a list of technical topics at real
engineering depth — exact field names, payloads, configs, limits, and traps. Triggers on requests
like "explain these concepts" or "make me a reference page for X, Y and Z".

## Installing this marketplace

Inside Claude Code, add this repo as a plugin marketplace:

```
/plugin marketplace add netanele/agentnet-marketplace
```

Then install whichever plugin(s) you want:

```
/plugin install planex@agentnet-marketplace
/plugin install session-terminal-replay@agentnet-marketplace
/plugin install tech-deep-dive-artifact@agentnet-marketplace
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
