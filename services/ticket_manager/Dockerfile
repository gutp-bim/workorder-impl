FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/ticket_manager/ services/ticket_manager/
RUN uv sync --frozen --package gutp-ticket-manager
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_ticket_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
