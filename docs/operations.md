# 運用メモ

このリポジトリは PoC 実装です。認証、永続 DB、durable NATS stream、本番向け observability はありません。以下はローカル開発と検証向けの手順です。

## 起動と停止

```bash
docker compose up -d
docker compose ps
```

停止:

```bash
docker compose down
```

E2E:

```bash
bash scripts/e2e_test.sh
```

このスクリプトは Compose を起動し、health check を待ち、`pytest tests/e2e/` を実行し、`trap` で Compose を停止します。

## ヘルスチェック

HTTP API を持つサービスは以下を公開します。

```text
GET /healthz
```

既定のホスト URL:

| サービス | Health URL |
|---|---|
| building-registry | `http://localhost:8000/healthz` |
| obs-collector | `http://localhost:8001/healthz` |
| issue-manager | `http://localhost:8002/healthz` |
| ticket-manager | `http://localhost:8003/healthz` |
| wo-manager | `http://localhost:8004/healthz` |
| payment-manager | `http://localhost:8005/healthz` |
| ops-dashboard | `http://localhost:8006/healthz` |
| notify-dispatcher | `http://localhost:8007/healthz` |
| wo-scheduler | `http://localhost:8008/healthz` |

`obs-analyzer` は worker であり、health endpoint はありません。

## ログ確認

サービス単位のログ:

```bash
docker compose logs obs-analyzer
docker compose logs wo-manager
docker compose logs notify-dispatcher
```

見るべきポイント:

| サービス | 確認内容 |
|---|---|
| obs-analyzer | IoT event 処理失敗、Report escalation scan 失敗、`escalated report`。 |
| wo-manager | ticket fetch 失敗、`wo.assigned published`、緊急 WO 完了イベント。 |
| notify-dispatcher | adapter 失敗、retry、delivery record。 |
| wo-scheduler | issue, ticket, estimate, approve の各 HTTP 呼び出し失敗。 |
| building-registry | Building OS sync の building 単位の失敗。 |

## よく使う確認コマンド

flow 一覧:

```bash
curl http://localhost:8006/ops/flows
```

problem flow 一覧:

```bash
curl http://localhost:8006/ops/problems
```

通知配信履歴:

```bash
curl http://localhost:8007/deliveries
```

dashboard UI:

```text
http://localhost:8006/dashboard
```

サービス別 API docs:

```text
http://localhost:8004/docs
```

## 典型的な切り分け

| 症状 | 可能性 | 確認先 |
|---|---|---|
| IoTEvent から Issue が作成されない | NATS 不通、`obs-analyzer` 停止、または `event_state` が `ACTIVE` ではない | `docker compose ps`, `docker compose logs obs-analyzer`, `GET /issues` |
| Estimate 承認後に WorkOrder が作成されない | `wo-manager` が Ticket を取得できない、または NATS subscribe できていない | `docker compose logs wo-manager`, `GET /work-orders` |
| Report escalation が出ない | `ESCALATION_THRESHOLD_SEC` 未満、または `obs-analyzer` 停止 | `docker compose logs obs-analyzer`, `GET /deliveries` |
| Slack/webhook 通知が失敗する | `SLACK_WEBHOOK_URL` または `WEBHOOK_URL` 未設定 | `docker compose logs notify-dispatcher` |
| dashboard の flow が欠ける | upstream service が停止、またはインメモリ状態が空 | `GET /ops/flows`, upstream `/healthz`, upstream list endpoint |

## 本番化前の必須課題

| 領域 | 現状 |
|---|---|
| 永続化 | 各サービスのインメモリ dict。 |
| 認証 | HTTP endpoint に認証なし。 |
| 認可 | RBAC や service identity なし。 |
| メッセージ耐久性 | Plain NATS subscription。JetStream / DLQ なし。 |
| 冪等性 | event de-duplication なし。 |
| 可観測性 | 基本ログのみ。 |
| 設定 | 環境変数のみ。 |
| secrets | secret manager 連携なし。 |
| 外部 adapter | email はログ出力 stub。Slack/webhook は URL 設定が必要。 |
