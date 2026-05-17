# API リファレンス

このドキュメントは、各サービスが実装している HTTP API を一覧化したものです。FastAPI の自動生成ドキュメントは、各 API サービスの `/docs`、機械可読な OpenAPI スキーマは `/openapi.json` で確認できます。

下記の URL は `docker-compose.yml` の既定ホストポートです。Compose ネットワーク内では、各 API サービスはコンテナ内 `:8000` で待ち受けます。

## サービス URL

| サービス | ホスト URL | コンテナ内 URL |
|---|---|---|
| building-registry | `http://localhost:8000` | `http://building-registry:8000` |
| obs-collector | `http://localhost:8001` | `http://obs-collector:8000` |
| issue-manager | `http://localhost:8002` | `http://issue-manager:8000` |
| ticket-manager | `http://localhost:8003` | `http://ticket-manager:8000` |
| wo-manager | `http://localhost:8004` | `http://wo-manager:8000` |
| payment-manager | `http://localhost:8005` | `http://payment-manager:8000` |
| ops-dashboard | `http://localhost:8006` | `http://ops-dashboard:8000` |
| notify-dispatcher | `http://localhost:8007` | `http://notify-dispatcher:8000` |
| wo-scheduler | `http://localhost:8008` | `http://wo-scheduler:8000` |

`obs-analyzer` は NATS worker であり、HTTP API は公開しません。

## building-registry

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `GET` | `/topology/buildings` | 同期済み building 一覧。 |
| `GET` | `/topology/buildings/{building_dt_id}/floors` | building 配下の floor 一覧。 |
| `GET` | `/topology/spaces` | space 一覧。 |
| `GET` | `/topology/devices` | device 一覧。 |
| `POST` | `/topology/sync` | Building OS からのトポロジ同期を非同期で開始。 |

## obs-collector

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/ingest/iot-event` | IoTEvent を受信し、インメモリ保存後に `obs.iot-event.created` を publish。 |
| `POST` | `/ingest/report` | Report を受信し、インメモリ保存後に `obs.report.created` を publish。 |
| `GET` | `/iot-events/{iot_event_id}` | 受信済み IoTEvent の取得。 |
| `GET` | `/reports/{report_id}` | 受信済み Report の取得。 |

## issue-manager

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/issues` | Issue を作成し、`issue.created` を publish。 |
| `GET` | `/issues` | Issue 一覧。 |
| `GET` | `/issues/{issue_id}` | Issue 取得。 |
| `PATCH` | `/issues/{issue_id}/review` | レビュー操作。body は `{"action": "accept"}` または `{"action": "reject"}`。 |
| `PATCH` | `/issues/{issue_id}/resolve` | Issue を解決済みにし、`issue.resolved` を publish。 |

`issue-manager` は `obs.report.evaluated` も subscribe します。評価済み Report 由来の open issue が存在する場合、その Issue を `PendingReview` に遷移させます。

## ticket-manager

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/tickets` | Ticket 作成。 |
| `GET` | `/tickets` | Ticket 一覧。 |
| `GET` | `/tickets/{ticket_id}` | Ticket 取得。 |
| `POST` | `/estimates` | 既存 Ticket に対する Estimate 作成。 |
| `PATCH` | `/estimates/{estimate_id}/approve` | Estimate を承認し、`ticket.estimate.approved` を publish。 |

`ticket-manager` は `issue.created` を subscribe しますが、現時点では Issue から Ticket を自動起票しません。

## wo-manager

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/work-orders` | WorkOrder 手動作成。 |
| `POST` | `/work-orders/emergency` | 緊急 WorkOrder を `InProgress` で作成し、`wo.assigned` を publish。 |
| `GET` | `/work-orders` | WorkOrder 一覧。 |
| `GET` | `/work-orders/{wo_id}` | WorkOrder 取得。 |
| `POST` | `/work-orders/{wo_id}/tasks` | 完了前の WorkOrder に task を追加。 |
| `PATCH` | `/work-orders/{wo_id}/tasks/{task_id}/complete` | task を完了。全 task 完了時は WorkOrder も完了。 |
| `POST` | `/bookings` | tentative booking を作成。同一 WorkOrder の重複時間帯は 409。 |
| `PATCH` | `/bookings/{booking_id}/confirm` | booking を確定し、open WorkOrder を `InProgress` に遷移。 |
| `PATCH` | `/work-orders/{wo_id}/complete-emergency` | 緊急 WorkOrder を完了し、`wo.emergency.completed` を publish。 |

`wo-manager` は `ticket.estimate.approved` を subscribe し、関連 Ticket を取得できた場合に corrective maintenance の WorkOrder を自動生成します。

## payment-manager

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/payments` | 参照先 WorkOrder の存在確認後に Payment 作成。 |
| `GET` | `/payments` | Payment 一覧。 |
| `GET` | `/payments/{payment_id}` | Payment 取得。 |
| `PATCH` | `/payments/{payment_id}/mark-paid` | Payment を paid に遷移。 |

現実装は WorkOrder の存在だけを確認し、WorkOrder が完了済みかは検証しません。

## ops-dashboard

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `GET` | `/dashboard` | 静的ダッシュボード UI。 |
| `GET` | `/ops/flows` | Issue -> Ticket -> WorkOrder -> Payment の連鎖を集約。 |
| `GET` | `/ops/flows/{flow_id}` | 単一 flow 取得。 |
| `GET` | `/ops/flows/{flow_id}/timeline` | timeline placeholder を返却。 |
| `GET` | `/ops/problems` | `pending_review` や `unpaid` などの problem flag を持つ flow 一覧。 |
| `GET` | `/ops/work-orders` | `wo-manager` の WorkOrder 一覧を proxy。 |
| `POST` | `/ops/work-orders/{wo_id}/tasks` | task 作成を `wo-manager` へ proxy。 |
| `POST` | `/ops/actions` | 管理操作を対象サービスへ転送。 |

## notify-dispatcher

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `GET` | `/deliveries` | インメモリの通知配信履歴。 |

`notify-dispatcher` は `wo.assigned`、`wo.emergency.completed`、`obs.report.escalation` を subscribe します。

## wo-scheduler

| Method | Path | 内容 |
|---|---|---|
| `GET` | `/healthz` | ヘルスチェック。 |
| `POST` | `/schedules` | 予防保全スケジュール作成。 |
| `GET` | `/schedules` | スケジュール一覧。 |
| `DELETE` | `/schedules/{schedule_id}` | スケジュール削除。 |

スケジュールが due になると、`wo-scheduler` は Issue、Ticket、Estimate を作成し、その Estimate を承認します。承認イベントを受けて `wo-manager` が WorkOrder を作成します。
