---
name: tech-deep-dive-artifact
description: Build a local, RavTech-themed HTML file (written to the project root, not published) that explains a list of technical topics at real engineering depth — exact field names, real payloads, config files, limits, and the traps — instead of a shallow overview. Use this whenever the user hands over a list or cluster of technical subjects and wants them explained, documented, taught, or turned into a reference/explainer/cheat-sheet/one-pager/artifact/page, including phrasings like "explain these concepts", "make me an artifact about X, Y and Z", "write up a technical deep dive on…", "build a reference page for…", or "turn this into course material" — even when they never say "artifact". Also use it when they point at an existing deck slide, doc or transcript and ask for a deeper standalone page out of it.
---

# Technical deep-dive artifact

## What this produces

One local HTML file, written to the root of the project's working directory (not published as an
Artifact): a scrolling, English, RavTech-themed reference page that covers every
requested topic at the depth an engineer needs to actually *do* the thing — real key names, real
payloads, real commands, the limits, and the traps — not a marketing overview.

The reader is a competent engineer who does not know this specific subject. They should be able to
close the page and implement from memory, and come back to it as a lookup table.

## The one thing that makes or breaks the page

**Depth beats coverage.** A page that says "hooks let you run scripts at lifecycle points" is
worthless — the reader already guessed that. A page that shows the exact stdin JSON each hook event
receives, which exit code blocks, and the one event where blocking silently does nothing, is worth
keeping open in a tab.

Every section must carry at least three of these, or it is not finished:

| Depth marker | What it looks like |
| --- | --- |
| **Exact identifiers** | real field/flag/env-var names, spelled as the software spells them |
| **A real artifact** | the actual config file, payload, command, or file tree — not pseudo-code |
| **Numbers** | limits, defaults, timeouts, sizes, versions, prices, complexity |
| **Semantics that surprise** | what happens on the failure path, precedence order, what's silently ignored |
| **A trap** | the mistake people actually make, and why the software doesn't warn you |
| **Boundaries** | what this thing is *not*, and the neighbouring thing it gets confused with |

If you cannot fill those for a topic, that is a signal to go research harder, not to pad with prose.

## Workflow

### 1. Take the topic list literally, and pin the depth

Each topic the user names becomes exactly one section, in the order they gave. Don't merge two of
their topics into one section, don't invent extra ones. If they asked for a specific comparison,
table, or slide to be ported in, that is a hard requirement — fetch the original and carry the real
content, not a paraphrase.

Ask only when the answer would change the page's structure (e.g. "audience: beginners or the team
that already ships this?"). Otherwise assume: experienced engineer, English, single page, read-only.

### 2. Verify before you write — always

Facts on a page get repeated by whoever reads it, so shipping a plausible-but-wrong field name is
the worst failure mode this skill has. Before writing any section, gather primary sources.

**Spawn one verification agent per topic** (not per sub-question), in parallel, and give each the
same four instructions — the first one matters most:

1. **"Write your findings to `<scratchpad>/<topic>-facts.md` and reply with just the path and a
   20-line digest."** A report that exists only in a hand-back is lost if anything goes wrong on
   the way home, and then the research is paid for twice. The file is the deliverable.
2. **"Name the pages you checked."** Give them the doc root to start from. A fact that is real but
   lives on a page nobody opened reads exactly like a fact that doesn't exist — one run marked an
   env-var default "not documented" because it had only grepped the feature page, not the
   environment-variables page.
3. **"Quote exact field names, payload shapes, version numbers and limits."** Paraphrase is where
   correct research turns into a wrong page.
4. **"List separately what you could NOT confirm, and never fill a gap from memory."**

Keep it bounded: aim for a digest of a few hundred lines per topic, not an exhaustive transcript of
the docs. A fact-check that runs longer than the page takes to write is over-scoped — split the
topic or narrow the question, and say so in the prompt.

Then:

- **Prefer the project's own artifacts** over recollection: the real config file in the repo, the
  real transcript, the real slide. Read them.
- **Treat an agent's report as a lead, not as truth**, and spot-check anything load-bearing against
  the source yourself. Anything it flags unconfirmed either gets cut, or stated as the weaker claim
  you *can* support — say "check its README for the current setup" rather than inventing the setup.
- **Watch for a superseded baseline.** If a checker reports that the version you assumed is no
  longer current, that is a finding for the page, not an inconvenience: teach both eras when
  deployed systems still run the old one.
