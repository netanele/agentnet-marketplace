---
name: live-demo-animation
description: Turn a technical topic into an animated, hands-on live demo — a local HTML file that plays inside a pixel-faithful replica of the Claude Code desktop IDE (file tree on the left, the Claude Code terminal or an opened file in the main pane, a shell terminal at the bottom) — so course students watch "a human" open the real files, type the real prompts, run the real commands and see the real output. It first gathers the topic's knowledge by running the tech-deep-dive-artifact skill (research + the local deep-dive page), then storyboards and builds the animation from real captures in a real project, writes it next to the deep-dive file in the project root and links the two. Use this whenever the user asks for a demo, live demo, walkthrough, hands-on animation, screencast, "show it running", "show how X is implemented", "animate a Claude Code session doing X", or wants students to *see* a Claude Code feature (hooks, skills, MCP, agents, settings, workflows, CLAUDE.md, permissions…) in action — even if they never say "animation", "IDE" or "HTML". Also use it when they hand over a deep-dive page, slide or topic list and ask for "the demo version" of it.
---

# Live demo animation

## What this produces

Two local HTML files in the root of the project's working directory (the directory this skill is
run from), not published anywhere:

1. `<slug>-live-demo.html` — a self-contained animation of the Claude Code desktop app: sidebar
   file tree, main pane (Claude Code terminal ⇄ file viewer), bottom shell. The topic is
   demonstrated end to end the way a presenter would do it live: open the config, open the code,
   run it in the shell, then ask Claude to do the thing and watch the harness react. Play / pause /
   step / scrub, a caption strip, keyboard control, and a `📄 Deep dive ↗` link in the player bar.
2. `<something>-deep-dive.html` — the explainer page the deep-dive skill writes first, under
   whatever descriptive filename it picks (not necessarily sharing the demo's slug). The demo links
   to it by that relative filename, so the two files travel together.

The student should be able to say afterwards: "I saw where it lives, what it says, what happens
when it runs, and what Claude showed me." That is the bar — not "I saw a diagram of it".

## Why it is built this way

- **The look has to be the real app.** Students will open Claude Code after the session and it
  must look like what they saw. The template (`assets/ide-template.html`) was matched against
  screenshots of the real IDE (`assets/reference/`); it is not a stylised "terminal aesthetic".
  Don't restyle it; if something diverges from a new real screenshot, fix the template against
  that screenshot and say so.
- **The content has to be real too.** Every file the animation opens is read from a real project
  on disk at build time, and every command output is one you actually ran. An invented `npm test`
  transcript is the same failure as an invented field name in a reference page — it gets copied.
  The tree is generated from the real directory, so even the sidebar is honest.
- **Knowledge first, storyboard second.** A demo that only shows "the happy path click" teaches
  nothing; a demo chosen from the topic's traps and exact semantics (which the deep-dive already
  dug out) shows the moment that makes the concept click — the hook that vetoes, the rule that
  loads only for one path, the agent that can't see the parent's context.
- **Local files, not artifacts.** The course keeps its material on disk (decks iframe local pages,
  sessions run offline), and the deep-dive skill writes locally too. Same root folder, relative
  link — nothing to publish, nothing to expire. (The template does load JetBrains Mono from Google
  Fonts over the network for fidelity to the real app's font; everything else is inline. Say so if
  the user needs a fully offline copy.)

## Workflow

### 1. Gather the knowledge — run the deep-dive skill

Invoke `tech-deep-dive-artifact:tech-deep-dive-artifact` with the user's topic(s). It verifies
facts with per-topic agents, writes `<scratchpad>/<topic>-facts.md` files, and writes its
explainer page into the project root as `<something>-deep-dive.html`. Note that filename — the
demo links to it. If the user says they don't need the explainer page, still do that skill's
research step (the fact files) and skip its build — never storyboard from memory; then omit
`meta.deepDive`.

Read the fact files when they're done and pull out, per topic: the exact identifiers, the real
artifact (config/file/command), the surprising semantic, and the trap. Those four are the
candidates for what the demo shows.

### 2. Pick the project and the beats

**Project.** The project root is the working directory the skill runs in, unless the user names
another. In the course repo that is usually `projects/file-browser` — it carries a real `.claude/`
layer with hooks, rules, skills, agents, workflows, and sample hook events under
`.claude/hooks/samples/`. The project must really contain the artifacts the demo opens; if it
lacks one (no hook, no skill), add the minimal real file *only if the user asked for that*, else
pick a topic-adjacent artifact that does exist and say so.

**Beats.** A demo is a sequence of 4–8 beats, each one thing the student watches happen. The
shape that works for nearly every Claude Code feature:

| beat | what the viewer sees | timeline events |
| --- | --- | --- |
| Where it lives | the sidebar opens to the real file, the viewer scrolls to the lines that matter | `tree.expand`, `file.open`, `file.highlight`, `wait` |
| What it says | 1–2 highlights on the exact keys/lines, caption naming the semantic | `file.highlight`, `caption` |
| Run it bare | the shell runs the script/command by hand with real output | `term.cmd` (captured output) |
| Now through Claude | a prompt typed into the composer; tool lines; the harness reacts | `claude.type` (switches the main pane back to Claude on its own if a file is still open), `claude.status`, `claude.tool`, `claude.text`, `claude.done` |
| The effect | the file/log/test that changed, opened in the viewer or shown in the shell | `file.write` + `file.open`, or `term.cmd` |
| The trap (optional) | the variant that silently does nothing / the wrong exit code / the wrong scope | another short `claude.type`…`claude.done` or `term.cmd` |

Not every beat is mandatory — a `CLAUDE.md` demo has no "run it bare" — but "now through Claude"
almost always is, because the topic is about what Claude does with the artifact. A negative case
("the rule did *not* load for this file") is often the most convincing beat of all.

