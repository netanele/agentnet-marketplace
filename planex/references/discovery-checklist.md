# Discovery checklist — dimensions to walk with the user

Use this during planning-mode step 2. For each dimension: is it answered by the
user's request, settled by research, worth a question, or a named assumption in
the plan? A dimension nobody addressed is a finding — raise it. The examples
under each dimension are prompts for *you*, not scripts to recite; phrase real
questions in the project's own vocabulary, and skip dimensions that genuinely
don't apply (a CLI tool has no browser story — don't ask about one).

## Goal & success

- What does "done" look like, measurably? Push vague goals ("faster", "cleaner")
  into thresholds the Success-criteria table can hold.
- What is explicitly *out* of scope? Users rarely say; the plan must.
- Is this a parity effort (behavior preserved) or an improvement effort (behavior
  allowed to change)? Where drift is allowed, name it.

## Sequencing & shippability

- Incremental (always shippable, more throwaway shims) vs big-bang (clean end
  state, nothing usable until late)? Recommend based on how well-tested the
  current contract is.
- What's the earliest end-to-end demo ("spine") worth building first?
- Is there a hard deadline, or a cost ceiling that caps the team size?
- Where does the work integrate? Not a question — standing rule: a fresh
  `planex/<slug>` branch cut from the branch the skill was invoked from.
  Record the invoking branch's name in the execution plan; never ask.

## Platforms & environments

- Which OSes/targets ship? (Users routinely add one mid-flight — ask now.)
- Minimum versions, architectures, install constraints per platform?
- Dev environment vs packaged environment differences (permissions, paths,
  signing, sandboxing)?

## Data & continuity

- What existing user data must survive (state, settings, history)? Field-level
  or best-effort?
- Migration/import path for current users? Rollback story if cutover fails?

## Interfaces & contracts

- Which external contracts are frozen (file formats, protocols, URLs, CLI flags,
  third-party tools spawned)? Which are free to redesign?
- Who else consumes them (scripts, integrations, muscle memory)?

## Security & privacy

- What's the current threat model and which mitigations are load-bearing? Any
  known past incidents/exploits that should become permanent regression tests?
- Secrets handling, network egress rules, local-first expectations?

## Performance & footprint

- Baseline-relative or absolute targets? (Either way: record the baseline from
  the live system before work starts.)
- Binary/bundle size, memory, startup, latency — which ones does the user
  actually care about?

## Quality & verification

- What does the existing test suite cover, and is full parity expected?
  Coverage gate carried over?
- What can only be verified manually or on hardware? Who does that, when?

## Packaging & distribution

- Installers, signing/notarization, update path, uninstall?
- What does a brand-new user's first run look like on each platform?

## Operations & lifecycle

- Logs, diagnostics, crash behavior, config surface — preserved or redesigned?
- Long-running stability expectations (soak, leaks, reconnects)?

## People & process

- Who signs off at milestones? How often do they want demos?
- Any parts of the system the user considers untouchable or sacred?
