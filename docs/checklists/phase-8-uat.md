# Phase 8 UAT Checklist - Docker Release and GHCR Automation

Date: 2026-10-09
Tester: hutch
Environment/Branch: main
Service Name: recipelab

---

## 1) Preconditions

- [x] `ship/.env_ship.sh` exists with `DOCKER_SERVICE_NAME=recipelab` and `APP_TYPE=py`
- [x] Repo contains `.github/workflows/docker-release.yml`
- [x] Repo contains `Dockerfile`
- [x] Server docker directory exists with `docker-compose.yml` based on `docker-compose-example.yml`
- [x] Server `.env` is present in `/home/hutch/dockers/recipelab/.env`

---

## 2) Local Quality Gate

Run:

```bash
.venv/bin/python -m black --check .
.venv/bin/python -m flake8 .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall app tests run.py
```

- [x] Black check passes
- [x] Flake8 passes
- [x] Unit test suite passes
- [x] Compile check passes

---

## 3) GitHub Release Trigger

Run (example):

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push --follow-tags
```

- [ ] Tag push triggers `Docker Release` workflow
- [ ] Workflow `test` job passes
- [ ] Workflow `release` job passes

---

## 4) GHCR Image Validation

- [ ] `ghcr.io/hutchybop/recipelab:vX.Y.Z` exists
- [ ] `ghcr.io/hutchybop/recipelab:latest` updated
- [ ] Optional trace tag exists (`sha-<shortsha>`)

---

## 5) Server Deployment Validation

Deploy via ship script (`deploy = y`):

```bash
bash /Users/hutch/Coding/ship/ship.sh
```

- [ ] Script polls and detects newer `latest` image
- [ ] `docker compose pull` succeeds on server
- [ ] `docker compose up -d` succeeds on server
- [ ] Container `recipelab` is healthy

Smoke checks:
- [ ] `GET /api/health` returns OK from running container
- [ ] UI home page loads
- [ ] No critical runtime errors in container logs

---

## 6) Validation Gate Decision

Gate requirement: deploy from GHCR image and pass smoke checklist.

Overall Result:
- [ ] PASS - Phase 8 complete
- [ ] FAIL - remediation required

Notes / Issues Found:

```
TBD
```

Remediation Tasks (if any):

```
TBD
```

Sign-off:
- Name: 
- Date: 
