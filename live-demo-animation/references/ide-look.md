# What the real IDE looks like — fidelity checklist

The template reproduces the Claude Code desktop app's three-pane layout. The screenshots in
`assets/reference/` are the ground truth (`ide-claude-pane.png`: Claude pane + terminal;
`ide-file-viewer.png`: a file open in the main pane). When something looks off, open them next to
your screenshot; do not restyle from memory. (If that folder is empty, ask the user for a fresh
screenshot of their app before touching any colour or metric.)

## Layout (1280×720 reference frame)

The layout is fluid (no fixed 1280×720 anywhere in the template), so this checklist's pixel widths
are only true at that viewport — set the Playwright CLI browser window to 1280×720 before
screenshotting, or the sidebar/status-line checks below will fail spuriously at another size.

```
┌ sidebar 236px ┬ main pane ─────────────────────────────────────────┐
│ Search in     │ ▌ Claude Code pane (black)  OR  file viewer (cream) │
│ project       │                                                     │
│ ⌄ ⌂ project   │ ───────────────────────────── (grey rule)           │
│  › 📁 .claude │ ❯ [⧉ In App.tsx] █                                  │
│  › 📁 src     │ ───────────────────────────── (grey rule)           │
│    M↓ CLAUDE… │ → project git:(main) ✗ [Fable 5.1 · high] ██▒▒ 29% · Session (5hr) 4% … │
│               │ ▶▶ auto mode on (shift+tab to cycle)                │
│               │ ⧉ +2 more · index · deep-dive · /artifacts to see all │
│               ├──── cream split line ───────────────────────────────┤
│               │ [− 14 +][+][⌄][⛶][⊠] │ ➜ project pwd               │
│               │ >_ pwd            ×  │ /Users/…/project            │
└───────────────┴──────────────────────┴─────────────────────────────┘
  caption strip (navy, outside the app)         player controls (navy)
```

- **Sidebar**: near-black `#0c0f14`, JetBrains Mono 12.5px, 20px rows, chevrons `›` that rotate
  when open, blue folder glyphs (special colours: `.github` orange, `node_modules` green,
  `src` outlined; `.claude` is a plain blue folder like the rest), file badges by type (`M↓` blue for Markdown, `{..}` JSON,
  `</>` orange HTML, red `npm` for package files, `TS`, `⚛` for tsx, `◆` orange for .gitignore).
  Long names are cut with an ellipsis (`post-edit-check.…`); the selected file row has a grey
  `#1f242b` band; the root row carries an orange dot at its right edge when the repo is dirty.
  Folders sort before files, both case-insensitively — the build script does this.
- **A thin blue scroll thumb sits on the LEFT edge of the main pane** (`#4a7ede`), — visible at the
  top of the pane in both reference shots (Claude pane and viewer). Keep it; it is one of the
  tells that this is the real app. If a future screenshot shows it belongs to the sidebar instead,
  move it then, not before.
- **Claude pane**: pure black, `#e6e6e6` text. A small bordered `✻ Welcome to Claude Code` box at
  the top of a fresh session. Assistant prose starts with a `●` bullet; tool calls are
  `⏺ Name(arg)` with the name in clay `#e5645a` and the result under a `⎿` elbow in grey (a
  blocked call's result is clay); the spinner is `✻ Baking… (3s · esc to interrupt)`; a finished
  turn prints `❋ Worked for 9s · done 10:49 AM` in grey; background notices use a pink dot; the
  composer is `❯` + a cyan `[⧉ In <file>]` chip when a file is open + a green outlined block
  cursor, **bracketed by a grey rule above and below**. The status line: `→` grey, project name
  cyan bold, `git:(main) ✗` in a repo, `[Fable 5.1 · high]` magenta, a green context bar (solid
  fill, hatched remainder) + `29%`, `· Session (5hr) 4% (resets 3h)`; second line `▶▶ auto mode
  on` yellow bold + `(shift+tab to cycle)` dim yellow; an optional third row `⧉ +2 more · … ·
  /artifacts to see all` when the session has artifacts.
- **File viewer**: cream `#f5f0e6`, a 58px right-aligned grey gutter, 19px lines, no wrapping
  (long lines run off the right edge, exactly as in the app). Syntax colours: keywords crimson
  `#c8213a`, identifiers/components purple `#6f42c1`, strings green `#3f7d2c`, comments grey
  `#7a7a7a`. **No tab strip** above the file — line 1 sits flush under the pane's top edge (the
  template only draws one if `meta.tabs:true`).
- **Terminal panel**: black; left column 174px with the dark rounded toolbar buttons
  (`− 14 +`, `+`, `⌄`, `⛶`, `⊠`) and the tab list (`>_ name ×`, selected tab on dark blue
  `#182636`); right column is the shell: `➜` green, project name cyan bold, command green,
  output plain white. In a git repo the prompt is `➜ project git:(main) ✗` (`git:(` blue, branch red,
  `✗` yellow when dirty) and the same segment follows the project name in the status line — set
  `meta.gitBranch`. After a command runs, the app renames the tab to that command.

## The pointer and the typing

- The pointer is a white macOS arrow with a dark outline. It travels (≈0.5 s ease) to the row or
  button it is about to click, dips on the click, and hides while text is typed. It does not
  wander when nothing needs clicking.
- Human typing runs at ~58 ms per character in both the composer and the shell; Claude's own
  prose streams much faster (~9 ms/char). Do not make Claude "type" at human speed — the real
  terminal streams.
- Output appears line by line (~70 ms per line), not as a single paste.

## What to check in every QA screenshot

1. Sidebar still 236px wide, nothing wrapped, the opened file's row highlighted.
2. Nothing in the main pane overflows vertically — the Claude pane scrolls to the bottom on its
   own; a long file scrolls to the requested line.
3. Status line intact (project name, model pill, usage bar, mode line) — a stray `undefined`
   there means a missing `meta` key.
4. The caption strip (navy, between the IDE and the controls — deliberately outside the app so it
   never covers it) holds one line (~90 chars); longer captions wrap and push the IDE up.
5. The `📄 Deep dive ↗` link is present in the player bar and opens the deep-dive file.
6. The frame you screenshot at `?t=<ms>` is what a student sees when the presenter pauses there:
   it must make sense on its own. (`?step=N` also works, but `N` counts individual timeline events,
   not storyboard beats — prefer `t` computed from the timeline JSON you wrote.)
