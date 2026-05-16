/* CS-OPS-DASHBOARD — main app */

const { useState, useEffect, useMemo } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "comfortable",
  "theme": "light",
  "primary_view": "chain",
  "accent": "#3b5cdb"
}/*EDITMODE-END*/;

function App() {
  const [t, setTweak] = window.useTweaks(TWEAK_DEFAULTS);
  const [nav, setNav]                 = useState("flows");
  const [tab, setTab]                 = useState("all");
  const [kpi, setKpi]                 = useState(null);
  const [filters, setFilters]         = useState({ building: null, entity: null, agent: null, range: "直近 7日" });
  const [selected, setSelected]       = useState(null);
  const [drawerOpen, setDrawerOpen]   = useState(false);
  const [manifestoOpen, setManifesto] = useState(() => {
    try { return localStorage.getItem("ops_manifesto_seen") !== "1"; }
    catch { return true; }
  });
  const closeManifesto = () => {
    try { localStorage.setItem("ops_manifesto_seen", "1"); } catch {}
    setManifesto(false);
  };
  const [theme, setTheme]             = useState(t.theme || "light");

  useEffect(() => { setTheme(t.theme || "light"); }, [t.theme]);

  /* Filter pipeline */
  const filteredFlows = useMemo(() => {
    let xs = window.FLOWS.slice();

    if (tab === "problems") xs = xs.filter(f => f.problem && f.problem !== "none");
    if (tab === "reports")  xs = xs.filter(f => f.origin === "report" && (f.problem === "stale_report" || f.chain[0].status === "report_pending"));
    if (tab === "emergency_settlement") xs = xs.filter(f => f.problem === "unsettled");

    if (kpi) xs = xs.filter(f => f.problem === kpi);

    if (filters.building) xs = xs.filter(f => f.building === filters.building);

    // sort: problems first (danger > warn > info > ok), then by updated desc
    const toneOrder = { danger: 0, warn: 1, info: 2, ok: 3 };
    xs.sort((a, b) => {
      const ta = (window.PROBLEM_TYPES[a.problem] || { tone: "ok" }).tone;
      const tb = (window.PROBLEM_TYPES[b.problem] || { tone: "ok" }).tone;
      if (toneOrder[ta] !== toneOrder[tb]) return toneOrder[ta] - toneOrder[tb];
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
    return xs;
  }, [tab, kpi, filters]);

  /* Counts */
  const counts = useMemo(() => ({
    allFlows: window.FLOWS.length,
    problems: window.FLOWS.filter(f => f.problem && f.problem !== "none").length,
    reportQueue: window.FLOWS.filter(f => f.origin === "report" && f.chain[0].status === "report_pending").length,
    emergency: window.FLOWS.filter(f => f.problem === "unsettled").length,
  }), []);

  const tabs = [
    { key: "all",      label: "すべて",         count: window.FLOWS.length },
    { key: "problems", label: "問題のみ",       count: counts.problems },
    { key: "reports",  label: "Report 評価",   count: counts.reportQueue },
    { key: "emergency_settlement", label: "緊急精算", count: counts.emergency },
  ];

  const selectedFlow = useMemo(() =>
    window.FLOWS.find(f => f.id === selected), [selected]);

  const onSelectFlow = (id) => {
    setSelected(id);
    setDrawerOpen(true);
  };

  const onToggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    setTweak("theme", next);
  };

  const onFilter = (key, val) => setFilters(f => ({ ...f, [key]: val }));

  /* Scope label for breadcrumb */
  const scope =
    nav === "problems" ? "問題キュー" :
    nav === "reports"  ? "Report 評価キュー" :
    nav === "schedules" ? "予防保全スケジュール" :
    nav === "settings"  ? "設定" :
    nav === "overview"  ? "Overview" :
                          "業務フロー";

  return (
    <div className="app"
         data-theme={theme}
         data-density={t.density || "comfortable"}>

      <window.Rail active={nav}
                   onChange={setNav}
                   counts={counts} />

      <window.TopBar onOpenManifesto={() => setManifesto(true)}
                     scope={scope}
                     theme={theme}
                     onToggleTheme={onToggleTheme} />

      <main className="main">
        <div className="page-header">
          <div className="page-title">
            <h1>業務フロー監視</h1>
            <p>
              Report / IoTEvent → Issue → Ticket → WorkOrder → Payment の
              チェーン状態を6つのCSから集約。問題があるものから対応してください。
            </p>
          </div>
          <div className="page-actions">
            <span style={{
              fontSize: 11.5, color: "var(--c-text-3)", marginRight: 6,
            }}>
              現在時刻 <span className="mono">2026-05-17 10:00</span> · 30秒ごとに自動更新
            </span>
            <button className="btn ghost">
              <Icon name="external" size={12} /> CSV
            </button>
            <button className="btn primary">
              <Icon name="check" size={12} /> 全レビュー対象を一括処理
            </button>
          </div>
        </div>

        <window.KPIBar items={window.PROBLEM_KPIS}
                       selected={kpi}
                       onSelect={setKpi} />

        <window.FilterBar tab={tab}
                          onTab={setTab}
                          tabs={tabs}
                          filters={filters}
                          onFilter={onFilter} />

        <div className="flow-table">
          {filteredFlows.length === 0 ? (
            <EmptyState />
          ) : (
            filteredFlows.map(f =>
              <window.FlowRow key={f.id}
                              flow={f}
                              selected={selected === f.id}
                              onSelect={onSelectFlow} />
            )
          )}
        </div>
      </main>

      <window.DetailDrawer flow={selectedFlow}
                           open={drawerOpen}
                           onClose={() => setDrawerOpen(false)} />

      <window.Manifesto open={manifestoOpen}
                        onClose={closeManifesto} />

      {/* Tweaks panel */}
      <window.TweaksPanel title="Tweaks">
        <window.TweakSection label="表示" />
        <window.TweakRadio
          label="密度"
          value={t.density}
          options={[
            { value: "comfortable", label: "Comfort" },
            { value: "compact",     label: "Compact" },
          ]}
          onChange={(v) => setTweak("density", v)}
        />
        <window.TweakRadio
          label="テーマ"
          value={t.theme}
          options={[
            { value: "light", label: "Light" },
            { value: "dark",  label: "Dark"  },
          ]}
          onChange={(v) => { setTweak("theme", v); setTheme(v); }}
        />

        <window.TweakSection label="主ビュー" />
        <window.TweakRadio
          label="FlowRow 構成"
          value={t.primary_view}
          options={[
            { value: "chain",  label: "Chain" },
            { value: "kanban", label: "Kanban" },
          ]}
          onChange={(v) => setTweak("primary_view", v)}
        />

        <window.TweakSection label="クイックアクション" />
        <window.TweakButton label="UX 提言を再表示"
                            onClick={() => setManifesto(true)} />
        <window.TweakButton label="フィルタをリセット"
                            secondary
                            onClick={() => { setKpi(null); setTab("all"); setFilters({ building: null, entity: null, agent: null, range: "直近 7日" }); }} />
      </window.TweaksPanel>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{
      padding: "60px 20px",
      textAlign: "center",
      color: "var(--c-text-3)",
    }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: "var(--c-text)", marginBottom: 6 }}>
        対象のフローはありません
      </div>
      <div style={{ fontSize: 12 }}>
        フィルタ条件を緩めるか、KPI タイルを再選択してください。
      </div>
    </div>
  );
}

window.App = App;
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