Write the storyboard as a short list before touching JSON: beat → files/commands → caption. Ask
the user only if two storyboards would demonstrate materially different things (e.g. "the
PreToolUse block or the Stop-hook loop?"); otherwise pick the one the fact file marks as the trap.

### 3. Capture reality

For each beat, get the real material:

- **Files:** confirm the path exists and find the line numbers to highlight with `grep -n` on the
  real file. Line numbers in the timeline are 1-based and must match the file on disk today.
- **Shell commands:** run them (from the project root) and keep the output verbatim; trim to what
  the terminal panel can show (~10 lines) with `… +N lines` where you cut. Only run commands that
  are safe and reversible in that project; for anything destructive, run it against a sample input
  (the hook-sample JSON files exist exactly for this) or show it being blocked.
- **Claude's turn:** two options, in order of preference:
  1. **Capture a real run** when the turn is the point of the demo:
     `claude -p "<prompt>" --output-format stream-json --verbose > run.jsonl` (use
     `--allowedTools`/`--permission-mode` so it doesn't stall on a prompt; consider
     `--max-turns 6`), then `python3 <skill-dir>/scripts/claude_stream_to_events.py --input
     run.jsonl --prompt "<prompt>" > events.json` to get `claude.*` events in the terminal's own
     conventions. If `claude`
     is a shell alias that adds flags, call the binary (`command -v claude`, usually
     `~/.local/bin/claude`) so the run stays headless. Run it in a **scratchpad copy of the
     project** (`cp -R`, or `rsync -a --exclude .git`) so the project's own hooks, audit logs and
     the captured turn's edits don't land in the real tree; the copy's tree is identical, so
     nothing in the animation changes. For a multi-turn demo, capture the follow-ups with
     `--resume <session-id>` (the id is in the run's first `system/init` line). Keep `run.jsonl`
     in the scratchpad and mention its path in the hand-off — it is the proof the turn is real.
  2. **Author it** when a real run would be slow, non-deterministic or need credentials — but
     author it in the real terminal's conventions (`⏺ Read(path)` / `⎿ Read 120 lines`,
     `Updated (+3 -1 lines)`, a hook's stderr verbatim under `status:"warn"`), with tool calls
     that are plausible for that prompt and results copied from what those tools really return.
     Say in the hand-off which turns were authored.
- **Diffs** for `Update`/`Write` tools: real before/after lines, and then a `file.write` so the
  viewer can open the changed file.

### 4. Write the timeline and build

Read `references/timeline-schema.md` — it is the full event reference (fields, defaults,
result-line conventions). Write `<scratchpad>/<slug>/timeline.json`, set `meta.deepDive` to the
deep-dive file's name (relative — both files sit in the project root), and build straight into the
project root:

```bash
python3 <skill-dir>/scripts/build_demo.py \
  --timeline <scratchpad>/<slug>/timeline.json \
  --project-root <project> \
  --out <project>/<slug>-live-demo.html
```

It prints the embedded files, the tree size and a `problems` list (unknown event types, missing
fields, a `file.open` path that isn't in the tree, a `deepDive.href` that doesn't exist next to
the output). Fix every problem — the animation will not play past a broken event. The script still
writes `--out` even when `problems` is non-empty (exit code 2), so don't mistake a stale file left
over from a broken build for a working one — always check `problems` before opening the output.

Timeline craft that makes it feel like a person:
- A `caption` before each beat ("Step 2 · the hook script — exit 2 blocks"), then a `wait` of
  1.5–2.5 s after anything the student needs to read. Without waits the demo is a blur.
- Prompts typed to Claude read like a real request in the presenter's voice, one sentence, not a
  spec. The composer types at human speed; Claude's reply streams fast — that contrast is real.
- Keep a `claude.status` spinner alive across the tool lines and end the turn with `claude.done`.
- Use the `[⧉ In <file>]` chip naturally: open the file first, then go back and ask Claude about
  it — that's how people use the app.
- 60–120 seconds total at 1× is right for a slide; longer demos become two files.

### 5. Look at it, fix

Serve the project root over HTTP (`python3 -m http.server`; `file://` is blocked by the
Playwright CLI) and screenshot the frames a student will pause on. The player's `?step=N` counts
individual timeline events, not storyboard beats — a beat is usually several events, so don't guess
N. Instead read the `start`/`dur` (ms) of the last event in each storyboard beat straight from the
timeline JSON you wrote, and load `?t=<ms>&paused=1` (add `&frac=0.4`-style math on top of a
`start` if you want a mid-event frame). Read `references/ide-look.md` for what to check. Look at
every beat's frame, not just the first, and click the deep-dive link once. Fix, rebuild with the
same `--out`, and re-shoot the frames you changed — screenshots from an older build with different
event timings confuse whoever reviews them.

### 6. Hand over

Give both file paths (demo, deep-dive), then the beats in one line each, then — plainly — which
Claude turns were captured (with the `run.jsonl` path) vs authored, and any output you trimmed.
Give the timeline JSON path so the user can tweak captions or timing and rebuild with the same
command.

## Anti-patterns

- **A slideshow in a terminal costume.** If a beat has no file opened, no command run and no
  prompt sent, it is a slide — cut it or turn it into an action.
- **Claude turns with no tool lines.** Real work shows `⏺` lines. A reply that just narrates is
  the tell of an authored turn.
- **Scrolling text walls.** Highlight 3–12 lines, not the whole file; trim command output.
- **Guessing line numbers or output.** `grep -n` and run the command. Every time.
- **Restyling the IDE** to taste. Its job is to look like the real thing.
- **Publishing.** The deliverable is the local file; don't reach for the Artifact tool.
