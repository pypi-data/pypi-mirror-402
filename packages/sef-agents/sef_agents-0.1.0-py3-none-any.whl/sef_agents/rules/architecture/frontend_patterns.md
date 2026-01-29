---
description: Apply when frontend code scan is requested
alwaysApply: false
---
# Frontend Quality Fragments

## 1. Input & Data
- **Forms**: Validate constraints/types. Mark required fields.
- **API**: Check req/res schemas (Zod/Yup).
- **Sanitize**: Encode HTML. Prevent `dangerouslySetInnerHTML` misuse.

## 2. Error & Resilience
- **Global**: Use React Error Boundaries. Catch unhandled promise rejections.
- **Network**: Handle timeouts/offline. Implement retries.
- **Async**: Wrap `async/await` in `try-catch`.

## 3. Security
- **XSS**: Sanitize user content. Define CSP.
- **Auth**: Guard routes. Secure token storage.
- **Privacy**: No sensitive data in logs/LocalStorage.

## 4. Performance
- **Loading**: Lazy-load large components. Code-split.
- **Memory**: Cleanup `useEffect` (listeners/subscriptions).
- **Assets**: Optimize images. Use efficient loading.

## 5. UX & A11y
- **Feedback**: Clear error/loading/empty states.
- **A11y**: ARIA labels. Keyboard-nav. Semantic HTML.
- **Forms**: Clear validation feedback.

## 6. Architecture & Quality
- **State**: Consolidate state. Handle side-effects cleanly.
- **Structure**: Separate logic from presentation. Refactor complex components.
- **Tests**: Verify critical paths and error scenarios.

## 7. Report Output
- **Directory**: `scancheck/frontend`
- **Scores**: CRITICAL(0-3), HIGH(4-6), MEDIUM(7-8), LOW(9-10).
- **Summary**: Overall quality score (0-100). Top 5 issues. PASS/FAIL recommendation.
