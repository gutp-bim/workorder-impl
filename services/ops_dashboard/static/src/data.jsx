/* Mock data for CS-OPS-DASHBOARD prototype.
 * Shapes are aligned to interfaces.yaml / functions.yaml of workorder-systems.
 * Each "flow" is the chain Report|IoTEvent -> Issue -> Ticket -> WorkOrder -> Payment.
 */

const PROBLEM_TYPES = {
  pending_review: { label: "レビュー待ち", tone: "warn" },
  conflicted:     { label: "Booking競合", tone: "danger" },
  stale_report:   { label: "Report滞留", tone: "warn" },
  unsettled:      { label: "精算未完了", tone: "info" },
  overdue:        { label: "期限超過", tone: "danger" },
  approval_wait:  { label: "見積承認待ち", tone: "warn" },
  none:           { label: "正常", tone: "ok" },
};

const ENTITY_META = {
  observation: { label: "観測",      short: "OBS",  hue: 270 },
  issue:       { label: "Issue",     short: "ISS",  hue: 35 },
  ticket:      { label: "Ticket",    short: "TKT",  hue: 215 },
  workorder:   { label: "WorkOrder", short: "WO",   hue: 152 },
  payment:     { label: "Payment",   short: "PAY",  hue: 195 },
};

const STATUS_META = {
  // observation
  iot_received:       { label: "受信",          tone: "ok" },
  report_pending:     { label: "Pending",       tone: "warn" },
  report_approved:    { label: "Approved",      tone: "ok" },
  report_rejected:    { label: "Rejected",      tone: "muted" },
  // issue
  pending_review:     { label: "Pending Review", tone: "warn" },
  open:               { label: "Open",          tone: "info" },
  closed:             { label: "Closed",        tone: "muted" },
  // ticket / estimate
  estimate_pending:   { label: "見積中",        tone: "warn" },
  estimate_approved:  { label: "承認済",        tone: "ok" },
  // workorder
  wo_open:            { label: "Open",          tone: "info" },
  wo_in_progress:     { label: "InProgress",    tone: "warn" },
  wo_completed:       { label: "Completed",     tone: "ok" },
  // booking
  booking_confirmed:  { label: "Confirmed",     tone: "ok" },
  booking_conflicted: { label: "Conflicted",    tone: "danger" },
  // payment
  pay_pending:        { label: "未払",          tone: "warn" },
  pay_paid:           { label: "Paid",          tone: "ok" },
  pay_unsettled:      { label: "精算未完了",    tone: "info" },
  not_started:        { label: "—",             tone: "muted" },
};

const BUILDINGS = [
  { id: "B-001", name: "Otemachi Tower" },
  { id: "B-002", name: "Shibuya Annex" },
  { id: "B-003", name: "Tennozu Logistics" },
];

const AGENTS = [
  { id: "A-001", name: "佐藤 健一",   team: "電気設備" },
  { id: "A-002", name: "Lin Wei",     team: "空調"     },
  { id: "A-003", name: "中村 美穂",   team: "清掃"     },
  { id: "A-004", name: "外部委託 #12", team: "防災"     },
  { id: "A-005", name: "高橋 直樹",   team: "電気設備" },
];

const ISSUE_TYPES = [
  "設備資産", "ITインフラ", "EHS",
  "スペース設計", "オペレーション管理", "オフィスサービス",
];

const WO_TYPES = [
  // 保守
  "予防保全", "是正対応",
  // 施工
  "設置", "更新・機種変更", "撤去・廃止",
  // 安全・緊急対応
  "緊急・アラーム対応", "インシデント対応", "避難誘導",
  // オフィスサービス
  "消耗品管理", "清掃", "廃棄物管理",
];

/* Each flow row:
 *   id, origin (report|iot|schedule), priority, building, floor, space,
 *   chain: [{kind, id, status, label, problem?}]
 *   problem: top-level problem flag (one of PROBLEM_TYPES)
 *   updatedAt, openedAt
 *   timeline: state transition log
 */
