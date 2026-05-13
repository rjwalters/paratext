.PHONY: install format lint test generate run-explicit run-implicit analyze report clean help

PY ?= python
PIP ?= $(PY) -m pip
MODEL ?= mock/echo
LIMIT ?= 0
VARIANTS ?= data/variants/variants.jsonl
EXPLICIT_OUT ?= data/runs/explicit.jsonl
IMPLICIT_OUT ?= data/runs/implicit.jsonl
REPORT_OUT ?= reports/mvp_report.md

help:
	@echo "Targets:"
	@echo "  install        - Install package in editable mode with dev extras"
	@echo "  format         - Run ruff format"
	@echo "  lint           - Run ruff check"
	@echo "  test           - Run pytest"
	@echo "  generate       - Generate variant prompts from seed dataset"
	@echo "  run-explicit   - Run explicit-state experiment (MODEL=$(MODEL))"
	@echo "  run-implicit   - Run implicit-response experiment (MODEL=$(MODEL))"
	@echo "  analyze        - Generate Markdown report from runs"
	@echo "  report         - Alias for analyze"
	@echo "  clean          - Remove generated runs and reports"

install:
	$(PIP) install -e ".[dev,openai]"

format:
	$(PY) -m ruff format textual_intuition tests scripts

lint:
	$(PY) -m ruff check textual_intuition tests scripts

test:
	$(PY) -m pytest

generate:
	$(PY) -m textual_intuition.cli generate-variants \
		--input data/seed_prompts.yaml \
		--output $(VARIANTS)

run-explicit:
	$(PY) -m textual_intuition.cli run-explicit \
		--variants $(VARIANTS) \
		--model $(MODEL) \
		--output $(EXPLICIT_OUT) \
		--limit $(LIMIT)

run-implicit:
	$(PY) -m textual_intuition.cli run-implicit \
		--variants $(VARIANTS) \
		--model $(MODEL) \
		--output $(IMPLICIT_OUT) \
		--limit $(LIMIT)

analyze:
	$(PY) -m textual_intuition.cli analyze \
		--explicit $(EXPLICIT_OUT) \
		--implicit $(IMPLICIT_OUT) \
		--output $(REPORT_OUT)

report: analyze

clean:
	rm -rf data/runs/*.jsonl reports/*.md
	rm -rf .pytest_cache **/__pycache__
