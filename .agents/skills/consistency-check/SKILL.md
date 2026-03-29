---
name: consistency-check
description: >-
  Review consistency between documentation pages, documentation and code,
  and within code itself for the poolman Home Assistant integration.
  Produces a detailed markdown report with findings and suggested actions.
  Use when asked to check consistency, review documentation accuracy,
  verify docs match code, audit code conventions, or when the user
  mentions "consistency", "drift", "out of date", "sync docs",
  "review docs", or "check documentation".
compatibility: Requires file reading and code search tools
---

# Consistency Check

Review the poolman codebase for consistency issues across documentation, code,
and translations. Produce a structured report and offer to fix findings.

## Workflow

This skill follows a 4-phase interactive workflow:

1. **Ask** - Clarify the review scope with the user
2. **Analyze** - Systematically check the repository
3. **Report** - Present findings as structured markdown
4. **Act** - Offer and apply fixes

## Phase 1: Ask the User

Present the user with a choice of review scope. Use the question tool if available,
otherwise ask in plain text:

**Review types:**

- **Documentation consistency** - Check consistency across all documentation pages
  in `docs/` and `README.md` (terminology, cross-references, formatting, navigation)
- **Documentation-code consistency** - Verify that documentation accurately reflects
  the current codebase (entities, modes, chemistry parameters, rules, config flow)
- **Code consistency** - Audit internal code conventions (translations parity,
  constant alignment, naming, type hints, docstrings, test coverage)
- **Full review** - Run all three checks

If the user already specified a scope in their request, skip this phase and proceed
directly to analysis.

## Phase 2: Analyze

Based on the selected scope, load the appropriate reference file(s) and
systematically check every rule listed in them.

| Scope              | Reference file to read                                                   |
| ------------------ | ------------------------------------------------------------------------ |
| Documentation      | [references/doc-consistency.md](references/doc-consistency.md)           |
| Documentation-code | [references/doc-code-consistency.md](references/doc-code-consistency.md) |
| Code               | [references/code-consistency.md](references/code-consistency.md)         |
| Full review        | All three files above                                                    |

For each reference file loaded, follow the check rules it describes. Use file
reading and search tools to inspect the actual files in the repository. Do not
guess or assume -- verify every claim by reading the source.

**Analysis approach:**

1. Read the reference file for the selected scope
2. For each check rule, read the relevant source files
3. Compare expected vs actual content
4. Record any discrepancy as a finding with:
   - **Location**: file path and line number (e.g. `docs/entities.md:42`)
   - **Issue**: clear, concise description of the inconsistency
   - **Severity**: `critical` (factually wrong / breaks functionality),
     `warning` (misleading or incomplete), or `info` (style / minor)
   - **Suggested fix**: specific corrective action

Use task agents when available to parallelize checks across independent files.
For full reviews, run all three analysis scopes concurrently.

## Phase 3: Report

Present findings using this exact template:

```markdown
# Consistency Check Report

**Date:** YYYY-MM-DD
**Scope:** [Documentation / Documentation-Code / Code / Full Review]

## Summary

| Severity | Count |
| -------- | ----- |
| Critical | X     |
| Warning  | Y     |
| Info     | Z     |

## Findings

### [Category Name]

| # | Location    | Issue                            | Severity | Suggested Fix  |
| - | ----------- | -------------------------------- | -------- | -------------- |
| 1 | `file:line` | Description of the inconsistency | warning  | What to change |

<!-- Repeat ### Category sections as needed -->

## Suggested Actions

### Quick Fixes
<!-- Changes that take less than 5 minutes, like typo corrections or missing keys -->

1. Description of fix — `file:line`

### Moderate Changes
<!-- Changes that require some thought but are straightforward -->

1. Description of change — affected files

### Larger Refactors
<!-- Changes that span multiple files or require design decisions -->

1. Description of refactor — scope and rationale
```

After displaying the report, ask the user:

> Would you like to save this report to `reports/consistency-report.md`?

If the user agrees, write the report to that file (create the `reports/` directory
if it does not exist).

## Phase 4: Actions

After the report, present the suggested actions grouped by effort and ask:

> Which actions would you like me to apply? You can pick specific numbers,
> a category (e.g. "all quick fixes"), or "all".

For each action the user selects:

1. Make the change in the appropriate file(s)
2. Mark it as done in the todo list if available
3. After all selected actions are applied, offer to re-run the relevant checks
   to verify the fixes

If the user declines all actions, acknowledge and end the workflow.
