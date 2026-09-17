#!/usr/bin/env python3
"""Build a self-contained live-demo animation (Claude Code IDE look) from a
timeline JSON + a real project directory.

    python3 build_demo.py --timeline demo.json --project-root /path/to/project \
        --out /path/to/project/hooks-live-demo.html

What it does (stdlib only):
  * reads the real file tree from --project-root (top level + every directory
    the timeline expands/opens), so the sidebar is the real sidebar;
  * reads every file the timeline opens from disk (unless the timeline gives
    inline `content`), so the viewer shows real code;
  * validates the events and reports anything that will not render, including
    a meta.deepDive.href that does not exist next to the output file;
  * embeds it all into assets/ide-template.html and writes ONE self-contained
    HTML file — the deliverable is a local file, not a published artifact.

Timeline schema: see ../references/timeline-schema.md
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "ide-template.html")

DEFAULT_IGNORE = {".git", ".DS_Store", "__pycache__", ".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CHILDLESS = {"node_modules", "dist", "build", ".playwright-cli", "test-results", ".venv", "coverage"}
MAX_ENTRIES = 80
MAX_FILE_LINES = 600

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


def build_tree(root, want_dirs, ignore, depth_limit):
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
        return out[:MAX_ENTRIES]
    return walk(root, "", 1)


def read_file(root, rel):
    root_real = os.path.realpath(root)
    full = os.path.realpath(os.path.join(root, rel))
    if os.path.commonpath([root_real, full]) != root_real:
        raise OSError(f"path escapes project root: {rel!r}")
    with open(full, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    if len(lines) > MAX_FILE_LINES:
        lines = lines[:MAX_FILE_LINES] + [f"… ({len(lines) - MAX_FILE_LINES} more lines not shown)"]
    return "\n".join(lines)


def parents(path):
    parts = path.split("/")
    return ["/".join(parts[: i + 1]) for i in range(len(parts) - 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--out", help="the HTML file to write, e.g. <project>/hooks-live-demo.html (preferred)")
    ap.add_argument("--out-dir", help="alternatively a directory; index.html is written into it")
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

    meta = tl.get("meta", {})
    meta.setdefault("project", os.path.basename(root))
    events = tl.get("events", [])
    files = dict(tl.get("files", {}))
    problems = []

    written = {ev["path"] for ev in events if ev.get("t") == "file.write" and "path" in ev}
    written_so_far = set()

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
                # a prior file.write already supplies this path's content at
                # runtime (the template reads it from the event itself, not
                # from `files`)
                pass
            elif path in written:
                problems.append(f"event {i}: file.open {path} comes before its file.write — reorder them or the viewer will be empty at this point")
            elif path not in files:
                try:
                    files[path] = read_file(root, path)
                except OSError as e:
                    problems.append(f"event {i}: cannot read {path}: {e}")
        if t == "file.write":
            written_so_far.add(ev["path"])
        if t == "claude.tool" and ev.get("diff"):
            for r in ev["diff"]:
                if r.get("t") not in ("ctx", "add", "del") or "text" not in r:
                    problems.append(f"event {i}: diff rows need t∈{{ctx,add,del}} and text"); break

    dd = meta.get("deepDive")
    if dd and dd.get("href") and not re.match(r"^https?://", dd["href"]):
        if not os.path.exists(os.path.join(os.path.dirname(out), dd["href"])):
            problems.append(f"meta.deepDive.href {dd['href']!r} does not exist next to {out} — the link would 404")

    ignore = set(DEFAULT_IGNORE) | {s for s in args.ignore.split(",") if s}
    tree = build_tree(root, want_dirs, ignore, args.tree_depth)

    def in_tree(path):
        nodes = tree
        for part in path.split("/"):
            nxt = next((n for n in nodes if n["name"] == part), None)
            if not nxt:
                return False
            nodes = nxt.get("children", [])
        return True
    for ev in events:
        if ev.get("t") == "file.open" and ev.get("path") and not in_tree(ev["path"]) and ev["path"] not in written:
            problems.append(f"file.open {ev['path']}: not in the sidebar tree (hidden by ignore list, or path typo?)")

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
        "steps": sum(1 for e in events if e.get("t") != "caption"),
        "files_embedded": sorted(files.keys()),
        "tree_top_level": len(tree),
        "deep_dive_link": (dd or {}).get("href"),
        "problems": problems,
        "bytes": len(html),
    }, indent=2, ensure_ascii=False))
    if problems:
        sys.exit(2)


if __name__ == "__main__":
    main()
