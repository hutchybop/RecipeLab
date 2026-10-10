# Phase 9 UAT Checklist - Responsive Foundation (Phase 1)

Date: 2026-10-10
Tester: hutch
Environment/Branch: main
Mongo DB Name Used: recipelab

---

## 1) Preconditions

- [x] `.env` is valid and app is running on `http://localhost:3009`
- [x] `GET /api/health` responds successfully
- [x] Browser dev tools are available for responsive viewport testing

---

## 2) Global Navigation - Mobile Behavior

Test viewport: iPhone 12/13/14 (`390x844`) and iPhone SE (`375x667`).

Manual checks (repeat on `/`, `/recipes`, `/suggestions`, `/generate`, `/import`, `/profile`, `/settings`):

- [x] Navbar does **not** show piled/overlapping links at page load
- [x] Hamburger/toggler is visible on mobile widths
- [x] Tapping toggler expands nav links
- [x] Tapping toggler again collapses nav links
- [x] Expanded nav links are readable and easy to tap
- [x] Each nav link routes to the correct page

---

## 3) Global Navigation - Desktop/Tablet Regression

Test viewports: `1366x768` and `1920x1080` (desktop), `768x1024` (tablet).

- [x] Desktop navbar remains expanded (no unwanted collapse)
- [x] Brand/logo alignment looks correct
- [x] Link spacing/alignment looks consistent with prior behavior
- [x] No visual clipping in navbar at tablet widths

---

## 4) Shared Responsive Foundation Sanity Checks

Manual checks:

- [x] No new horizontal page overflow on key pages
- [x] Focus ring appears on navbar toggler when keyboard-focused
- [x] Dark theme contrast remains acceptable for navbar controls/text

---

## 5) Smoke + Regression Checks

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

## 6) Validation Gate Decision

Gate requirement: mobile navbar is fully usable and no desktop navbar regressions.

Overall Result:
- [x] PASS - Phase 1 responsive foundation complete
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
