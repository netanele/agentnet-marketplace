---
name: live-demo-animation
description: Build an animated demo of a technical topic for course students — something that moves, not a page to read. Two forms chosen with the user — an "IDE animation" (a pixel-faithful replica of the Claude Code desktop IDE where "a human" opens the real files, types the real prompts, runs the real commands) or a "Concept animation" (a RavTech-themed moving diagram of the mechanism — panels, arrows, payloads, state filling up). Use this whenever the user asks for a demo, live demo, walkthrough, screencast, hands-on or explainer animation, "show it running", "show how X works", "animate a Claude Code session doing X", or wants students to *see* a Claude Code feature (hooks, skills, MCP, agents, settings, workflows, CLAUDE.md, permissions…) in action — even if they never say "animation", "IDE" or "HTML". It runs the tech-deep-dive-artifact skill itself for the facts and the explainer page, so when the ask is only for a page/reference/cheat-sheet to read, use that skill instead; when the ask is for a demo of a topic, or "the demo version" of an existing deep-dive or slide, use this one.
---

# Live demo animation

## What this produces

Two local HTML files in the root of the project's working directory (the directory this skill is
run from), not published anywhere:

1. The animation — one of two forms (see below):
   - `<slug>-ide-animation.html` — **IDE animation**: a self-contained replica of the Claude Code
     desktop app (sidebar file tree · main pane that switches between the Claude Code terminal and
     a file viewer · bottom shell). The topic is demonstrated the way a presenter would do it live:
     open the config, open the code, run it in the shell, ask Claude, watch the harness react.
   - `<slug>-concept-animation.html` — **Concept animation**: a RavTech-themed stage where the
     mechanism is drawn as panels (config, script, session, a state view) that light up, exchange
     payloads over arrows, flip badges (`exit 2 · BLOCK`), and end on a recap card.
   Both have play / pause / step / restart, captions per scene, keyboard control, and a
   `📄 Deep dive ↗` link.
2. `<something>-deep-dive.html` — the explainer page the deep-dive skill writes first, under
   whatever filename it picks. The animation links to it by relative filename, so the two files
   travel together.

## The two forms — and why you ask

| | IDE animation | Concept animation |
| --- | --- | --- |
| Answers | "How do I actually do this?" | "What happens inside when this runs?" |
| Shows | real files opened from the real tree, prompts typed at human speed, real command output, Claude's tool lines as the terminal prints them | the wiring: which file points at which script, the JSON on stdin, the glob test with ✓/✗, the context window filling up, the exit code turning into a message |
| Truth | byte-identical files, captured output, ideally a captured `claude -p` turn | verified facts; source may be abridged (and labelled so); the session panel is a diagram of a turn |
| Best for | labs, "follow along", the moment before students try it themselves | lecture explanation of a mechanism that a real session never shows on screen |
| Fails when | the interesting part is invisible in the UI (a payload, a decision, a scope) — or the topic is not a Claude Code feature at all (the main pane *is* the Claude Code terminal) | the student needs to know where to click and what to type |

They are different teaching moves, so **ask which one the user wants** before building — with
`AskUserQuestion`, one question, options "IDE animation (Recommended)", "Concept animation",
"Both". Put a one-line "use it when…" on each option. Skip the question only when the user already
named a form (the words "IDE animation" / "concept animation", or an unmistakable description such
as "looks exactly like Claude Code" vs "a diagram that animates"). If they pick both, build the
IDE one first; the two share the deep-dive, the facts and the captures.

## Why it is built this way

- **The IDE look has to be the real app.** Students open Claude Code after the session and it must
  look like what they saw. `assets/ide-template.html` was matched against screenshots of the real
  IDE (`assets/reference/`); it is not a stylised "terminal aesthetic". Don't restyle it.
- **The concept look has to be the course.** `assets/concept-base.html` is on the RavTech deck
  palette (navy / cyan / orange, red = block, green = allow) so it sits inside a slide without a
  seam. Don't add colours.
- **The content has to be real in both.** Every file the IDE form opens is read from disk at build
  time and every command output is one you ran; the concept form may abridge, but every fact,
  number, exit code and message on it comes from the deep-dive fact files or from running the
  thing. An invented `npm test` transcript is the same failure as an invented field name.
- **Knowledge first, storyboard second.** A demo chosen from the topic's traps and exact semantics
  (which the deep-dive dug out) shows the moment that makes the concept click — the hook that
  vetoes, the rule that loads only for one path, the agent that can't see the parent's context.
- **Local files, not artifacts.** The course keeps its material on disk and the deep-dive skill
  writes locally too. Same root folder, relative link — nothing to publish, nothing to expire.
  (Both templates load fonts from Google Fonts; everything else is inline.)

