SHELL := /bin/bash

DEV_APP_PORT ?= 3022
DEPLOY_ENV_FILE ?= deploy/config/environments/prod.gcp.env
IMAGE_TAG ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo manual)

LEGACY_COURSES ?=

.PHONY: help context doctor setup devkit-bootstrap submodules-master submodules-master-check clean clean-python clean-all clean-deps dev-up build start lint typecheck format format-check check course-dataset docker-build deploy-plan deploy

DEVKIT_MAKE := $(MAKE) --no-print-directory -C dev/devkit REPO_ROOT=$(CURDIR)

help: context

devkit-bootstrap:
	@if [ ! -f dev/devkit/Makefile ]; then git submodule update --init -- dev/devkit; fi

context: devkit-bootstrap
	@$(DEVKIT_MAKE) context
	@echo
	@DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh context

doctor: devkit-bootstrap
	@$(DEVKIT_MAKE) doctor
	@DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh doctor

setup: devkit-bootstrap
	$(DEVKIT_MAKE) setup
	npm install

submodules-master: devkit-bootstrap
	$(DEVKIT_MAKE) submodules-master

submodules-master-check: devkit-bootstrap
	$(DEVKIT_MAKE) submodules-master-check

clean: devkit-bootstrap
	$(DEVKIT_MAKE) clean

clean-python: devkit-bootstrap
	$(DEVKIT_MAKE) clean-python

clean-all: devkit-bootstrap
	$(DEVKIT_MAKE) clean-all

clean-deps: devkit-bootstrap
	$(DEVKIT_MAKE) clean-deps

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

course-dataset:
	@test -n "$(LEGACY_COURSES)" || (echo "LEGACY_COURSES is required, for example: make course-dataset LEGACY_COURSES=/path/to/courses.py" && exit 1)
	python3 scripts/youtube_sync/generate_course_dataset.py --legacy-file "$(LEGACY_COURSES)"

docker-build:
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh docker-build

deploy-plan:
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh plan

deploy:
	DEPLOY_ENV_FILE="$(DEPLOY_ENV_FILE)" IMAGE_TAG="$(IMAGE_TAG)" bash deploy/cloudrun/deploy.sh deploy
