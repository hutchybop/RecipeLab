# Phase 11 UAT Checklist - Web UI Phase 3 (Accessibility + Final Responsive Polish)

Date: 2026-10-10
Tester: hutch
Environment/Branch: main
Mongo DB Name Used: recipelab

---

## 1) Preconditions

- [x] App is running at `http://localhost:3009`
- [x] `GET /api/health` responds successfully
- [x] Browser dev tools are available for viewport/device simulation

---

## 2) Cross-Device Viewport Matrix

Run checks at:

- [x] `375x667` (small phone)
- [x] `390x844` (modern phone)
- [x] `768x1024` (tablet)
- [x] `1366x768` (laptop)
- [x] `1920x1080` (desktop)

---

## 3) Keyboard and Focus Accessibility

Manual checks:

- [x] Pressing `Tab` from top of page exposes **Skip to main content**
- [x] Skip-link moves focus to main content section
- [x] Interactive controls show clear focus style (`nav`, links, buttons, inputs/selects)
- [x] Focus order is logical and usable across primary pages

Pages to sample:
- [x] `/`
- [x] `/recipes`
- [x] `/suggestions`
- [x] `/generate`
- [x] `/import`
- [x] `/profile`
- [x] `/settings`

---

## 4) Navigation Orientation and Mobile Behavior

- [x] Current section is visually highlighted in top nav
- [x] Active page link includes expected current-page semantics in browser accessibility tree
- [x] On mobile, opening nav and selecting a link collapses menu automatically
- [x] No nav overlap/clipping at phone/tablet widths

---

## 5) Touch Ergonomics and Visual Consistency

Manual checks on phone viewports:

- [x] Primary actions are comfortably tappable
- [x] Small action buttons remain usable (e.g., profile Apply/Reject)
- [x] Forms and controls are not cramped
- [x] Card spacing and typography remain readable and consistent
- [x] No unexpected horizontal scroll in core flows

Core flows to validate:
- [x] Generate -> Suggestions
- [x] Import -> Suggestions
- [x] Suggestions -> Detail -> Edit
- [x] Recipe Library -> Recipe Detail -> Edit
- [x] Profile suggestion apply/reject
- [x] Settings model save

---

## 6) Regression Suite

Run:

```bash
.venv/bin/python -m unittest tests.test_web_routes -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

- [x] Web route tests pass
- [x] Full test suite passes
- [x] Compile check passes

---

## 7) Validation Gate Decision

Gate requirement: user confirms UI is comfortable and reliable on both mobile and desktop.

Overall Result:
- [x] PASS - Web UI Phase 3 complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
Nil
```

Remediation Tasks (if any):

```
Nil
```

Sign-off:
- Name: Hutch
- Date: 26-10-10
