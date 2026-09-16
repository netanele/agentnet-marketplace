---
name: session-terminal-replay
description: Turns the CURRENT Claude Code session's on-disk transcript into a self-contained, animated terminal-replay HTML artifact — reproducing only what a real Claude Code terminal actually shows a user (messages, short per-tool result lines like "Read 42 lines" or "Updated (+3 -1 lines)", never raw tool-call JSON or harness/system plumbing), with play/pause, speed, and scrub controls. Every subagent it spawned gets its own switchable pane, exactly like switching to view a spawned agent's own session in the real product. Use this whenever the user asks to turn "this conversation", "this session", "what we just did", or "this chat" into a replay, recording, demo, animation, video, or terminal recreation — including phrasings like "make a video of this session", "show this as a Claude Code recording", "animate our conversation", or "create an artifact that plays back everything we did" — even if they never say "transcript", "JSONL", or name this skill directly. Always reach for this instead of hand-reconstructing the conversation from your own context: your context can be compacted or summarized as the session grows, but this skill reads the real on-disk session log, so nothing gets lost or invented, no matter how long the session or its subagents ran.
---

# Session terminal replay

## Why this works the way it does

Claude Code logs every session to disk as JSONL, independent of what's still
in your own context window (which can get compacted). Each subagent you
spawn gets its own JSONL file too. Reading those files directly, instead of
recalling the conversation yourself, is the only reliable way to reconstruct
a long session — your own context is not a trustworthy source once
compaction has happened.

Files live at:

- Main session: `~/.claude/projects/<slug>/<session-id>.jsonl`, where
  `<slug>` is the project's absolute working directory with every `/`
  replaced by `-` (e.g. `/Users/x/Desktop/app` → `-Users-x-Desktop-app`).
- Each subagent: `agent-<agentId>.jsonl` somewhere under
  `~/.claude/projects/<slug>/<session-id>/`.

`scripts/build_replay.py` does the finding, parsing, and rendering. Plain
Python 3 stdlib — nothing to install.

## The guiding rule: only what the terminal actually shows

The first version of this skill dumped everything in the log — raw tool-call
JSON, harness plumbing (`mode`, `system`, `agent-name`, hook summaries,
attachments), full untruncated file contents. That is *not* what a Claude
Code session looks like to the person watching it, and it made the replay
unwatchable. The rule now is: **reproduce the real terminal's own display
conventions**, including the ones that summarize or truncate — because doing
that faithfully is what "what I see in a real session" means.

Concretely, `build_replay.py` only emits:

- **Human messages** — full text, exactly as typed. Injected/synthetic
  "user" turns (system-reminders, tool-rejection wrappers) are not human
  messages and are dropped.
- **Assistant text** — full text. Internal `thinking` blocks are dropped;
  they're not part of the normal visible transcript.
- **Tool calls**, rendered the way the CLI renders them: a short head line
  (`⏺ Read(path)`) plus a short result line, never the raw JSON input or the
  full raw output. `Read`/`Write`/`Edit` report line counts; everything else
  gets the first ~8 lines of its result with a "+N more lines" tail, matching
  the CLI's own collapsed-by-default behavior. `AskUserQuestion` and
  `ExitPlanMode` show their actual interactive content (questions, chosen
  answers, approve/reject), since that genuinely is what's shown on screen.
- **All harness/system plumbing is dropped entirely** — it was never visible
  to the user in the first place.

Every subagent (`Agent`/`Task`) becomes its own **pane** — like switching to
view a spawned agent's own session in the real product — rather than being
inlined into the parent's scrollback. The parent pane only ever shows the
call line and a one-line completion summary (`Done · 12 tool calls`) with a
"(view …)" jump link; the agent's own tool calls only appear inside its own
pane, exactly as they would if you switched to watch it live. During
playback the active pane auto-follows whichever one is "currently talking";
clicking any tab (or the jump link) pins that pane manually, and a "↩ follow"
button snaps back to auto-follow.

## Steps

1. **Find this session's identity.** Your environment info names your
   scratchpad directory, shaped like
   `.../<project-slug>/<session-id>/scratchpad`. The `<session-id>` segment
   (the UUID directory that directly contains `scratchpad/`) is this
   session's id. If your environment doesn't expose that, omit
   `--session-id`; the script then falls back to the most-recently-modified
   `.jsonl` directly under the project folder (usually correct, but can be
   wrong with more than one Claude Code window open on the same project —
   flag that to the user if it happens).

2. **Run the build script**, writing output into your scratchpad directory
   (the Artifact tool requires files to live under the working directory or
   the scratchpad):

   ```bash
   python3 <this-skill-dir>/scripts/build_replay.py \
     --cwd "<the project's working directory>" \
     --session-id "<session-id-from-step-1>" \
     --out-dir "<scratchpad>/session-replay"
   ```

   It prints a JSON summary: `event_count`, `data_files`, `html_file`, and
   subagent stats (`agent_calls`, `agents_expanded`, `agents_not_found`). If
   `agents_not_found` > 0, some spawned agent's transcript file couldn't be
   located (can happen for Workflow-spawned agents, or an older session) —
   that call still shows a normal collapsed line in the parent pane, just
   without its own pane to switch into. Mention this to the user rather than
   silently under-delivering.

3. **Publish with the Artifact tool.** `file_path` is the generated
   `index.html`; pass every name in `data_files` through the `files`
   parameter, mapped to itself (there's more than one part file only for
   extremely long sessions). Use `favicon: "🖥️"`, `icon: "terminal"`, and a
   one-sentence `description`. Don't proactively share it further — artifacts
   publish private by default, and this one reflects the real session's
   content.

4. **Report back concisely**: the link, the event count, and any caveat from
   step 2. Don't re-narrate the session in chat — the artifact is the
   deliverable.

## Regenerating for a different session

If the user wants a replay of a *past* session rather than the current one,
list `~/.claude/projects/<slug>/*.jsonl` (skip files inside subagent
subdirectories) and confirm which one with the user if it's not obvious from
timestamps — then pass that file's UUID as `--session-id`.
