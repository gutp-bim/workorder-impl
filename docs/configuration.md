# 設定

各サービスは環境変数から設定を読み込みます。コード上の既定値と `docker-compose.yml` の値は、ホスト実行か Compose 実行かによって異なる場合があります。

## 実行時の環境変数

| 変数 | コード上の既定値 | Compose の値 | サービス | 備考 |
|---|---|---|---|---|
| `NATS_URL` | `nats://localhost:4222` | `nats://nats:4222` | obs-collector, obs-analyzer, issue-manager, ticket-manager, wo-manager, notify-dispatcher | NATS server URL。 |
| `ISSUE_MANAGER_URL` | `http://issue-manager:8000` | `http://issue-manager:8000` | obs-analyzer, wo-scheduler, ops-dashboard | HTTP 依存先。 |
| `TICKET_MANAGER_URL` | `http://ticket-manager:8000` | `http://ticket-manager:8000` | wo-manager, wo-scheduler, ops-dashboard | HTTP 依存先。 |
| `WO_MANAGER_URL` | `http://wo-manager:8000` | `http://wo-manager:8000` | payment-manager, ops-dashboard | HTTP 依存先。 |
| `PAYMENT_MANAGER_URL` | `http://payment-manager:8000` | `http://payment-manager:8000` | ops-dashboard | HTTP 依存先。 |
| `BUILDING_OS_URL` | `http://localhost:5000` | `${BUILDING_OS_URL:-http://localhost:5000}` | building-registry shared client | Building OS base URL。 |
| `BUILDING_OS_TOKEN` | empty | `${BUILDING_OS_TOKEN:-}` | building-registry shared client | Building OS 用 optional bearer token。 |
| `BUILDING_SYNC_INTERVAL_SEC` | `300` | `300` | building-registry | トポロジ同期の background interval。 |
| `ESCALATION_THRESHOLD_SEC` | `1800` | `1800` | obs-analyzer | Report を escalation するまでの pending 秒数。 |
| `ESCALATION_CHECK_INTERVAL_SEC` | `60` | not set | obs-analyzer | pending Report の scan interval。 |
| `SCHEDULE_INTERVAL_SEC` | `300` | `300` | wo-scheduler | 予防保全 schedule の評価 interval。 |
| `NOTIFY_ADAPTER` | `email` | `${NOTIFY_ADAPTER:-email}` | notify-dispatcher | `email`, `slack`, `webhook` のいずれか。 |
| `SLACK_WEBHOOK_URL` | empty | `${SLACK_WEBHOOK_URL:-}` | notify-dispatcher | `NOTIFY_ADAPTER=slack` のとき必須。 |
| `WEBHOOK_URL` | empty | `${WEBHOOK_URL:-}` | notify-dispatcher | `NOTIFY_ADAPTER=webhook` のとき必須。 |
| `SMTP_HOST` | 現行コードでは未使用 | `${SMTP_HOST:-}` | notify-dispatcher | Compose には存在するが、email adapter は現時点ではログ出力 stub。 |

## Compose にあるが現行コードでは未使用の変数

以下は `docker-compose.yml` には存在しますが、対応サービスの現行実装では読み込まれていません。

| 変数 | サービス | 現状 |
|---|---|---|
| `WO_MANAGER_URL` | wo-scheduler | 未使用。WorkOrder 作成は Estimate 承認イベント経由で間接的に行う。 |
| `BUILDING_REGISTRY_URL` | wo-scheduler | 未使用。schedule 生成にトポロジ情報は使っていない。 |
| `OBS_COLLECTOR_URL` | ops-dashboard | 未使用。dashboard は issue, ticket, work order, payment を集約する。 |
| `BUILDING_REGISTRY_URL` | ops-dashboard | 未使用。dashboard は現時点でトポロジ情報を表示しない。 |
| `SMTP_HOST` | notify-dispatcher | 未使用。email adapter は SMTP 送信ではなくログ出力。 |

これらは、サービスコードが読み込むようになるまでは有効な integration point とみなさないでください。

## ホスト直接実行

`uv run` でサービスをホスト上から直接起動し、依存先を Compose で動かす場合は、依存先 URL をホストポートへ上書きしてください。

```bash
NATS_URL=nats://localhost:4222 \
ISSUE_MANAGER_URL=http://localhost:8002 \
uv run python services/obs_analyzer/gutp_obs_analyzer/main.py
```

通常の開発では、全サービスを Compose で起動する方が単純です。

```bash
docker compose up -d
docker compose ps
```
