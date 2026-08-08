---
name: achievements-registration-lifecycle
description: Review register/unregister, handlers, timers, draw handlers, and Scene properties.
---

# Achievements Registration Lifecycle

Use for registration lifecycle work.

Check:
- Every registered class is unregistered.
- Every `bpy.types.Scene` property is removed.
- Every handler is removed.
- Every timer is not left in a repeated dirty state.
- Draw handlers are cleared.
- Repeated register/unregister should not leak state.
