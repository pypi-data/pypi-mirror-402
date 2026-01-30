---
work_package_id: "WPxx"
subtasks:
  - "Txxx"
title: "Replace with work package title"
phase: "Phase N - Replace with phase name"
lane: "planned"  # Edit directly or use: spec-kitty agent tasks move-task <WPID> --to <lane>
assignee: ""      # Optional friendly name when in doing/for_review
agent: ""         # CLI agent identifier (claude, codex, etc.)
shell_pid: ""     # PID captured when the task moved to the current lane
review_status: "" # empty | has_feedback | acknowledged (populated by reviewers/implementers)
reviewed_by: ""   # Agent ID of the reviewer (if reviewed)
history:
  - timestamp: "{{TIMESTAMP}}"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---
*Path: [templates/task-prompt-template.md](templates/task-prompt-template.md)*


# Work Package Prompt: {{work_package_id}} – {{title}}

## 🚨 CRITICAL: Complete Implementation Required

**THIS WORK PACKAGE MUST BE FULLY IMPLEMENTED - NO EXCEPTIONS**

- **DO NOT skip this work package** for "token efficiency", "context length", or any other reason
- **DO NOT abbreviate or summarize** - implement all subtasks completely
- **DO NOT defer to "future work"** - complete everything defined in this prompt
- **All subtasks listed below are mandatory** - each one must be fully completed
- If you encounter technical blockers, document them and request clarification - do NOT skip work

**Your implementation is not complete until:**
- Every subtask below is fully implemented
- All code is written and functional
- All acceptance criteria are met
- You can honestly report "implementation complete and tested"

---

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Objectives & Success Criteria

- Summarize the exact outcomes that mark this work package complete.
- Call out key acceptance criteria or success metrics for the bundle.

## Context & Constraints

- Reference prerequisite work and related documents.
- Link to supporting specs: `.kittify/memory/constitution.md`, `kitty-specs/.../plan.md`, `kitty-specs/.../tasks.md`, data model, contracts, research, quickstart.
- Highlight architectural decisions, constraints, or trade-offs to honor.

## Subtasks & Detailed Guidance

### Subtask TXXX – Replace with summary
- **Purpose**: Explain why this subtask exists.
- **Steps**: Detailed, actionable instructions.
- **Files**: Canonical paths to update or create.
- **Parallel?**: Note if this can run alongside others.
- **Notes**: Edge cases, dependencies, or data requirements.

### Subtask TYYY – Replace with summary
- Repeat the structure above for every included `Txxx` entry.

## Test Strategy (include only when tests are required)

- Specify mandatory tests and where they live.
- Provide commands or scripts to run.
- Describe fixtures or data seeding expectations.

## Risks & Mitigations

- List known pitfalls, performance considerations, or failure modes.
- Provide mitigation strategies or monitoring notes.

## Definition of Done Checklist

- [ ] All subtasks completed and validated
- [ ] Documentation updated (if needed)
- [ ] Metrics/telemetry added (if applicable)
- [ ] Observability/logging requirements satisfied
- [ ] `tasks.md` updated with status change

## Review Guidance

- Key acceptance checkpoints for `/spec-kitty.review`.
- Any context reviewers should revisit before approving.

## Activity Log

> Append entries when the work package changes lanes. Include timestamp, agent, shell PID, lane, and a short note.

- {{TIMESTAMP}} – system – lane=planned – Prompt created.

---

## Available Commands Reference

**Task Lane Management:**
```bash
# Move this work package to next lane
spec-kitty agent tasks move-task {{work_package_id}} --to for_review --note "Ready for review"

# Add history note without changing lane
spec-kitty agent tasks add-history {{work_package_id}} --note "Progress update"

# List all work packages for this feature
spec-kitty agent tasks list-tasks

# List work packages in specific lane
spec-kitty agent tasks list-tasks --lane doing
spec-kitty agent tasks list-tasks --lane for_review

# Rollback to previous lane (if needed)
spec-kitty agent tasks rollback-task {{work_package_id}}
```

**Workflow Commands:**
```bash
# Start implementing next planned work package
spec-kitty agent workflow implement

# Start reviewing next work package in review queue
spec-kitty agent workflow review
```

**⚠️ IMPORTANT: Only use commands listed above. Do not invent commands like:**
- ❌ `spec-kitty view tasks` (does not exist)
- ❌ `spec-kitty list` (does not exist)
- ❌ `spec-kitty show` (does not exist)
- ✅ Use `spec-kitty agent tasks list-tasks` instead

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"`

The CLI command also updates the activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### File Structure

All WP files live in a flat `tasks/` directory. The lane is determined by the `lane:` frontmatter field, not the directory location.
