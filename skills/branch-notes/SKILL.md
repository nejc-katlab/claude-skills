---
name: branch-notes
description: Capture and surface time/branch/version-scoped reminders. Use when the user defers a task to a future branch, version, or date ("do X when we get to 4.9", "after the SDK changes on Sept 1, switch Y", "next time we're on the appsflyer branch, fix Z"), or asks to add/list/clear a branch note. A hook auto-surfaces matching notes each session and on every prompt, so the main job here is writing a well-formed note or consuming one.
---

# branch-notes

A deferred-reminder system. The user often realizes a change should happen *later* —
on a specific branch, once a version is reached, or after a date — but can't do it now.
Capture it as a note; a hook reminds them automatically the moment the trigger matches.

## How it fires (already wired, no action needed)
- Global hooks (`SessionStart` + `UserPromptSubmit` in `~/.claude/settings.json`) run
  `~/.claude/skills/branch-notes/check.py` on every session start and every user message.
- The script reads notes, checks the current git branch / today's date, and injects any
  matching `pending` note into your context as `BRANCH NOTE(S) triggered ...`.
- It de-dupes per session+branch, so you're reminded once per branch, again if the user
  switches away and back. `UserPromptSubmit` is what catches branch switches the user makes
  in their own terminal mid-conversation — `SessionStart`/`/clear` alone would miss those.

## When a note surfaces in your context
Don't bury it. Before diving into the user's actual request, naturally remind them, e.g.
"Before we start — you left a note for this branch: <title>. <one-line gist>. Want to handle
it now or later?" Then proceed. When the task is actually done, **consume** it (below).

## Note store
- Per-project: `<project>/.claude/branch-notes.json` (preferred — keeps notes with the repo).
- Global: `~/.claude/branch-notes.json` (for notes not tied to one repo; may set `match.project`).
- Format: a JSON array of note objects.

## Note schema
```json
{
  "id": "kebab-unique-id",
  "title": "short human title",
  "match": { "...": "..." },
  "status": "pending",
  "created": "YYYY-MM-DD",
  "note": "Full context: what to do, why it was deferred, where in the code, refs."
}
```

### `match` keys (ALL present keys must hold — logical AND)
| key | fires when | example |
|-----|-----------|---------|
| `branch` | current branch equals it exactly | `"release/4.8.0"` |
| `branchGlob` | glob match, or plain substring if no glob chars | `"release/4.9.*"` or `"4.9"` |
| `keywords` | any list entry is a substring of the branch (case-insensitive) | `["appsflyer","ios"]` |
| `versionMin` | version parsed from the branch ≥ this | `"4.9.0"` |
| `dateAfter` | today ≥ this ISO date (SDK deadlines etc.) | `"2026-09-01"` |
| `project` | project dir basename equals it (scope a global note) | `"swamp-attack-1"` |

Pick the *narrowest* trigger that captures intent. "When we get to 4.9" → usually
`versionMin: "4.9.0"` (fires on 4.9 and beyond) or `branchGlob: "*4.9*"` (only 4.9 branches).
Combine keys for "on the 4.9 branch AND after Sept 1": `{ "versionMin":"4.9.0", "dateAfter":"2026-09-01" }`.

## Adding a note (your job when the user defers something)
1. Choose the right store (per-project unless it's clearly cross-repo).
2. Read the existing JSON, append a note with a unique `id`, `status:"pending"`,
   today's `created` date, a precise `match`, and a `note` body rich enough that
   future-you can act without re-deriving context (include file paths, line hints, why).
3. Confirm to the user what will trigger it and when.

## Consuming / clearing a note
When the deferred task is actually completed (or no longer relevant), set its
`"status"` to `"done"` in the file (don't delete — keeps an audit trail; the engine
ignores non-`pending`). If the user says "drop it / forget it", you may delete the entry.

## Listing / debugging
- Show what would fire right now: `python3 ~/.claude/skills/branch-notes/check.py <project> --plain`
- `--no-dedupe` ignores session state; `--plain` prints human text instead of hook JSON.
- Session dedupe state: `~/.claude/skills/branch-notes/.state/` (auto-pruned after 7 days).
