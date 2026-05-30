# Codex Hooks

These hooks are intentionally fast. They print repository context, nudge prompts toward Blender/Python rules, and run static verifiers after common edit tools, including `apply_patch`. They do not run Blender background smoke checks after every edit; Blender smoke belongs to deep and ship gates.