## Workflow

### 0. Choose the form

Ask, as described above, unless the user already chose. Remember the answer — it decides steps 4
and 5. Everything before that is shared.

### 1. Gather the knowledge — run the deep-dive skill

Invoke `tech-deep-dive-artifact:tech-deep-dive-artifact` with the user's topic(s). It verifies
facts with per-topic agents, writes `<scratchpad>/<topic>-facts.md` files, and writes its
explainer page into the project root as `<something>-deep-dive.html`. Note that filename — the
animation links to it. Run it even when the user says they don't want the explainer page — the
fact files are the research and the page costs nothing extra; tell them they can delete the page
and omit the deep-dive link. Never storyboard from memory.

Read the fact files and pull out, per topic: the exact identifiers, the real artifact
(config/file/command), the surprising semantic, and the trap. Those four are the candidates for
what the demo shows.

### 2. Pick the project and the beats

**Project.** The project root is the working directory the skill runs in, unless the user names
another. In the course repo that is usually `projects/file-browser` — it carries a real `.claude/`
layer with hooks, rules, skills, agents, workflows, and sample hook events under
`.claude/hooks/samples/`. The project must really contain the artifacts the demo opens; if it
lacks one (no hook, no skill), add the minimal real file *only if the user asked for that*, else
pick a topic-adjacent artifact that does exist and say so.

**Beats.** A demo is 4–8 beats (IDE) or 8–14 scenes (concept), each one thing the student watches
happen. The shape that works for nearly every Claude Code feature:

| beat | IDE animation shows | Concept animation shows |
| --- | --- | --- |
| Where it lives | the sidebar opens to the real file, the viewer scrolls to the lines that matter | the config panel lights up, the wiring line highlighted, an arrow to the script it names |
| What it says | 1–2 highlights on the exact keys/lines | the mechanism line by line: stdin read, the decision, the exit |
| Run it bare | the shell runs the script with real output | (usually skipped — or a `sh` line in the session panel) |
| Now through Claude | a prompt typed into the composer; tool lines; the harness reacts | the session panel: prompt → tool call *prepared, not run* → hook/rule fires → result |
| The invisible part | — (this is where the IDE form is weak) | the payload card, the glob test, the context-window slots, the exit badge |
| The effect / contrast | the changed file opened, or a second command | the safe command that sails through; the non-matching file that loads nothing |
| Recap | last caption | the recap card: contract · traps · what it is not · try-it command |

