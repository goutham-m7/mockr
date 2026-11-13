.PHONY: demo test lint serve

demo:
	uv run mockr demo

test:
	uv run pytest --cov=mockr_coach --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .
	node --check src/mockr_coach/static/app.js

serve:
	uv run mockr serve
