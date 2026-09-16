---
name: tech-deep-dive-artifact
description: Build a published, RavTech-themed HTML artifact that explains a list of technical topics at real engineering depth — exact field names, real payloads, config files, limits, and the traps — instead of a shallow overview. Use this whenever the user hands over a list or cluster of technical subjects and wants them explained, documented, taught, or turned into a reference/explainer/cheat-sheet/one-pager/artifact/page, including phrasings like "explain these concepts", "make me an artifact about X, Y and Z", "write up a technical deep dive on…", "build a reference page for…", or "turn this into course material" — even when they never say "artifact". Also use it when they point at an existing deck slide, doc or transcript and ask for a deeper standalone page out of it.
---

# Technical deep-dive artifact

## What this produces

One published Artifact: a scrolling, English, RavTech-themed reference page that covers every
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
the worst failure mode this skill has. Before writing any section, gather primary sources:

- **Spawn verification agents in parallel** (one per topic cluster) against official docs, and use
  the doc-fetching MCP if one is configured. Ask for *exact field names, exact payload shapes,
  version numbers and limits*, and explicitly ask them to mark anything they could not confirm.
- **Prefer the project's own artifacts** over recollection: the real config file in the repo, the
  real transcript, the real slide. Read them.
- **Treat an agent's report as a lead, not as truth.** Anything it flags unconfirmed either gets
  cut, or stated as the weaker claim you *can* support. Say "check its README for the current
  setup" rather than inventing the setup.
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

Non-negotiables inherited from the RavTech decks and the artifact platform:

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

Write the file to your scratchpad directory, not into the user's repo, unless they asked for a file
in the project.

### 5. Look once, fix, publish

Take **one** screenshot of the local file (serve it over HTTP — `file://` is blocked by the
Playwright CLI — then `npx playwright-cli navigate` + `screenshot --full-page`). Slice a tall page
into parts and read the slices that cover the sections the user cared about most, not just the top.
Fix what it shows in one pass, then publish with the Artifact tool: a specific two-to-four-word
`<title>`, one emoji favicon, and a one-sentence description.

Mojibake in a local screenshot (`â€"`, `Â·`) is almost always the local server sending no charset —
check the file with `grep -c 'â€' file.html` before "fixing" anything.

### 6. Hand it over

Give the link, then a short list of what's in it, then — importantly — **the claims you could not
verify**. Do not bury that.

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
