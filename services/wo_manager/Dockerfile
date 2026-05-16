FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/wo_manager/ services/wo_manager/
RUN uv sync --frozen --package gutp-wo-manager
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_wo_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
