#!/usr/bin/env bash
# demo/e2e_iot_to_payment.sh
#
# シナリオ: IoTEvent 起点の自動ワークオーダー発行 E2E デモ
#
#   IoTEvent → backend /ingest/iot-event → Issue 自動生成
#   → Ticket → Estimate承認 → WO自動発行
#   → ServiceTask完了 → Payment登録 → Ops Dashboard確認
#
# 前提:
#   - docker compose up -d で全サービスが起動・healthyになっていること
#   - jq が PATH 上にあること
#
# 使用例:
#   bash demo/e2e_iot_to_payment.sh
#   BACKEND_URL=http://localhost:8000 bash demo/e2e_iot_to_payment.sh
#
# 既知の仕様 vs 実装の差分:
#   - Booking競合: 仕様「CONFLICTED ステータスで生成・発行継続」
#                  実装「409 を返して Booking 拒否」(routes/workorders.py)
#   - 自動生成 WO のタスク: ticket.estimate.approved トリガーで生成される WO は
#                  tasks=[] で作成される。step 9 でこの動作を明示する。

set -euo pipefail

# ── サービス URL ──────────────────────────────────────────────────────────────
BACKEND="${BACKEND_URL:-http://localhost:8000}"
OPS_DASHBOARD="${OPS_DASHBOARD_URL:-http://localhost:8006}"

# 処理待機秒数（非同期処理の完了を待つ）
WAIT_SEC="${PROPAGATION_WAIT_SEC:-1}"

# ── 表示ヘルパー ──────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

step()  { echo -e "\n${BOLD}${CYAN}▶ $*${RESET}"; }
ok()    { echo -e "${GREEN}  ✓ $*${RESET}"; }
info()  { echo -e "${YELLOW}  ℹ $*${RESET}"; }
fail()  { echo -e "${RED}  ✗ $*${RESET}"; exit 1; }

curl_post() {
    curl -sf --max-time 10 -X POST "$1" \
        -H "Content-Type: application/json" \
        -d "$2"
}
curl_patch() { curl -sf --max-time 10 -X PATCH "$1"; }
curl_get()   { curl -sf --max-time 10 "$1"; }

# ── ヘルスチェック ────────────────────────────────────────────────────────────
step "0. サービス起動確認"
for url_label in \
        "${BACKEND}/healthz:backend" \
        "${OPS_DASHBOARD}/healthz:ops-dashboard"; do
    url="${url_label%%:*}"
    label="${url_label##*:}"
    if curl -sf --max-time 5 "${url}" > /dev/null 2>&1; then
        ok "${label} → healthy"
    else
        fail "${label} (${url}) が応答しません。docker compose up -d を実行してください。"
    fi
done

# ── Step 1: IoTEvent 投入 ─────────────────────────────────────────────────────
step "1. IoTEvent 投入 → backend POST /ingest/iot-event"
IOT_RESP=$(curl_post "${BACKEND}/ingest/iot-event" '{
    "iot_event_type": "gutp:SmokeAlarm",
    "event_state":    "ACTIVE",
    "source_id":      "device-sensor-demo-001"
}')
echo "  ${IOT_RESP}"
ok "IoTEvent 受付 (202 Accepted)"

# ── Step 2: 非同期処理待ち ────────────────────────────────────────────────────
step "2. 非同期処理待ち: IoTEvent → obs_analyzer → Issue 生成 (${WAIT_SEC}s)"
sleep "${WAIT_SEC}"

# ── Step 3: Issue 自動生成確認 ───────────────────────────────────────────────
step "3. Issue 自動生成確認 → backend GET /issues"
ISSUES=$(curl_get "${BACKEND}/issues")
ISSUE_COUNT=$(echo "${ISSUES}" | jq 'length')

if [ "${ISSUE_COUNT}" -eq 0 ]; then
    fail "Issue が生成されていません。バックエンドのログを確認してください: docker compose logs backend"
fi

