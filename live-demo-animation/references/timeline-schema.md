# Timeline schema

The build script turns one JSON file into the animation. Everything the viewer sees comes from
here plus the real project directory (tree + file contents are read from disk at build time).

```json
{
  "meta": { … },
  "files": { "path/in/project": "inline content (optional override)" },
  "events": [ { "t": "…", … }, … ]
}
```

## `meta`

| key | default | what it drives |
| --- | --- | --- |
| `title` | `Live demo` | `<title>` and the label in the player bar |
| `project` | basename of `--project-root` | root row of the tree, the cyan name in the status line and the shell prompt |
| `model`, `effort` | `Sonnet 5`, `high` | the magenta `[Sonnet 5 · high]` pill in the status line |
| `contextPct`, `weeklyPct`, `resets` | `8`, `33`, `3d` | the green usage bar and the weekly counter |
| `mode` | `auto mode on` | the yellow `▶▶ auto mode on (shift+tab to cycle)` line |
| `clock` | — | the `done 10:49 AM` time used by `claude.done` when the event gives none |
| `gitBranch`, `gitDirty` | —, `true` | when set, the shell prompt and status line read `project git:(main) ✗` exactly as the app shows a git repo (`gitDirty:false` drops the ✗) |
| `terminalTab` | `zsh` | name of the first terminal tab before any command runs |
| `expanded` | `[]` | tree folders that start open |
| `tabs` | `true` | show the file tab strip (`App.tsx ×`) above an open file; `file.close` clicks its × |
| `welcome` | `true` | Claude Code's startup banner in the empty pane (`cwd`, `version`, `plan` fill it) |
| `deepDive` | — | `{"href":"hooks-deep-dive.html","label":"Deep dive"}` — renders a `📄 Deep dive ↗` link in the player bar. Give the deep-dive file's name **relative to the demo file** (both live in the project root); the build script flags a target that doesn't exist. |
| `typeMs`, `streamMs` | `58`, `9` | ms per character for human typing / Claude's streamed prose |
| `autoplay` | `true` | start playing on load |

## Events

Every event has `t` (type) and an optional `ms` that overrides its default duration. Pointer
movement, the click blip and the pane switch are all implied by the event — you never script the
mouse directly.

### Narration

| event | fields | what happens |
| --- | --- | --- |
| `caption` | `text` (supports `**bold**` and `` `code` ``) | sets the caption strip under the IDE; empty text hides it. Zero duration. |
| `wait` | `ms` (800) | holds the frame — use it after every reveal the viewer needs to read |
| `pointer.hide` | — | hides the mouse pointer |

### Sidebar and file viewer

| event | fields | what happens |
| --- | --- | --- |
| `tree.expand` / `tree.collapse` | `path` | pointer travels to the folder's chevron, clicks, folder opens/closes |
| `file.open` | `path`, `line` (1), `content` (optional) | pointer travels to the row, clicks; the main pane becomes the file viewer scrolled to `line`, the composer chip becomes `[⧉ In <file>]`. Content is read from `--project-root` unless given. Parent folders auto-expand. |
| `file.scroll` | `line` | smooth-scrolls the viewer so `line` is near the top |
| `file.highlight` | `from`, `to` (=from), `scroll` (true) | tints lines `from..to`; scrolls them into view unless `scroll:false`. Send `from:null` to clear. |
| `file.write` | `path`, `content` | the file appears / changes (adds it to the tree if new). Use after a `claude.tool` Write/Update so the viewer can open the result. |
| `file.close` | — | pointer clicks the tab's ×; the main pane returns to Claude Code |
| `claude.show` | — | same as `file.close` without the click (use when the presenter "switches back") |

Line numbers are 1-based and must match the real file — verify with `grep -n` before authoring.

### Claude Code pane

| event | fields | what happens |
| --- | --- | --- |
| `claude.type` | `text`, `keepFile` (false) | the prompt is typed into the composer character by character, then Enter: it becomes a `❯` message. If a file viewer is open, this also switches the main pane back to Claude first (same as `claude.show`) unless `keepFile:true` — a file must be closed (via `file.close`/`claude.show`, or left implicitly by this event) before the composer is visible |
| `claude.status` | `text` (Thinking), `secs`, `secsFrom` (0), `ms` (1200), `keep` (true) | the spinner line `✻ Baking… (3s · esc to interrupt)`; `secsFrom` sets the counter's starting value; it stays on screen through the following tool events until `claude.done`, or clears early if `keep:false` |
| `claude.tool` | `name`, `arg`, `result`, `status` (`ok`/`warn`), `diff` | `⏺ Name(arg)` then, half-way through, `⎿ result`. `diff` is a list of `{t:"ctx"|"add"|"del", old, new, text}` rows rendered like the real Update() view |
| `claude.text` | `text` (markdown-lite: `**bold**`, `` `code` ``, `# heading`) | Claude's prose streams in with a `●` bullet |
| `claude.notice` | `text`, `pink` (true) | a background notification line (pink dot), e.g. a hook's message or a background task result |
| `claude.right` | `text` | a right-aligned green line (`✔ Update installed · Restart to update`) |
| `claude.done` | `secs`, `time`, `verb` (Worked) | removes the spinner and prints `❋ Worked for 9s · done 10:49 AM` |

Result-line conventions (these are what the real terminal prints — copy them):
`Read 120 lines` · `Wrote 34 lines` · `Updated (+3 -1 lines)` · the first ~8 lines of Bash output then `… +N lines` · `Done · 12 tool calls` for an agent · a hook block shows `PreToolUse:Bash hook error: [<command>]: <stderr>` verbatim with `status:"warn"`.

### Terminal panel

| event | fields | what happens |
| --- | --- | --- |
| `term.cmd` | `cmd`, `out`, `html` (false), `keepTab` (false) | pointer clicks into the terminal, the command is typed, Enter, output lines appear one by one; the tab is renamed to the command's first word (as the app does) unless `keepTab` |
| `term.tab` | `name` | pointer clicks `+`, a new tab opens and is selected |
| `term.clear` | — | clears the output |

`out` is plain text. If you need colour (a test runner's green `ok`), set `html:true` and write
`<span class="ok">ok</span>` / `err` / `dim` / `cyan` / `yellow` / `bold` spans yourself — escape `<` and `&`.

## Playback

Keys: Space play/pause · ←/→ previous/next step · C captions · R restart · F fullscreen.
URL: `?step=N` jumps to the end of the Nth timeline event with nonzero duration, paused
(`&frac=0.5` for the middle of it) — N counts individual events, not storyboard beats, so prefer
`?t=<ms>&paused=1` for QA screenshots once you know a beat's boundary time from the timeline JSON
you wrote. `?paused=1` alone just pauses on load.
`window.__demo` exposes `beats`, `total`, `seek(ms)` and `state()` for QA scripts.
