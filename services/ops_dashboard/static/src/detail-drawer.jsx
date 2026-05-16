/* Detail drawer — vertical chain, timeline, action cards */

function VerticalChain({ flow }) {
  const labelFor = (kind) => ({
    observation: "Observation", issue: "Issue", ticket: "Ticket",
    workorder: "WorkOrder", payment: "Payment",
  })[kind] || kind;
  const ifFor = (kind) => ({
    observation: "IF-OBS-002", issue: "IF-ISSUE-001", ticket: "IF-TICKET-001",
    workorder: "IF-WO-001", payment: "IF-PAYMENT-001",
  })[kind];

  return (
    <div className="chain-vertical">
      {flow.chain.map((n, i) => {
        const cls = window.chainNodeClass ? window.chainNodeClass(n.status, n.problem) : "";
        const meta = window.STATUS_META[n.status] || { label: "—" };
        const stepCls =
          cls.replace("is-muted", "")
             .replace("is-active", "is-active")
             .replace("is-done", "is-done")
             .replace("is-warn", "is-warn")
             .replace("is-danger", "is-danger");
        return (
          <div key={i} className={"chain-step " + stepCls}>
            <span className="marker">
              {stepCls.includes("is-done") ? "✓" :
               stepCls.includes("is-warn") || stepCls.includes("is-danger") ? "!" :
               stepCls.includes("is-active") ? "·" : i + 1}
            </span>
            <div className="body">
              <div className="name">
                {labelFor(n.kind)}
                {n.id && <span className="id mono">{n.id}</span>}
              </div>
              <div className="desc">
                {n.status === "not_started"
                  ? "未着手"
                  : meta.label}
                {n.problem && (() => {
                  const pm = window.PROBLEM_TYPES[n.problem];
                  return pm ? ` · ${pm.label}` : "";
                })()}
              </div>
            </div>
            <span className="right cs-ref">{ifFor(n.kind)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Timeline({ entries }) {
  return (
    <div className="timeline">
      {entries.map((e, i) => {
        const d = new Date(e.t);
        const when = d.toLocaleString("ja-JP", {
          month: "2-digit", day: "2-digit",
          hour: "2-digit", minute: "2-digit",
        });
        return (
          <div key={i} className="timeline-row">
            <span className="when">{when}</span>
            <div className="what">
              <span className="evt">{e.evt}</span>
              <span className="who">{e.who}</span>
              {(e.from || e.to) && (
                <span className="delta">
                  {e.from || "∅"} <Icon name="arrow" size={10} /> {e.to || "∅"}
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* Action set depends on flow.problem and chain composition */
function pickActions(flow) {
  const actions = [];
  const prob = flow.problem;
  const has = (kind) => flow.chain.find(c => c.kind === kind && c.status !== "not_started");

  if (prob === "stale_report" || (has("observation") && !has("issue") && flow.origin === "report")) {
    actions.push({
      key: "approve_report", at: "Report を承認しIssue生成",
      desc: "PATCH /reports/{id}/evaluate · IssueType付与", forward: "IF-OBS-002",
      tone: "primary",
    });
    actions.push({
      key: "reject_report", at: "Report を却下",
      desc: "PATCH /reports/{id}/evaluate · action=reject", forward: "IF-OBS-002",
      tone: "danger",
    });
  }

  if (prob === "pending_review") {
    actions.push({
      key: "confirm_issue", at: "NonStdIssue を確定 (open化)",
      desc: "PATCH /issues/{id}/review · action=confirm", forward: "IF-ISSUE-001",
      tone: "primary",
    });
    actions.push({
      key: "reject_issue", at: "NonStdIssue を却下",
      desc: "PATCH /issues/{id}/review · action=reject", forward: "IF-ISSUE-001",
      tone: "danger",
    });
  }

  if (prob === "approval_wait") {
    actions.push({
      key: "approve_estimate", at: "Estimate を承認",
      desc: "PATCH /estimates/{id}/approve", forward: "IF-TICKET-001",
      tone: "primary",
    });
    actions.push({
      key: "request_revision", at: "見積を差し戻し",
      desc: "PATCH /estimates/{id}/revise", forward: "IF-TICKET-001",
    });
  }

  if (prob === "conflicted") {
    actions.push({
      key: "reassign", at: "担当を再アサイン",
      desc: "POST /ops/actions · booking.reassign", forward: "IF-WO-001",
      tone: "primary",
    });
    actions.push({
      key: "reschedule", at: "時間帯を変更",
      desc: "PATCH /bookings/{id} · start/end", forward: "IF-WO-001",
    });
  }

  if (prob === "overdue") {
    actions.push({
      key: "raise_priority", at: "優先度を上げる",
      desc: "PATCH /tickets/{id} · priority=+1", forward: "IF-TICKET-001",
      tone: "primary",
    });
    actions.push({
      key: "extend_due", at: "期限を延長",
      desc: "PATCH /tickets/{id} · dueAt+", forward: "IF-TICKET-001",
    });
  }

  if (prob === "unsettled") {
    actions.push({
      key: "post_ticket", at: "事後 Ticket を起票",
      desc: "POST /tickets · 緊急WO遡及", forward: "IF-TICKET-001",
      tone: "primary",
    });
    actions.push({
      key: "post_estimate", at: "実績ベースの Estimate を登録",
      desc: "POST /estimates · 遡及登録", forward: "IF-TICKET-001",
    });
  }

  // generic actions always present
  actions.push({
    key: "comment", at: "コメントを残す",
    desc: "監査証跡に記録される", forward: "IF-OPS-001",
  });
  actions.push({
    key: "open_cs", at: "対応CSの詳細画面を開く",
    desc: "新タブで CS UI へ", forward: "external",
  });

  return actions;
}

function DetailDrawer({ flow, open, onClose }) {
  if (!flow) {
    return <aside className="drawer" />;
  }
  const buildingName = (window.BUILDINGS.find(b => b.id === flow.building) || {}).name || flow.building;
  const actions = pickActions(flow);

  return (
    <React.Fragment>
      <div className={"drawer-scrim" + (open ? " open" : "")} onClick={onClose} />
      <aside className={"drawer" + (open ? " open" : "")} aria-hidden={!open}>
        <div className="drawer-head">
          <div className="meta">
            <div className="id mono">{flow.id}</div>
            <h2>{flow.title}</h2>
            <div className="submeta">
              <PriorityBadge p={flow.priority} />
              <ProblemTag kind={flow.problem} />
              <span><Icon name="pin" size={11} /> {buildingName} · {flow.floor} · {flow.space}</span>
              {flow.woType && <span><Icon name="check" size={11} /> {flow.woType}</span>}
            </div>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="閉じる">
            <Icon name="x" size={14} />
          </button>
        </div>

        <div className="drawer-body">
          {/* Note */}
          {flow.note && (
            <div style={{
              background: "var(--c-surface-2)",
              border: "1px solid var(--c-border)",
              borderLeft: "3px solid " +
                (flow.problem === "conflicted" || flow.problem === "overdue"
                  ? "var(--c-danger)"
                  : flow.problem === "unsettled" ? "var(--c-info)" : "var(--c-warn)"),
              padding: "10px 12px",
              borderRadius: "6px",
              fontSize: 12.5,
              color: "var(--c-text-2)",
            }}>
              {flow.note}
            </div>
          )}

          {/* Chain (vertical) */}
          <div>
            <h3 className="section-title">業務連鎖の状態（5ノード）</h3>
            <VerticalChain flow={flow} />
          </div>

          {/* Actions */}
          <div>
            <h3 className="section-title">推奨アクション · 対応CSへ転送</h3>
            <div className="actions-grid">
              {actions.map(a => (
                <button key={a.key}
                        className={"action-card" + (a.tone === "danger" ? " danger" : "")}>
                  <span className="at">{a.at}</span>
                  <span className="desc">{a.desc}</span>
                  <span className="cs-ref" style={{ marginTop: 4, alignSelf: "flex-start" }}>
                    {a.forward}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 className="section-title">状態遷移ログ · FUN-OPS-002</h3>
            <Timeline entries={flow.timeline} />
          </div>

          {/* Source CS APIs */}
          <div>
            <h3 className="section-title">参照CS（リクエスト時に集約）</h3>
            <div style={{
              display: "flex", gap: 6, flexWrap: "wrap",
              fontSize: 11.5, color: "var(--c-text-3)",
            }}>
              {["CS-OBS-COLLECTOR", "CS-ISSUE-MANAGER", "CS-TICKET-MANAGER",
                "CS-WO-MANAGER", "CS-PAYMENT-MANAGER", "CS-BUILDING-REGISTRY"
              ].map(cs => (
                <span key={cs} className="cs-ref">{cs}</span>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </React.Fragment>
  );
}

Object.assign(window, { DetailDrawer, VerticalChain, Timeline, pickActions });