# 最新 Issue を取得（受信順で最後尾）
ISSUE=$(echo "${ISSUES}" | jq '.[-1]')
ISSUE_ID=$(echo "${ISSUE}" | jq -r '.issue_id')
ISSUE_TYPE=$(echo "${ISSUE}" | jq -r '.issue_type')
ISSUE_STATUS=$(echo "${ISSUE}" | jq -r '.issue_status')
ok "Issue 自動生成: id=${ISSUE_ID}  type=${ISSUE_TYPE}  status=${ISSUE_STATUS}"

# ── Step 4: Ticket 起票 ──────────────────────────────────────────────────────
step "4. Ticket 起票 → backend POST /tickets"
TICKET_RESP=$(curl_post "${BACKEND}/tickets" "$(jq -n \
    --arg title "[DEMO] SmokeAlarm 対応チケット" \
    --arg issue_id "${ISSUE_ID}" \
    '{"title": $title, "addresses_issue_ids": [$issue_id], "priority": 10}')")
TICKET_ID=$(echo "${TICKET_RESP}" | jq -r '.ticket_id')
TICKET_STATUS=$(echo "${TICKET_RESP}" | jq -r '.ticket_status')
ok "Ticket 起票: id=${TICKET_ID}  status=${TICKET_STATUS}"

# ── Step 5: Estimate 作成 ────────────────────────────────────────────────────
step "5. Estimate 作成 → backend POST /estimates"
ESTIMATE_RESP=$(curl_post "${BACKEND}/estimates" "$(jq -n \
    --arg ticket_id "${TICKET_ID}" \
    '{
        "ticket_id":           $ticket_id,
        "title":               "[DEMO] 現場確認・煙感知器点検",
        "estimated_cost":      "45000",
        "estimated_duration":  "PT4H",
        "currency":            "JPY",
        "description":         "煙感知器の誤報原因確認と清掃作業"
    }')")
ESTIMATE_ID=$(echo "${ESTIMATE_RESP}" | jq -r '.estimate_id')
ESTIMATE_STATUS=$(echo "${ESTIMATE_RESP}" | jq -r '.estimate_status')
ok "Estimate 作成: id=${ESTIMATE_ID}  status=${ESTIMATE_STATUS}"

# ── Step 6: Estimate 承認 ────────────────────────────────────────────────────
step "6. Estimate 承認 → backend PATCH /estimates/${ESTIMATE_ID}/approve"
APPROVE_RESP=$(curl_patch "${BACKEND}/estimates/${ESTIMATE_ID}/approve")
APPROVED_STATUS=$(echo "${APPROVE_RESP}" | jq -r '.estimate_status')
ok "Estimate 承認: status=${APPROVED_STATUS}"

# ── Step 7: 非同期処理待ち ────────────────────────────────────────────────────
step "7. 非同期処理待ち: Estimate 承認 → WorkOrder 自動生成 (${WAIT_SEC}s)"
sleep "${WAIT_SEC}"

# ── Step 8: WorkOrder 自動発行確認 ───────────────────────────────────────────
step "8. WorkOrder 自動発行確認 → backend GET /work-orders"
WO_LIST=$(curl_get "${BACKEND}/work-orders")
WO_COUNT=$(echo "${WO_LIST}" | jq 'length')

if [ "${WO_COUNT}" -eq 0 ]; then
    fail "WorkOrder が生成されていません。ログを確認: docker compose logs backend"
fi

# Ticket ID が一致する WO を検索（なければ最新）
WO=$(echo "${WO_LIST}" | jq --arg tid "${TICKET_ID}" \
    'map(select(.ticket_id == $tid)) | last // .[-1]')
WO_ID=$(echo "${WO}" | jq -r '.work_order_id')
WO_STATUS=$(echo "${WO}" | jq -r '.work_order_status')
WO_TITLE=$(echo "${WO}" | jq -r '.title')
WO_TYPE=$(echo "${WO}" | jq -r '.work_order_type')
TASK_IDS=$(echo "${WO}" | jq -r '.task_ids[]' 2>/dev/null || true)
ok "WorkOrder 自動発行: id=${WO_ID}"
ok "  title=${WO_TITLE}  type=${WO_TYPE}  status=${WO_STATUS}"

