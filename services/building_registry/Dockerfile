FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/building_registry/ services/building_registry/
RUN uv sync --frozen --package gutp-building-registry
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_building_registry.main:app", "--host", "0.0.0.0", "--port", "8000"]
