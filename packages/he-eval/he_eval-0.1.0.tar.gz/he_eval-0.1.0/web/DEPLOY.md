# Deployment Guide

## Architecture

```
Local machine                        VPS (cyber-task-horizons.com)
+------------------+                 +---------------------------+
| make deploy      |  --SSH-->       | /opt/human-eval/          |
|   - build images |                 |   docker-compose.yml      |
|   - push ghcr.io |                 |   data/                   |
|   - ssh + pull   |                 |     human_eval.db         |
+------------------+                 |     eval_logs/            |
                                     +---------------------------+
```

## Manual Workflow

### Deploy web changes

After committing and pushing changes to `human-eval/web/`:

```bash
cd human-eval/web
make deploy
```

This will:
1. Build Docker images locally
2. Push to ghcr.io/lyptus-research/lyptus-mono/backend:VERSION
3. SSH to VPS, pull new images, restart containers

### Rollback

If something breaks:

```bash
make rollback V=abc1234   # Use a previous git commit/tag
```

### Check logs

```bash
make logs
```

### SSH into VPS

```bash
make ssh
```

## Data Persistence

Data survives container updates because it's mounted as a volume:

| Data | Container path | VPS path |
|------|----------------|----------|
| SQLite DB | `/app/data/human_eval.db` | `/opt/human-eval/data/human_eval.db` |
| Eval logs | `/app/data/eval_logs/` | `/opt/human-eval/data/eval_logs/` |

Containers are stateless - all persistent data lives on the VPS filesystem.

## Initial VPS Setup (one-time)

1. SSH into VPS and install Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

2. Authenticate with GitHub Container Registry:
   ```bash
   echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin
   ```

3. Create `.env.production` locally with real values, then:
   ```bash
   make setup-vps
   ```

4. Get SSL certificate:
   ```bash
   ssh $VPS_HOST
   sudo certbot certonly --standalone -d cyber-task-horizons.com
   ```

5. First deploy:
   ```bash
   make deploy
   ```

## Environment Variables

Required in `.env` on VPS:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `CORS_ORIGINS` | `["https://cyber-task-horizons.com"]` |
| `DOMAIN` | `cyber-task-horizons.com` |

## CLI Releases (PyPI)

The CLI is a separate package. To release a new version:

```bash
cd human-eval
# Update version in pyproject.toml
uv build
uv publish
```

Evaluators update with: `pip install --upgrade human-eval`