const FLOWS = [
  {
    id: "F-2026-0517-001",
    priority: "P1",
    origin: "report",
    building: "B-001", floor: "12F", space: "Meeting Room 12-3",
    title: "会議室 12-3 の空調が効かない",
    woType: null, issueType: null,
    openedAt: "2026-05-16T08:42",
    updatedAt: "2026-05-17T09:11",
    problem: "stale_report",
    note: "テナント報告。28時間レビュー無し。",
    chain: [
      { kind: "observation", id: "RPT-8821", status: "report_pending", label: "Report" },
      { kind: "issue",       id: null,       status: "not_started",     label: "Issue" },
      { kind: "ticket",      id: null,       status: "not_started",     label: "Ticket" },
      { kind: "workorder",   id: null,       status: "not_started",     label: "WO" },
      { kind: "payment",     id: null,       status: "not_started",     label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-16T08:42", who: "STK-REPORTER (山田)", evt: "Report 投稿",         from: null, to: "pending" },
      { t: "2026-05-17T08:42", who: "system",              evt: "滞留24h 超過を検出", from: "pending", to: "pending (stale)" },
    ],
  },

  {
    id: "F-2026-0517-002",
    priority: "P2",
    origin: "iot",
    building: "B-001", floor: "B1F", space: "Pump Room",
    title: "給水ポンプ #3 の振動異常（複合トレンド検知）",
    woType: null, issueType: "設備資産",
    openedAt: "2026-05-15T14:10",
    updatedAt: "2026-05-17T07:25",
    problem: "pending_review",
    note: "OBS-ANALYZER が NonStandardIssue として生成。確定 or 却下が必要。",
    chain: [
      { kind: "observation", id: "IOT-77321", status: "iot_received",   label: "IoTEvent" },
      { kind: "issue",       id: "ISS-3318",  status: "pending_review", label: "Issue (NonStd)" },
      { kind: "ticket",      id: null,        status: "not_started",    label: "Ticket" },
      { kind: "workorder",   id: null,        status: "not_started",    label: "WO" },
      { kind: "payment",     id: null,        status: "not_started",    label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-15T14:10", who: "STK-IOT",       evt: "IoTEvent 受信",                  from: null, to: "received" },
      { t: "2026-05-16T03:00", who: "OBS-ANALYZER",  evt: "トレンド分析でNonStdIssue検出", from: null, to: "pending_review" },
      { t: "2026-05-17T07:25", who: "system",        evt: "OPSダッシュボードに昇格表示",   from: "pending_review", to: "pending_review (escalated)" },
    ],
  },

  {
    id: "F-2026-0517-003",
    priority: "P3",
    origin: "schedule",
    building: "B-002", floor: "5F", space: "Server Room",
    title: "サーバー室 定期点検（月次・予防保全）",
    woType: "予防保全", issueType: "ITインフラ",
    openedAt: "2026-05-12T09:00",
    updatedAt: "2026-05-14T18:40",
    problem: "approval_wait",
    note: "Estimate 承認待ち。期限 2026-05-20。",
    chain: [
      { kind: "observation", id: null,        status: "not_started",      label: "—" },
      { kind: "issue",       id: "ISS-3290",  status: "open",             label: "StdIssue" },
      { kind: "ticket",      id: "TKT-9012",  status: "estimate_pending", label: "Ticket" },
      { kind: "workorder",   id: null,        status: "not_started",      label: "WO" },
      { kind: "payment",     id: null,        status: "not_started",      label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-12T09:00", who: "WO-SCHEDULER", evt: "予防保全スケジュール発火", from: null,    to: "scheduled" },
      { t: "2026-05-12T09:00", who: "ISSUE-MGR",    evt: "StandardIssue 生成",      from: null,    to: "open" },
      { t: "2026-05-12T09:00", who: "TICKET-MGR",   evt: "Ticket 自動起票",         from: null,    to: "estimate_pending" },
      { t: "2026-05-14T18:40", who: "STK-WORKER",   evt: "Estimate 登録",           from: "estimate_pending", to: "estimate_pending (submitted)" },
    ],
  },

  {
    id: "F-2026-0517-004",
    priority: "P1",
    origin: "iot",
    building: "B-001", floor: "8F", space: "EPS 8-N",
    title: "分電盤異常（火災検知連動）— 緊急対応",
    woType: "緊急・アラーム対応", issueType: "EHS",
    openedAt: "2026-05-17T03:14",
    updatedAt: "2026-05-17T06:22",
    problem: "unsettled",
    note: "緊急WO 完了済。事後Ticket / Estimate が未登録。精算ループ未閉。",
    chain: [
      { kind: "observation", id: "IOT-77501", status: "iot_received",   label: "IoTEvent" },
      { kind: "issue",       id: "ISS-3325",  status: "open",           label: "Issue" },
      { kind: "ticket",      id: null,        status: "not_started",    label: "Ticket (事後)" },
      { kind: "workorder",   id: "WO-4451",   status: "wo_completed",   label: "WO 緊急" },
      { kind: "payment",     id: null,        status: "pay_unsettled",  label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-17T03:14", who: "STK-IOT",     evt: "火災検知IoTEvent 受信",       from: null, to: "received" },
      { t: "2026-05-17T03:14", who: "ISSUE-MGR",   evt: "Issue 自動生成",              from: null, to: "open" },
      { t: "2026-05-17T03:16", who: "STK-FM",      evt: "緊急WO 即時発行 (Estimate免除)", from: null, to: "wo_open" },
      { t: "2026-05-17T03:18", who: "STK-WORKER",  evt: "現場到着・着手",              from: "wo_open", to: "wo_in_progress" },
      { t: "2026-05-17T06:22", who: "STK-WORKER",  evt: "全ServiceTask完了",           from: "wo_in_progress", to: "wo_completed" },
      { t: "2026-05-17T06:22", who: "WO-MGR",      evt: "wo.emergency.completed 発行", from: null, to: "事後精算待ち" },
    ],
  },

  {
    id: "F-2026-0517-005",
    priority: "P2",
    origin: "report",
    building: "B-002", floor: "3F", space: "Office Floor 3",
    title: "天井照明のチラつき（複数席）",
    woType: "是正対応", issueType: "設備資産",
    openedAt: "2026-05-13T11:20",
    updatedAt: "2026-05-17T08:55",
    problem: "conflicted",
    note: "Booking が佐藤氏の別案件と時間競合。",
    chain: [
      { kind: "observation", id: "RPT-8801",  status: "report_approved",   label: "Report" },
      { kind: "issue",       id: "ISS-3301",  status: "open",              label: "Issue" },
      { kind: "ticket",      id: "TKT-9001",  status: "estimate_approved", label: "Ticket" },
      { kind: "workorder",   id: "WO-4432",   status: "wo_open",           label: "WO (競合)", problem: "conflicted" },
      { kind: "payment",     id: null,        status: "not_started",       label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-13T11:20", who: "STK-REPORTER (鈴木)", evt: "Report 投稿",         from: null, to: "pending" },
      { t: "2026-05-13T14:02", who: "STK-FM",              evt: "Report 承認・Issue化", from: "pending", to: "approved" },
      { t: "2026-05-14T09:11", who: "STK-FM",              evt: "Ticket 起票",          from: null, to: "open" },
      { t: "2026-05-15T10:00", who: "STK-WORKER",          evt: "Estimate 登録",        from: null, to: "estimate_pending" },
      { t: "2026-05-16T13:30", who: "STK-FM",              evt: "Estimate 承認",        from: "estimate_pending", to: "approved" },
      { t: "2026-05-17T08:55", who: "WO-MGR",              evt: "WO 発行・Booking競合検出", from: null, to: "conflicted" },
    ],
  },

  {
    id: "F-2026-0517-006",
    priority: "P3",
    origin: "report",
    building: "B-003", floor: "1F", space: "Loading Bay",
    title: "床面の油汚れ（清掃要請）",
    woType: "清掃", issueType: "オフィスサービス",
    openedAt: "2026-05-16T09:30",
    updatedAt: "2026-05-17T06:10",
    problem: "none",
    note: "標準フロー。担当者割り当て済。",
    chain: [
      { kind: "observation", id: "RPT-8830", status: "report_approved",   label: "Report" },
      { kind: "issue",       id: "ISS-3320", status: "open",              label: "Issue" },
      { kind: "ticket",      id: "TKT-9020", status: "estimate_approved", label: "Ticket" },
      { kind: "workorder",   id: "WO-4460",  status: "wo_in_progress",   label: "WO" },
      { kind: "payment",     id: null,       status: "not_started",       label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-16T09:30", who: "STK-REPORTER", evt: "Report 投稿",   from: null, to: "pending" },
      { t: "2026-05-16T10:02", who: "STK-FM",       evt: "Report 承認",   from: "pending", to: "approved" },
      { t: "2026-05-16T10:10", who: "TICKET-MGR",   evt: "Ticket 起票",   from: null, to: "open" },
      { t: "2026-05-16T11:00", who: "STK-FM",       evt: "Estimate 承認", from: null, to: "approved" },
      { t: "2026-05-17T05:55", who: "WO-MGR",       evt: "WO 発行・担当割当", from: null, to: "wo_open" },
      { t: "2026-05-17T06:10", who: "STK-WORKER",   evt: "現場着手",       from: "wo_open", to: "wo_in_progress" },
    ],
  },

  {
    id: "F-2026-0517-007",
    priority: "P3",
    origin: "iot",
    building: "B-001", floor: "屋上", space: "Roof Unit 1",
    title: "空調機 RTU-1 フィルター交換（予防保全）",
    woType: "予防保全", issueType: "設備資産",
    openedAt: "2026-05-10T07:00",
    updatedAt: "2026-05-16T19:30",
    problem: "none",
    note: "Payment 登録済。チェーン完了済。",
    chain: [
      { kind: "observation", id: null,        status: "not_started",       label: "—" },
      { kind: "issue",       id: "ISS-3280",  status: "closed",            label: "StdIssue" },
      { kind: "ticket",      id: "TKT-8995",  status: "estimate_approved", label: "Ticket" },
      { kind: "workorder",   id: "WO-4420",   status: "wo_completed",      label: "WO" },
      { kind: "payment",     id: "PAY-2210",  status: "pay_paid",          label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-10T07:00", who: "WO-SCHEDULER", evt: "予防保全 発火",   from: null, to: "scheduled" },
      { t: "2026-05-14T15:00", who: "STK-WORKER",   evt: "WO 完了",         from: "wo_in_progress", to: "wo_completed" },
      { t: "2026-05-16T19:30", who: "STK-FINANCE",  evt: "Payment 登録",    from: null, to: "paid" },
    ],
  },

  {
    id: "F-2026-0517-008",
    priority: "P1",
    origin: "report",
    building: "B-002", floor: "2F", space: "Cafe Area",
    title: "コーヒー什器から水漏れ",
    woType: null, issueType: null,
    openedAt: "2026-05-17T07:05",
    updatedAt: "2026-05-17T07:05",
    problem: "stale_report",
    note: "報告確信度 high。早期評価推奨。",
    chain: [
      { kind: "observation", id: "RPT-8842", status: "report_pending", label: "Report" },
      { kind: "issue",       id: null,       status: "not_started",     label: "Issue" },
      { kind: "ticket",      id: null,       status: "not_started",     label: "Ticket" },
      { kind: "workorder",   id: null,       status: "not_started",     label: "WO" },
      { kind: "payment",     id: null,       status: "not_started",     label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-17T07:05", who: "STK-REPORTER (田中)", evt: "Report 投稿 (confidence: high)", from: null, to: "pending" },
    ],
  },

  {
    id: "F-2026-0517-009",
    priority: "P2",
    origin: "iot",
    building: "B-001", floor: "9F", space: "Pantry 9-W",
    title: "冷蔵庫温度逸脱 (10°C超)",
    woType: "是正対応", issueType: "設備資産",
    openedAt: "2026-05-17T05:40",
    updatedAt: "2026-05-17T08:15",
    problem: "overdue",
    note: "Ticket 期限超過 (本日 06:00)。",
    chain: [
      { kind: "observation", id: "IOT-77410", status: "iot_received",      label: "IoTEvent" },
      { kind: "issue",       id: "ISS-3322",  status: "open",              label: "Issue" },
      { kind: "ticket",      id: "TKT-9018",  status: "estimate_approved", label: "Ticket (期限超)", problem: "overdue" },
      { kind: "workorder",   id: null,        status: "not_started",       label: "WO" },
      { kind: "payment",     id: null,        status: "not_started",       label: "Pay" },
    ],
    timeline: [
      { t: "2026-05-17T05:40", who: "STK-IOT",   evt: "IoTEvent 受信",  from: null, to: "received" },
      { t: "2026-05-17T05:41", who: "ISSUE-MGR", evt: "Issue 自動生成", from: null, to: "open" },
      { t: "2026-05-17T05:45", who: "TICKET-MGR", evt: "Ticket 起票 (due 06:00)", from: null, to: "estimate_pending" },
      { t: "2026-05-17T05:55", who: "STK-FM",    evt: "Estimate 承認",  from: null, to: "approved" },
      { t: "2026-05-17T08:15", who: "system",    evt: "期限超過を検出", from: "approved", to: "overdue" },
    ],
  },
];

/* KPI tile definitions — order = display order */
const PROBLEM_KPIS = [
  { key: "stale_report",   label: "Report 滞留",      desc: ">24h 未評価", count: 2, trend: "+1" },
  { key: "pending_review", label: "NonStd レビュー",  desc: "FM確定待ち",  count: 1, trend: "0" },
  { key: "approval_wait",  label: "見積承認待ち",     desc: "WO発行前",    count: 1, trend: "0" },
  { key: "conflicted",     label: "Booking 競合",     desc: "解消要",      count: 1, trend: "+1" },
  { key: "overdue",        label: "期限超過",         desc: "Ticket / WO", count: 1, trend: "+1" },
  { key: "unsettled",      label: "緊急WO 精算未完了", desc: "事後Ticket要", count: 1, trend: "+1" },
];

/* Origin label */
const ORIGIN_META = {
  report:   { label: "Report",      icon: "person" },
  iot:      { label: "IoTEvent",    icon: "sensor" },
  schedule: { label: "Scheduled",   icon: "clock"  },
};

Object.assign(window, {
  PROBLEM_TYPES, ENTITY_META, STATUS_META,
  BUILDINGS, AGENTS, ISSUE_TYPES, WO_TYPES,
  FLOWS, PROBLEM_KPIS, ORIGIN_META,
});
