# Compliance Report: function_app.py

**Generated:** 2026-01-07 20:55:17
**Date:** 2026-01-07
**Time:** 20:55:17

---

⚠️ Issues Found:
- [ ] Found standard `logging`. Use `structlog`.
  - **Note:** Other code uses `logging`. Mixed logging libraries may cause issues. Consider deferring until codebase-wide migration.
- [ ] Line 1195: Code-echoing: getter comment (Curator protocol violation).
