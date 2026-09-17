#!/usr/bin/env python3
"""Build a self-contained IDE animation (Claude Code IDE look) from a timeline
JSON + a real project directory.

    python3 build_demo.py --timeline demo.json --project-root /path/to/project \
        --out /path/to/project/hooks-ide-animation.html

What it does (stdlib only):
  * reads the real file tree from --project-root (top level + every directory
    the timeline expands/opens), so the sidebar is the real sidebar;
  * reads every file the timeline opens from disk (unless the timeline gives
    inline `content`), so the viewer shows real code;
  * validates the events (types, required fields, line numbers against the
    real file, file.open-before-file.write ordering, the deep-dive link) and
    reports `problems` (won't play) and `warnings` (will play, but check);
  * prints the beat table — every event's start/end in ms, the total, and
    ready-made `?t=<ms>&paused=1` QA URLs — so nobody hand-sums durations;
  * embeds it all into assets/ide-template.html and writes ONE self-contained
    HTML file — the deliverable is a local file, not a published artifact.

Timeline schema: see ../references/timeline-schema.md
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "ide-template.html")

DEFAULT_IGNORE = {".git", ".DS_Store", "__pycache__", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CHILDLESS = {"node_modules", "dist", "build", ".playwright-cli", "test-results", ".venv", "coverage"}
MAX_ENTRIES = 80        # per directory — the sidebar shows at most this many rows of one folder
MAX_FILE_LINES = 600    # per opened file — longer files are cut with a marker line

EVENT_TYPES = {
    "caption", "wait", "pointer.hide",
    "tree.expand", "tree.collapse",
    "file.open", "file.close", "file.scroll", "file.highlight", "file.write",
    "claude.show", "claude.type", "claude.status", "claude.tool", "claude.text",
    "claude.notice", "claude.right", "claude.done",
    "term.tab", "term.cmd", "term.clear",
}
REQUIRED = {
    "caption": ["text"], "tree.expand": ["path"], "tree.collapse": ["path"],
    "file.open": ["path"], "file.scroll": ["line"], "file.highlight": ["from"],
    "file.write": ["path", "content"], "claude.type": ["text"], "claude.tool": ["name"],
    "claude.text": ["text"], "claude.notice": ["text"], "claude.right": ["text"],
    "term.cmd": ["cmd"],
}


def duration_of(ev, type_ms=58, stream_ms=9):
    """Mirror of durationOf() in the template — keep the two in sync."""
    if "ms" in ev and ev["ms"] is not None:
        return int(ev["ms"])
    t = ev.get("t")
    out_lines = 0 if ev.get("out") is None else len(str(ev["out"]).split("\n"))
    table = {
        "caption": 0, "wait": 800, "tree.expand": 900, "tree.collapse": 900,
        "file.open": 1200, "file.scroll": 700, "file.highlight": 500,
        "file.close": 800, "claude.show": 800, "claude.status": 1200,
        "claude.done": 500, "claude.notice": 600, "claude.right": 400,
        "term.tab": 800, "term.clear": 300, "file.write": 700, "pointer.hide": 200,
    }
    if t in table:
        return table[t]
    if t == "claude.type":
        return 350 + len(ev.get("text", "")) * type_ms + 450
    if t == "claude.tool":
        return 700 + (len(ev["diff"]) * 90 if ev.get("diff") else 0)
    if t == "claude.text":
        return max(700, len(ev.get("text", "")) * stream_ms)
    if t == "term.cmd":
        return 400 + len(ev.get("cmd", "")) * (type_ms + 8) + 350 + out_lines * 70
    return 500


def term_cmd_min_ms(ev, type_ms=58):
    out_lines = 0 if ev.get("out") is None else len(str(ev["out"]).split("\n"))
    return 400 + len(ev.get("cmd", "")) * (type_ms + 8) + 350 + out_lines * 70


def build_tree(root, want_dirs, ignore, depth_limit, warnings):
    """Sidebar tree: dirs first, then files, sorted case-insensitively (as the
    app does). Children are included for the top level, for every directory in
    want_dirs (paths the timeline expands or opens through), and down to
    depth_limit."""
    def walk(dirpath, rel, depth):
        try:
            names = sorted(os.listdir(dirpath), key=lambda s: s.lower())
        except OSError:
            return []
        dirs = [n for n in names if os.path.isdir(os.path.join(dirpath, n)) and n not in ignore]
        files = [n for n in names if not os.path.isdir(os.path.join(dirpath, n)) and n not in ignore]
        out = []
        for n in dirs + files:
            p = os.path.join(dirpath, n)
            relp = f"{rel}/{n}" if rel else n
            if os.path.isdir(p):
                node = {"name": n, "kind": "dir"}
                expand = (relp in want_dirs) or (depth < depth_limit and n not in CHILDLESS)
                node["children"] = walk(p, relp, depth + 1) if expand else []
                out.append(node)
            else:
                out.append({"name": n, "kind": "file"})
        if len(out) > MAX_ENTRIES:
            warnings.append(f"tree: {rel or '<root>'} has {len(out)} entries; only the first {MAX_ENTRIES} are shown (dirs first, then files) — pass --ignore to hide noise if a needed file fell off")
            out = out[:MAX_ENTRIES]
        return out
    return walk(root, "", 1)


def read_file(root, rel):
    root_real = os.path.realpath(root)
    full = os.path.realpath(os.path.join(root, rel))
    if os.path.commonpath([root_real, full]) != root_real:
        raise OSError(f"path escapes project root: {rel!r}")
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    truncated = False
    if len(lines) > MAX_FILE_LINES:
        lines = lines[:MAX_FILE_LINES] + [f"… ({len(lines) - MAX_FILE_LINES} more lines not shown)"]
        truncated = True
    return "\n".join(lines), truncated


def parents(path):
    parts = path.split("/")
    return ["/".join(parts[: i + 1]) for i in range(len(parts) - 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--out", help="the HTML file to write, e.g. <project>/hooks-ide-animation.html (preferred)")
    ap.add_argument("--out-dir", help="alternatively a directory; index.html is written into it")
    ap.add_argument("--final-dir", help="where the file will finally live, if different from --out's folder (the deep-dive link is checked there)")
    ap.add_argument("--qa-base", default=None, help="base URL for the printed QA links (default http://localhost:8000/<out basename>)")
    ap.add_argument("--tree-depth", type=int, default=1, help="how deep to pre-load children (1 = top level only; dirs the timeline touches are always loaded)")
    ap.add_argument("--ignore", default="", help="comma-separated extra names to hide from the tree")
    args = ap.parse_args()
    if not args.out and not args.out_dir:
        sys.exit("give --out <file.html> (preferred) or --out-dir <dir>")

    with open(args.timeline, "r", encoding="utf-8") as f:
        tl = json.load(f)
    root = os.path.abspath(args.project_root)
    if not os.path.isdir(root):
        sys.exit(f"project root not found: {root}")
    out = os.path.abspath(args.out) if args.out else os.path.join(os.path.abspath(args.out_dir), "index.html")
    final_dir = os.path.abspath(args.final_dir) if args.final_dir else os.path.dirname(out)

    meta = tl.get("meta", {})
    meta.setdefault("project", os.path.basename(root))
    events = tl.get("events", [])
    files = dict(tl.get("files", {}))
    problems, warnings = [], []
    type_ms = int(meta.get("typeMs", 58)); stream_ms = int(meta.get("streamMs", 9))

    written = {ev["path"] for ev in events if ev.get("t") == "file.write" and "path" in ev}
    written_so_far = set()
    file_lines = {}   # path -> line count as embedded
    open_file = None

    want_dirs = set()
    for p in meta.get("expanded", []):
        want_dirs.add(p); want_dirs.update(parents(p))
    for i, ev in enumerate(events):
        t = ev.get("t")
        if t not in EVENT_TYPES:
            problems.append(f"event {i}: unknown type {t!r}"); continue
        missing = [k for k in REQUIRED.get(t, []) if k not in ev]
        if missing:
            problems.append(f"event {i} ({t}): missing required field(s) {', '.join(map(repr, missing))}")
            continue
        if t in ("tree.expand", "tree.collapse"):
            want_dirs.add(ev["path"]); want_dirs.update(parents(ev["path"]))
        if t in ("file.open", "file.write"):
            want_dirs.update(parents(ev["path"]))
        if t == "file.open":
            path = ev["path"]
            if "content" in ev:
                files[path] = ev.pop("content")
            elif path in written_so_far:
                pass  # a prior file.write supplies the content at runtime
            elif path not in files:
                try:
                    files[path], truncated = read_file(root, path)
                    if truncated:
                        warnings.append(f"event {i}: {path} is longer than {MAX_FILE_LINES} lines; the viewer shows the first {MAX_FILE_LINES} plus a marker")
                except OSError as e:
                    if path in written:
                        problems.append(f"event {i}: file.open {path} comes before the file.write that creates it and it is not on disk — reorder them or the viewer will be empty here")
                    else:
                        problems.append(f"event {i}: cannot read {path}: {e}")
            if path in files:
                file_lines[path] = len(files[path].split("\n"))
            open_file = path
            if ev.get("line") and open_file in file_lines and int(ev["line"]) > file_lines[open_file]:
                problems.append(f"event {i}: file.open line {ev['line']} > {open_file} has {file_lines[open_file]} lines")
        if t == "file.write":
            written_so_far.add(ev["path"])
            file_lines[ev["path"]] = len(str(ev["content"]).split("\n"))
        if t in ("file.close", "claude.show"):
            open_file = None
        if t in ("file.scroll", "file.highlight"):
            if not open_file:
                problems.append(f"event {i}: {t} with no file open (put a file.open before it)")
            else:
                n = file_lines.get(open_file)
                for k in ("line", "from", "to"):
                    v = ev.get(k)
                    if v is not None and n is not None and (int(v) < 1 or int(v) > n):
                        problems.append(f"event {i}: {t} {k}={v} is outside {open_file} ({n} lines) — re-check with grep -n")
        if t == "claude.tool" and ev.get("diff"):
            for r in ev["diff"]:
                if r.get("t") not in ("ctx", "add", "del") or "text" not in r:
                    problems.append(f"event {i}: diff rows need t∈{{ctx,add,del}} and text"); break
        if t == "term.cmd" and ev.get("ms") is not None and int(ev["ms"]) < term_cmd_min_ms(ev, type_ms):
            warnings.append(f"event {i}: term.cmd ms={ev['ms']} is below its natural {term_cmd_min_ms(ev, type_ms)} ms — it will play faster than a person types")

    dd = meta.get("deepDive")
    if dd and dd.get("href") and not re.match(r"^https?://", dd["href"]):
        if not os.path.exists(os.path.join(final_dir, dd["href"])):
            problems.append(f"meta.deepDive.href {dd['href']!r} does not exist in {final_dir} — the link would 404 (use --final-dir if the file will be moved)")

    ignore = set(DEFAULT_IGNORE) | {s for s in args.ignore.split(",") if s}
    tree = build_tree(root, want_dirs, ignore, args.tree_depth, warnings)

    def in_tree(path):
        nodes = tree
        for part in path.split("/"):
            nxt = next((n for n in nodes if n["name"] == part), None)
            if not nxt:
                return False
            nodes = nxt.get("children", [])
        return True
    for ev in events:
        if ev.get("t") == "file.open" and not in_tree(ev["path"]) and ev["path"] not in written:
            problems.append(f"file.open {ev['path']}: not in the sidebar tree (hidden by the ignore list, cut by the {MAX_ENTRIES}-entry cap, or a typo?)")

    # beat table — same arithmetic as the player
    beats, t0 = [], 0
    for i, ev in enumerate(events):
        d = duration_of(ev, type_ms, stream_ms)
        label = ev.get("text") or ev.get("path") or ev.get("cmd") or ev.get("name") or ""
        beats.append({"i": i, "t": ev.get("t"), "start": t0, "end": t0 + d, "label": str(label)[:60]})
        t0 += d
    qa_base = args.qa_base or f"http://localhost:8000/{os.path.basename(out)}"
    qa = [f"{qa_base}?t={b['end'] - 1}&paused=1  # {b['i']} {b['t']} {b['label']}" for b in beats if b["end"] > b["start"] and b["t"] not in ("wait", "pointer.hide")]

    data = {"meta": meta, "tree": tree, "files": files, "events": events}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{TITLE}}", meta.get("title", "Live demo")).replace("{{DATA_JSON}}", payload)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(json.dumps({
        "html_file": out,
        "events": len(events),
        "steps": sum(1 for b in beats if b["end"] > b["start"]),
        "total_ms": t0,
        "files_embedded": sorted(files.keys()),
        "tree_top_level": len(tree),
        "deep_dive_link": (dd or {}).get("href"),
        "problems": problems,
        "warnings": warnings,
        "beats": beats,
        "qa_urls": qa,
        "bytes": len(html),
    }, indent=2, ensure_ascii=False))
    if problems:
        sys.exit(2)


if __name__ == "__main__":
    main()
