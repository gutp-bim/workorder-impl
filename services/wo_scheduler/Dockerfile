FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/wo_scheduler/ services/wo_scheduler/
RUN uv sync --frozen --package gutp-wo-scheduler
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "gutp_wo_scheduler.main:app", "--host", "0.0.0.0", "--port", "8000"]
