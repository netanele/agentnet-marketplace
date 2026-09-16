#!/usr/bin/env python3
"""
Reads a Claude Code session's on-disk JSONL transcript (and every subagent
JSONL spawned from it) and turns it into what the terminal actually SHOWS a
user during a real session: human messages, assistant replies, and short
per-tool result lines (not raw JSON tool input, not harness/system plumbing,
not internal thinking). Switching to a subagent's own view is modeled as a
separate "pane" the player can switch into, matching how Claude Code lets you
view a spawned agent's own session.

Usage:
  python3 build_replay.py --cwd /path/to/project [--session-id ID] --out-dir DIR
"""
import argparse
import glob
import json
import os
import re


def escape_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))

MAX_CHUNK_BYTES = 12 * 1024 * 1024  # stay well under the 16MB per-file artifact cap
RESULT_PREVIEW_LINES = 8
ARG_MAX = 100

AGENT_ID_RE = re.compile(r"agentId:\s*([a-f0-9]{6,})", re.IGNORECASE)


def project_slug(cwd):
    return os.path.abspath(cwd).replace("/", "-")


def find_session_file(project_dir, session_id):
    if session_id:
        path = os.path.join(project_dir, session_id + ".jsonl")
        if not os.path.exists(path):
            raise SystemExit(f"No session file at {path}")
        return path
    candidates = [p for p in glob.glob(os.path.join(project_dir, "*.jsonl")) if os.path.isfile(p)]
    if not candidates:
        raise SystemExit(f"No session .jsonl files found in {project_dir}")
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def read_jsonl(path):
    objs = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                objs.append(json.loads(line))
            except Exception:
                pass
    return objs


def short(s, n=ARG_MAX):
    if s is None:
        return None
    s = s.strip().split("\n")[0]
    return s if len(s) <= n else s[: n - 1] + "…"


def preview(text, n=RESULT_PREVIEW_LINES):
    if not text:
        return ""
    lines = text.rstrip("\n").split("\n")
    shown = "\n".join(lines[:n])
    remaining = len(lines) - n
    if remaining > 0:
        shown += f"\n… (+{remaining} more lines)"
    return shown


def line_count(text):
    if not text:
        return 0
    return text.count("\n") + 1


def find_arg(tool_input):
    for key in ("file_path", "path", "pattern", "command", "url", "query", "skill", "prompt"):
        v = tool_input.get(key)
        if isinstance(v, str):
            return short(v)
    return None


def summarize_tool(name, tool_input, result_text, is_error):
    """Returns (arg, body, variant) the way Claude Code's own terminal would
    show this call: a short head-line argument and a short result line, not
    the raw tool input or the full raw output."""
    variant = "warn" if is_error else None

    if name == "Read":
        arg = find_arg(tool_input)
        if is_error:
            return arg, preview(result_text), "warn"
        return arg, f"Read {line_count(result_text)} lines", None

    if name == "Write":
        arg = find_arg(tool_input)
        if is_error:
            return arg, preview(result_text), "warn"
        return arg, f"Wrote {line_count(tool_input.get('content', ''))} lines", None

    if name in ("Edit", "NotebookEdit"):
        arg = find_arg(tool_input)
        if is_error:
            return arg, preview(result_text), "warn"
        added = line_count(tool_input.get("new_string", ""))
        removed = line_count(tool_input.get("old_string", ""))
        return arg, f"Updated (+{added} -{removed} lines)", None

    if name == "AskUserQuestion":
        qs = tool_input.get("questions", []) or []
        lines = []
        for q in qs:
            lines.append(q.get("question", ""))
            for opt in q.get("options", []) or []:
                lines.append("   - " + (opt.get("label", "") if isinstance(opt, dict) else str(opt)))
        body = "\n".join(lines)
        if result_text:
            body += "\n\n" + preview(result_text)
        return None, body, variant

    if name == "ExitPlanMode":
        # The full plan text is what the real terminal shows for review before
        # the user approves or rejects it — unlike Bash/Read output, it is not
        # collapsed, since the point is that the user has to read all of it.
        plan_text = tool_input.get("plan", "")
        if is_error:
            status = preview(result_text) or "Rejected."
            return None, (plan_text + "\n\n" if plan_text else "") + status, "warn"
        return None, (plan_text + "\n\n" if plan_text else "") + "Plan approved.", "ok"

    if name == "Skill":
        return tool_input.get("skill") or find_arg(tool_input), "", None

    arg = find_arg(tool_input)
    body = preview(result_text) if result_text else ("Error." if is_error else "")
    return arg, body, variant


