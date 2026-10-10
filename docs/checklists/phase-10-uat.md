# Phase 10 UAT Checklist - Web UI Phase 2 (Page Layout Responsiveness)

Date: 2026-10-10
Tester: hutch
Environment/Branch: main
Mongo DB Name Used: recipelab

---

## 1) Preconditions

- [x] App is running at `http://localhost:3009`
- [x] `GET /api/health` responds successfully
- [x] Browser dev tools are available for responsive viewport testing

---

## 2) Viewport Matrix

Test each relevant flow at:

- [x] Mobile small: `375x667`
- [x] Mobile standard: `390x844`
- [x] Tablet: `768x1024`
- [x] Laptop: `1366x768`
- [x] Desktop: `1920x1080`

---

## 3) Header and Action-Row Responsiveness

Pages: `/recipes`, `/suggestions`, `/recipes/<id>`, `/suggestions/<id>`, `/profile`, `/settings`, `/generate`, `/import`, `/`

- [x] Header title and action controls do not overlap on mobile
- [x] Action buttons stack cleanly on small screens
- [x] Action buttons remain inline/usable on larger screens
- [x] Long titles/wrapped text remain readable (no clipping)

---

## 4) List and Detail Screens

### `/recipes` and `/suggestions`
- [x] List rows keep title + badge readable on mobile
- [x] Badges do not push content off-screen

### `/recipes/<id>` and `/suggestions/<id>`
- [x] Top title + status/source badge remain readable on mobile
- [x] Feedback note input + buttons remain fully accessible on mobile
- [x] Bottom action buttons stack without overlap/cropping

---

## 5) Form-Heavy Screens

Pages: `/generate`, `/import`, `/settings`, `/recipes/<id>/edit`, `/suggestions/<id>/edit`, `/profile`

- [x] Primary/secondary action buttons are easy to tap on mobile
- [x] Buttons don’t collide with each other or form fields
- [x] Long read-only values (provider/endpoint/model) wrap instead of overflowing
- [x] Pending profile suggestion actions (Apply/Reject) stay usable on mobile

---

## 6) Regression Test Suite

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

Gate requirement: user can complete core flows on mobile without layout collisions or hidden controls.

Overall Result:
- [x] PASS - Web UI Phase 2 complete
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
