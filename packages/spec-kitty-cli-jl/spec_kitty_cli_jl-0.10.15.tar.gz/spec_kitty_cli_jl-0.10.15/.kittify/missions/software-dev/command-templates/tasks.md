---
description: Generate grouped work packages with actionable subtasks and matching prompt files for the feature in one pass.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Location Pre-flight Check (CRITICAL for AI Agents)

Before proceeding, verify you are in the correct working directory:

**Check your current branch:**
```bash
git branch --show-current
```

**Expected output:** A feature branch like `001-feature-name`
**If you see `main`:** You are in the wrong location!

**This command MUST run from a feature worktree, not the main repository.**

If you're on the `main` branch:
1. Check for available worktrees: `ls .worktrees/`
2. Navigate to the appropriate feature worktree: `cd .worktrees/<feature-name>`
3. Verify you're in the right place: `git branch --show-current` should show the feature branch
4. Then re-run this command

The script will fail if you're not in a feature worktree. This is intentional - worktrees provide isolation for parallel feature development.

## Outline

1. **Setup**: Run `spec-kitty agent feature check-prerequisites --json --paths-only --include-tasks` from the worktree root and parse JSON for:
   - `feature_dir`: Absolute path to feature directory
   - `spec_file`: Absolute path to spec.md
   - `tasks_file`: Absolute path to tasks.md (if exists)
   - `tasks_dir`: Absolute path to tasks/ directory (if exists)

   **CRITICAL**: The command returns JSON with `feature_dir` as an ABSOLUTE path (e.g., `C:\Users\user\project\kitty-specs\001-feature-name`).

   **YOU MUST USE THIS PATH** for ALL subsequent file operations. Example:
   ```
   feature_dir = "C:\\Users\\user\\project\\kitty-specs\\001-feature-name"
   tasks.md location: feature_dir + "/tasks.md"
   prompt location: feature_dir + "/tasks/WP01-slug.md"
   ```

   **DO NOT CREATE** paths like:
   - ❌ `tasks/WP01-slug.md` (missing feature_dir prefix)
   - ❌ `/tasks/WP01-slug.md` (wrong root)
   - ❌ `feature_dir/tasks/planned/WP01-slug.md` (WRONG - no subdirectories!)
   - ❌ `WP01-slug.md` (wrong directory)

2. **Load design documents** from `feature_dir` (only those present):
   - **Required**: plan.md (tech architecture, stack), spec.md (user stories & priorities)
   - **Optional**: data-model.md (entities), contracts/ (API schemas), research.md (decisions), quickstart.md (validation scenarios)
   - Scale your effort to the feature: simple UI tweaks deserve lighter coverage, multi-system releases require deeper decomposition.

3. **Derive fine-grained subtasks** (IDs `T001`, `T002`, ...):
   - Parse plan/spec to enumerate concrete implementation steps, tests (only if explicitly requested), migrations, and operational work.
   - Capture prerequisites, dependencies, and parallelizability markers (`[P]` means safe to parallelize per file/concern).
   - Maintain the subtask list internally; it feeds the work-package roll-up and the prompts.

4. **Roll subtasks into work packages** (IDs `WP01`, `WP02`, ...):
   - Target 4–10 work packages. Each should be independently implementable, rooted in a single user story or cohesive subsystem.
   - Ensure every subtask appears in exactly one work package.
   - Name each work package with a succinct goal (e.g., “User Story 1 – Real-time chat happy path”).
   - Record per-package metadata: priority, success criteria, risks, dependencies, and list of included subtasks.

5. **Write `tasks.md`** using `.kittify/templates/tasks-template.md`:
   - **Location**: Write to `<feature_dir>/tasks.md` (use the absolute feature_dir path from step 1)
   - Populate the Work Package sections (setup, foundational, per-story, polish) with the `WPxx` entries
   - Under each work package include:
     - Summary (goal, priority, independent test)
     - Included subtasks (checkbox list referencing `Txxx`)
     - Implementation sketch (high-level sequence)
     - Parallel opportunities, dependencies, and risks
   - Preserve the checklist style so implementers can mark progress

