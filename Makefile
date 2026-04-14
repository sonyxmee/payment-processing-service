.PHONY: dev lint format sync

dev:
	uv run uvicorn main:payment_app --reload 

lint:
	uv run ruff check .

format:
	uv run ruff format .

sync:
	uv sync