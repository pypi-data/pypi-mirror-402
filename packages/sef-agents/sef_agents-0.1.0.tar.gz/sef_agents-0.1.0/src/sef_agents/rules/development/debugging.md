# Debugging Protocol (Curator)

## 1. Triage
- **Severity**: Critical (Data Loss/Outage) vs Non-Critical.
- **Reproduce**: Create minimal repro case. Script it.

## 2. Root Cause Analysis
- **5 Whys**: Ask "Why?" 5 times deeply.
- **Ishikawa (Fishbone)**: Check Inputs, Logic, Env, Deps.
- **Binary Search**: Bisect code/commits to find injection point.

## 3. Fix Protocol
1.  **Isolate**: Confirm Fix in isolation.
2.  **Verify**: Run Repro script -> Must Pass.
3.  **Regress**: Run full suite -> No side effects.
4.  **Codify**: Add regression test to repo.

## 4. Output
## 4. Output: Fix Plan (Chat Only)
**Do NOT generate a file.** Output to Chat.

```markdown
### Bug
[Desc]
### Root Cause
[Analysis]
### Fix
[Code]
### Verification
- Repro: Pass
- Suite: Pass
```
