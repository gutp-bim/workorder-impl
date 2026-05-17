# フローと状態遷移

このリポジトリは PoC 実装です。各サービスの状態はインメモリに保持されるため、サービスを再起動するとそのサービス内のレコードは失われます。

## IoT 起点の主フロー

```text
IoTEvent -> Issue -> Ticket -> Estimate approval -> WorkOrder -> Payment
```

1. `obs-collector` が `POST /ingest/iot-event` を受け付けます。
2. `obs-collector` がイベントをインメモリ保存し、`obs.iot-event.created` を publish します。
3. `obs-analyzer` がイベントを評価します。現行ルールでは `event_state == "ACTIVE"` の IoTEvent から Issue を作成します。
4. `issue-manager` が Issue を保存し、`issue.created` を publish します。
5. `ticket-manager` で Ticket を手動起票します。
6. `ticket-manager` で Estimate を作成し、承認します。
7. `ticket-manager` が `ticket.estimate.approved` を publish します。
8. `wo-manager` が承認イベントを受信し、Ticket を取得して corrective maintenance の WorkOrder を作成し、`wo.assigned` を publish します。
9. `notify-dispatcher` が `wo.assigned` を受信し、通知配信履歴を記録します。
10. `payment-manager` で WorkOrder に対する Payment を作成できます。

## Report フロー

現行実装では、`obs-analyzer` は Report から Issue を自動生成しません。

1. `obs-collector` が `POST /ingest/report` を受け付けます。
2. `obs-collector` が Report をインメモリ保存し、`obs.report.created` を publish します。
3. `obs-analyzer` が Report をインメモリ pending queue に登録します。
4. 外部の FM 評価フローが `obs.report.evaluated` を publish した場合、`obs-analyzer` は該当 Report を pending queue から削除します。
5. Report が `ESCALATION_THRESHOLD_SEC` を超えて pending のまま残ると、`obs-analyzer` が `obs.report.escalation` を publish します。
6. `notify-dispatcher` が escalation を受信し、通知配信履歴を記録します。

`issue-manager` も `obs.report.evaluated` を subscribe します。`derived_from_id == report_id` の open issue が既に存在する場合、その Issue を `PendingReview` に遷移させます。

## 予防保全フロー

1. `wo-scheduler` が `POST /schedules` を受け付けます。
2. background loop が `SCHEDULE_INTERVAL_SEC` ごとに due な schedule を評価します。
3. due な schedule ごとに Issue、Ticket、Estimate を作成し、Estimate を承認します。
4. Estimate 承認により `ticket.estimate.approved` が publish されます。
5. `wo-manager` が承認イベントを受けて WorkOrder を作成します。
6. schedule の `last_triggered_at` が更新され、`next_trigger_at` は `interval_days` 分だけ進みます。

現行実装では、schedule 生成時に Building Registry のトポロジ情報は利用していません。

## 緊急 WorkOrder フロー

1. `wo-manager` が `POST /work-orders/emergency` を受け付けます。
2. `EmergencyMaintenance` の WorkOrder を `InProgress` で作成します。
3. `wo.assigned` を publish します。
4. `notify-dispatcher` が通知配信履歴を記録します。
5. `PATCH /work-orders/{wo_id}/complete-emergency` により緊急 WorkOrder を完了し、`wo.emergency.completed` を publish します。

## 状態遷移

### Issue

| From | Trigger | To |
|---|---|---|
| none | `POST /issues` | `Open` |
| `Open` | matching `derived_from_id` に対する `obs.report.evaluated` | `PendingReview` |
| `Open` or `PendingReview` | `PATCH /issues/{id}/review` with `{"action":"accept"}` | `UnderReview` |
| `Open`, `PendingReview`, or `UnderReview` | `PATCH /issues/{id}/review` with `{"action":"reject"}` | `Open` |
| any non-resolved status | `PATCH /issues/{id}/resolve` | `Resolved` |

`Resolved` の Issue は review できません。

### Estimate

| From | Trigger | To |
|---|---|---|
| none | `POST /estimates` | `Draft` |
| `Draft` | `PATCH /estimates/{id}/approve` | `Approved` |

Estimate 承認時に `ticket.estimate.approved` が publish されます。

### WorkOrder

| From | Trigger | To |
|---|---|---|
| none | `POST /work-orders` or Estimate 承認イベント | `Open` |
| none | `POST /work-orders/emergency` | `InProgress` |
| `Open` | 初回 task 完了 | `InProgress` |
| `Open` | booking confirm | `InProgress` |
| `Open` or `InProgress` | 全 task 完了 | `Completed` |
| `InProgress` emergency WO | `PATCH /work-orders/{id}/complete-emergency` | `Completed` |

`Completed` の WorkOrder には task を追加できません。

### Booking

| From | Trigger | To |
|---|---|---|
| none | `POST /bookings` | `Tentative` |
| `Tentative` | `PATCH /bookings/{id}/confirm` | `Confirmed` |

同一 WorkOrder の booking は、重複する時間帯を拒否します。

### Payment

| From | Trigger | To |
|---|---|---|
| none | `POST /payments` | `Pending` |
| `Pending` | `PATCH /payments/{id}/mark-paid` | `Paid` |

## NATS サブジェクト

| Subject | Publisher | Subscriber |
|---|---|---|
| `obs.iot-event.created` | obs-collector | obs-analyzer |
| `obs.report.created` | obs-collector | obs-analyzer |
| `obs.report.evaluated` | external FM evaluation flow | obs-analyzer, issue-manager |
| `obs.report.escalation` | obs-analyzer | notify-dispatcher |
| `issue.created` | issue-manager | ticket-manager |
| `issue.resolved` | issue-manager | none |
| `ticket.estimate.approved` | ticket-manager | wo-manager |
| `wo.assigned` | wo-manager | notify-dispatcher |
| `wo.emergency.completed` | wo-manager | notify-dispatcher |

`issue.updated` と `ticket.status.updated` は定数としては定義されていますが、現行サービスコードからは publish されていません。