- If the repo has a rule about verifying facts (e.g. `.claude/rules/verify-facts.md`), follow it.

When you drop or soften a claim, tell the user at the end which ones and why. That short list is
what makes the rest of the page trustworthy.

### 3. Design each section's form from its content

The fastest way to make the page feel generated is to stamp the same card grid seven times. Pick the
form each topic's own shape asks for:

| The content is… | Render it as |
| --- | --- |
| a set of mutually exclusive modes | 2–4 panels side by side, each with its invocation line |
| two things people confuse | a comparison table, subject A column tinted |
| a sequence that really is ordered | a horizontal flow strip of nodes with arrows |
| per-variant data of the same shape (events, endpoints, error codes) | tabs, one code block per variant + a facts list beside it |
| a procedure | numbered steps, each ending in the real file or command |
| limits, defaults, pricing | a plain two-column table |
| a decision or judgment | one rule sentence in a callout, stated in plain language |

Numbering is for real sequences only. Don't number a list of independent concepts.

### 4. Build it

Read `assets/ravtech-base.html` — it is the complete theme: tokens, three-state dark mode, and every
component this skill uses (panels, code blocks with syntax spans, tables, tabs, flow strips, steps,
callouts). Start from it and fill it in. Read `references/components.md` for the copy-paste markup of
each component and the rules that keep it from breaking.

Non-negotiables inherited from the RavTech decks and standard artifact-design conventions:

- **Palette:** navy `#0a1f3d` · blue `#1e4d8b` · cyan `#00c8ff` · orange `#ff7a00`, greys
  `#51637c`/`#7c8aa3`, red `#dc4b3e` for warnings. **Fonts:** Rubik (headings), Heebo (body),
  JetBrains Mono (code). The base file already wires these; don't introduce new colors or faces.
- **Code panels stay dark in both themes** (they are terminals), and every `<pre>` gets
  `overflow-x:auto`. Escape `<` as `&lt;` inside code.
- **English only.** These pages are not bilingual, even though the decks are.
- **No emoji as section markers.** A section's eyebrow is its real invocation (`/loop`,
  `PreToolUse`, `pg_stat_statements`) or its category.
- **Everything readable at rest** — no scroll-triggered reveals, nothing parked at `opacity:0`.
- Side gutter ≥16px, stacks cleanly at ~400px, wide tables/code scroll in their own container.

Write the file directly into the root of the project's working directory (the directory this skill
is run from) — a specific, descriptive filename (e.g. `hooks-and-mcp-deep-dive.html`), not into the
scratchpad and not published anywhere. `ravtech-base.html` is already a complete standalone document
(`<!doctype>`, `<html>`, `<head>` with charset/viewport, `<body>`) — just fill in its `<title>`,
masthead, TOC, sections and footer.

### 5. Look once, fix

Take **one** screenshot of the local file (serve it over HTTP — `file://` is blocked by the
Playwright CLI — then `npx playwright-cli navigate` + `screenshot --full-page`). Slice a tall page
into parts and read the slices that cover the sections the user cared about most, not just the top.
Fix what it shows in one pass.

Mojibake in a local screenshot (`â€"`, `Â·`) is almost always the local server sending no charset —
check the file with `grep -c 'â€' file.html` before "fixing" anything. Zero hits means the bytes are
fine; don't add a second charset meta on top of the one already in the file.

### 6. Hand it over

Give the local file path, then a short list of what's in it, then — importantly — **the claims you
could not verify**. Do not bury that.

## Writing the prose

Explain the mechanism, then the consequence. "`stop_hook_active` is true when Claude is already
continuing because of a Stop hook — check it or you'll loop" teaches more in one line than a
paragraph about hook design philosophy.

Keep sentences short and declarative. Cut every "it's important to note", "powerful", "seamlessly".
Write from the reader's side: what they type, what they see, what breaks. A section's lede should
say what the thing *is* in one sentence and what question it answers — the reader decides from that
whether to keep reading.

## Anti-patterns that make these pages fail

- **Restating the name.** "The `timeout` field sets the timeout." Say the default and the unit.
- **Coverage without a spine.** Ten shallow sections beat by three deep ones — but the user asked
  for ten topics, so make all ten deep instead of trimming the list.
- **Inventing plausible fields.** A field name you half-remember is a bug you shipped to a reader.
- **One giant hero.** The page is a reference; the masthead is compact, with jump links.
- **Uniform cards.** See step 3 — form follows content.
