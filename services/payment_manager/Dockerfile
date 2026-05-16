FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock* ./
COPY shared/ shared/
COPY services/payment_manager/ services/payment_manager/
RUN uv sync --frozen --package gutp-payment-manager
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "uvicorn", "gutp_payment_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
