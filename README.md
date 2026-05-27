# claude-skills

Personal collection of Claude Code skills.

## Skills

| Skill | Purpose |
| --- | --- |
| [`stay-aligned`](skills/stay-aligned/SKILL.md) | Build a non-trivial feature in continuous alignment with the user — grill the plan upfront, then pause at every consequential decision (architectural fork, public/long-lived naming, scope expansion, plan-vs-reality mismatch) rather than silently picking a direction. |

## Install

Symlink the skill you want into your global Claude skills directory:

```bash
ln -s "$(pwd)/skills/stay-aligned" ~/.claude/skills/stay-aligned
```

Or copy the whole `skills/` tree.

## Layout

```
skills/
  <skill-name>/
    SKILL.md
```

Each skill is a directory containing a `SKILL.md` with frontmatter (`name`, `description`) followed by the skill body. Claude Code triggers a skill when the user request matches its `description`.
