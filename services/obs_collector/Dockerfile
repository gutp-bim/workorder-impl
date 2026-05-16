FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/obs_collector/ services/obs_collector/
RUN uv sync --frozen --package gutp-obs-collector
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_obs_collector.main:app", "--host", "0.0.0.0", "--port", "8000"]
