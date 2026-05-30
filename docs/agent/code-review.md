# Code Review

Final delivery must include a `/review` step. If no slash command is callable, use this fallback:

1. Compare the diff against the requested plan.
2. Lead with findings, ordered by severity.
3. Include file and line references for actionable issues.
4. Check that no add-on behavior changed during preparation work.
5. Check that verifiers and docs agree on command names and scope.
6. Check that Blender smoke does not write outside temporary user directories.
7. List verification commands run and any failures.
8. List residual risks, especially known frozen drift.

Do not treat a missing optional visual QA pass as a blocker unless the task changed Blender UI behavior.