def find_subagent_file(session_dir, agent_id):
    matches = glob.glob(os.path.join(session_dir, "**", f"agent-{agent_id}.jsonl"), recursive=True)
    return matches[0] if matches else None


def next_pane_id(counter):
    counter[0] += 1
    return f"agent-{counter[0]}"


def diff_from_patch(structured_patch):
    """Turns Claude Code's own structuredPatch (real unified-diff hunks, with
    real line numbers against the actual file) into the row list the
    renderer draws — the same data the real terminal's diff view is built
    from, so line numbers and hunk boundaries match exactly."""
    hunks = []
    for hunk in structured_patch or []:
        old_num = hunk.get("oldStart", 1)
        new_num = hunk.get("newStart", 1)
        rows = []
        for raw in hunk.get("lines", []) or []:
            marker, text = (raw[0], raw[1:]) if raw else (" ", "")
            if marker == "+":
                rows.append({"t": "add", "text": text, "old": None, "new": new_num})
                new_num += 1
            elif marker == "-":
                rows.append({"t": "del", "text": text, "old": old_num, "new": None})
                old_num += 1
            else:
                rows.append({"t": "ctx", "text": text, "old": old_num, "new": new_num})
                old_num += 1
                new_num += 1
        if rows:
            hunks.append(rows)
    return hunks


def process_stream(objs, session_dir, pane, events, pane_counter, stats, skip_first_user=False):
    results_by_id = {}
    for obj in objs:
        if obj.get("type") != "user":
            continue
        content = obj.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        tool_results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
        # toolUseResult is a single object per JSONL line; only trust it when
        # there is exactly one tool_result on this line, so it can't be
        # misattributed to the wrong call.
        structured = obj.get("toolUseResult") if len(tool_results) == 1 else None
        for block in tool_results:
            tid = block.get("tool_use_id")
            if tid:
                text = block.get("content")
                if isinstance(text, list):
                    text = "\n".join(
                        b.get("text", "") for b in text if isinstance(b, dict) and b.get("type") == "text"
                    )
                elif not isinstance(text, str):
                    text = ""
                results_by_id[tid] = {
                    "text": text,
                    "is_error": bool(block.get("is_error")),
                    "structured": structured if isinstance(structured, dict) else None,
                }

    for idx, obj in enumerate(objs):
        t = obj.get("type")
        if t == "assistant":
            for block in obj.get("message", {}).get("content", []) or []:
                if not isinstance(block, dict):
                    continue
                bt = block.get("type")
                if bt == "text":
                    text = block.get("text", "")
                    if text:
                        events.append({"pane": pane, "kind": "assistant_text", "body": text, "markdown": True})
                elif bt == "tool_use":
                    name = block.get("name", "tool")
                    tool_input = block.get("input", {}) or {}
                    result = results_by_id.get(block.get("id"), {})
                    result_text = result.get("text", "")

                    if name in ("Agent", "Task"):
                        stats["agent_calls"] += 1
                        desc = tool_input.get("description") or tool_input.get("subagent_type") or "agent"
                        events.append({"pane": pane, "kind": "tool", "tool": "Task", "arg": short(desc), "body": ""})
                        m = AGENT_ID_RE.search(result_text or "")
                        sub_path = find_subagent_file(session_dir, m.group(1)) if m else None
                        if sub_path:
                            stats["agents_expanded"] += 1
                            sub_pane = next_pane_id(pane_counter)
                            sub_objs = read_jsonl(sub_path)
                            before = len(events)
                            first_prompt = None
                            if sub_objs:
                                msg = sub_objs[0].get("message", {})
                                if isinstance(msg.get("content"), str):
                                    first_prompt = msg["content"]
                            events.append({
                                "pane": sub_pane, "kind": "human",
                                "body": first_prompt or "(no prompt captured)",
                                "label": desc,
                            })
                            process_stream(sub_objs[1:], session_dir, sub_pane, events, pane_counter, stats)
                            tool_calls = sum(
                                1 for e in events[before:]
                                if e["pane"] == sub_pane and e["kind"] == "tool" and e.get("tool")
                            )
                            events.append({
                                "pane": pane, "kind": "tool", "tool": None, "arg": None,
                                "body": f"Done · {tool_calls} tool call{'s' if tool_calls != 1 else ''}",
                                "targetPane": sub_pane, "targetLabel": desc,
                            })
                        else:
                            stats["agents_not_found"] += 1
                            events.append({
                                "pane": pane, "kind": "tool", "tool": None, "arg": None,
                                "body": preview(result_text) or "Done.",
                            })
                    else:
                        is_error = result.get("is_error", False)
                        arg, body, variant = summarize_tool(name, tool_input, result_text, is_error)
                        display_name = name
                        diff = None
                        if not is_error:
                            structured = result.get("structured") or {}
                            wants_diff = name in ("Edit", "NotebookEdit") or (
                                name == "Write" and structured.get("type") == "update"
                            )
                            if wants_diff:
                                diff = diff_from_patch(structured.get("structuredPatch")) or None
                            if name in ("Edit", "NotebookEdit"):
                                display_name = "Update"
                            elif name == "Write":
                                display_name = "Create" if structured.get("type") == "create" else "Update"
                        events.append({"pane": pane, "kind": "tool", "tool": display_name, "arg": arg,
                                        "body": body, "variant": variant, "diff": diff,
                                        "markdown": name == "ExitPlanMode"})

        elif t == "user":
            if skip_first_user and idx == 0:
                continue
            msg = obj.get("message", {})
            content = msg.get("content")
            if isinstance(content, str):
                is_human = (obj.get("origin", {}) or {}).get("kind") == "human"
                if is_human:
                    events.append({"pane": pane, "kind": "human", "body": content})
            # tool_result-only / injected list content: not shown in a real terminal, skip.


