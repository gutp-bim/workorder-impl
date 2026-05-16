FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/obs_analyzer/ services/obs_analyzer/
RUN uv sync --frozen --package gutp-obs-analyzer
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "gutp_obs_analyzer.main"]