6. **Generate prompt files (one per work package)** using a chunked file creation strategy:
   
   **Directory Setup**:
   - **CRITICAL PATH RULE**: All work package files MUST be created in a FLAT `<feature_dir>/tasks/` directory, NOT in subdirectories!
   - Correct structure: `<feature_dir>/tasks/WPxx-slug.md` (flat, no subdirectories)
   - WRONG (do not create): `<feature_dir>/tasks/planned/`, `<feature_dir>/tasks/doing/`, or ANY lane subdirectories
   - WRONG (do not create): `/tasks/`, `tasks/`, or any path not under feature_dir
   - Ensure `<feature_dir>/tasks/` exists (create as flat directory, NO subdirectories)
   
   **Chunked File Generation Strategy** (CRITICAL for avoiding context length issues):
   - **DO NOT attempt to generate all WP files in a single operation**
   - **Use batch creation**: Generate work package prompt files in groups of 2-3 at a time
   - **Process order**: Create WP01-03 first, then WP04-06, then WP07-09, etc.
   - **Per-chunk workflow**:
     1. Prepare content for 2-3 WP files in memory
     2. Write those files using file creation tools
     3. Report completion of that chunk with file paths
     4. Continue to next chunk until all WP files are created
   - **No self-imposed limits**: Do not skip or abbreviate work packages due to "context concerns" - the chunking strategy handles this
   - **Full detail required**: Each WP prompt must be complete and exhaustive per the template, regardless of how many WPs exist
   
   **Per Work Package**:
   - For each work package in the current chunk:
     - Derive a kebab-case slug from the title; filename: `WPxx-slug.md`
     - Full path example: `<feature_dir>/tasks/WP01-create-html-page.md` (use ABSOLUTE path from feature_dir variable)
     - Use `.kittify/templates/task-prompt-template.md` to capture:
       - Frontmatter with `work_package_id`, `subtasks` array, `lane: "planned"`, history entry
       - Objective, context, detailed guidance per subtask
       - Test strategy (only if requested)
       - Definition of Done, risks, reviewer guidance
     - Update `tasks.md` to reference the prompt filename
   - Keep prompts exhaustive enough that a new agent can complete the work package unaided

   **IMPORTANT**: All WP files live in flat `tasks/` directory. Lane status is tracked ONLY in the `lane:` frontmatter field, NOT by directory location. Agents can change lanes by editing the `lane:` field directly or using `spec-kitty agent tasks move-task`.

7. **Report**: Provide a concise outcome summary:
   - Path to `tasks.md`
   - Work package count and per-package subtask tallies
   - Parallelization highlights
   - MVP scope recommendation (usually Work Package 1)
  - Prompt generation stats (files written, directory structure, any skipped items with rationale)
   - Next suggested command (e.g., `/spec-kitty.analyze` or `/spec-kitty.implement`)

Context for work-package planning: {ARGS}

The combination of `tasks.md` and the bundled prompt files must enable a new engineer to pick up any work package and deliver it end-to-end without further specification spelunking.

## Task Generation Rules

**Tests remain optional**. Only include testing tasks/steps if the feature spec or user explicitly demands them.

1. **Subtask derivation**:
   - Assign IDs `Txxx` sequentially in execution order.
   - Use `[P]` for parallel-safe items (different files/components).
   - Include migrations, data seeding, observability, and operational chores.

2. **Work package grouping**:
   - Map subtasks to user stories or infrastructure themes.
   - Keep each work package laser-focused on a single goal; avoid mixing unrelated stories.
   - Do not exceed 10 work packages. Merge low-effort items into broader bundles when necessary.

3. **Prioritisation & dependencies**:
   - Sequence work packages: setup → foundational → story phases (priority order) → polish.
   - Call out inter-package dependencies explicitly in both `tasks.md` and the prompts.

4. **Prompt composition**:
   - Mirror subtask order inside the prompt.
   - Provide actionable implementation and test guidance per subtask—short for trivial work, exhaustive for complex flows.
   - Surface risks, integration points, and acceptance gates clearly so reviewers know what to verify.
   - **CRITICAL**: The task-prompt-template.md includes anti-skipping language at the top - do NOT remove or weaken this language. It prevents agents from self-limiting due to perceived context constraints.

5. **Think like a tester**: Any vague requirement should be tightened until a reviewer can objectively mark it done or not done.

6. **Agent behavior enforcement**: When generating WP prompts, preserve the "🚨 CRITICAL: Complete Implementation Required" section from the template. This prevents agents from skipping work packages for efficiency reasons.
