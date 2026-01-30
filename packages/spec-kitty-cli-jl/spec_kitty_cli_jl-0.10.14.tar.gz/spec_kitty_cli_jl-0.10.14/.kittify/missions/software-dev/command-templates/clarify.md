---
description: Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

Goal: Detect and reduce ambiguity or missing decision points in the active feature specification and record the clarifications directly in the spec file.

Note: This clarification workflow is expected to run (and be completed) BEFORE invoking `/spec-kitty.plan`. If the user explicitly states they are skipping clarification (e.g., exploratory spike), you may proceed, but must warn that downstream rework risk increases.

Execution steps:

1. Run the prerequisites check command from repo root **once** with combined JSON and paths-only flags:
   
   ```bash
   spec-kitty agent feature check-prerequisites --json --paths-only
   ```
   
   Parse the JSON payload fields:
   - `feature_dir`: Absolute path to the feature directory
   - `spec_file`: Absolute path to spec.md
   - `checklists_dir`: Absolute path to checklists/ directory (if exists)
   - `research_dir`: Absolute path to research/ directory (if exists)
   - `tasks_dir`: Absolute path to tasks/ directory (if exists)
   
   If JSON parsing fails or returns an error, abort and instruct user to re-run `/spec-kitty.specify` or verify feature branch environment.

   **Note**: The command automatically detects the current feature context whether you're in the main repo or a worktree.

2. Load the current spec file using the `spec_file` path from the JSON output. Perform a structured ambiguity & coverage scan using this taxonomy. For each category, mark status: Clear / Partial / Missing. Produce an internal coverage map used for prioritization (do not output raw map unless no questions will be asked).

   Functional Scope & Behavior:
   - Core user goals & success criteria
   - Explicit out-of-scope declarations
   - User roles / personas differentiation

   Domain & Data Model:
   - Entities, attributes, relationships
   - Identity & uniqueness rules
   - Lifecycle/state transitions
   - Data volume / scale assumptions

   Interaction & UX Flow:
   - Critical user journeys / sequences
   - Error/empty/loading states
   - Accessibility or localization notes

   Non-Functional Quality Attributes:
   - Performance (latency, throughput targets)
   - Scalability (horizontal/vertical, limits)
   - Reliability & availability (uptime, recovery expectations)
   - Observability (logging, metrics, tracing signals)
   - Security & privacy (authN/Z, data protection, threat assumptions)
   - Compliance / regulatory constraints (if any)

   Integration & External Dependencies:
   - External services/APIs and failure modes
   - Data import/export formats
   - Protocol/versioning assumptions

   Edge Cases & Failure Handling:
   - Negative scenarios
   - Rate limiting / throttling
   - Conflict resolution (e.g., concurrent edits)

   Constraints & Tradeoffs:
   - Technical constraints (language, storage, hosting)
   - Explicit tradeoffs or rejected alternatives

   Terminology & Consistency:
   - Canonical glossary terms
   - Avoided synonyms / deprecated terms

   Completion Signals:
   - Acceptance criteria testability
   - Measurable Definition of Done style indicators

   Misc / Placeholders:
   - TODO markers / unresolved decisions
   - Ambiguous adjectives ("robust", "intuitive") lacking quantification

   For each category with Partial or Missing status, add a candidate question opportunity unless:
   - Clarification would not materially change implementation or validation strategy
   - Information is better deferred to planning phase (note internally)

3. Generate (internally) a prioritized queue of candidate clarification questions (maximum 5). Do NOT output them all at once. Apply these constraints:
    - Maximum of 10 total questions across the whole session.
    - Each question must be answerable with EITHER:
       * A short multiple‑choice selection (2–5 distinct, mutually exclusive options), OR
       * A one-word / short‑phrase answer (explicitly constrain: "Answer in <=5 words").
   - Only include questions whose answers materially impact architecture, data modeling, task decomposition, test design, UX behavior, operational readiness, or compliance validation.
   - Ensure category coverage balance: attempt to cover the highest impact unresolved categories first; avoid asking two low-impact questions when a single high-impact area (e.g., security posture) is unresolved.
   - Exclude questions already answered, trivial stylistic preferences, or plan-level execution details (unless blocking correctness).
    - Favor clarifications that reduce downstream rework risk or prevent misaligned acceptance tests.
    - Scale thoroughness to the feature’s complexity: a lightweight enhancement may only need one or two confirmations, while multi-system efforts warrant the full question budget if gaps remain critical.
   - If more than 5 categories remain unresolved, select the top 5 by (Impact * Uncertainty) heuristic.

