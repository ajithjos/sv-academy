SHELL := /bin/bash

DEV_APP_PORT ?= 3022
GCP_PROJECT_ID ?=
CLOUD_RUN_REGION ?= us-central1
CLOUD_RUN_SERVICE ?= systemverilog-academy
IMAGE_NAME ?= systemverilog-academy-web
IMAGE_TAG ?= manual

.PHONY: help install-dev dev build start lint typecheck format format-check check docker-build cloudrun-deploy cloudrun-deploy-plan

help:
	@echo "Common targets: install-dev, dev, build, check"
	@echo "Deploy targets: docker-build, cloudrun-deploy-plan, cloudrun-deploy"

install-dev:
	npm install

dev:
	npm run dev -- --hostname 127.0.0.1 --port $(DEV_APP_PORT)

build:
	npm run build

start:
	npm run start -- --hostname 127.0.0.1 --port $(APP_PORT)

lint:
	npm run lint

typecheck:
	npm run typecheck

format:
	npm run format

format-check:
	npm run format:check

check: lint typecheck build

docker-build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

cloudrun-deploy-plan:
	bash deploy/cloudrun/deploy.sh --plan

cloudrun-deploy:
	bash deploy/cloudrun/deploy.sh
