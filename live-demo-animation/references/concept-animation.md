# Concept animation — authoring guide

The **Concept animation** explains *how the mechanism works*: what talks to what, in which order,
with what data — laid out as a diagram that moves. It is the right form when the interesting
thing is invisible in a real session (a hook's stdin payload, a rule entering the context window,
a matcher deciding, an exit code turning into a message). The IDE animation shows the keystrokes;
this one shows the wiring.

Start from `assets/concept-base.html`: the theme, the stage scaling, the panel/card/arrow engine
and the player are all there. You only fill in the `CONFIG` block (`window.CONCEPT`), then write
the file as `<project>/<slug>-concept-animation.html`. Everything else in the file stays as is.

## Stage geometry

1280×720, scaled to fit the window. Header occupies the top 56px, footer (caption + controls)
the bottom 116px, so panels live in **y 72 … 606** and **x 20 … 1260** (`x+w ≤ 1260`,
`y+h ≤ 606`). Typical layouts:

| concept shape | layout |
| --- | --- |
| a config + a script + what happens (hooks, MCP, skills) | two code panels stacked left (`w:548`), one session panel right (`x:604 w:656 h:534`) |
| a file tree + a session + a state that fills (rules, memory, context) | three columns: tree/state `w:262`, session `w:600`, state `w:342` |
| a sequence of stages (pipeline, workflow, agent team) | one wide state panel with `.slot`s that light up in order, a session panel under it |

Pick the layout from the content; don't stamp the same three boxes on every topic.

## Vocabulary (the `CONFIG` keys)

- `meta`: `kicker` (topic · form), `title`, `path` (the real files, `projects/x · a → b`),
  `deepDive` `{href,label}` — a relative link to the deep-dive HTML in the same folder;
  `autoplay:true` to start playing on load (default: paused on step 1).
- `panels[]`: `{id, kind:'code'|'term'|'state', title, tag, x,y,w,h, …}`
  - `code`: `lines[]` (strings) + `lang` (`json` `sh` `ts` `py` `yaml` `txt` `raw`). Line numbers
    are the array index — see "Abridging" below.
  - `term`: a session/shell panel; `welcome` is the html shown before any line. Lines are appended
    by steps from the shared `lines` map.
  - `state`: free html (`.slot`, `.chip`, a table, `.big` numbers); a step can replace it via
    `panels.<id>.html`.
- `cards[]`: floating callouts (`{id,x,y,w,cls:'or'|'cy',title,sub,pre|body}`) — a payload, a
  decision, a "what the model sees" box. Shown by listing the id in a step's `cards`.
- `lines{}`: `{key:{c, h}}` with `c` ∈ `u` (user prompt) `cl` (Claude prose, `⏺` in `.b`) `tool`
  `res` `err` `okr` `hook` `sh` (`$` prefix) `out` `dim` `gap`. `h` is html; use `.badge.wait|blk|ok|info`
  inline for state badges like "tool never ran".
- `steps[]`: one scene each — `title`, `cap` (html; `<code>`, `<em>` for the key word), `dur` ms
  at 1×, then what changes: `panels{id:{on|hot|good, hl[], hotl[], okl[], badge{text,cls}, tag, live, hidden, html}}`,
  `term{id:[lineKeys]}` (cumulative; `{lines:[…], clear:true}` to wipe first), `cards[ids]`,
  `arrows[{from,to,cls,label,fromSide,toSide,rail}]` where an endpoint is `{panel,line}` (a code
  line), `{panel}`, `{card}` or `{sel}`; `recap` html (three `.rcard`s + a `.try` box).

Steps are cumulative for terminals, explicit for everything else: a panel not mentioned in a step
goes dim. That is deliberate — the viewer's eye should be on one thing per scene.

## What makes it teach

- **One decision per scene.** A scene shows one thing changing (a line lights up, a payload
  arrives, a badge flips to `exit 2 · BLOCK`). If you need two highlights, that is two scenes.
- **The invisible made visible.** The best scenes are the ones a real session never shows: the
  JSON on stdin, the glob test with ✓/✗ per pattern, the running total of loaded lines, the
  "prepared · not run yet" state of a tool call. Build those from the deep-dive facts.
- **A negative case and a contrast.** "The safe command sails through", "the non-matching Read
  loads nothing". One scene each; they are what makes the rule stick.
- **A recap card**: three columns (the contract · the traps · what it is not) and a `.try` line
  with the real command the student can run afterwards.
- 8–14 scenes, 4–7 s each. Read every caption aloud once; cut what you would not say.

## Truth rules (same bar as the IDE form)

- Facts come from the deep-dive fact files and from running things in the real project. The
  session panel's Claude turn may be authored (it is a diagram of a turn, not a recording), but
  every tool line, exit code, message and number in it must be one the real system produces.
  Capture a real `claude -p` run when in doubt and copy its lines.
- **Abridging is allowed, hiding it is not.** A `code` panel may shorten a real file to the lines
  that matter, but then its `tag` says `abridged` and captions must not cite its line numbers as
  the file's — say "the `block()` function", not "line 7". If a caption needs a real line number,
  show the real lines around it verbatim.
- Numbers on screen (line counts, sizes, percentages) are measured (`wc -l`, real output), never
  typed from memory.
- English only; RavTech palette only (navy/cyan/orange, red for blocks, green for allow). The
  base file already defines every colour — don't add new ones.

## QA

First run the validator — it parses the config, checks stage geometry, arrow endpoints, line
ranges, line keys, card ids and the deep-dive link, and prints the QA URLs:

```bash
python3 <skill-dir>/scripts/check_concept.py <project>/<slug>-concept-animation.html
```

Then serve the folder over HTTP and screenshot `?step=N&noanim=1` for every scene (N is 1-based
and here it *is* the scene number; `noanim` freezes transitions so the frame is deterministic —
arrows use transform-immune geometry, so they land the same with or without it). Check: no panel overlaps the footer (`y+h ≤ 606`), arrows land on the
element they mean, long code lines are ellipsised not clipped mid-glyph, the deep-dive link is
present, the recap fits without scrolling. Then read each frame as a student would: does it make
sense with only the caption?
