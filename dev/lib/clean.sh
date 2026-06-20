#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-routine}"
DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "$DEV_DIR/.." >/dev/null 2>&1 && pwd)"

cd "$REPO_ROOT"

remove_path() {
	local path="$1"
	[[ -e "$path" || -L "$path" ]] || return 0
	rm -rf "$path"
}

clean_python() {
	find . \
		-path ./.git -prune -o \
		-path ./node_modules -prune -o \
		-path './*/node_modules' -prune -o \
		-path ./.venv -prune -o \
		-path './*/.venv' -prune -o \
		-type d \( \
			-name __pycache__ -o \
			-name .pytest_cache -o \
			-name .ruff_cache -o \
			-name .mypy_cache -o \
			-name .pyright \
		\) -prune -exec rm -rf {} +

	find . \
		-path ./.git -prune -o \
		-path ./node_modules -prune -o \
		-path './*/node_modules' -prune -o \
		-path ./.venv -prune -o \
		-path './*/.venv' -prune -o \
		-type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

	remove_path .coverage
}

clean_routine() {
	clean_python
	remove_path coverage
	remove_path htmlcov
	remove_path .next
	remove_path out
	remove_path .turbo
	remove_path .parcel-cache
	remove_path .dart_tool
	find . -maxdepth 3 -type f -name '*.tsbuildinfo' -delete
}

clean_all() {
	clean_routine
	remove_path build
	remove_path dist
	remove_path site
	remove_path docs_site/build
	remove_path docs_site/.docusaurus
	find . \
		-path ./.git -prune -o \
		-path ./node_modules -prune -o \
		-path './*/node_modules' -prune -o \
		-path ./.venv -prune -o \
		-path './*/.venv' -prune -o \
		-type d \( -name '*.egg-info' -o -name '*.egg' -o -name .eggs \) -prune -exec rm -rf {} +

	if [[ "${DEV_CLEAN_INCLUDE_DEPS:-0}" == "1" ]]; then
		remove_path .venv
		remove_path node_modules
		remove_path rust/target
		remove_path target
	fi
}

case "$MODE" in
	python|pc)
		clean_python
		;;
	routine|dev)
		clean_routine
		;;
	all|aggressive)
		clean_all
		;;
	*)
		echo "Usage: dev/lib/clean.sh {python|routine|all}" >&2
		exit 2
		;;
esac

echo "[dev-clean] Completed $MODE cleanup in $REPO_ROOT"