def chunk_and_write(events, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    files = []
    chunk, chunk_bytes, part = [], 0, 1

    def flush():
        nonlocal chunk, chunk_bytes, part
        if not chunk:
            return
        name = f"transcript-data-part{part}.js"
        # Escape sequences that would let embedded conversation content (e.g. a
        # Read of an HTML file, or Bash output) break out of a <script> block if
        # this JSON ever ends up inlined in HTML rather than loaded as an
        # external file. Valid JSON string escapes, so this is a no-op on the
        # decoded values.
        safe_json = (json.dumps(chunk)
                     .replace("</", "<\\/")
                     .replace("<!--", "<\\u0021--"))
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write("(function(){window.__TR=window.__TR||[];window.__TR.push.apply(window.__TR,")
            f.write(safe_json)
            f.write(");})();\n")
        files.append(name)
        part += 1
        chunk, chunk_bytes = [], 0

    for ev in events:
        s = json.dumps(ev)
        if chunk_bytes + len(s) > MAX_CHUNK_BYTES and chunk:
            flush()
        chunk.append(ev)
        chunk_bytes += len(s)
    flush()
    return files


def render_html(out_dir, template_path, project_name, event_count, data_files):
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    script_tags = "\n".join(f'<script src="{name}"></script>' for name in data_files)
    html = html.replace("{{DATA_SCRIPTS}}", script_tags)
    html = html.replace("{{SESSION_LABEL}}", escape_html(f"claude — {project_name}"))
    html = html.replace("{{EVENT_COUNT}}", str(event_count))
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--session-id", default=None)
    ap.add_argument("--out-dir", required=True)
    default_template = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                     "assets", "replay-template.html")
    ap.add_argument("--template", default=default_template)
    args = ap.parse_args()

    project_dir = os.path.join(os.path.expanduser("~"), ".claude", "projects", project_slug(args.cwd))
    if not os.path.isdir(project_dir):
        raise SystemExit(f"No Claude Code project directory at {project_dir}")

    session_file = find_session_file(project_dir, args.session_id)
    session_id = os.path.splitext(os.path.basename(session_file))[0]
    session_dir = os.path.join(project_dir, session_id)

    events = []
    stats = {"agent_calls": 0, "agents_expanded": 0, "agents_not_found": 0}
    process_stream(read_jsonl(session_file), session_dir, "main", events, [0], stats)

    files = chunk_and_write(events, args.out_dir)
    html_path = render_html(args.out_dir, args.template, os.path.basename(os.path.abspath(args.cwd)),
                             len(events), files)

    print(json.dumps({
        "session_id": session_id, "session_file": session_file, "event_count": len(events),
        "data_files": files, "html_file": html_path, "out_dir": args.out_dir, **stats,
    }, indent=2))


if __name__ == "__main__":
    main()
