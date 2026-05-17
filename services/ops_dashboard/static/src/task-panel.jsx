/* CS-OPS-DASHBOARD — タスク登録パネル
 * WO を選択し、ServiceTask を wo-manager に登録する操作画面。
 * バックエンドプロキシ:
 *   GET  /ops/work-orders              → wo-manager GET /work-orders
 *   POST /ops/work-orders/{id}/tasks   → wo-manager POST /work-orders/{id}/tasks
 */

const { useState, useEffect } = React;

const WO_STATUS_LABEL = {
  Open:        { label: "Open",        cls: "info" },
  InProgress:  { label: "InProgress",  cls: "warn" },
  Completed:   { label: "Completed",   cls: "ok"   },
};

function StatusBadge({ status }) {
  const m = WO_STATUS_LABEL[status] || { label: status, cls: "muted" };
  return (
    <span className={"badge " + m.cls} style={{ fontSize: 10, padding: "2px 6px" }}>
      {m.label}
    </span>
  );
}

function TaskPanel() {
  const [wos, setWos]             = useState([]);
  const [loading, setLoading]     = useState(true);
  const [fetchErr, setFetchErr]   = useState(null);

  const [selectedWo, setSelectedWo] = useState(null);
  const [title, setTitle]           = useState("");
  const [desc, setDesc]             = useState("");
  const [performedAt, setPerformedAt] = useState("");
  const [performedOn, setPerformedOn] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [result, setResult]         = useState(null); // { ok: bool, message: string, wo?: object }

  /* WO 一覧フェッチ */
  useEffect(() => {
    fetch("/ops/work-orders")
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => { setWos(data); setLoading(false); })
      .catch(e => { setFetchErr(e.message); setLoading(false); });
  }, [result]); // タスク登録後に再フェッチして task_ids を更新

  const selectedWoData = wos.find(w => w.work_order_id === selectedWo) || null;

  const canSubmit = selectedWo && title.trim() && !submitting;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setResult(null);
    try {
      const body = { title: title.trim() };
      if (desc.trim())        body.description  = desc.trim();
      if (performedAt.trim()) body.performed_at  = performedAt.trim();
      if (performedOn.trim()) body.performed_on  = performedOn.trim();

      const resp = await fetch(`/ops/work-orders/${selectedWo}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (resp.ok) {
        setResult({ ok: true, message: `タスク「${title.trim()}」を登録しました。`, wo: data });
        setTitle(""); setDesc(""); setPerformedAt(""); setPerformedOn("");
      } else {
        setResult({ ok: false, message: data.detail || `HTTP ${resp.status}` });
      }
    } catch (err) {
      setResult({ ok: false, message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "0 24px 48px" }}>

      <div className="page-header" style={{ paddingTop: 0 }}>
        <div className="page-title">
          <h1>タスク登録</h1>
          <p>WorkOrder を選択して ServiceTask を追加します。自動生成 WO はタスクなしで作成されるため、ここで作業内容を登録してください。</p>
        </div>
      </div>

      {/* WO 選択 */}
      <section style={{ marginBottom: 24 }}>
        <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: "var(--c-text)" }}>
          対象 WorkOrder を選択
        </div>

        {loading && (
          <div style={{ color: "var(--c-text-3)", fontSize: 13 }}>WorkOrder を読み込み中…</div>
        )}
        {fetchErr && (
          <div className="callout-err" style={{
            background: "var(--c-danger-bg, #fff0f0)", border: "1px solid var(--c-danger, #e53e3e)",
            borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "var(--c-danger, #e53e3e)",
          }}>
            wo-manager への接続に失敗しました: {fetchErr}
          </div>
        )}
        {!loading && !fetchErr && wos.length === 0 && (
          <div style={{ color: "var(--c-text-3)", fontSize: 13 }}>
            WorkOrder がありません。先に Estimate を承認してください。
          </div>
        )}

        {!loading && wos.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {wos.map(wo => (
              <button
                key={wo.work_order_id}
                onClick={() => { setSelectedWo(wo.work_order_id); setResult(null); }}
                style={{
                  display: "flex", alignItems: "flex-start", gap: 12,
                  padding: "12px 14px", borderRadius: 8, textAlign: "left",
                  border: "1.5px solid " + (selectedWo === wo.work_order_id
                    ? "var(--c-accent)" : "var(--c-border)"),
                  background: selectedWo === wo.work_order_id
                    ? "color-mix(in srgb, var(--c-accent) 8%, transparent)"
                    : "var(--c-surface)",
                  cursor: "pointer", transition: "border-color .15s",
                }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: "var(--c-text)" }}>
                    {wo.title}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--c-text-3)", marginTop: 2, fontFamily: "var(--font-mono)" }}>
                    {wo.work_order_id.slice(0, 16)}…
                  </div>
                  <div style={{ fontSize: 11, color: "var(--c-text-3)", marginTop: 2 }}>
                    タスク: {wo.task_ids.length} 件　タイプ: {wo.work_order_type}
                  </div>
                </div>
                <StatusBadge status={wo.work_order_status} />
              </button>
            ))}
          </div>
        )}
      </section>

      {/* 現在のタスク一覧 */}
      {selectedWoData && (
        <section style={{
          background: "var(--c-surface-2, var(--c-surface))",
          border: "1px solid var(--c-border)",
          borderRadius: 8, padding: "12px 16px", marginBottom: 24,
        }}>
          <div style={{ fontWeight: 600, fontSize: 12, color: "var(--c-text-3)", marginBottom: 8 }}>
            現在のタスク（{selectedWoData.task_ids.length} 件）
          </div>
          {selectedWoData.task_ids.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--c-text-3)" }}>タスクなし — 以下のフォームで追加できます</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {selectedWoData.task_ids.map((tid, i) => (
                <div key={tid} style={{ fontSize: 12, color: "var(--c-text-2)", display: "flex", gap: 8 }}>
                  <span style={{ color: "var(--c-text-4)", fontFamily: "var(--font-mono)" }}>{i + 1}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{tid.slice(0, 20)}…</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* タスク入力フォーム */}
      {selectedWo && (
        <form onSubmit={handleSubmit}>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 14, color: "var(--c-text)" }}>
            新しいタスクを追加
          </div>

          <Field label="タスク名" required>
            <input
              className="field-input"
              placeholder="例: 煙感知器の清掃・動作確認"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              style={fieldStyle}
            />
          </Field>

          <Field label="作業内容（任意）">
            <textarea
              className="field-input"
              placeholder="作業手順や注意事項を記述…"
              value={desc}
              onChange={e => setDesc(e.target.value)}
              rows={3}
              style={{ ...fieldStyle, resize: "vertical" }}
            />
          </Field>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Field label="実施場所 ID（任意）">
              <input
                className="field-input"
                placeholder="rec:Space-001"
                value={performedAt}
                onChange={e => setPerformedAt(e.target.value)}
                style={fieldStyle}
              />
            </Field>
            <Field label="対象設備 ID（任意）">
              <input
                className="field-input"
                placeholder="rec:Asset-fan-01"
                value={performedOn}
                onChange={e => setPerformedOn(e.target.value)}
                style={fieldStyle}
              />
            </Field>
          </div>

          {result && (
            <div style={{
              padding: "10px 14px", borderRadius: 8, marginBottom: 16, fontSize: 13,
              background: result.ok ? "var(--c-ok-bg, #f0fff4)" : "var(--c-danger-bg, #fff0f0)",
              border: "1px solid " + (result.ok ? "var(--c-ok, #38a169)" : "var(--c-danger, #e53e3e)"),
              color: result.ok ? "var(--c-ok, #38a169)" : "var(--c-danger, #e53e3e)",
            }}>
              {result.ok ? "✓ " : "✗ "}{result.message}
              {result.ok && result.wo && (
                <span style={{ marginLeft: 8, color: "var(--c-text-3)", fontSize: 11 }}>
                  WO タスク数: {result.wo.task_ids.length}
                </span>
              )}
            </div>
          )}

          <button
            type="submit"
            className="btn primary"
            disabled={!canSubmit}
            style={{ marginTop: 4, opacity: canSubmit ? 1 : 0.5, cursor: canSubmit ? "pointer" : "not-allowed" }}>
            <Icon name="plus" size={13} />
            {submitting ? "登録中…" : "タスクを登録"}
          </button>
        </form>
      )}
    </div>
  );
}

function Field({ label, required, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "var(--c-text-2)", marginBottom: 5 }}>
        {label}{required && <span style={{ color: "var(--c-danger, #e53e3e)", marginLeft: 3 }}>*</span>}
      </label>
      {children}
    </div>
  );
}

const fieldStyle = {
  width: "100%", boxSizing: "border-box",
  padding: "8px 10px", borderRadius: 6,
  border: "1.5px solid var(--c-border)",
  background: "var(--c-input-bg, var(--c-bg))",
  color: "var(--c-text)", fontSize: 13,
  fontFamily: "var(--font-sans)",
  outline: "none",
  transition: "border-color .15s",
};

window.TaskPanel = TaskPanel;
