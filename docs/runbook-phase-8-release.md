# Phase 8 Runbook - GHCR Release and Deploy (`recipelab`)

## Purpose

Release a Docker image to GHCR and deploy it on longrunner using the existing `ship` scripts.

## One-time setup checks

1. In this repo, ensure `ship/.env_ship.sh` contains:

```bash
export DOCKER_SERVICE_NAME="recipelab"
export APP_TYPE="py"
```

2. On server, ensure `/home/hutch/dockers/recipelab/docker-compose.yml` uses:

- `image: ghcr.io/hutchybop/recipelab:latest`
- `container_name: recipelab`
- `env_file: .env`

3. Ensure `/home/hutch/dockers/recipelab/.env` exists on server.

## Release + deploy flow

From repo root (`/Users/hutch/Coding/docker-apps/recipelab`):

```bash
bash /Users/hutch/Coding/ship/ship.sh
```

When prompted:

1. Let script run Python checks (`black`, `flake8`).
2. Choose deploy = `y`.
3. Enter commit message.
4. Enter release tag (`vX.Y.Z`).

Script behavior:

- pushes commit + tag
- GitHub Action builds and pushes GHCR image
- script polls for newer `ghcr.io/hutchybop/recipelab:latest`
- server runs `docker compose up -d`

## Post-deploy smoke checks

1. Verify app health endpoint from deployed environment:
- `/api/health` returns OK/degraded as expected for DB state

2. Verify app UI loads.

3. Check server logs for startup/runtime errors:

```bash
docker logs recipelab --tail 100
```

## Roll-forward note

If deploy misses the new image due to timing, rerun redeploy path:

- run ship script again with no code changes
- choose redeploy option when prompted
