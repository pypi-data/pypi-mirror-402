# Makefile for human-eval web deployment
#
# Configuration: Set these in your environment or .env file
#   GITHUB_REPO - GitHub repository (e.g., lyptus-research/lyptus-mono)
#   VPS_HOST    - VPS SSH target (e.g., user@eval.lyptus.dev)
#   VPS_DIR     - Directory on VPS (default: /opt/human-eval)
#
# Usage:
#   make dev           # Run locally with docker compose
#   make build         # Build images locally
#   make push          # Push images to ghcr.io
#   make deploy        # Build, push, and deploy to VPS
#   make rollback V=x.y.z  # Rollback to specific version
#   make logs          # Tail logs on VPS

SHELL := /bin/bash

# Configuration with defaults
GITHUB_REPO ?= lyptus-research/lyptus-mono
VPS_HOST ?= $(error VPS_HOST not set - run: export VPS_HOST=user@your-server)
VPS_DIR ?= /opt/human-eval
REGISTRY := ghcr.io/$(GITHUB_REPO)

# Version from git (short commit hash, or tag if on one)
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")

.PHONY: dev build push deploy rollback logs ssh setup-vps clean help

# Default target
help:
	@echo "human-eval web deployment"
	@echo ""
	@echo "Usage:"
	@echo "  make dev           Run locally with docker compose"
	@echo "  make build         Build Docker images"
	@echo "  make push          Push images to ghcr.io"
	@echo "  make deploy        Build, push, and deploy to VPS"
	@echo "  make rollback V=x  Rollback to version x"
	@echo "  make logs          Tail VPS logs"
	@echo "  make ssh           SSH into VPS"
	@echo "  make setup-vps     Initial VPS setup (run once)"
	@echo ""
	@echo "Configuration:"
	@echo "  GITHUB_REPO=$(GITHUB_REPO)"
	@echo "  VPS_HOST=$(VPS_HOST)"
	@echo "  VPS_DIR=$(VPS_DIR)"
	@echo "  VERSION=$(VERSION)"

# Local development
dev:
	docker compose up --build

dev-down:
	docker compose down

# Build images
build:
	@echo "Building images with version $(VERSION)..."
	docker build -t $(REGISTRY)/backend:$(VERSION) -t $(REGISTRY)/backend:latest ./backend
	docker build -t $(REGISTRY)/frontend:$(VERSION) -t $(REGISTRY)/frontend:latest ./frontend

# Push to registry
push: build
	@echo "Pushing images to $(REGISTRY)..."
	docker push $(REGISTRY)/backend:$(VERSION)
	docker push $(REGISTRY)/backend:latest
	docker push $(REGISTRY)/frontend:$(VERSION)
	docker push $(REGISTRY)/frontend:latest

# Deploy to VPS
deploy: push
	@echo "Deploying version $(VERSION) to $(VPS_HOST)..."
	ssh $(VPS_HOST) "cd $(VPS_DIR) && \
		export VERSION=$(VERSION) && \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d && \
		docker image prune -f"
	@echo "Deployed! Check: make logs"

# Rollback to specific version
rollback:
ifndef V
	$(error V is not set. Usage: make rollback V=1.2.3)
endif
	@echo "Rolling back to version $(V)..."
	ssh $(VPS_HOST) "cd $(VPS_DIR) && \
		export VERSION=$(V) && \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"

# Tail logs
logs:
	ssh $(VPS_HOST) "cd $(VPS_DIR) && docker compose logs -f --tail=100"

# SSH into VPS
ssh:
	ssh $(VPS_HOST)

# Initial VPS setup (run once)
setup-vps:
	@echo "Setting up VPS at $(VPS_HOST)..."
	ssh $(VPS_HOST) "mkdir -p $(VPS_DIR)/data/eval_logs"
	scp docker-compose.yml docker-compose.prod.yml nginx-ssl.conf .env.production $(VPS_HOST):$(VPS_DIR)/
	ssh $(VPS_HOST) "cd $(VPS_DIR) && mv .env.production .env"
	@echo "VPS setup complete. Configure SSL with certbot, then run: make deploy"

# Clean local Docker resources
clean:
	docker compose down --rmi local -v
	docker image prune -f
