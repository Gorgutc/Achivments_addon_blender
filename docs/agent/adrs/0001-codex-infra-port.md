# ADR 0001: Port Codex Infrastructure To Blender Add-on Stack

Status: accepted for preparation layer.

Context: sibling repositories contain useful Codex orchestration patterns, including repo-local instructions, plugins, skills, agents, hooks, docs, and verification commands. Their application stack assumptions are not portable to this Blender add-on.

Decision:
- Reuse the orchestration shape: AGENTS instructions, repo-local plugin, skills, agents, hooks, docs, and verifiers.
- Rewrite all active instructions around Python, `bpy`, Blender 5.0+, add-on registration, persistence, and Blender smoke tests.
- Keep package-manager and web application rules out of active docs. Web-stack rules are not copied.
- Keep add-on code frozen during this preparation task.

Consequences:
- The repository gains a Codex work layer without changing add-on behavior.
- Future work can run static and Blender smoke gates before touching add-on code.
- Known drift remains documented until a later add-on-code task addresses it.
