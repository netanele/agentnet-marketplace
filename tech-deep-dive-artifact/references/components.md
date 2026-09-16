# Component markup

Copy-paste markup for each block in `assets/ravtech-base.html`. All classes already exist in the
base stylesheet — don't restyle them per page; if a section needs something new, add one small rule
rather than inventing a parallel system.

## Contents

- [Section shell](#section-shell)
- [Code panel](#code-panel)
- [Panel grid (modes / facts)](#panel-grid)
- [Tables](#tables)
- [Callouts](#callouts)
- [Flow strip](#flow-strip)
- [Tabs (per-variant data)](#tabs)
- [Numbered steps](#numbered-steps)
- [Page chrome](#page-chrome)

## Section shell

One per topic, in the order the user listed them. The eyebrow (`.kind`) is a category or the real
invocation; the lede is one sentence saying what this is and what it answers.

```html
<section id="hooks">
  <div class="sec-head">
    <span class="kind">Deterministic control</span>
    <h2><code>Hooks</code> — your code, at fixed points</h2>
    <p class="lede">A hook is your code that the harness runs at a fixed point…</p>
  </div>
  …content…
</section>
```

## Code panel

The workhorse. The bar holds the real filename (or `stdin`, or the shell) and a right-side label.
Syntax spans: `.k` key/identifier · `.s` string · `.c` comment · `.w` keyword/shell builtin ·
`.ok` boolean/success. Escape `<` as `&lt;` and `&` as `&amp;`.

```html
<div class="code">
  <div class="bar"><i></i><i></i><i></i><span class="nm">.claude/settings.json</span><span class="lbl">project</span></div>
<pre>{
  <span class="k">"hooks"</span>: { <span class="k">"PreToolUse"</span>: [ … ] }
}</pre>
</div>
```

`<pre>` must start at column 0 in the HTML source — indentation inside `<pre>` is rendered.

`.prose` is a **container** class — a `<div>` holding several paragraphs, stacked with `gap`. On a
single `<p>` the base file resets it to `display:block`; without that reset every inline `<code>`
becomes its own flex item and the sentence shatters into one word per line.

## Panel grid

For 2–4 mutually exclusive modes, or for short "facts worth their own box". `.sig` is a monospace
invocation line. `.tag` colors: `cy` (neutral/info), `or` (control/caution), `gr` (good), `rd` (bad).

```html
<div class="grid g3">
  <div class="panel">
    <span class="tag cy">interval + prompt</span>
    <h3>Fixed schedule</h3>
    <div class="sig">/loop 5m check the deploy</div>
    <p>What it does, what it costs, when it stops.</p>
  </div>
</div>
```

`g2` = min 300px columns, `g3` = min 240px. Both wrap on their own; never set a fixed column count.

## Tables

Always wrapped in `.tscroll` so a wide table scrolls instead of the page. First column is the label
column (bold, no wrap). Add `.cmp` when column 2 is "subject A" in an A-vs-B comparison — it tints
that column and colors the two headers.

```html
<div class="tscroll">
  <table class="cmp">
    <thead><tr><th style="width:20%">Capability</th><th>Agent</th><th>Skill</th></tr></thead>
    <tbody>
      <tr><td>Execution context</td><td><b>Always</b> separate</td><td><b>Inline</b> by default</td></tr>
      <tr><td>Agent-only</td><td colspan="2"><div class="keys"><code>maxTurns</code><code>memory</code></div></td></tr>
    </tbody>
  </table>
</div>
```

`.keys` is a wrapping row of `<code>` chips — use it for "all the fields that only exist here".
`<span class="yes">Yes</span>` for a positive cell.

## Callouts

```html
<p class="note">Plain aside — a neighbouring command, a "see also".</p>
<p class="note warn"><b>Not a typo:</b> the trap, and why nothing warns you.</p>
<p class="note rule">The one-line rule the reader should remember instead of the table.</p>
```

Use `.rule` at most once or twice per page — it's the sentence you'd want them to quote back.

## Flow strip

Only for a real sequence. Wrap in `.flow` (it scrolls horizontally); `.hot` marks the step that can
intervene; `.loopgroup` boxes a sub-sequence that repeats, and prints its caption from CSS
(`content:` in the base file — edit that string to match your loop).

```html
<div class="flow" role="img" aria-label="…describe the sequence for screen readers…">
  <ol>
    <li><div class="node"><b>SessionStart</b><span>startup · resume</span></div><span class="arr">→</span></li>
    <li><div class="node hot"><b>PreToolUse</b><span>can block</span></div></li>
  </ol>
</div>
<div class="side-events"><div><b>Notification</b> — fires out of band</div></div>
```

`.side-events` is for events/branches that don't sit on the main line.

## Tabs

The right form for N variants of one shape: events, endpoints, error codes, providers. Each pane is
a code block plus a facts list (`<dl>`), so the reader gets the payload and its rules together.
The base file's script handles selection and arrow keys; keep `aria-selected`, `tabindex`, `hidden`
and the `id`/`aria-controls` pairing intact, and give the first pane no `hidden`.

```html
<div class="tabs" id="payloads">
  <div class="tablist" role="tablist" aria-label="Hook event payloads">
    <button role="tab" id="t-pre" aria-controls="p-pre" aria-selected="true">PreToolUse</button>
    <button role="tab" id="t-post" aria-controls="p-post" aria-selected="false" tabindex="-1">PostToolUse</button>
  </div>
  <div class="tabpane" role="tabpanel" id="p-pre" aria-labelledby="t-pre">
    <div class="code">…</div>
    <div class="explain">
      <dl><dt>Matcher</dt><dd>tool name</dd><dt>Exit 2</dt><dd><b>Blocks the call</b></dd></dl>
      <p class="muted">One line of judgment the table can't carry.</p>
    </div>
  </div>
  <div class="tabpane" role="tabpanel" id="p-post" aria-labelledby="t-post" hidden>…</div>
</div>
```

Keep the `<dt>` labels identical across panes (Matcher / Exit 2 / JSON / …) so the reader can scan
between tabs and compare the same row.

## Numbered steps

For a procedure. Each step ends in a real file or command — a step with only prose is a paragraph
wearing a number.

```html
<div class="steps">
  <div class="step"><div>
    <h3>Register hooks in settings</h3>
    <p class="muted" style="max-width:70ch">Why this shape…</p>
    <div class="code">…</div>
  </div></div>
</div>
```

## Page chrome

- **Masthead**: eyebrow (course/product + version), `<h1>` with one cyan-accented span, a ≤62ch
  sub, `.jump` pills linking to every section (they double as the phone nav), and a `.stamp` line
  saying what the page was checked against and when.
- **TOC**: `nav.toc` is sticky and appears at ≥1040px only; keep its entries in section order.
- **Footer**: the source list — the actual doc paths or file paths you verified against.

Anchors: `id` on every `<section>`, and the same ids in both `.jump` and `.toc`.