4. Batch question presentation (interactive):
    - Present ALL questions at once in a numbered list format (1, 2, 3, etc.)
    - For multiple-choice questions, format with one option per line:
      
      ```
      1. [Question text]
      Options:
      Option A: describe option A
      Option B: describe option B  
      Option C: describe option C [RECOMMENDED: rationale]
      Option D: short custom answer (<=5 words)
      ```
      
      **Important**: When one option is clearly more appropriate based on common patterns, industry standards, or best practices, mark it with [RECOMMENDED: brief rationale]. For example:
      - If asking about data retention and industry standard is 90 days: `Option B: 90 days [RECOMMENDED: industry standard]`
      - If asking about authentication and OAuth is best for the context: `Option C: OAuth2 [RECOMMENDED: secure, widely supported]`
      - Only mark as recommended when there's a clear technical/practical advantage, not arbitrary preference
      
    - For short-answer style questions (no meaningful discrete options), format as:
      ```
      2. [Question text]
      Format: Short answer (<=5 words)
      ```
    
    - After presenting all questions, ask the user to respond with their answers for all questions (e.g., "1: A, 2: custom answer, 3: B")
    - After the user provides all answers:
       * Validate each answer maps to an option or fits constraints
       * If any answer is ambiguous, ask for clarification on that specific question
       * Once all answers are satisfactory, record them in working memory and proceed to integration
    - If user signals early termination ("skip", "done", "proceed"), accept partial answers and proceed with what was provided
    - If no valid questions exist at start, immediately report no critical ambiguities.

5. Integration after ALL answers are collected (batch update approach):
    - Maintain in-memory representation of the spec (loaded once at start) plus the raw file contents.
    - Create or update the `## Clarifications` section:
       * Ensure a `## Clarifications` section exists (create it just after the highest-level contextual/overview section per the spec template if missing).
       * Under it, create (if not present) a `### Session YYYY-MM-DD` subheading for today.
    - For each question-answer pair, append a bullet line: `- Question: <question> → Answer: <final answer>`.
    - Then apply all clarifications to the appropriate section(s) in one pass:
       * Functional ambiguity → Update or add a bullet in Functional Requirements.
       * User interaction / actor distinction → Update User Stories or Actors subsection (if present) with clarified role, constraint, or scenario.
       * Data shape / entities → Update Data Model (add fields, types, relationships) preserving ordering; note added constraints succinctly.
       * Non-functional constraint → Add/modify measurable criteria in Non-Functional / Quality Attributes section (convert vague adjective to metric or explicit target).
       * Edge case / negative flow → Add a new bullet under Edge Cases / Error Handling (or create such subsection if template provides placeholder for it).
       * Terminology conflict → Normalize term across spec; retain original only if necessary by adding `(formerly referred to as "X")` once.
    - If any clarification invalidates an earlier ambiguous statement, replace that statement instead of duplicating; leave no obsolete contradictory text.
    - Save the spec file ONCE after all integrations are complete to minimize disk I/O.
    - Preserve formatting: do not reorder unrelated sections; keep heading hierarchy intact.
    - Keep each inserted clarification minimal and testable (avoid narrative drift).

6. Validation (performed after the single batch write):
   - Clarifications session contains exactly one bullet per accepted answer (no duplicates).
   - Total asked (accepted) questions ≤ 5.
   - Updated sections contain no lingering vague placeholders the new answer was meant to resolve.
   - No contradictory earlier statement remains (scan for now-invalid alternative choices removed).
   - Markdown structure valid; only allowed new headings: `## Clarifications`, `### Session YYYY-MM-DD`.
   - Terminology consistency: same canonical term used across all updated sections.

7. Write the updated spec back to the `spec_file` path.

8. Report completion (after all questions answered and integrated):
   - Number of questions asked & answered.
   - Path to updated spec file.
   - Sections touched (list names).
   - Coverage summary listing each taxonomy category with a status label (Resolved / Deferred / Clear / Outstanding). Present as plain text or bullet list, not a table.
   - If any Outstanding or Deferred remain, recommend whether to proceed to `/spec-kitty.plan` or run `/spec-kitty.clarify` again later post-plan.
   - Suggested next command.

Behavior rules:
- If no meaningful ambiguities found (or all potential questions would be low-impact), respond: "No critical ambiguities detected worth formal clarification." and suggest proceeding.
- If spec file missing, instruct user to run `/spec-kitty.specify` first (do not create a new spec here).
- Never exceed 5 total questions per session.
- Avoid speculative tech stack questions unless the absence blocks functional clarity.
- Respect user early termination signals ("skip", "done", "proceed").
 - If no questions asked due to full coverage, output a compact coverage summary (all categories Clear) then suggest advancing.
 - If some questions remain unanswered due to early termination, process only the answered questions and note which were skipped.

Context for prioritization: {ARGS}
