#!/usr/bin/env bash
# E2E テストスクリプト
# 使用法: bash scripts/e2e_test.sh
# 動作: docker compose up → ヘルスチェック待機 → pytest tests/e2e/ → docker compose down

set -euo pipefail

SCHEDULE_INTERVAL_SEC=${SCHEDULE_INTERVAL_SEC:-5}
export SCHEDULE_INTERVAL_SEC

echo "==> Starting services (SCHEDULE_INTERVAL_SEC=${SCHEDULE_INTERVAL_SEC})"
SCHEDULE_INTERVAL_SEC="${SCHEDULE_INTERVAL_SEC}" docker compose up -d

echo "==> Waiting for all services to be healthy (up to 120s)..."
for i in $(seq 1 24); do
    # unhealthy なサービス数をカウント
    unhealthy=$(docker compose ps --format json 2>/dev/null \
        | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
services = []
for line in lines:
    try:
        services.append(json.loads(line))
    except json.JSONDecodeError:
        pass
print(sum(1 for s in services if s.get('Health') == 'unhealthy'))
" 2>/dev/null || echo 0)

    # 全サービスが起動済みかつ unhealthy がゼロなら抜ける
    running=$(docker compose ps --format json 2>/dev/null \
        | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
services = []
for line in lines:
    try:
        services.append(json.loads(line))
    except json.JSONDecodeError:
        pass
print(sum(1 for s in services if s.get('State') == 'running'))
" 2>/dev/null || echo 0)

    if [ "${unhealthy}" -eq 0 ] && [ "${running}" -gt 0 ]; then
        echo "==> All services healthy (running=${running})."
        break
    fi
    echo "    Waiting... attempt ${i}/24 (unhealthy=${unhealthy}, running=${running})"
    sleep 5
done

echo "==> Running E2E tests..."
uv run pytest tests/e2e/ -v --tb=short
EXIT_CODE=$?

echo "==> Stopping services..."
docker compose down

exit $EXIT_CODE
