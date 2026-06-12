#!/usr/bin/env python3
"""Surface pending branch-notes whose trigger matches the current context.

Invoked by hooks (SessionStart + UserPromptSubmit) and runnable by hand.
Reads notes from <project>/.claude/branch-notes.json and ~/.claude/branch-notes.json,
evaluates each pending note's `match` block against the current git branch / date,
and emits matching notes as hook additionalContext (or plain text with --plain).

Because UserPromptSubmit fires on every message, results are de-duplicated per
session+branch: a note is surfaced once, and again only if you switch away from
and back to a matching branch. State lives in ~/.claude/skills/branch-notes/.state.

A note surfaces when status == "pending" AND every key in its `match` block is
satisfied (logical AND). Supported match keys:
  branch      exact current-branch match
  branchGlob  glob (release/4.9.*) or plain substring (4.9) match on branch name
  keywords    list; satisfied if ANY entry is a case-insensitive substring of branch
  versionMin  satisfied once the version parsed from the branch is >= this (e.g. 4.9.0)
  dateAfter   satisfied once today >= this ISO date (YYYY-MM-DD) — for SDK deadlines
  project     restricts a (global) note to a project dir basename
"""
import os
import re
import sys
import json
import time
import fnmatch
import datetime
import subprocess

STATE_DIR = os.path.expanduser("~/.claude/skills/branch-notes/.state")


def read_hook_stdin():
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def load_notes(path):
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def current_branch(project_dir):
    try:
        out = subprocess.run(
            ["git", "-C", project_dir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def version_tuple(s):
    m = re.search(r"(\d+(?:\.\d+){0,3})", s or "")
    if not m:
        return None
    return tuple(int(p) for p in m.group(1).split("."))


def ge_version(a, b):
    if a is None or b is None:
        return False
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) >= b + (0,) * (n - len(b))


def satisfied(match, branch, project_name, today):
    if not isinstance(match, dict) or not match:
        return False
    bl = (branch or "").lower()
    for key, val in match.items():
        if key == "branch":
            if branch != val:
                return False
        elif key == "branchGlob":
            pat = str(val)
            if any(c in pat for c in "*?[]"):
                if not fnmatch.fnmatch(branch or "", pat):
                    return False
            elif pat.lower() not in bl:
                return False
        elif key == "keywords":
            kws = val if isinstance(val, list) else [val]
            if not any(str(k).lower() in bl for k in kws):
                return False
        elif key == "versionMin":
            if not ge_version(version_tuple(branch), version_tuple(str(val))):
                return False
        elif key == "dateAfter":
            try:
                d = datetime.date.fromisoformat(str(val))
            except ValueError:
                return False
            if today < d:
                return False
        elif key == "project":
            if project_name != val:
                return False
        else:
            return False
    return True


def load_state(session_id):
    path = os.path.join(STATE_DIR, f"{session_id}.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(session_id, state):
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        cutoff = time.time() - 7 * 86400
        for fn in os.listdir(STATE_DIR):
            fp = os.path.join(STATE_DIR, fn)
            if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                os.remove(fp)
        with open(os.path.join(STATE_DIR, f"{session_id}.json"), "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def main():
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    plain = "--plain" in flags
    no_dedupe = "--no-dedupe" in flags
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    payload = read_hook_stdin()
    project_dir = (args[0] if args else payload.get("cwd")
                   or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    project_dir = os.path.abspath(project_dir)
    project_name = os.path.basename(project_dir.rstrip("/"))
    session_id = payload.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or "default"
    event = (payload.get("hook_event_name")
             or os.environ.get("CLAUDE_HOOK_EVENT") or "SessionStart")

    branch = current_branch(project_dir)
    today = datetime.date.today()

    sources = [
        os.path.join(project_dir, ".claude", "branch-notes.json"),
        os.path.expanduser("~/.claude/branch-notes.json"),
    ]
    seen, hits = set(), []
    for path in sources:
        for n in load_notes(path):
            nid = str(n.get("id") or id(n))
            if nid in seen or n.get("status", "pending") != "pending":
                continue
            if satisfied(n.get("match", {}), branch, project_name, today):
                seen.add(nid)
                hits.append((path, nid, n))

    if not no_dedupe and not plain:
        state = load_state(session_id)
        if state.get("branch") != branch:
            state = {"branch": branch, "shown": []}
        shown = set(state.get("shown", []))
        fresh = [(p, nid, n) for (p, nid, n) in hits if nid not in shown]
        if hits:
            state["shown"] = sorted(shown | {nid for _, nid, _ in hits})
            save_state(session_id, state)
        hits = fresh

    if not hits:
        return

    where = branch or project_name
    lines = [
        f"BRANCH NOTE(S) triggered for '{where}'. These are deferred tasks you queued "
        f"earlier for this exact point (branch / version / date). Open by naturally "
        f"reminding the user about each one before getting into their request; once a "
        f"note is handled, set its \"status\" to \"done\" in its file so it stops firing."
    ]
    for path, _nid, n in hits:
        lines.append(
            f"\n- [{n.get('id','?')}] {n.get('title','')}\n"
            f"  trigger: {json.dumps(n.get('match', {}))}\n"
            f"  {n.get('note','')}\n"
            f"  (stored in: {path})"
        )
    msg = "\n".join(lines)

    if plain:
        print(msg)
        return

    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": event, "additionalContext": msg}
    }))


if __name__ == "__main__":
    main()
