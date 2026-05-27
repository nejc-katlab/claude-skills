---
name: stay-aligned
description: Build a non-trivial feature in continuous alignment with the user. Phase 1 grills the plan upfront (interview, walk the design tree, recommend an answer per branch). Phase 2 holds that alignment during implementation by pausing before consequential decisions — architectural forks, public or long-lived naming, scope expansion, plan-vs-reality mismatches, encoded assumptions, defensible trade-offs — rather than silently picking a direction. Skip checkpoints for trivial details (local variable names, mechanical refactors, formatting, lint fixes) since they are cheap to reverse later. Use when starting a feature, refactor, or multi-step change where mid-flight divergence would be expensive to undo, or when the user says "stay aligned", "build this with me", "grill me through the build", or asks for grilling with checkpoints throughout.
---

# Stay Aligned

Two phases, one principle: **never silently branch off in a direction the user wasn't planning.**

Trivial details (local variable names, mechanical refactor steps, formatting) can be reversed cheaply — do not interrupt the user about them. Direction-of-implementation decisions and long-lived names are expensive to undo — surface them.

---

## Phase 1 — Grill the plan upfront

Interview the user relentlessly about every aspect of the plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

- Ask one question at a time. Wait for the answer before continuing.
- If a question can be answered by exploring the codebase, explore the codebase instead. Do not ask the user things you can verify yourself.
- Be willing to disagree. If the user's plan has a flaw you can name, name it before moving on.

End Phase 1 when the design tree has no unresolved branches that would meaningfully change the implementation direction.

Close Phase 1 by stating the agreed plan back in 3–8 bullets and asking for confirmation before starting the build.

---

## Phase 2 — Stay aligned during the build

Before each meaningful step:

1. State in one sentence what you are about to do.
2. Make the change.
3. If you hit a fork mid-step, stop and surface it before continuing.

### Stop and ask when you encounter

- **A feature-path fork.** "This could be implemented as X or Y; they lead to different places."
- **Naming of long-lived concepts.** Public APIs, exported types, schemas, file or directory layout, message or event names, table or column names. Anything other code (or other people) will reference.
- **Scope expansion.** You found something out-of-scope that wants fixing while you are here. Surface it; do not silently bundle it in.
- **Plan-vs-reality mismatch.** The code on disk does not look the way the plan assumed. Stop. Re-align before continuing.
- **Encoded assumption.** You are about to write code that depends on "I think they meant X". Confirm X.
- **A defensible trade-off.** Performance vs simplicity, abstraction now vs duplication now, validation here vs there. The kind of choice that would warrant an ADR in a codebase that has them.

### Do not stop for

- Local variable names, internal helper names.
- Mechanical refactor steps within the agreed direction.
- Formatting or style that follows existing conventions in the file.
- Type or lint fixes.
- Small obvious bug fixes you stumble on. Mention them in the next status line — do not open a full checkpoint.

### Shape of a checkpoint

Keep it short. Frame it as a fork.

> Before I continue: I'm about to do **X**. The alternative is **Y**.
> X: <one-line reason>
> Y: <one-line reason>
> My recommendation: **X**, because <reason>.
> Confirm or redirect?

Then wait. Do not write code while waiting.

### Push back when you see a problem

Silent agreement is worse than honest disagreement. If the user's chosen direction has a flaw you can name — a bug, a scaling cliff, a contradiction with code already shipped, a violation of a stated invariant — name it before implementing. State the issue, the cost of going their way, your recommendation. Let the user decide. Do not implement a path you believe is wrong without first making them see what you see.

---

## Closing the loop

When the feature is done, give a short reconciliation before declaring it complete:

- What was actually built vs what the Phase 1 plan said.
- Anywhere reality diverged from the plan, and why.
- Any small decisions made without opening a checkpoint, listed so they are not invisible.

The closing reconciliation is not optional — it is what makes divergence visible to the user instead of hidden in the diff.
