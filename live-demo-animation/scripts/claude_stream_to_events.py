#!/usr/bin/env python3
"""Convert a REAL Claude Code run into timeline `claude.*` events.

Input: either
  * the stdout of  `claude -p "<prompt>" --output-format stream-json --verbose`
    (one JSON object per line), or
  * a session transcript `~/.claude/projects/<slug>/<session-id>.jsonl`.

Output: a JSON array of events you paste into a timeline's `events` list,
rendered with the same conventions the real terminal uses (short head line
per tool, `Read N lines` / `Updated (+a -b lines)` result lines, collapsed
output with a `+N more lines` tail). Absolute paths under the run's cwd are
shortened to project-relative, as the terminal shows them.

    python3 claude_stream_to_events.py --input run.jsonl --prompt "the prompt you sent" > events.json

Why this exists: the most realistic Claude turn is one Claude actually
produced. Author the shell and file parts of a demo from real captures, and
when the Claude turn matters, capture that too instead of writing it.
"""
import argparse, json, sys

RESULT_PREVIEW_LINES = 8
ARG_MAX = 90


def short(s, n=ARG_MAX):
    s = str(s or "").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def line_count(text):
    return 0 if not text else text.count("\n") + (0 if text.endswith("\n") else 1)


def preview(text, n=RESULT_PREVIEW_LINES):
    lines = (text or "").rstrip("\n").split("\n")
    if len(lines) <= n:
        return "\n".join(lines)
    return "\n".join(lines[:n]) + f"\n… +{len(lines) - n} lines"


def find_arg(tool_input):
    if not isinstance(tool_input, dict):
        return short(tool_input)
    for k in ("file_path", "command", "pattern", "url", "query", "description", "prompt", "skill", "path"):
        if k in tool_input and tool_input[k]:
            return short(tool_input[k])
    return ""


def result_text(block):
    c = block.get("content")
    if isinstance(c, list):
        return "\n".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    return str(c or "")


def summarize(name, tool_input, res, is_error):
    # find_arg() already tolerates non-dict input; ti is only for the
    # dict-specific .get() lookups below, so a malformed tool_input still
    # falls through to find_arg's own arg instead of losing it.
    ti = tool_input if isinstance(tool_input, dict) else {}
    status = "warn" if is_error else None
    if name == "Read" and not is_error:
        return find_arg(tool_input), f"Read {line_count(res)} lines", None
    if name == "Write" and not is_error:
        return find_arg(tool_input), f"Wrote {line_count(ti.get('content', ''))} lines", None
    if name in ("Edit", "NotebookEdit") and not is_error:
        a = line_count(ti.get("new_string", "")); r = line_count(ti.get("old_string", ""))
        return find_arg(tool_input), f"Updated (+{a} -{r} lines)", None
    if name == "Skill":
        return ti.get("skill") or find_arg(tool_input), "", None
    if name in ("Agent", "Task"):
        return short(ti.get("description") or ti.get("prompt", "")), "Done", "ok"
    return find_arg(tool_input), preview(res) if res else ("Error." if is_error else ""), status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="stream-json stdout or a session .jsonl")
    ap.add_argument("--prompt", default=None, help="the human prompt to emit first as claude.type; "
                     "also the switch that adds the opening claude.status and closing claude.done "
                     "bookends around the captured tool/text events — omit only if you're splicing "
                     "these events into a turn whose bookends you're authoring yourself")
    ap.add_argument("--status", default="Baking", help="spinner verb while tools run")
    ap.add_argument("--cwd", default=None, help="project root to strip from absolute paths (defaults to the run's own cwd from its init event)")
    args = ap.parse_args()

    objs = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                objs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    cwd = args.cwd
    for o in objs:
        if o.get("type") == "system" and o.get("cwd") and not cwd:
            cwd = o["cwd"]

    def rel(a):
        if cwd and isinstance(a, str) and a.startswith(cwd.rstrip("/") + "/"):
            return a[len(cwd.rstrip("/")) + 1:]
        return a

    events = []
    if args.prompt:
        events.append({"t": "claude.type", "text": args.prompt})
        events.append({"t": "claude.status", "text": args.status, "ms": 900})

    pending = {}  # tool_use_id -> event dict (result filled later)
    duration_ms = None
    for o in objs:
        typ = o.get("type")
        msg = o.get("message") if isinstance(o.get("message"), dict) else None
        if typ == "assistant" and msg:
            for b in msg.get("content", []) or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    events.append({"t": "claude.text", "text": b["text"].strip()})
                elif b.get("type") == "tool_use":
                    ev = {"t": "claude.tool", "name": b.get("name", "Tool"), "arg": rel(find_arg(b.get("input", {}))), "result": ""}
                    ev["_input"] = b.get("input", {})
                    pending[b.get("id")] = ev
                    events.append(ev)
        elif typ == "user" and msg:
            for b in msg.get("content", []) or []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    ev = pending.pop(b.get("tool_use_id"), None)
                    if ev is None:
                        continue
                    arg, body, status = summarize(ev["name"], ev.pop("_input", {}), result_text(b), bool(b.get("is_error")))
                    ev["arg"] = rel(arg); ev["result"] = body
                    if status:
                        ev["status"] = status
        elif typ == "result":
            duration_ms = o.get("duration_ms")
    for ev in events:
        ev.pop("_input", None)
    if args.prompt:
        events.append({"t": "claude.done", "secs": round((duration_ms or 12000) / 1000)})
    json.dump(events, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
