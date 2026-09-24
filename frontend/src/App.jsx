import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [activeView, setActiveView] = useState("Overview");
  const [showUpload, setShowUpload] = useState(false);
  const [reports, setReports] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [reportsResponse, historyResponse] = await Promise.all([
          fetch(`${API_BASE}/api/reports`),
          fetch(`${API_BASE}/api/history`),
        ]);
        if (!reportsResponse.ok || !historyResponse.ok) throw new Error("The dashboard data could not be loaded.");
        const reportsData = await reportsResponse.json();
        const historyData = await historyResponse.json();
        setReports(reportsData.reports);
        setHistory(historyData.events);
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const latestReport = reports[0];
  const changeView = (view) => {
    setActiveView(view);
    setSelectedReport(null);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">M</span><span>MediClear</span></div>
        <div className="profile-card"><div className="avatar">AS</div><div><strong>Alex Sharma</strong><span>Patient account</span></div><button className="more-button" aria-label="Account options">...</button></div>
        <nav className="nav-list" aria-label="Main navigation">
          {["Overview", "My reports", "Health history"].map((item) => <button className={activeView === item ? "nav-item active" : "nav-item"} key={item} onClick={() => changeView(item)}><span className="nav-icon">{item === "Overview" ? "◈" : item === "My reports" ? "▤" : "⌁"}</span>{item}</button>)}
        </nav>
        <div className="sidebar-bottom"><button className="nav-item"><span className="nav-icon">?</span>Help center</button><div className="privacy-note"><span className="privacy-dot" />Your health data is private and secure.</div></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div><p className="eyebrow">PATIENT DASHBOARD</p><h1>{activeView}</h1></div><div className="top-actions"><span className="last-sync">Last synced just now</span><button className="icon-button" aria-label="Notifications">♧</button><button className="small-avatar">AS</button></div></header>
        <section className="welcome-row"><div><h2>{activeView === "Health history" ? "Your health timeline." : activeView === "My reports" ? "Your reports, in one place." : "Good morning, Alex."}</h2><p>{activeView === "Health history" ? "A simple record of your report activity over time." : "Here is a clear view of your recent health results."}</p></div><button className="primary-button" onClick={() => setShowUpload(true)}><span>+</span> Upload report</button></section>

        {loading && <div className="data-state">Loading your health data...</div>}
        {error && <div className="data-state error-state">{error} <button className="text-button" onClick={() => window.location.reload()}>Try again</button></div>}

        {!loading && !error && activeView === "Overview" && <section className="summary-grid" aria-label="Health summary">
          <article className="summary-card featured"><div className="card-label">LATEST REPORT</div><div className="summary-main"><span className="report-symbol">↗</span><div><h3>{latestReport?.name || "No reports yet"}</h3><p>{latestReport ? `Reviewed ${latestReport.date}` : "Upload your first report"}</p></div></div><div className="status-line"><span className="status-dot green-dot" />{latestReport?.summary || "Ready for your report"}<span className="arrow">→</span></div></article>
          <article className="summary-card"><div className="card-label">RESULTS OVERVIEW</div><div className="metric"><strong>{reports.reduce((total, report) => total + report.tests, 0)}</strong><span>tests tracked</span></div><div className="progress"><span /></div><p className="muted">Across {reports.length} reports</p></article>
          <article className="summary-card"><div className="card-label">NEXT STEP</div><div className="next-step"><span className="calendar-icon">□</span><div><h3>{reports[1]?.name || "Upload a report"}</h3><p>{reports[1]?.summary || "Start your health record"}</p></div></div><button className="text-button" onClick={() => reports[1] && setSelectedReport(reports[1])}>View details <span>→</span></button></article>
        </section>}

        {!loading && !error && activeView === "Health history" && <section className="panel history-panel"><div className="panel-heading"><div><p className="eyebrow">YOUR RECORD</p><h2>Health history</h2></div></div><div className="history-list">{history.map((event) => <div className="history-event" key={`${event.date}-${event.title}`}><span className={`history-marker ${event.tone}`} /><div><small>{event.date}</small><strong>{event.title}</strong><p>{event.detail}</p></div></div>)}</div></section>}
        {!loading && !error && activeView !== "Health history" && <section className="content-grid"><article className="panel reports-panel"><div className="panel-heading"><div><p className="eyebrow">YOUR RECORD</p><h2>{activeView === "My reports" ? "All reports" : "Recent reports"}</h2></div><span className="report-count">{reports.length} reports</span></div><div className="report-list">{reports.map((report) => <button className="report-row" key={report.id} onClick={() => setSelectedReport(report)}><span className="file-icon">▤</span><span className="report-info"><strong>{report.name}</strong><small>{report.date} <b>·</b> {report.tests} tests</small></span><span className={`pill ${report.tone}`}>{report.status}</span><span className="row-arrow">›</span></button>)}</div></article><article className="panel understanding-panel"><div className="panel-heading"><div><p className="eyebrow">PLAIN ENGLISH</p><h2>Understanding your results</h2></div><span className="sparkle">✦</span></div><p className="large-copy">Your latest report looks reassuring overall. Most of your results are within the expected range for your profile.</p><div className="tip"><span>i</span><p>Keeping a regular record helps you and your clinician notice changes over time.</p></div><button className="secondary-button" onClick={() => changeView("Health history")}>Explore health history <span>→</span></button></article></section>}
        <footer className="disclaimer">MediClear helps you understand your reports in plain English. It does not diagnose conditions or replace advice from your healthcare professional.</footer>
      </main>

      {showUpload && <div className="modal-backdrop" onClick={() => setShowUpload(false)}><div className="upload-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setShowUpload(false)} aria-label="Close upload dialog">×</button><span className="upload-icon">↑</span><h2>Upload a lab report</h2><p>Choose a PDF or image of your report to get a plain-English summary.</p><label className="drop-zone"><strong>Drop your file here</strong><span>or click to browse from your device</span><input type="file" accept=".pdf,.jpg,.jpeg,.png" /></label><button className="secondary-button" onClick={() => setShowUpload(false)}>Cancel</button></div></div>}
      {selectedReport && <div className="modal-backdrop" onClick={() => setSelectedReport(null)}><div className="upload-modal report-detail" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setSelectedReport(null)} aria-label="Close report details">×</button><p className="eyebrow">REPORT DETAILS</p><h2>{selectedReport.name}</h2><p>{selectedReport.date} · {selectedReport.tests} tests</p><div className={`detail-status ${selectedReport.tone}`}>{selectedReport.status}</div><p className="large-copy">{selectedReport.summary} Your report is ready to discuss with your healthcare professional.</p><button className="secondary-button" onClick={() => setSelectedReport(null)}>Close</button></div></div>}
    </div>
  );
}

export default App;
