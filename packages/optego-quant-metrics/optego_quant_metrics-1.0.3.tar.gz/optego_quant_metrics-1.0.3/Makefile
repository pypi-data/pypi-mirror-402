.PHONY: dep
dep:
	uv sync --extra dev
	uv run pre-commit install

.PHONY: fmt
fmt:
	uv run pre-commit run --all-files

.PHONY: run
run:
	uv run python -m main

.PHONY: tests
tests:
	uv run python -m pytest tests -rP

.PHONY: ft
ft: fmt tests

.PHONY: build
build:
	uv run python -m build

.PHONY: publish
publish: build
	uv run twine upload dist/*

.PHONY: publish-test
publish-test: build
	uv run twine upload --repository testpypi dist/*

.PHONY: major
major:
	uv run bump2version major

.PHONY: minor
minor:
	uv run bump2version minor

.PHONY: patch
patch:
	uv run bump2version patch