# ── Step 9: ServiceTask 完了報告 ─────────────────────────────────────────────
step "9. ServiceTask 完了報告 → backend"
if [ -z "${TASK_IDS}" ]; then
    info "自動生成 WO のタスクリストは空です（既知の動作）"
    info "FUN-WO-001 実装: _auto_create_work_order は tasks=[] で WO を生成します"
    info "手動で POST /work-orders (tasks フィールド付き) した場合はここで PATCH が発行されます"
    info "WO ステータスは ${WO_STATUS} のままです（全タスク完了で Completed へ遷移）"
else
    for TASK_ID in ${TASK_IDS}; do
        COMPLETE_RESP=$(curl_patch "${BACKEND}/work-orders/${WO_ID}/tasks/${TASK_ID}/complete")
        NEW_WO_STATUS=$(echo "${COMPLETE_RESP}" | jq -r '.work_order_status')
        ok "Task 完了: task_id=${TASK_ID}  wo_status=${NEW_WO_STATUS}"
    done
    WO_STATUS="${NEW_WO_STATUS:-${WO_STATUS}}"
fi

# ── Step 10: Payment 登録 ────────────────────────────────────────────────────
step "10. Payment 登録 → backend POST /payments"
PAYMENT_RESP=$(curl_post "${BACKEND}/payments" "$(jq -n \
    --arg wo_id "${WO_ID}" \
    '{
        "applies_to_work_order_id": $wo_id,
        "paid_to":                  "rec:Contractor-Demo-001",
        "payment_amount":           "45000",
        "currency":                 "JPY"
    }')")
PAYMENT_ID=$(echo "${PAYMENT_RESP}" | jq -r '.payment_id')
ok "Payment 登録: id=${PAYMENT_ID}"

# ── Step 11: Ops Dashboard フロー確認 ────────────────────────────────────────
step "11. Ops Dashboard フロー確認 → ops-dashboard GET /ops/flows"
FLOWS=$(curl_get "${OPS_DASHBOARD}/ops/flows")
FLOW_COUNT=$(echo "${FLOWS}" | jq '.flows | length')
ok "集約フロー件数: ${FLOW_COUNT}"

FLOW=$(echo "${FLOWS}" | jq --arg wid "${WO_ID}" \
    '.flows[] | select(.work_orders != null and (.work_orders[] | .work_order_id == $wid))' 2>/dev/null \
    | head -c 1000 || true)
if [ -n "${FLOW}" ]; then
    PROBLEMS=$(echo "${FLOW}" | jq -r '.problem_flags | length' 2>/dev/null || echo "?")
    ok "対象フロー発見: problem_flags=${PROBLEMS}"
else
    info "WO ID でのフロー直接特定不可（Ops Dashboard の集約ロジックによる）"
    info "GET ${OPS_DASHBOARD}/ops/flows  で全フロー参照可能"
    info "GET ${OPS_DASHBOARD}/ops/problems  で未解決問題のみ表示"
fi

# ── サマリー ─────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BOLD}${GREEN} DEMO COMPLETE${RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Issue    : ${ISSUE_ID}  (${ISSUE_STATUS})"
echo "  Ticket   : ${TICKET_ID}"
echo "  Estimate : ${ESTIMATE_ID}  (${APPROVED_STATUS})"
echo "  WO       : ${WO_ID}  (${WO_STATUS})"
echo "  Payment  : ${PAYMENT_ID}"
echo "  Flows    : ${FLOW_COUNT} フロー in Ops Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "追加確認:"
echo "  ダッシュボード UI : ${OPS_DASHBOARD}/dashboard"
echo "  未解決問題一覧    : ${OPS_DASHBOARD}/ops/problems"
echo "  バックエンドログ  : docker compose logs backend"
echo "  全フロー詳細      : curl -s ${OPS_DASHBOARD}/ops/flows | jq ."
echo ""
echo "仕様 vs 実装の既知差分:"
echo "  Booking競合 : 仕様=CONFLICTED ステータスで継続、実装=409 で拒否"
echo "                → services/backend/gutp_backend/routes/workorders.py"
echo "  自動生成 WO : FUN-WO-001 で tasks=[] となる（別途タスク追加 API が必要）"
