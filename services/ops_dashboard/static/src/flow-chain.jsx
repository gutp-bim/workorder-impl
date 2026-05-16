/* Flow chain visualization & flow row */

/* Map status -> chain node state */
function chainNodeClass(status, hasProblem) {
  if (hasProblem === "conflicted" || hasProblem === "overdue") return "is-danger";
  if (hasProblem === "pending_review" || hasProblem === "stale_report" || hasProblem === "approval_wait") return "is-warn";
  if (status === "not_started") return "is-muted";
  if (status === "pay_unsettled") return "is-warn";
  const t = (window.STATUS_META[status] || {}).tone;
  if (t === "ok")   return "is-done";
  if (t === "info") return "is-active";
  if (t === "warn") return "is-warn";
  if (t === "danger") return "is-danger";
  return "is-muted";
}
function chainLinkClass(left, right) {
  const leftOk  = left  && left.status  !== "not_started";
  const rightOk = right && right.status !== "not_started";
  if (leftOk && rightOk) return "is-active";
  if (leftOk && !rightOk) return "is-pending";
  return "";
}

function Chain({ chain, compact = false }) {
  const labelFor = (kind) => ({
    observation: "OBS", issue: "ISS", ticket: "TKT", workorder: "WO", payment: "PAY",
  })[kind] || kind;

  return (
    <div className="chain">
      {chain.map((n, i) => {
        const cls = chainNodeClass(n.status, n.problem);
        const meta = window.STATUS_META[n.status] || { label: "—" };
        return (
          <React.Fragment key={i}>
            <div className={"node " + cls} title={`${labelFor(n.kind)}: ${meta.label}`}>
              <div className="node-pill">
                {meta.label === "—" ? labelFor(n.kind) : meta.label}
              </div>
              {!compact && (
                <div className="node-id">{n.id || labelFor(n.kind)}</div>
              )}
            </div>
            {i < chain.length - 1 && (
              <span className={"link " + chainLinkClass(chain[i], chain[i+1])} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function PriorityBadge({ p }) {
  return <span className={"priority-badge " + p.toLowerCase()}>{p}</span>;
}

function ProblemTag({ kind, compact }) {
  if (!kind || kind === "none") {
    return <span className="problem-tag ok"><span className="pulse" />正常</span>;
  }
  const meta = window.PROBLEM_TYPES[kind] || { label: kind, tone: "info" };
  return (
    <span className={"problem-tag " + meta.tone}>
      <span className="pulse" />
      {meta.label}
    </span>
  );
}

function OriginPill({ origin }) {
  const m = window.ORIGIN_META[origin] || {};
  return (
    <span className="origin-pill">
      <Icon name={m.icon} size={11} />
      {m.label}
    </span>
  );
}

function fmtWhen(iso) {
  const d = new Date(iso);
  const now = new Date("2026-05-17T10:00:00");
  const diff = (now - d) / 3600e3; // hours
  if (diff < 1)  return Math.round(diff * 60) + "m前";
  if (diff < 24) return Math.round(diff) + "h前";
  return Math.round(diff / 24) + "d前";
}

function FlowRow({ flow, selected, onSelect }) {
  const probTone = (window.PROBLEM_TYPES[flow.problem] || {}).tone || "ok";
  const cls = "flow-row" +
    (selected ? " is-selected" : "") +
    " is-problem-" + probTone;

  const buildingName = (window.BUILDINGS.find(b => b.id === flow.building) || {}).name || flow.building;

  return (
    <div className={cls}
         aria-selected={selected}
         onClick={() => onSelect(flow.id)}>
      <div className="col-priority">
        <PriorityBadge p={flow.priority} />
        <OriginPill origin={flow.origin} />
      </div>

      <div className="col-meta">
        <div className="title">{flow.title}</div>
        <div className="submeta">
          <span className="id mono">{flow.id}</span>
          <span className="loc"><Icon name="pin" size={10} />{buildingName} · {flow.floor} · {flow.space}</span>
        </div>
      </div>

      <div className="col-chain">
        <Chain chain={flow.chain} compact />
      </div>

      <div className="col-problem">
        <ProblemTag kind={flow.problem} />
        {flow.woType && <span style={{ fontSize: 11, color: "var(--c-text-3)" }}>{flow.woType}</span>}
      </div>

      <div className="col-updated">
        <span className="when">{fmtWhen(flow.updatedAt)}</span>
        <span style={{ color: "var(--c-text-4)", fontSize: 10 }}>updated</span>
      </div>
    </div>
  );
}

Object.assign(window, { Chain, FlowRow, ProblemTag, OriginPill, PriorityBadge, fmtWhen });
