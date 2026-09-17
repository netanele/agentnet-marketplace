#!/usr/bin/env python3
"""Validate a Concept animation file before you look at it.

    python3 check_concept.py <project>/<slug>-concept-animation.html

Checks (stdlib + node for the syntax pass):
  * the <script id="conceptConfig"> block parses (node --check) — a config
    error would otherwise only show as a red banner in the browser;
  * every panel fits the stage: x+w <= 1260, y+h <= 606 (header 56px, footer 116px);
  * every arrow endpoint names a panel/card/sel that exists, and a code line
    that exists in that panel; arrows use fromSide/toSide, not `side`;
  * every step's panel ids, term ids, card ids and line keys exist;
  * meta.deepDive.href resolves next to the file;
  * <title> was replaced.
Prints JSON with `problems` (fix before shipping) and `warnings`.
"""
import json, os, re, subprocess, sys, tempfile


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = os.path.abspath(sys.argv[1])
    html = open(path, "r", encoding="utf-8").read()
    problems, warnings = [], []
    m = re.search(r'<script id="conceptConfig">(.*?)</script>', html, re.S)
    if not m:
        sys.exit(json.dumps({"problems": ["no <script id=\"conceptConfig\"> block found"]}))
    cfg_js = m.group(1)
    if "{{TITLE}}" in html:
        problems.append("<title> still says {{TITLE}}")
    if re.search(r"\bside:", cfg_js):
        problems.append("arrows use `side:` — the engine reads `fromSide:` / `toSide:`")

    # syntax pass + evaluation via node (config is plain JS, not JSON)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
        tf.write("var window={};\n" + cfg_js + "\nprocess.stdout.write(JSON.stringify(window.CONCEPT));")
        tmp = tf.name
    try:
        r = subprocess.run(["node", tmp], capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        sys.exit(json.dumps({"problems": ["node is not installed — cannot evaluate the config block"]}))
    finally:
        os.unlink(tmp)
    if r.returncode != 0:
        sys.exit(json.dumps({"problems": ["config block does not evaluate:\n" + r.stderr.strip()[:800]]}, indent=2))
    C = json.loads(r.stdout or "{}")
    meta, panels, cards, lines, steps = C.get("meta", {}), C.get("panels", []), C.get("cards", []), C.get("lines", {}), C.get("steps", [])

    pid = {p["id"]: p for p in panels}
    cid = {c["id"]: c for c in cards}
    for p in panels:
        if p.get("x", 0) + p.get("w", 0) > 1260 or p.get("y", 0) + p.get("h", 0) > 606 or p.get("y", 0) < 72:
            problems.append(f"panel {p['id']}: outside the stage area (x+w<=1260, 72<=y, y+h<=606) — got x={p.get('x')} y={p.get('y')} w={p.get('w')} h={p.get('h')}")
        if p.get("kind") == "code" and not p.get("lines"):
            warnings.append(f"panel {p['id']}: code panel with no lines")
        if p.get("kind") == "code" and "abridged" not in (p.get("tag") or "").lower():
            warnings.append(f"panel {p['id']}: code panel not tagged 'abridged' — fine only if it shows the whole real file verbatim")

    def endpoint_ok(e, where):
        if not isinstance(e, dict):
            problems.append(f"{where}: endpoint must be an object"); return
        if "panel" in e:
            if e["panel"] not in pid:
                problems.append(f"{where}: unknown panel {e['panel']!r}")
            elif e.get("line") and (pid[e["panel"]].get("kind") != "code" or e["line"] > len(pid[e["panel"]].get("lines", []))):
                problems.append(f"{where}: line {e['line']} does not exist in panel {e['panel']!r}")
        elif "card" in e:
            if e["card"] not in cid:
                problems.append(f"{where}: unknown card {e['card']!r}")
        elif "sel" not in e:
            problems.append(f"{where}: endpoint needs panel / card / sel")

    if not steps:
        problems.append("no steps")
    for si, s in enumerate(steps, 1):
        for k in (s.get("panels") or {}):
            if k not in pid:
                problems.append(f"step {si}: unknown panel {k!r}")
            else:
                st = s["panels"][k]
                n = len(pid[k].get("lines", []))
                for key in ("hl", "hotl", "okl"):
                    for ln in st.get(key) or []:
                        if ln < 1 or ln > n:
                            problems.append(f"step {si}: panel {k!r} {key} line {ln} out of range (1..{n})")
        for k, v in (s.get("term") or {}).items():
            if k not in pid or pid[k].get("kind") != "term":
                problems.append(f"step {si}: term target {k!r} is not a term panel")
            keys = v if isinstance(v, list) else (v.get("lines") or [])
            for key in keys:
                if key not in lines:
                    problems.append(f"step {si}: line key {key!r} not in lines{{}}")
        for c in s.get("cards") or []:
            if c not in cid:
                problems.append(f"step {si}: unknown card {c!r}")
        for ai, a in enumerate(s.get("arrows") or []):
            endpoint_ok(a.get("from"), f"step {si} arrow {ai} from")
            endpoint_ok(a.get("to"), f"step {si} arrow {ai} to")
        if not s.get("title") or not s.get("cap"):
            warnings.append(f"step {si}: missing title or cap")
        if s.get("dur") and s["dur"] < 2500:
            warnings.append(f"step {si}: dur {s['dur']} ms is short for a caption to be read")

    dd = meta.get("deepDive")
    if dd and dd.get("href") and not re.match(r"^https?://", dd["href"]):
        if not os.path.exists(os.path.join(os.path.dirname(path), dd["href"])):
            problems.append(f"meta.deepDive.href {dd['href']!r} does not exist next to {path}")
    elif not dd:
        warnings.append("no meta.deepDive — the Deep dive link will be hidden")

    total = sum(s.get("dur", 5000) for s in steps)
    print(json.dumps({"file": path, "steps": len(steps), "total_ms": total, "panels": list(pid), "cards": list(cid),
                      "qa_urls": [f"http://localhost:8000/{os.path.basename(path)}?step={i}&noanim=1" for i in range(1, len(steps) + 1)],
                      "problems": problems, "warnings": warnings}, indent=2, ensure_ascii=False))
    if problems:
        sys.exit(2)


if __name__ == "__main__":
    main()
