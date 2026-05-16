FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/issue_manager/ services/issue_manager/
RUN uv sync --frozen --package gutp-issue-manager
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_issue_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
