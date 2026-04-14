FROM python:3.14-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON=/usr/local/bin/python \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uvicorn", "main:payment_app", "--host", "0.0.0.0", "--port", "8000"]