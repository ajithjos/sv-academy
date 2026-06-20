SHELL := /bin/bash

DEV_APP_PORT ?= 3022
DEPLOY_ENV_FILE ?= deploy/config/environments/prod.gcp.env
IMAGE_TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo manual)

.PHONY: help context doctor setup clean clean-python clean-all clean-deps dev-up build start lint typecheck format format-check check docker-build deploy-plan deploy

help: context

context:
	@cat dev/repo-info.md
	@echo
	@DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh context

doctor:
	@DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh doctor

setup:
	npm install

clean:
	bash dev/lib/clean.sh routine

clean-python:
	bash dev/lib/clean.sh python

clean-all:
	bash dev/lib/clean.sh all

clean-deps:
	bash dev/lib/clean.sh deps

dev-up:
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
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh docker-build

deploy-plan:
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh plan

deploy:
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh deploy