Write the storyboard as a short list before touching any file: beat → files/commands → caption.
Ask the user only if two storyboards would demonstrate materially different things (e.g. "the
PreToolUse block or the Stop-hook loop?"); otherwise pick the one the fact file marks as the trap.

### 3. Capture reality

For each beat, get the real material:

- **Files:** confirm the path exists and find the line numbers to highlight with `grep -n` on the
  real file. In the IDE form line numbers are the file's and must match disk today. In the concept
  form a panel may be abridged — then its tag says `abridged` and captions never cite its line
  numbers as the file's.
- **Shell commands:** run them (from the project root) and keep the output verbatim; trim to what
  the panel can show (~10 lines) with `… +N lines` where you cut. Only run commands that are safe
  and reversible in that project; for anything destructive, run it against a sample input (the
  hook-sample JSON files exist exactly for this) or show it being blocked.
- **Claude's turn:** two options, in order of preference:
  1. **Capture a real run** when the turn is the point of the demo:
     `claude -p "<prompt>" --output-format stream-json --verbose > run.jsonl` (use
     `--allowedTools`/`--permission-mode` so it doesn't stall on a prompt; consider
     `--max-turns 6`), then `python3 <skill-dir>/scripts/claude_stream_to_events.py --input
     run.jsonl --prompt "<prompt>" > events.json` to get the turn in the terminal's own
     conventions (IDE form: paste as events; concept form: copy its tool/result lines). If
     `claude` is a shell alias that adds flags, call the binary (`command -v claude`, usually
     `~/.local/bin/claude`) so the run stays headless. Run it in a **scratchpad copy of the
     project** (`cp -R`, or `rsync -a --exclude .git`) so the project's own hooks, audit logs and
     the captured turn's edits don't land in the real tree. For a multi-turn demo, capture the
     follow-ups with `--resume <session-id>` (the id is in the run's first `system/init` line).
     Keep `run.jsonl` in the scratchpad and mention its path in the hand-off — it is the proof.
  2. **Author it** when a real run would be slow, non-deterministic or need credentials — but
     author it in the real terminal's conventions (`⏺ Read(path)` / `⎿ Read 120 lines`,
     `Updated (+3 -1 lines)`, a hook's stderr verbatim), with tool calls that are plausible for
     that prompt and results copied from what those tools really return. Say so in the hand-off.
- **Diffs** for `Update`/`Write` tools: real before/after lines.

### 4A. IDE animation — write the timeline and build

Read `references/timeline-schema.md` — the full event reference (fields, defaults, result-line
conventions). Write `<scratchpad>/<slug>/timeline.json`, set `meta.deepDive` to the deep-dive
file's name (relative — both sit in the project root), and build straight into the project root:

```bash
python3 <skill-dir>/scripts/build_demo.py \
  --timeline <scratchpad>/<slug>/timeline.json \
  --project-root <project> \
  --out <project>/<slug>-ide-animation.html
```

It prints the embedded files, a `problems` list (unknown event types, missing fields, a line
number outside the opened file, a `file.open` path that isn't in the tree, a `deepDive.href`
that doesn't exist next to the output), a `warnings` list (files cut at 600 lines, directories
cut at 80 entries, a `term.cmd` shorter than a person types), the **beat table** (each event's
start/end in ms, the total) and ready-made **`qa_urls`** for step 5. Fix every problem — the
animation will not play past a broken event. The script still writes `--out` when `problems` is
non-empty (exit 2), so check `problems` before opening. If the file will be moved after the
build, pass `--final-dir` so the deep-dive link is checked where it will actually live.

Timeline craft that makes it feel like a person:
- A `caption` before each beat ("Step 2 · the hook script — exit 2 blocks"), then a `wait` of
  1.5–2.5 s after anything the student needs to read. Without waits the demo is a blur.
- Prompts typed to Claude read like a real request in the presenter's voice, one sentence, not a
  spec. The composer types at human speed; Claude's reply streams fast — that contrast is real.
- Keep a `claude.status` spinner alive across the tool lines and end the turn with `claude.done`.
- Use the `[⧉ In <file>]` chip naturally: open the file first, then go back and ask Claude about
  it — that's how people use the app.
- 60–120 seconds total at 1× is right for a slide; longer demos become two files.

### 4B. Concept animation — fill the config and write the file

Read `references/concept-animation.md` — the stage geometry, the `CONFIG` vocabulary (panels,
cards, lines, steps, arrows, recap), the layouts per concept shape, and the truth rules. Copy
`assets/concept-base.html` to `<project>/<slug>-concept-animation.html`, replace `<title>`, and
edit only the `<script id="conceptConfig">` block. Set `meta.deepDive` to the deep-dive filename.
Validate before looking: `python3 <skill-dir>/scripts/check_concept.py <file>` parses the block,
checks stage geometry, arrow endpoints, line ranges, card/line keys and the deep-dive link, and
prints the QA URLs (a config error also shows as a red banner on the stage, never a silent
blank).

Scene craft: one decision per scene; the invisible thing made visible (payload card, glob test,
loaded-lines counter, "prepared · not run yet" badge); a negative case and a contrast; a recap
card with a try-it command; 4–7 s per scene, captions you would say aloud.

### 5. Look at it, fix

Serve the project root over HTTP (`python3 -m http.server`; `file://` is blocked by the
Playwright CLI) and screenshot the frames a student will pause on:

- IDE: the `qa_urls` the build printed — one `?t=<ms>&paused=1` per event; open the ones that end
  a beat. Check against `references/ide-look.md`.
- Concept: the `qa_urls` from `check_concept.py` — `?step=N&noanim=1` per scene (`noanim` freezes
  transitions so the frame is deterministic). Check the list at the end of
  `references/concept-animation.md`.

Look at every frame, not just the first, and click the deep-dive link once. Fix, rebuild to the
same path, and re-shoot the frames you changed — stale screenshots from an older build confuse
whoever reviews them.

### 6. Hand over

Give the file paths (animation, deep-dive), then the beats in one line each, then — plainly —
which Claude turns were captured (with the `run.jsonl` path) vs authored, what was abridged
(concept form), and any output you trimmed. Give the timeline JSON / the config block location so
the user can tweak captions or timing and rebuild with the same command.

## Anti-patterns

- **A slideshow in a terminal costume.** If a beat has no file opened, no command run and no
  prompt sent, it is a slide — cut it or turn it into an action (IDE) or a visible state change
  (concept).
- **Claude turns with no tool lines.** Real work shows `⏺` lines. A reply that just narrates is
  the tell of an authored turn.
- **Scrolling text walls.** Highlight 3–12 lines, not the whole file; trim command output.
- **Guessing line numbers or output.** `grep -n` and run the command. Every time.
- **Restyling the IDE** to taste, or **adding colours** to the concept stage.
- **Building the form you find easier** instead of the one the user asked for. Ask.
- **Publishing.** The deliverable is the local file; don't reach for the Artifact tool.
