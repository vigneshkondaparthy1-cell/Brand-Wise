import re
import os
import shutil

print("Building enhanced The-Final-Draft-Hackathon-Updated.html...")

# We will construct the complete HTML document with all PDF features integrated seamlessly into the exact 4-image layout.
HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1" name="viewport"/>
<meta content="#e6e9f2" name="theme-color"/>
<title>Brand Wise — Brand Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,700;0,800;0,900;1,800&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">

<script>
try {
  if (localStorage.getItem('brandwise-theme') === 'dark') {
    document.documentElement.dataset.theme = 'dark';
  }
} catch {}
</script>
<style>
:root {
  --bg: #e6e9f2;
  --shell: #f4f5fa;
  --card-bg: #ffffff;
  --card-elevated: #f8f9fd;
  --card-subtle: #edf0f7;
  --line: #d8deeb;
  --line-strong: #c2ccdf;
  
  --navy: #102238;
  --text: #14253d;
  --text-muted: #677790;
  --text-dim: #8b99ad;
  
  --blue: #0073cc;
  --blue-hover: #0060aa;
  --blue-light: #e6f1fb;
  --blue-glow: rgba(0, 115, 204, 0.22);
  
  --orange: #f26b1d;
  --orange-hover: #dc5c11;
  --orange-light: #fef0e7;
  
  --green: #10b981;
  --green-light: #e8f8f2;
  --red: #eb4444;
  --red-light: #fde8e8;
  --amber: #f59e0b;
  --amber-light: #fef3c7;
  
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 22px;
  --radius-xl: 32px;
  --radius-pill: 999px;
  
  --shadow-subtle: 0 4px 18px rgba(16, 34, 56, 0.04);
  --shadow-card: 0 8px 30px rgba(16, 34, 56, 0.06);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-size: 13px;
  line-height: 1.55;
  min-height: 100vh;
  display: flex;
  overflow-x: hidden;
}

h1, h2, h3, h4, .brand-font {
  font-family: 'Barlow Condensed', Impact, sans-serif;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.025em;
  color: var(--navy);
}
h1 { font-size: 52px; line-height: 0.94; }
h2 { font-size: 26px; line-height: 1.1; }
h3 { font-size: 18px; font-weight: 800; }
p { color: var(--text-muted); }
button, a { cursor: pointer; text-decoration: none; font-family: inherit; transition: all .16s ease; }
input, select, textarea { font-family: inherit; font-size: 13px; color: var(--text); background: var(--card-bg); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 8px 12px; outline: none; }
input:focus, select:focus, textarea:focus { border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-glow); }

/* Sidebar */
.sidebar {
  width: 215px;
  flex-shrink: 0;
  background: var(--card-elevated);
  border-right: 1px solid var(--line);
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  z-index: 20;
}
.brand-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}
.brand-logo-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #0073cc;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  box-shadow: 0 4px 10px var(--blue-glow);
}
.brand-title {
  font-size: 16px;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--navy);
  line-height: 1;
}
.brand-subtitle {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--blue-text, var(--blue));
  text-transform: uppercase;
  margin-top: 2px;
}

.workspace-status-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: var(--card-bg);
  border: 1px solid var(--line);
  padding: 5px 8px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  white-space: nowrap;
  margin-bottom: 24px;
}
.workspace-status-badge .pill-val {
  flex-shrink: 0;
  background: var(--orange-light);
  color: var(--orange);
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  font-weight: 800;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 10px 14px;
  border-radius: var(--radius-pill);
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
  position: relative;
}
.nav-link:hover {
  background: var(--card-subtle);
  color: var(--navy);
}
.nav-link.active {
  background: var(--blue);
  color: #ffffff;
  box-shadow: 0 4px 12px var(--blue-glow);
}
.nav-link svg { width: 17px; height: 17px; flex-shrink: 0; }

.sidebar-bottom-score {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: auto;
}
.score-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}
.score-header small {
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-dim);
}
.score-header strong {
  font-family: 'Barlow Condensed', sans-serif;
  font-size: 22px;
  font-weight: 900;
  color: var(--blue-text, var(--blue));
}
.sidebar-progress-track {
  height: 5px;
  background: var(--card-subtle);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.sidebar-progress-fill {
  width: 98.4%;
  height: 100%;
  background: var(--blue);
  border-radius: var(--radius-pill);
}
.score-subtext {
  font-size: 10.5px;
  color: var(--text-dim);
  line-height: 1.3;
}

/* Main Canvas Wrapper */
.main-wrapper {
  flex: 1;
  min-width: 0;
  padding: 14px 22px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Top Bar */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px;
  height: 44px;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card-elevated);
  border: 1px solid var(--line);
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  font-size: 11.5px;
  color: var(--text-muted);
  font-weight: 600;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.btn-support {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-muted);
  padding: 6px 12px;
}
.btn-quick-scan {
  background: var(--orange);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 8px 18px;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 14px rgba(242, 107, 29, 0.28);
}
.btn-quick-scan:hover { background: var(--orange-hover); transform: translateY(-1px); }
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #112a4c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 11.5px;
}

/* Giant Main Shell Card */
.page-shell {
  background: var(--card-elevated);
  border: 1px solid var(--line);
  border-radius: var(--radius-xl);
  padding: 34px 40px;
  box-shadow: var(--shadow-card);
  min-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.page-shell[hidden] { display: none !important; }

/* Sub-header Pills row */
.kicker-pills {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.pill-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 11px;
  border-radius: var(--radius-pill);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: none;
  cursor: pointer;
}
.pill-blue { background: var(--blue-light); color: var(--blue-text, var(--blue)); }
.pill-orange { background: var(--orange-light); color: var(--orange); }
.pill-gray { background: var(--card-subtle); color: var(--text-muted); }
.pill-green { background: var(--green-light); color: var(--green); }
.pill-tag.active {
  background: var(--blue) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 8px var(--blue-glow);
}

/* Buttons & Badges */
.btn-pill-primary {
  background: var(--blue);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 8px 18px;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 12px var(--blue-glow);
  border: none;
}
.btn-pill-primary:hover { background: var(--blue-hover); transform: translateY(-1px); }
.btn-pill-orange {
  background: var(--orange);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 8px 18px;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 12px rgba(242, 107, 29, 0.25);
  border: none;
}
.btn-pill-orange:hover { background: var(--orange-hover); transform: translateY(-1px); }
.btn-pill-ghost {
  background: var(--card-bg);
  border: 1px solid var(--line);
  color: var(--text);
  border-radius: var(--radius-pill);
  padding: 8px 16px;
  font-size: 11.5px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-pill-ghost:hover { background: var(--card-subtle); border-color: var(--line-strong); }

/* Common Panels */
.white-panel {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 22px;
  box-shadow: var(--shadow-subtle);
}

/* ========================================================================= */
/* TAB 1: AUDIT WORKSPACE (IMAGE 2)                                         */
/* ========================================================================= */
.hero-center {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 10px 0 16px;
  position: relative;
}
.hero-center h1 {
  font-size: 64px;
  max-width: 680px;
}
.hero-center h1 em { font-style: normal; color: var(--blue-text, var(--blue)); }
.hero-center h1 b { color: var(--orange); }
.hero-center p {
  max-width: 600px;
  font-size: 13.5px;
  line-height: 1.6;
}

.spec-badges-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.spec-badge {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-pill);
  padding: 6px 14px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 6px;
}

.workspace-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: stretch;
}
.panel-kicker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.panel-kicker-head h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  text-transform: none;
}
.panel-kicker-head h3 span.badge-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #112a4c;
  color: #fff;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.workspace-textarea {
  width: 100%;
  min-height: 165px;
  background: var(--card-elevated);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px;
  font-size: 13px;
  line-height: 1.65;
  resize: vertical;
}

.report-breakdown-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 14px 0;
}
.report-bar-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.report-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
}
.report-track {
  height: 6px;
  background: var(--card-subtle);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.report-fill {
  height: 100%;
  border-radius: var(--radius-pill);
}

.suggestion-box {
  background: var(--amber-light);
  border: 1px solid #fae4be;
  border-radius: var(--radius-md);
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11.5px;
  color: light-dark(#8c5b05, #f8c767);
}

.giant-audit-btn-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}
.giant-audit-btn {
  background: var(--blue);
  color: #fff;
  border-radius: var(--radius-pill);
  padding: 16px 42px;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 8px 24px var(--blue-glow);
  border: none;
}
.giant-audit-btn:hover { background: var(--blue-hover); transform: translateY(-2px); }

/* Findings List inside Panel 02 */
.findings-accordion {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  max-height: 240px;
  overflow-y: auto;
}
.finding-card-item {
  background: var(--card-elevated);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11.5px;
}
.finding-card-item.sev-critical { border-left: 3px solid var(--red); }
.finding-card-item.sev-high { border-left: 3px solid var(--orange); }
.finding-card-item.sev-medium { border-left: 3px solid var(--amber); }
.finding-card-item.sev-low { border-left: 3px solid var(--blue); }

/* ========================================================================= */
/* TAB 2: OFFICIAL GUIDELINES (IMAGE 3)                                     */
/* ========================================================================= */
.guidelines-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.95fr;
  gap: 20px;
}
.rule-item-box {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
  position: relative;
}
.rule-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rule-item-header small {
  font-size: 9.5px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-dim);
}

.drop-doc-zone {
  border: 2px dashed #c8d3e8;
  border-radius: var(--radius-lg);
  padding: 30px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: var(--card-elevated);
  cursor: pointer;
  transition: all .2s ease;
}
.drop-doc-zone.dragover {
  border-color: var(--blue);
  background: var(--blue-light);
}

.banner-playful {
  background: linear-gradient(135deg, #102644, #19385f);
  color: #fff;
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  position: relative;
  overflow: hidden;
}
.banner-playful h4 {
  color: #fff;
  font-size: 20px;
  margin-bottom: 4px;
}
.banner-playful p {
  color: #b0c5e2;
  font-size: 11.5px;
}

/* ========================================================================= */
/* TAB 3: AUDIT HISTORY & INSIGHTS (IMAGE 1)                                */
/* ========================================================================= */
.four-stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.stat-box {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-box.highlight-blue {
  background: var(--blue);
  color: #ffffff;
  border-color: var(--blue);
}
.stat-box.highlight-blue p, .stat-box.highlight-blue small { color: #d0e4f7; }
.stat-box.highlight-blue strong { color: #ffffff; }

.charts-split {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 18px;
}
.chart-card {
  background: var(--card-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Table in Audit Archive Log */
.table-container {
  overflow-x: auto;
  margin-top: 10px;
}
table.styled-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  text-align: left;
}
table.styled-table th {
  padding: 10px 12px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-dim);
  border-bottom: 1px solid var(--line);
}
table.styled-table td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--line);
  vertical-align: middle;
}
table.styled-table tr:hover td { background: var(--card-elevated); }

/* Sub-views under Audit History */
.history-subview { display: none; }
.history-subview.active { display: block; }

/* ========================================================================= */
/* TAB 4: WORKSPACE SETTINGS (IMAGE 4)                                      */
/* ========================================================================= */
.settings-split-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}
.settings-nav-pane {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.settings-tab-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-align: left;
  border: none;
  background: transparent;
}
.settings-tab-btn:hover { background: var(--card-subtle); color: var(--navy); }
.settings-tab-btn.active {
  background: var(--blue);
  color: #fff;
}

.tiles-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.segmented-control {
  display: flex;
  background: var(--card-subtle);
  border-radius: var(--radius-pill);
  padding: 4px;
  gap: 4px;
}
.seg-btn {
  flex: 1;
  padding: 7px 12px;
  text-align: center;
  border-radius: var(--radius-pill);
  font-size: 11.5px;
  font-weight: 700;
  color: var(--text-muted);
  border: none;
  background: transparent;
}
.seg-btn.active {
  background: var(--blue);
  color: #fff;
  box-shadow: 0 2px 8px var(--blue-glow);
}

/* Modal System */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(16, 34, 56, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  pointer-events: none;
  transition: opacity .2s ease;
  padding: 20px;
}
.modal-overlay.open {
  opacity: 1;
  pointer-events: auto;
}
.modal-card {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  border: 1px solid var(--line);
  box-shadow: 0 20px 50px rgba(16, 34, 56, 0.16);
  width: 100%;
  max-width: 760px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  padding: 28px 32px;
  gap: 18px;
  transform: translateY(12px);
  transition: transform .2s ease;
}
.modal-overlay.open .modal-card {
  transform: translateY(0);
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding-bottom: 14px;
}
.modal-header h3 {
  font-size: 20px;
  color: var(--navy);
  margin: 0;
}
.btn-close-modal {
  background: var(--card-subtle);
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
}
.btn-close-modal:hover { background: var(--card-subtle); color: var(--navy); }

/* Toast */
#toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #112a4c;
  color: #fff;
  padding: 12px 20px;
  border-radius: var(--radius-pill);
  font-size: 12.5px;
  font-weight: 600;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 9999;
  opacity: 0;
  transform: translateY(10px);
  pointer-events: none;
  transition: all .2s;
}
#toast.show { opacity: 1; transform: translateY(0); pointer-events: auto; }

@media (max-width: 1050px) {
  body { flex-direction: column; }
  .sidebar {
    width: 100%;
    height: auto;
    position: static;
    padding: 14px 18px;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }
  .sidebar .brand-header { margin-bottom: 12px; }
  .sidebar-nav { flex-direction: row; flex-wrap: wrap; }
  .workspace-status-badge, .sidebar-bottom-score { display: none; }
  .topbar { height: auto; gap: 10px; flex-wrap: wrap; }
  .topbar-right { min-width: 0; flex-wrap: wrap; }
  .topbar-left svg, .topbar-right svg, .user-avatar { flex-shrink: 0; }
  .workspace-split, .charts-split, .guidelines-grid, .settings-split-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .four-stat-cards, .tiles-grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .sidebar { padding: 12px; }
  .sidebar-nav { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .nav-link { padding: 8px 10px; gap: 7px; line-height: 1.3; }
  .nav-link svg { flex-shrink: 0; }
  .main-wrapper { padding: 12px 10px 20px; gap: 12px; }
  .topbar { padding: 0; }
  .topbar-left { padding: 5px 10px; }
  .topbar-right { width: 100%; gap: 7px; }
  #userRoleSelect { max-width: 100%; }
  .page-shell { padding: 18px 14px; gap: 18px; border-radius: var(--radius-lg); }
  .hero-center { padding: 4px 0 8px; }
  .hero-center h1 { font-size: clamp(34px, 9vw, 52px); }
  .hero-center > div:first-child > span { display: none; }
  .tiles-grid-2, .mobile-stack { grid-template-columns: minmax(0, 1fr) !important; }
  .four-stat-cards > *, .page-shell .white-panel { min-width: 0; }
  .settings-nav-pane { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .table-container { max-width: 100%; overflow-x: auto; }
}
@media (max-width: 360px) {
  .four-stat-cards { grid-template-columns: minmax(0, 1fr); }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #101622;
  --shell: #151e2c;
  --card-bg: #1b2637;
  --card-elevated: #202e40;
  --card-subtle: #26354a;
  --line: #34445b;
  --line-strong: #495d77;
  --navy: #f0f5fd;
  --text: #e0e9f5;
  --text-muted: #acbed4;
  --text-dim: #99adc5;
  --blue-light: #203c58;
  --blue-text: #83c7ff;
  --orange-light: #432c21;
  --green-light: #19382e;
  --red-light: #47292f;
  --amber-light: #413522;
  --orange: #ff995e;
  --green: #61dbab;
  --red: #ff939a;
  --amber: #f8c767;
  --shadow-subtle: 0 4px 18px #0003;
  --shadow-card: 0 8px 30px #0004;
}
:root[data-theme="dark"] .pill-blue,
:root[data-theme="dark"] .btn-pill-ghost { color: #83c7ff; }
#appearancePanel { padding: 20px; }
#appearancePanel label { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 12px; }
.architecture-stage { display: grid; grid-template-columns: 74px minmax(0, 1fr); align-items: start; gap: 12px; padding: 12px 14px; border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--card-elevated); }
.architecture-stage .pill-tag { justify-self: start; white-space: nowrap; font-size: 10px; }
.architecture-stage > div { color: var(--text-muted); overflow-wrap: anywhere; }
.architecture-stage b { display: block; margin-bottom: 2px; color: var(--navy); }
@media (max-width: 420px) { .architecture-stage { grid-template-columns: minmax(0, 1fr); gap: 6px; } }
#userRoleSelect option { background-color: var(--card-bg); color: var(--text); }
</style>
</head>
<body>

<!-- Left Sidebar matching all 4 images -->
<aside class="sidebar">
  <div class="brand-header">
    <div class="brand-logo-circle">
      <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
    </div>
    <div>
      <div class="brand-title">BRAND WISE</div>
      <div class="brand-subtitle">BRAND INTELLIGENCE</div>
    </div>
  </div>

  <div class="workspace-status-badge">
    <span>WORKSPACE STATUS</span>
    <span class="pill-val">LIVE 2.4</span>
  </div>

  <nav class="sidebar-nav">
    <a href="#workspace" class="nav-link active" data-tab="workspace">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      Audit Workspace
    </a>
    <a href="#guidelines" class="nav-link" data-tab="guidelines">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      Official Guidelines
    </a>
    <a href="#history" class="nav-link" data-tab="history">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      Audit History
    </a>
    <a href="#settings" class="nav-link" data-tab="settings">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
      Settings
    </a>
  </nav>

  <div class="sidebar-bottom-score">
    <div class="score-header">
      <small>COMPLIANCE SCORE</small>
      <strong id="sidebarComplianceVal">98.4%</strong>
    </div>
    <div class="sidebar-progress-track">
      <div class="sidebar-progress-fill"></div>
    </div>
    <div class="score-subtext">34 brand assets aligned with Q3 corporate standards</div>
  </div>
</aside>

<!-- Main Wrapper -->
<div class="main-wrapper">
  <!-- Top Bar -->
  <header class="topbar">
    <div class="topbar-left">
      <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/></svg>
      <span>System Engine: Generative Compliance 2.1</span>
    </div>

    <div class="topbar-right">
      <!-- Role Switcher Navigation (Creator, Agency, Reviewer, Brand Manager, Admin) -->
      <div style="display:flex;align-items:center;gap:6px;background:var(--card-elevated);border:1px solid var(--line);padding:3px 10px;border-radius:var(--radius-pill);font-size:11px;font-weight:700;">
        <span style="color:var(--text-dim);font-size:9.5px;letter-spacing:0.04em;">ROLE:</span>
        <select id="userRoleSelect" style="border:none;background:transparent;padding:2px 4px;font-size:11.5px;font-weight:700;color:var(--navy);cursor:pointer;outline:none;">
          <option value="Creator">✍️ Creator</option>
          <option value="External Agency">🏢 External Agency</option>
          <option value="Reviewer">🔍 Reviewer / Legal</option>
          <option value="Brand Manager">⭐ Brand Manager</option>
          <option value="Admin">⚙️ Admin</option>
        </select>
        <span id="roleScopeTag" class="pill-tag pill-orange" style="display:none;font-size:8.5px;padding:2px 6px;">SCOPED</span>
      </div>

      <button class="btn-support" type="button" id="btnTopSupport">
        <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
        Support
      </button>

      <button class="btn-quick-scan" id="btnTopQuickScan" type="button">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
        Run Quick Scan
      </button>

      <div class="user-avatar" id="topAvatar">A</div>
    </div>
  </header>

  <!-- ========================================================================= -->
  <!-- TAB 1: AUDIT WORKSPACE (IMAGE 2)                                         -->
  <!-- ========================================================================= -->
  <main class="page-shell" id="view-workspace">
    <div class="kicker-pills" style="justify-content:center;">
      <button type="button" class="pill-tag pill-blue active" id="subtab-ws-live">📍 Live Workspace</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-diff">⚖️ Version Diff (v1 vs v2)</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-wcag">🎨 WCAG &amp; Contrast Studio</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-arch">📜 9-Stage Architecture</button>
    </div>

    <!-- Centered Hero -->
    <div class="hero-center">
      <div style="position:relative;display:inline-block;">
        <span style="position:absolute;left:-44px;top:-10px;font-size:24px;">👀</span>
        <h1>WE VERIFY<br><em>CONTENT PEOPLE</em><br><b>LOVE.</b></h1>
        <span style="position:absolute;right:-60px;top:0;font-size:12px;background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-pill);padding:4px 9px;font-weight:700;">🌈 FAST SCAN</span>
      </div>
      <p>Every statement deserves ammo, and a foundation. Audit digital claims, typography licenses, and brand assertions in real-time with cartoon clarity.</p>
      
      <div class="spec-badges-row">
        <span class="spec-badge">🛡 98.4% Precision Model</span>
        <span class="spec-badge">⚡ Instant Verification</span>
        <span class="spec-badge">⏱ &lt; 100ms Engine Speed</span>
      </div>
    </div>

    <!-- Content to Check vs Audit Report (Split Grid) -->
    <div class="workspace-split">
      <!-- 01 Content to Check -->
      <div class="white-panel" style="display:flex;flex-direction:column;gap:12px;">
        <div class="panel-kicker-head">
          <h3><span class="badge-num">01</span> Content To Check</h3>
          <span class="pill-tag pill-orange" id="docStatePill">UNDER REVIEW</span>
        </div>
        <p style="font-size:12px;color:var(--text-muted);">Draft claims, advertising hooks, and hero statements for automated compliance verification.</p>
        
        <textarea class="workspace-textarea" id="workspaceInput" placeholder="Paste marketing copy here...">"Lofty Creative Lab guarantees 10x faster engagement across omni-channel campaigns using patented generative creative synthesis with 100% cloud zero-carbon footprint."</textarea>
        
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--text-dim);">
          <span id="charCountLabel">⏱ 18 words · text pasted</span>
          <span>14 min</span>
        </div>

        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:10.5px;" id="btnLoadShortNote" title="Approved Claim CLM-001 with up to 20%">Short Note</button>
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:10.5px;" id="btnLoadInstagram" title="Indian English fairness test without tone penalties">Instagram Post</button>
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:10.5px;" id="btnLoadAdHeadline" title="Overpromising 10x claim with replacement">Ad Headline</button>
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:10.5px;" id="btnLoadPrivacy" title="Expired pricing claim CLM-005 ($49/mo) and corporate founding year">Privacy Review</button>
        </div>

        <div style="display:flex;gap:8px;margin-top:6px;border-top:1px dashed var(--line);padding-top:10px;">
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:11px;" id="btnOpenDiffFromPanel">⚖️ View Revision Diff</button>
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:11px;" id="btnOpenWcagFromPanel">🎨 Test WCAG Contrast</button>
        </div>
      </div>

      <!-- 02 Audit Report -->
      <div class="white-panel" style="display:flex;flex-direction:column;justify-content:space-between;">
        <div>
          <div class="panel-kicker-head">
            <h3><span class="badge-num">02</span> Audit Report</h3>
            <span class="pill-tag pill-blue" id="reportHeaderBadge">READY FOR REVIEW</span>
          </div>

          <div style="display:flex;align-items:baseline;justify-content:space-between;margin:10px 0 6px;">
            <div>
              <small style="font-size:10px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">CONFIDENCE SCORE</small>
              <div style="font-family:'Barlow Condensed',sans-serif;font-size:36px;font-weight:900;color:var(--navy);line-height:1;" id="reportConfidenceVal">94.8% <span style="font-size:12px;font-family:'Inter',sans-serif;font-weight:600;color:var(--text-muted);">Passed Level 2</span></div>
            </div>
            <div style="width:28px;height:28px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
          </div>

          <!-- 6-State Governance Lifecycle Controller -->
          <div style="display:flex;align-items:center;justify-content:space-between;background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-pill);padding:4px 10px;margin-bottom:12px;font-size:11px;">
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:9.5px;font-weight:800;color:var(--text-dim);text-transform:uppercase;">STAGE:</span>
              <span class="pill-tag pill-orange" id="lifecycleBadge" style="font-size:9px;padding:2px 8px;">In review</span>
            </div>
            <div style="display:flex;gap:4px;" id="governanceActionButtons">
              <button type="button" class="btn-pill-ghost" style="padding:2px 8px;font-size:10px;" id="btnReqChanges">Request Changes</button>
              <button type="button" class="btn-pill-primary" style="padding:2px 8px;font-size:10px;" id="btnApproveDraft">Approve</button>
              <button type="button" class="btn-pill-orange" style="padding:2px 8px;font-size:10px;" id="btnPublishDraft">Publish</button>
            </div>
          </div>

          <div class="report-breakdown-row">
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Factual Substantiation</span><span style="color:var(--green)" id="bar1Label">89% Verified</span></div>
              <div class="report-track"><div class="report-fill" id="bar1Fill" style="width:89%;background:var(--green);"></div></div>
            </div>
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Zero-Overpromising Standard</span><span style="color:var(--orange)" id="bar2Label">Needs Review</span></div>
              <div class="report-track"><div class="report-fill" id="bar2Fill" style="width:65%;background:var(--orange);"></div></div>
            </div>
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Trademark &amp; Asset Clarity</span><span style="color:var(--blue-text, var(--blue))" id="bar3Label">100% Ideal</span></div>
              <div class="report-track"><div class="report-fill" id="bar3Fill" style="width:100%;background:var(--blue);"></div></div>
            </div>
          </div>

          <!-- Suggestion Box with One-Click Fix -->
          <div class="suggestion-box" id="reportSuggestionBox">
            <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
            <div style="flex:1;">
              <b>Suggestion:</b> Replace <i>"guarantees 10x"</i> with <i>"accelerates engagement by up to 20%"</i> (Backed by Claim CLM-001).
              <div style="margin-top:6px;">
                <button type="button" class="btn-pill-orange" style="padding:2px 8px;font-size:10px;" id="btnApplyTopFix">Apply One-Click Fix</button>
              </div>
            </div>
          </div>

          <!-- Dynamic Findings Accordion -->
          <div class="findings-accordion" id="findingsContainer">
            <!-- Rendered dynamically -->
          </div>
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:12px;border-top:1px solid var(--line);font-size:11px;color:var(--text-dim);">
          <span id="analysisTimingLabel">⚡ Analyzed in 92 milliseconds</span>
          <button type="button" class="btn-pill-ghost" style="padding:4px 10px;font-size:10px;" id="btnExportPDF">EXPORT PDF</button>
        </div>
      </div>
    </div>

    <!-- Centered Giant Audit Content Action -->
    <div class="giant-audit-btn-wrap">
      <button class="giant-audit-btn" id="btnAuditContent" type="button">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        AUDIT CONTENT ➔
      </button>
      <span style="font-size:10px;font-weight:700;letter-spacing:0.12em;color:var(--text-dim);">GROUP · GOLD WATERBRAND 2.0</span>
    </div>

    <div style="text-align:center;font-size:11px;color:var(--text-dim);margin-top:4px;">
      ● CHECKING AGAINST 14 COMPANY FRAMEWORKS: ISO 27001, FTC Guidelines, SOC 2 Type Claims, Brand Voice 3.2
    </div>
  </main>

  <!-- ========================================================================= -->
  <!-- TAB 2: OFFICIAL GUIDELINES (IMAGE 3)                                     -->
  <!-- ========================================================================= -->
  <main class="page-shell" id="view-guidelines" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;">
          <span class="pill-tag pill-orange">v2.4 LIVE</span>
          <span class="pill-tag pill-blue">Source of Truth</span>
          <span class="pill-tag pill-gray">Updated 2d ago</span>
        </div>
        <h1>OFFICIAL GUIDELINES</h1>
        <p>Your approved facts, core messaging rules, and legal guardrails in one playful spot.</p>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn-pill-primary" id="btnGuidelinesScan">Quick Scan</button>
        <button class="btn-pill-ghost" id="btnJsonWebhookModal">JSON Webhook</button>
        <button class="btn-pill-ghost" id="btnExportApiBtn">Export API</button>
      </div>
    </div>

    <!-- Category selector pills (Clickable category filter) -->
    <div class="kicker-pills" style="border-bottom:1px solid var(--line);padding-bottom:12px;">
      <span style="font-size:10px;font-weight:800;text-transform:uppercase;color:var(--text-dim);margin-right:6px;">CATEGORIES:</span>
      <button type="button" class="pill-tag pill-blue active" data-glcat="all">All Rules</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="company">Company Identity</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="claims">Approved Claims Ledger</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="prohibited">Prohibited Words</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="legal">Legal Disclaimers</button>
    </div>

    <div class="guidelines-grid">
      <!-- Left Column: Core Truth Ledger -->
      <div class="white-panel">
        <div class="panel-kicker-head">
          <h3><span class="badge-num" style="background:var(--blue);">✓</span> Core Truth Ledger</h3>
          <span style="font-size:10.5px;color:var(--text-dim);font-weight:700;">SYNC: ACTIVE</span>
        </div>
        <p style="font-size:11.5px;color:var(--text-muted);margin-bottom:14px;">Active schema persistently validated on all copy.</p>

        <div id="guidelinesRulesList">
          <!-- Rule 1: Official Entity -->
          <div class="rule-item-box" data-rule-cat="company">
            <div class="rule-item-header">
              <small>OFFICIAL ENTITY</small>
              <span class="pill-tag pill-blue" style="font-size:9px;">Live in Core Flow</span>
            </div>
            <div style="font-size:15px;font-weight:800;color:var(--navy);">Acme Technologies</div>
            <div style="font-size:11px;color:var(--text-muted);">Verified corporate legal name. Never shorten to 'Acme Tech' in outward releases.</div>
          </div>

          <!-- Rule 2: Foundation Year -->
          <div class="rule-item-box" data-rule-cat="company">
            <div class="rule-item-header">
              <small>FOUNDATION YEAR</small>
              <span class="pill-tag pill-gray" style="font-size:9px;">Enforced Fact</span>
            </div>
            <div style="font-size:15px;font-weight:800;color:var(--navy);">2012</div>
            <div style="font-size:11px;color:var(--text-muted);">Citation: Delaware Certificate of Incorporation #4829104.</div>
          </div>

          <!-- Rule 3: Approved Claims -->
          <div class="rule-item-box" data-rule-cat="claims">
            <div class="rule-item-header">
              <small>APPROVED CLAIMS · CLM-001</small>
              <span class="pill-tag pill-blue" style="font-size:9px;">Product Performance</span>
            </div>
            <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;">Cuts onboarding time by up to 20%</div>
            <div style="font-size:11.5px;color:var(--text-muted);">
              Evidence: 2026 Enterprise Benchmark Study, Section 4.2. Owner: Sarah Jenkins (VP Product). Expiry: 2027-12-31.
            </div>
          </div>

          <!-- Rule 4: Expired Claim Demo -->
          <div class="rule-item-box" data-rule-cat="claims" style="background:var(--red-light);border-color:light-dark(#fbd8d8, #495064);">
            <div class="rule-item-header">
              <small style="color:var(--red);">EXPIRED CLAIM · CLM-005</small>
              <span class="pill-tag pill-orange" style="background:var(--red-light);color:var(--red);font-size:9px;">EXPIRED · NEEDS HUMAN CHECK</span>
            </div>
            <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;">Starter tiers start at $49/month</div>
            <div style="font-size:11.5px;color:var(--text-muted);">
              Superseded by 2026 Price Book ($79/mo). If referenced, system flags: <i>"Cannot verify — needs human check"</i>.
            </div>
          </div>

          <!-- Rule 5: Required Disclaimer -->
          <div class="rule-item-box" data-rule-cat="legal" style="background:var(--card-elevated);border-color:light-dark(#fce4d4, #495064);">
            <div class="rule-item-header">
              <small style="color:var(--orange);">REQUIRED DISCLAIMER</small>
              <span class="pill-tag pill-orange" style="font-size:9px;">FOOTER/LEGAL</span>
            </div>
            <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;">Terms and conditions apply.</div>
            <div style="font-size:11px;color:var(--orange);">Affixed to all CTAs. Enforced in external and promotional channels.</div>
          </div>
        </div>

        <div style="display:flex;gap:10px;margin-top:14px;">
          <button class="btn-pill-orange" id="btnAddRuleBtn" type="button">+ Add New Rule</button>
          <button class="btn-pill-primary" id="btnSaveGuidelinesBtn" type="button">Save Guidelines</button>
        </div>
      </div>

      <!-- Right Column: Docs Drop, Coverage & Playful Banner -->
      <div style="display:flex;flex-direction:column;gap:16px;">
        <!-- Drop docs zone -->
        <div class="drop-doc-zone" id="dropDocZone">
          <input type="file" id="fileDocUpload" style="display:none;" accept=".pdf,.docx,.txt,.json,.md">
          <div style="width:40px;height:40px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
          </div>
          <div style="font-weight:700;font-size:13px;color:var(--navy);">Drop company docs here</div>
          <p style="font-size:11px;">or browse from file agent workspace</p>
          <div style="display:flex;gap:6px;font-size:9.5px;font-weight:700;color:var(--text-dim);">
            <span>PDF</span> · <span>DOCX</span> · <span>GOOGLEDOC</span> · <span>SLIDES</span>
          </div>
          <button class="btn-pill-primary" style="padding:6px 16px;font-size:11.5px;margin-top:4px;" type="button" id="btnSelectFileDoc">Select File</button>
        </div>

        <!-- Rule Coverage -->
        <div class="white-panel" style="padding:16px 20px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <b style="font-size:12px;">Rule Coverage</b>
            <span style="font-size:10px;color:var(--green);font-weight:700;">6/6 Safeguards Complete</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;font-size:11.5px;">
            <div style="display:flex;justify-content:space-between;"><span>Company Identity</span><b>100%</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Approved Claims</span><b style="color:var(--blue-text, var(--blue));">6 Active / 1 Expired</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Prohibited Words</span><b style="color:var(--orange);">14 Rules</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Legal Disclaimers</span><b style="color:var(--green);">Active &amp; Enforced</b></div>
          </div>
          <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;font-size:10.5px;color:var(--text-dim);">
            <div style="width:16px;height:16px;border-radius:50%;border:2px solid var(--blue);border-top-color:transparent;animation:spin 1s linear infinite;"></div>
            <span>Auto-Syncing: Changes reflect immediately in production audits.</span>
          </div>
        </div>

        <!-- Playful Banner -->
        <div class="banner-playful">
          <small style="font-size:9px;font-weight:800;letter-spacing:0.1em;color:var(--orange);text-transform:uppercase;">PLAYFUL FACT</small>
          <h4>NO BORING POLICIES.</h4>
          <p>Creative freedom lives inside crystal clear boundaries.</p>
        </div>
      </div>
    </div>

    <!-- Disallowed Vocabulary Footer Strip -->
    <div class="white-panel" style="padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
      <div style="display:flex;align-items:center;gap:10px;">
        <span class="pill-tag pill-orange">DISALLOWED VOCABULARY</span>
        <span style="font-size:11.5px;color:var(--text-muted);">Flagged automatically during scans:</span>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;" id="disallowedPills">
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">guaranteed</span>
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">flawless</span>
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">mega</span>
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">#1</span>
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">Brandwise</span>
        <span class="pill-tag pill-gray" style="text-decoration:line-through;color:var(--red);">world's leading</span>
      </div>
    </div>

    <div style="font-size:11px;color:var(--text-dim);display:flex;justify-content:space-between;">
      <span>💡 Pro-Tip: The scanner engine reads Indian English phrases ('prepone', 'revert back') contextually without penalization.</span>
      <a href="#" style="color:var(--blue-text, var(--blue));font-weight:600;" id="btnIndianEnglishNote">Read Guidance</a>
    </div>
  </main>

  <!-- ========================================================================= -->
  <!-- TAB 3: AUDIT HISTORY & INSIGHTS (IMAGE 1)                                -->
  <!-- ========================================================================= -->
  <main class="page-shell" id="view-history" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;">
          <button type="button" class="pill-tag pill-blue active" id="subtab-hist-archive">● LIVE ARCHIVE</button>
          <button type="button" class="pill-tag pill-orange" id="subtab-hist-ambiguous">● AMBIGUOUS RULES</button>
          <button type="button" class="pill-tag pill-gray" id="subtab-hist-agency">● AGENCY BENCHMARKS</button>
          <button type="button" class="pill-tag pill-gray" id="subtab-hist-impact">● IMPACT METRICS</button>
        </div>
        <h1>AUDIT HISTORY &amp; INSIGHTS</h1>
        <p>Track past creative audits, monitor the compliance drift, and zap issues before campaigns launch to market.</p>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button class="btn-pill-ghost">📅 All time</button>
        <button class="btn-pill-ghost">⇕ Sort</button>
        <button class="btn-pill-orange" id="btnHistoryAuditNow">+ Audit Now</button>
      </div>
    </div>

    <!-- 4 Stats Tiles -->
    <div class="four-stat-cards">
      <div class="stat-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>TOTAL AUDITS</small>
          <span style="color:var(--green)">▤</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);" id="histTotalAudits">7</strong>
          <span class="pill-tag pill-blue" style="font-size:9px;">+2 this week</span>
        </div>
        <p style="font-size:11px;">Across 3 active brand workstreams</p>
      </div>

      <div class="stat-box highlight-blue">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>AVG COMPLIANCE</small>
          <span>✦</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;">81%</strong>
          <span style="font-size:10px;background:rgba(255,255,255,0.2);padding:2px 6px;border-radius:var(--radius-pill);">Target 85%</span>
        </div>
        <p style="font-size:11px;">+1.4% jump since Q1 update</p>
      </div>

      <div class="stat-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>ISSUES DETECTED</small>
          <span style="color:var(--orange)">⚠</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);">9</strong>
          <span class="pill-tag pill-orange" style="font-size:9px;">7 Resolved</span>
        </div>
        <p style="font-size:11px;">6 auto-resolutions suggested</p>
      </div>

      <div class="stat-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>PASSED AUDITS</small>
          <span style="color:var(--green)">✓</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);">4</strong>
          <span class="pill-tag pill-green" style="font-size:9px;">57.1% Pass Rate</span>
        </div>
        <p style="font-size:11px;">Strictly signed on first-pass quality</p>
      </div>
    </div>

    <!-- Charts Split -->
    <div class="charts-split">
      <!-- Trajectory Chart -->
      <div class="chart-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">TRAJECTORY</small>
            <h3 style="font-size:16px;">Compliance Health Drift</h3>
          </div>
          <div style="display:flex;gap:10px;font-size:10.5px;font-weight:600;">
            <span style="color:var(--blue-text, var(--blue))">● Score Trend</span>
            <span style="color:var(--orange)">- - Threshold (85%)</span>
          </div>
        </div>

        <svg viewBox="0 0 450 160" style="width:100%;height:160px;overflow:visible;">
          <defs>
            <linearGradient id="driftGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#0073cc" stop-opacity="0.25"/>
              <stop offset="100%" stop-color="#0073cc" stop-opacity="0.0"/>
            </linearGradient>
          </defs>
          <line x1="10" y1="35" x2="440" y2="35" stroke="var(--line)" stroke-dasharray="3 3"/>
          <line x1="10" y1="85" x2="440" y2="85" stroke="#f26b1d" stroke-dasharray="4 4" stroke-width="1.5"/>
          <line x1="10" y1="135" x2="440" y2="135" stroke="var(--line)" stroke-dasharray="3 3"/>
          <path d="M 20 120 C 100 110, 180 80, 260 70 S 370 60, 430 45 L 430 150 L 20 150 Z" fill="url(#driftGrad)"/>
          <path d="M 20 120 C 100 110, 180 80, 260 70 S 370 60, 430 45" fill="none" stroke="#0073cc" stroke-width="3" stroke-linecap="round"/>
          <circle cx="20" cy="120" r="4" fill="#0073cc" stroke="#fff" stroke-width="2"/>
          <circle cx="150" cy="95" r="4" fill="#0073cc" stroke="#fff" stroke-width="2"/>
          <circle cx="280" cy="68" r="4" fill="#0073cc" stroke="#fff" stroke-width="2"/>
          <circle cx="430" cy="45" r="5" fill="#f26b1d" stroke="#fff" stroke-width="2"/>
        </svg>

        <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-dim);font-weight:600;">
          <span>May 01 (Run 1)</span>
          <span>May 08 (Run 2)</span>
          <span>Jun 15 (Run 3)</span>
          <span style="color:var(--orange)">Today (Run 7: 78.4%)</span>
        </div>
      </div>

      <!-- Impact Focus & Distribution -->
      <div class="chart-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">IMPACT FOCUS</small>
            <h3 style="font-size:16px;">Issue Distribution</h3>
          </div>
          <span class="pill-tag pill-gray" style="font-size:9px;">7 Total</span>
        </div>
        <p style="font-size:11px;">Violations category breakdown for the Q3 Design &amp; Typography handbook.</p>

        <div style="display:flex;flex-direction:column;gap:8px;margin-top:4px;">
          <div>
            <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;">
              <span>● Critical Violations</span><span style="color:var(--red);">3 Issues</span>
            </div>
            <div class="report-track" style="margin-top:3px;"><div class="report-fill" style="width:42%;background:var(--red);"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;">
              <span>● High Severity</span><span style="color:var(--orange);">4 Issues</span>
            </div>
            <div class="report-track" style="margin-top:3px;"><div class="report-fill" style="width:57%;background:var(--orange);"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;">
              <span>● Medium Priority</span><span style="color:var(--amber);">1 Issue</span>
            </div>
            <div class="report-track" style="margin-top:3px;"><div class="report-fill" style="width:14%;background:var(--amber);"></div></div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;">
              <span>● Low Advisory</span><span style="color:var(--blue-text, var(--blue));">1 Issue</span>
            </div>
            <div class="report-track" style="margin-top:3px;"><div class="report-fill" style="width:14%;background:var(--blue);"></div></div>
          </div>
        </div>

        <div style="background:var(--amber-light);border:1px solid light-dark(#f9e2b9, #495064);border-radius:var(--radius-sm);padding:8px 12px;font-size:10.5px;color:light-dark(#855403, #f8c767);display:flex;align-items:center;gap:6px;">
          <span>📍</span>
          <span>Color contrast and <b>Hero Demand v2</b> accounts for 4 high issues</span>
        </div>
      </div>
    </div>

    <!-- SUB-VIEW 1: Audit Archive Log (Table) -->
    <div class="white-panel history-subview active" id="subview-hist-archive" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
        <div>
          <h3>Audit Archive Log</h3>
          <p style="font-size:11.5px;">Indexed historical reviews across campaigns and design systems.</p>
        </div>
        <div style="display:flex;gap:8px;">
          <input type="text" id="archiveSearch" placeholder="Search audit name or tag..." style="width:230px;border-radius:var(--radius-pill);padding:6px 14px;">
          <button class="btn-pill-ghost">Filters</button>
        </div>
      </div>

      <div class="table-container">
        <table class="styled-table">
          <thead>
            <tr>
              <th>DOCUMENT / CAMPAIGN</th>
              <th>AUDIT MODE</th>
              <th>DATE / LOGGED</th>
              <th>SCORE</th>
              <th>ISSUES</th>
              <th>STATUS</th>
              <th>ACTIONS</th>
            </tr>
          </thead>
          <tbody id="historyTableRows">
            <!-- Populated via API & Fallback -->
            <tr data-audit-id="BW-2026-001">
              <td>
                <div style="font-weight:700;color:var(--navy);">Lofty Studio Landing 2026</div>
                <div style="font-size:10.5px;color:var(--text-dim);">Production · Web + Paid Ad</div>
              </td>
              <td>Generative 2.1</td>
              <td>Today, 14:32 PST</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--navy);">98.4%</b></td>
              <td><span style="color:var(--green)">3 Solved</span></td>
              <td><span class="pill-tag pill-blue">● PASS</span></td>
              <td><button class="btn-pill-ghost btn-view-audit-report" style="padding:3px 10px;font-size:10.5px;">View Report</button></td>
            </tr>
            <tr data-audit-id="BW-2026-002">
              <td>
                <div style="font-weight:700;color:var(--navy);">Creator Billboard San/Oat</div>
                <div style="font-size:10.5px;color:var(--text-dim);">30-min trial · Display + Retails</div>
              </td>
              <td>Deep Contrast Visual</td>
              <td>Jun 24, 11:20 JST</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--orange);">64.0%</b></td>
              <td><span style="color:var(--orange)">3 Flagged</span></td>
              <td><span class="pill-tag pill-orange">● FLAGGED</span></td>
              <td><button class="btn-pill-ghost btn-view-audit-report" style="padding:3px 10px;font-size:10.5px;">View Report</button></td>
            </tr>
            <tr data-audit-id="BW-2026-003">
              <td>
                <div style="font-weight:700;color:var(--navy);">Summer Drop Visual Styleguide</div>
                <div style="font-size:10.5px;color:var(--text-dim);">Brand Asset &amp; Color Flow</div>
              </td>
              <td>Rule Compliance 2.0</td>
              <td>Jun 11, 09:40 JST</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--navy);">92.0%</b></td>
              <td><span style="color:var(--text-dim)">Clean</span></td>
              <td><span class="pill-tag pill-blue">● PASS</span></td>
              <td><button class="btn-pill-ghost btn-view-audit-report" style="padding:3px 10px;font-size:10.5px;">View Report</button></td>
            </tr>
            <tr data-audit-id="BW-2026-004">
              <td>
                <div style="font-weight:700;color:var(--navy);">Social Promo Canvas Bundle</div>
                <div style="font-size:10.5px;color:var(--text-dim);">Instagram &amp; TikTok Paid Feed</div>
              </td>
              <td>Generative 2.1</td>
              <td>Jun 04, 17:15 PST</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--red);">52.8%</b></td>
              <td><span style="color:var(--red)">1 Violation</span></td>
              <td><span class="pill-tag pill-orange" style="background:var(--red-light);color:var(--red);">● REVISE</span></td>
              <td><button class="btn-pill-ghost btn-view-audit-report" style="padding:3px 10px;font-size:10.5px;">View Report</button></td>
            </tr>
            <tr data-audit-id="BW-2026-005">
              <td>
                <div style="font-weight:700;color:var(--navy);">Interactive Prototype v0.9</div>
                <div style="font-size:10.5px;color:var(--text-dim);">Figma Hand-off Sync</div>
              </td>
              <td>Typography Strict</td>
              <td>May 20, 18:00 EST</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--navy);">88.5%</b></td>
              <td><span style="color:var(--orange)">2 Flagged</span></td>
              <td><span class="pill-tag pill-blue">● PASS</span></td>
              <td><button class="btn-pill-ghost btn-view-audit-report" style="padding:3px 10px;font-size:10.5px;">View Report</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:11px;color:var(--text-dim);">
        <span>Viewing 5 of 7 audited artifacts</span>
        <div style="display:flex;gap:4px;">
          <button class="btn-pill-ghost" style="padding:2px 8px;">&lt;</button>
          <button class="btn-pill-primary" style="padding:2px 8px;">1</button>
          <button class="btn-pill-ghost" style="padding:2px 8px;">2</button>
          <button class="btn-pill-ghost" style="padding:2px 8px;">&gt;</button>
        </div>
      </div>
    </div>

    <!-- SUB-VIEW 2: Ambiguous Rules Detection (PDF Page 10) -->
    <div class="white-panel history-subview" id="subview-hist-ambiguous" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Ambiguous Guideline Detection</h3>
          <p style="font-size:11.5px;">Highlights rules frequently disputed or dismissed by creators across production cycles.</p>
        </div>
        <span class="pill-tag pill-orange">3 RULES FLAGGED FOR CLARIFICATION</span>
      </div>

      <div class="table-container">
        <table class="styled-table">
          <thead>
            <tr>
              <th>RULE ID</th>
              <th>RULE TITLE &amp; INTENT</th>
              <th>DISMISSALS</th>
              <th>DISPUTE RATE</th>
              <th>RECOMMENDATION &amp; ACTION</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><code>GL-SUPERLATIVE-01</code></td>
              <td>
                <b>Avoid ungrounded superlatives</b>
                <div style="font-size:10.5px;color:var(--text-dim);">Flags 'world leading', 'best' without third-party proof</div>
              </td>
              <td><b style="color:var(--orange);">7 dismissals</b></td>
              <td><span class="pill-tag pill-orange">28%</span></td>
              <td>
                <div style="font-size:11.5px;">Specify threshold for industry recognition vs absolute superlatives to reduce creator friction.</div>
                <button type="button" class="btn-pill-ghost" style="padding:2px 8px;font-size:10px;margin-top:4px;" onclick="toast('Rule updated with clarification guidelines')">Clarify Scope</button>
              </td>
            </tr>
            <tr>
              <td><code>CLM-005</code></td>
              <td>
                <b>Legacy starter pricing claim ($49/mo)</b>
                <div style="font-size:10.5px;color:var(--text-dim);">Expired 2024 pricing book</div>
              </td>
              <td><b style="color:var(--red);">5 dismissals</b></td>
              <td><span class="pill-tag pill-orange" style="background:var(--red-light);color:var(--red);">22%</span></td>
              <td>
                <div style="font-size:11.5px;">Update Claim Ledger to 2026 pricing ($79/mo) and officially retire expired $49 reference.</div>
                <button type="button" class="btn-pill-orange" style="padding:2px 8px;font-size:10px;margin-top:4px;" onclick="toast('CLM-005 archived in ledger')">Retire Claim</button>
              </td>
            </tr>
            <tr>
              <td><code>GL-TONE-INDIAN-ENG</code></td>
              <td>
                <b>Formal phrasing in regional dialects</b>
                <div style="font-size:10.5px;color:var(--text-dim);">'Prepone' and 'revert back' in formal correspondence</div>
              </td>
              <td><b style="color:var(--blue-text, var(--blue));">3 dismissals</b></td>
              <td><span class="pill-tag pill-blue">14%</span></td>
              <td>
                <div style="font-size:11.5px;">Clarified: Indian English expressions 'prepone' and 'revert back' are marked valid.</div>
                <button type="button" class="btn-pill-ghost" style="padding:2px 8px;font-size:10px;margin-top:4px;" onclick="toast('Dialect exception rule active')">Verified Active</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SUB-VIEW 3: External Agency Benchmarks (PDF Page 9) -->
    <div class="white-panel history-subview" id="subview-hist-agency" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Agency Compliance Scorecard</h3>
          <p style="font-size:11.5px;">Benchmarking submission quality, turnaround time, and first-pass approval across creative partners.</p>
        </div>
        <span class="pill-tag pill-blue">3 PARTNERS BENCHMARKED</span>
      </div>

      <div class="table-container">
        <table class="styled-table">
          <thead>
            <tr>
              <th>AGENCY / TEAM</th>
              <th>SUBMISSIONS</th>
              <th>AVG SCORE</th>
              <th>FIRST-PASS PASS RATE</th>
              <th>AVG TURNAROUND</th>
              <th>ACCESS TIER</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <b>In-house Brand Team</b>
                <div style="font-size:10.5px;color:var(--text-dim);">Full corporate catalog access</div>
              </td>
              <td>18</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--green);">94.0%</b></td>
              <td><span class="pill-tag pill-blue">92%</span></td>
              <td>1.8 hours</td>
              <td><span class="pill-tag pill-gray">INTERNAL LEAD</span></td>
            </tr>
            <tr>
              <td>
                <b>Apex Digital Agency</b>
                <div style="font-size:10.5px;color:var(--text-dim);">Performance &amp; Social Retainers</div>
              </td>
              <td>12</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--navy);">88.0%</b></td>
              <td><span class="pill-tag pill-blue">83%</span></td>
              <td>3.4 hours</td>
              <td><span class="pill-tag pill-orange">EXTERNAL PARTNER</span></td>
            </tr>
            <tr>
              <td>
                <b>SocialPulse Creative</b>
                <div style="font-size:10.5px;color:var(--text-dim);">Influencer &amp; UGC Assets</div>
              </td>
              <td>9</td>
              <td><b style="font-family:'Barlow Condensed',sans-serif;font-size:18px;color:var(--orange);">76.0%</b></td>
              <td><span class="pill-tag pill-orange">67%</span></td>
              <td>6.1 hours</td>
              <td><span class="pill-tag pill-orange">RESTRICTED SCOPE</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- SUB-VIEW 4: Business Impact & ROI Metrics (PDF Page 11) -->
    <div class="white-panel history-subview" id="subview-hist-impact" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Enterprise Impact &amp; Evidence Metrics</h3>
          <p style="font-size:11.5px;">Measurable governance outcomes and operational acceleration (BrandWise Solution Proposal Section 06).</p>
        </div>
        <span class="pill-tag pill-green">PILOT BENCHMARKS VALIDATED</span>
      </div>

      <div class="four-stat-cards" style="margin-top:10px;">
        <div class="stat-box" style="border-left:4px solid var(--blue);">
          <small>REVIEW CYCLE TIME</small>
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--blue-text, var(--blue));">78% Faster</strong>
          <p style="font-size:11.5px;">Turnaround dropped from <b>18.5 hours</b> down to <b>3.2 hours</b> per asset batch.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--green);">
          <small>SEEDED MISTAKES CAUGHT</small>
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--green);">94.2%</strong>
          <p style="font-size:11.5px;">Critical legal contradictions and expired claims flagged before public deployment.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--orange);">
          <small>TRUSTED CLAIM SHARE</small>
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--orange);">96.4%</strong>
          <p style="font-size:11.5px;">All live market assertions backed by active, non-expired citations in the truth ledger.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--navy);">
          <small>FALSE POSITIVE RATE</small>
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);">1.8%</strong>
          <p style="font-size:11.5px;">Contextual Indian English handling prevents creator friction and unnecessary edits.</p>
        </div>
      </div>
    </div>

    <!-- Notification Banner -->
    <div style="background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-pill);padding:10px 18px;display:flex;align-items:center;justify-content:space-between;font-size:11.5px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="color:var(--orange)">⚡</span>
        <span>Want autonomous background audits? Turn on <b>Real-time Design Webhooks</b> in Settings.</span>
      </div>
      <button class="btn-pill-ghost" style="padding:4px 12px;font-size:11px;" id="btnConfigureWebhooks">Configure</button>
    </div>
  </main>

  <!-- ========================================================================= -->
  <!-- TAB 4: WORKSPACE SETTINGS (IMAGE 4)                                      -->
  <!-- ========================================================================= -->
  <main class="page-shell" id="view-settings" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;">
          <span class="pill-tag pill-orange">SYNC ACTIVE</span>
          <span class="pill-tag pill-blue">LAST SYNC 2M AGO</span>
        </div>
        <h1>WORKSPACE SETTINGS</h1>
        <p>Personalize your brand intelligence workspace, strictness parameters, and audit dispatch triggers.</p>
      </div>
      <div style="display:flex;align-items:center;gap:8px;background:var(--card-bg);border:1px solid var(--line);padding:8px 16px;border-radius:var(--radius-md);">
        <div style="width:28px;height:28px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
        </div>
        <div>
          <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">PRIMARY TENANT</small>
          <div style="font-weight:700;font-size:12px;color:var(--navy);">Local &amp; Cloud Synced</div>
        </div>
      </div>
    </div>

    <!-- Settings Split Layout -->
    <div class="settings-split-layout">
      <!-- Left sub-nav -->
      <div class="settings-nav-pane">
        <span style="font-size:10px;font-weight:800;color:var(--text-dim);text-transform:uppercase;margin:0 0 4px 6px;">PREFERENCES V2.4</span>
        <button class="settings-tab-btn active" data-sub="general" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
            General
          </span>
          <span>➔</span>
        </button>
        <button class="settings-tab-btn" data-sub="profile" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
            Workspace Profile
          </span>
        </button>
        <button class="settings-tab-btn" data-sub="strictness" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/></svg>
            Audit Preferences
          </span>
        </button>
        <button class="settings-tab-btn" data-sub="brand" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/></svg>
            Brand Configuration
          </span>
        </button>
        <button class="settings-tab-btn" data-sub="visual" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>
            Appearance
          </span>
        </button>
        <button class="settings-tab-btn" data-sub="notifications" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
            Notifications
          </span>
          <span class="pill-tag pill-orange" style="font-size:9px;padding:2px 6px;">12</span>
        </button>
        <button class="settings-tab-btn" data-sub="apikeys" type="button">
          <span style="display:flex;align-items:center;gap:8px;">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
            Data &amp; Privacy / Keys
          </span>
        </button>
      </div>

      <!-- Right settings cards -->
      <div style="display:flex;flex-direction:column;gap:18px;">

        <section id="appearancePanel" class="white-panel" aria-labelledby="appearanceTitle" hidden>
          <h2 id="appearanceTitle">Appearance</h2>
          <label for="themePreference">
            Color theme
            <select id="themePreference">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
        </section>
        <!-- 4 summary tiles exactly as in screenshot 4 -->
        <div class="tiles-grid-2">
          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">TARGET WORKSPACE</small>
              <span>⚙</span>
            </div>
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:4px 0 8px;">Brand Wise</div>
            <div style="display:flex;gap:6px;font-size:10px;">
              <span class="pill-tag pill-gray">ID: BW-2026-HQ</span>
              <span class="pill-tag pill-blue">Primary Master</span>
            </div>
          </div>

          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">CONNECTED PARTNER</small>
              <span>🏢</span>
            </div>
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:4px 0 8px;">Acme Creative</div>
            <div style="display:flex;gap:6px;font-size:10px;">
              <span class="pill-tag pill-gray">Double Pass</span>
              <span class="pill-tag pill-blue">Unlimited Scans</span>
            </div>
          </div>

          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">ACTIVE COLOR FLOW</small>
              <div style="display:flex;gap:3px;">
                <span style="width:10px;height:10px;border-radius:50%;background:#0073cc;"></span>
                <span style="width:10px;height:10px;border-radius:50%;background:#f26b1d;"></span>
                <span style="width:10px;height:10px;border-radius:50%;background:#102238;"></span>
              </div>
            </div>
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:4px 0 8px;">Skybound Ray</div>
            <div style="display:flex;gap:6px;font-size:10px;">
              <span class="pill-tag pill-gray">Fluid Hierarchy</span>
              <span class="pill-tag pill-blue">Default Theme</span>
            </div>
          </div>

          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">AUDITING GUIDELINES</small>
              <span>🛡</span>
            </div>
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:4px 0 8px;">v2.4 <span style="font-size:11px;font-weight:600;color:var(--text-dim);">Updated 2 days ago</span></div>
            <div style="display:flex;gap:6px;font-size:10px;">
              <span class="pill-tag pill-gray">118 rules queued</span>
              <span class="pill-tag pill-blue">Check Updates</span>
            </div>
          </div>
        </div>

        <!-- Strictness & Passing Thresholds -->
        <div class="white-panel">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">AUDITING PARAMETERS</small>
              <h3 style="font-size:17px;">Strictness &amp; Passing Thresholds</h3>
            </div>
            <span class="pill-tag pill-orange">Auto-Release Scored</span>
          </div>

          <div style="margin-bottom:14px;">
            <label style="font-size:11px;font-weight:700;color:var(--text-dim);display:block;margin-bottom:6px;">Production Strictness</label>
            <div class="segmented-control">
              <button class="seg-btn" id="segLenient" type="button">Lenient (70%)</button>
              <button class="seg-btn active" id="segBalanced" type="button">Balanced (80%)</button>
              <button class="seg-btn" id="segStrict" type="button">Strict (90%)</button>
            </div>
          </div>

          <p style="font-size:11.5px;color:var(--text-muted);margin-bottom:16px;">
            Balanced flags semantic contradictions, prime color deviations, and headline scaling anomalies while tolerating exploratory pitch variants.
          </p>

          <div style="display:flex;align-items:center;justify-content:space-between;background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-md);padding:14px 18px;">
            <div>
              <strong style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--navy);line-height:1;" id="thresholdDisplayVal">80%</strong>
              <div style="font-size:11px;font-weight:700;color:var(--navy);">Target Passing Score</div>
              <div style="font-size:10.5px;color:var(--text-dim);">Submissions below 80% require compliance lead approval.</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;width:240px;">
              <span style="font-size:11px;color:var(--text-dim);">50%</span>
              <input type="range" id="thresholdSlider" min="50" max="95" value="80" style="flex:1;">
              <span style="font-size:11px;color:var(--text-dim);">95%</span>
            </div>
          </div>
        </div>

        <!-- Active Alerts Dispatch & Studio Preview -->
        <div class="tiles-grid-2">
          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:18px;">📬</span>
                <div>
                  <b style="font-size:12px;">Active Alerts Dispatch</b>
                  <div style="font-size:10.5px;color:var(--text-dim);">Slack, Webhook &amp; Email</div>
                </div>
              </div>
              <span class="pill-tag pill-orange">8 Active</span>
            </div>

            <div style="display:flex;flex-direction:column;gap:8px;font-size:11px;margin-top:10px;">
              <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--line);">
                <span>Critical Typographic Drift</span>
                <span class="pill-tag pill-orange" style="font-size:8.5px;">Instant Slack</span>
              </div>
              <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;">
                <span>Bi-weekly Synthesis Report</span>
                <span class="pill-tag pill-blue" style="font-size:8.5px;">All Lead Users</span>
              </div>
            </div>
          </div>

          <div class="white-panel" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <b style="font-size:12px;">Visual &amp; Style Studio</b>
              <button type="button" class="btn-pill-ghost" style="padding:2px 8px;font-size:9.5px;" id="btnInspectStudio">Inspect Live</button>
            </div>
            <div style="background:var(--card-subtle);border-radius:var(--radius-sm);height:75px;display:flex;align-items:center;justify-content:center;color:var(--navy);font-weight:700;font-size:11px;margin-bottom:8px;">
              Lofty Lab Creative Stage 2026
            </div>
            <div style="display:flex;justify-content:space-between;font-size:10.5px;color:var(--text-dim);">
              <span>Asset Resolutions</span>
              <b style="color:var(--navy);">Retina 2X / Vector Mode</b>
            </div>
          </div>
        </div>

        <!-- API Key Credentials Section (Connected to .env and Multi-engine) -->
        <div class="white-panel">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">CONNECTED SERVICES</small>
              <h3 style="font-size:17px;">AI Models &amp; Webhook Credentials</h3>
            </div>
            <span class="pill-tag pill-blue">LOCAL RULES + OPTIONAL AI</span>
          </div>

          <p style="font-size:11.5px;color:var(--text-muted);margin-bottom:16px;">
            Built-in rules run locally without an API key. Add a Google AI Studio key for optional Gemini reviews within its free-tier limits.
          </p>

          <div class="mobile-stack" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

            <div>
              <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Google Gemini API Key</label>
              <div style="display:flex;gap:6px;">
                <input type="password" id="keyGemini" placeholder="AIzaSy..." style="flex:1;">
                <button class="btn-pill-ghost" style="padding:4px 10px;font-size:11px;" id="testGeminiBtn" type="button">Test</button>
              </div>
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" style="display:block;width:fit-content;margin-top:4px;font-size:11px;font-weight:700;color:var(--blue-text, var(--blue));text-decoration:underline;">Get a free-tier Gemini API key &#8599;</a>
              <span style="font-size:10px;color:var(--text-dim);" id="geminiStatus">Gemini Flash-Lite</span>
            </div>


            <div>
              <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Slack Webhook URL</label>
              <div style="display:flex;gap:6px;">
                <input type="password" id="keySlack" placeholder="https://hooks.slack.com/services/..." style="flex:1;">
                <button class="btn-pill-ghost" style="padding:4px 10px;font-size:11px;" id="testSlackBtn" type="button">Test</button>
              </div>
              <a href="https://api.slack.com/apps" target="_blank" rel="noopener noreferrer" style="display:block;width:fit-content;margin-top:4px;font-size:11px;font-weight:700;color:var(--blue-text, var(--blue));text-decoration:underline;">Set up a Slack webhook &#8599;</a>
              <span style="font-size:10px;color:var(--text-dim);" id="slackStatus">#brand-governance-alerts</span>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:6px;">
          <div style="display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--text-muted);">
            <span style="color:var(--blue-text, var(--blue))">●</span>
            <span>12 unread notifications detected in audit directory.</span>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-pill-ghost" id="btnResetSettings" type="button">Reset to Defaults</button>
            <button class="btn-pill-orange" id="btnSaveSettings" type="button">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<!-- ========================================================================= -->
<!-- MODALS MATCHING SCREENSHOT UI DESIGN                                      -->
<!-- ========================================================================= -->

<!-- Modal 1: Version Comparison & Diff (Draft v1 vs Draft v2) -->
<div class="modal-overlay" id="modalDiff">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>Version Comparison &amp; Reviewer Discussion</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;">Compare initial submission with applied fixes across the 6-state governance lifecycle.</p>
      </div>
      <button class="btn-close-modal" id="btnCloseDiffModal">×</button>
    </div>

    <div class="mobile-stack" style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
      <div style="background:var(--red-light);border:1px solid light-dark(#fbd8d8, #495064);border-radius:var(--radius-md);padding:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <b style="color:var(--red);font-size:12px;">Draft Revision v1 (Initial)</b>
          <span class="pill-tag pill-orange" style="background:var(--red-light);color:var(--red);">Score: 68%</span>
        </div>
        <div style="font-size:12px;line-height:1.6;" id="diffV1Text">
          "Acme Technologies was <span style="background:var(--red-light);color:light-dark(#900, #ffb5ba);text-decoration:line-through;">founded in 2010</span>. Our BrandWise platform is the <span style="background:var(--red-light);color:light-dark(#900, #ffb5ba);text-decoration:line-through;">world's leading</span> review engine. Independent audits show BrandWise cuts onboarding time by <span style="background:var(--red-light);color:light-dark(#900, #ffb5ba);text-decoration:line-through;">30%</span> with <span style="background:var(--red-light);color:light-dark(#900, #ffb5ba);text-decoration:line-through;">guaranteed results</span>."
        </div>
      </div>

      <div style="background:var(--green-light);border:1px solid light-dark(#c9ecdd, #495064);border-radius:var(--radius-md);padding:14px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
          <b style="color:var(--green);font-size:12px;">Draft Revision v2 (Accepted Fixes)</b>
          <span class="pill-tag pill-blue" style="background:var(--green-light);color:var(--green);">Score: 98%</span>
        </div>
        <div style="font-size:12px;line-height:1.6;" id="diffV2Text">
          "Acme Technologies was <span style="background:var(--green-light);color:light-dark(#05603b, #8de6bd);font-weight:700;">established in 2012</span>. Our BrandWise platform is an industry-standard review engine. Independent audits show BrandWise cuts onboarding time by <span style="background:var(--green-light);color:light-dark(#05603b, #8de6bd);font-weight:700;">up to 20%</span>. Terms and conditions apply."
        </div>
      </div>
    </div>

    <!-- Reviewer Comments Thread -->
    <div>
      <h4 style="font-size:14px;color:var(--navy);margin-bottom:8px;">Reviewer &amp; Legal Comments</h4>
      <div id="commentsFeed" style="display:flex;flex-direction:column;gap:8px;max-height:140px;overflow-y:auto;">
        <div style="background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-sm);padding:8px 12px;font-size:11.5px;">
          <div style="display:flex;justify-content:space-between;color:var(--text-dim);font-size:10px;margin-bottom:2px;">
            <b>Marcus Vance (Chief Legal Counsel)</b>
            <span>Today, 14:35 PST</span>
          </div>
          <div>Confirmed 2012 incorporation date. Replaced unsupported 30% onboarding claim with CLM-001 up to 20% benchmark.</div>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:10px;">
        <input type="text" id="inputNewComment" placeholder="Add a review note..." style="flex:1;">
        <button class="btn-pill-primary" id="btnAddCommentBtn" type="button">Post Note</button>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;gap:8px;border-top:1px solid var(--line);padding-top:12px;">
      <button class="btn-pill-ghost" id="btnDismissDiffModal">Close</button>
      <button class="btn-pill-primary" id="btnApproveDiffModal">Approve Revision v2</button>
    </div>
  </div>
</div>

<!-- Modal 2: WCAG 2.1 & Readability Studio -->
<div class="modal-overlay" id="modalWcag">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>Visual &amp; Accessibility Studio</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;">WCAG 2.1 AA/AAA Color Contrast Verification &amp; Flesch-Kincaid Reading Grade (PDF Stage 5).</p>
      </div>
      <button class="btn-close-modal" id="btnCloseWcagModal">×</button>
    </div>

    <div class="mobile-stack" style="display:grid;grid-template-columns:1fr 1fr;gap:18px;">
      <!-- Color Contrast -->
      <div class="white-panel" style="padding:16px;">
        <h4 style="font-size:13px;margin-bottom:10px;">Color Contrast Calculator</h4>
        <div style="display:flex;flex-direction:column;gap:10px;">
          <div>
            <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Foreground Color</label>
            <div style="display:flex;align-items:center;gap:8px;">
              <input type="color" id="wcagFgColor" value="#0073cc" style="width:36px;height:32px;padding:0;cursor:pointer;">
              <input type="text" id="wcagFgHex" value="#0073cc" style="flex:1;font-family:'JetBrains Mono',monospace;">
            </div>
          </div>
          <div>
            <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Background Color</label>
            <div style="display:flex;align-items:center;gap:8px;">
              <input type="color" id="wcagBgColor" value="#ffffff" style="width:36px;height:32px;padding:0;cursor:pointer;">
              <input type="text" id="wcagBgHex" value="#ffffff" style="flex:1;font-family:'JetBrains Mono',monospace;">
            </div>
          </div>

          <div style="background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-md);padding:12px;text-align:center;margin-top:4px;">
            <div style="font-size:10px;color:var(--text-dim);font-weight:700;text-transform:uppercase;">CONTRAST RATIO</div>
            <strong style="font-family:'Barlow Condensed',sans-serif;font-size:32px;color:var(--navy);" id="wcagRatioValue">4.85:1</strong>
            <div style="display:flex;justify-content:center;gap:6px;margin-top:6px;">
              <span class="pill-tag pill-blue" id="wcagNormalBadge">AA Normal: PASS</span>
              <span class="pill-tag pill-blue" id="wcagLargeBadge">AAA Large: PASS</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Readability & Dialect Check -->
      <div class="white-panel" style="padding:16px;">
        <h4 style="font-size:13px;margin-bottom:10px;">Content Readability &amp; Fluency</h4>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <div style="background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-md);padding:14px;">
            <div style="font-size:10px;color:var(--text-dim);font-weight:700;text-transform:uppercase;">FLESCH-KINCAID GRADE</div>
            <strong style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--navy);" id="readabilityGrade">8.4 (Standard)</strong>
            <p style="font-size:11px;margin-top:2px;">Suitable for B2B Enterprise audience (target: Grade 7-10).</p>
          </div>

          <div style="background:var(--green-light);border:1px solid light-dark(#b5e8d3, #495064);border-radius:var(--radius-md);padding:12px;">
            <b style="font-size:11.5px;color:#065f46;">✓ Indian English Dialect Fairness Active</b>
            <p style="font-size:11px;color:#047857;margin-top:2px;">
              Phrases like <i>'kindly prepone the demo'</i> and <i>'please revert back'</i> are recognized as valid formal dialect idioms and will not be penalized.
            </p>
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;border-top:1px solid var(--line);padding-top:12px;">
      <button class="btn-pill-primary" id="btnDismissWcagModal">Done</button>
    </div>
  </div>
</div>

<!-- Modal 3: Add New Rule & Claim to Core Truth Ledger -->
<div class="modal-overlay" id="modalAddClaim">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>Add to Core Truth Ledger</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;">Submit approved facts, empirical performance claims, or legal disclaimers.</p>
      </div>
      <button class="btn-close-modal" id="btnCloseAddClaimModal">×</button>
    </div>

    <form id="formAddRule" style="display:flex;flex-direction:column;gap:12px;">
      <div>
        <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Rule Category</label>
        <select id="newRuleCategory" style="width:100%;">
          <option value="Approved Claims">Approved Claim (CLM-xxx)</option>
          <option value="Company Identity">Company Identity Fact</option>
          <option value="Prohibited Words">Prohibited Terminology</option>
          <option value="Legal Disclaimers">Mandatory Legal Disclaimer</option>
        </select>
      </div>

      <div>
        <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Official Statement / Term</label>
        <input type="text" id="newRuleStatement" placeholder="e.g. Cuts onboarding time by up to 20%" required style="width:100%;">
      </div>

      <div>
        <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Evidence Citation / Source Document</label>
        <input type="text" id="newRuleEvidence" placeholder="e.g. 2026 Customer Benchmark Study, Section 4.2" required style="width:100%;">
      </div>

      <div class="mobile-stack" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div>
          <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Owner / Approver</label>
          <input type="text" id="newRuleOwner" placeholder="Sarah Jenkins (VP Product)" required style="width:100%;">
        </div>
        <div>
          <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Expiration Date</label>
          <input type="date" id="newRuleExpiry" value="2027-12-31" style="width:100%;">
        </div>
      </div>

      <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:8px;">
        <button type="button" class="btn-pill-ghost" id="btnCancelAddClaim">Cancel</button>
        <button type="submit" class="btn-pill-orange">Save Rule to Ledger</button>
      </div>
    </form>
  </div>
</div>

<!-- Modal 4: Full Audit Report Detail Modal -->
<div class="modal-overlay" id="modalAuditDetail">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3 id="detailModalTitle">Lofty Studio Landing 2026</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;" id="detailModalSubtitle">Audit ID: BW-2026-001 · Generative 2.1 Engine</p>
      </div>
      <button class="btn-close-modal" id="btnCloseAuditDetailModal">×</button>
    </div>

    <div>
      <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px;">
        <span class="pill-tag pill-blue" id="detailModalScoreBadge">Score: 98.4%</span>
        <span class="pill-tag pill-gray" id="detailModalState">Status: Passed</span>
        <span style="font-size:11px;color:var(--text-dim);" id="detailModalDate">Logged: Today, 14:32 PST</span>
      </div>

      <div style="background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-md);padding:14px;font-size:12.5px;line-height:1.6;margin-bottom:14px;" id="detailModalContent">
        "Acme Technologies was established in 2012. BrandWise cuts onboarding time by up to 20% for high velocity teams. Terms and conditions apply."
      </div>

      <h4 style="font-size:13px;color:var(--navy);margin-bottom:8px;">Audit Trail &amp; Verification Checks</h4>
      <div style="display:flex;flex-direction:column;gap:6px;font-size:11.5px;" id="detailModalAuditTrail">
        <div style="padding:6px 10px;background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-sm);display:flex;justify-content:space-between;">
          <span>Draft Submitted by Alex Rivera (Creator)</span>
          <span style="color:var(--text-dim)">14:30 PST</span>
        </div>
        <div style="padding:6px 10px;background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-sm);display:flex;justify-content:space-between;">
          <span>Hybrid Evaluation Completed (Confidence: 94%)</span>
          <span style="color:var(--text-dim)">14:31 PST</span>
        </div>
        <div style="padding:6px 10px;background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-sm);display:flex;justify-content:space-between;">
          <span>Approved by Marcus Vance (Reviewer / Legal)</span>
          <span style="color:var(--green)">14:32 PST</span>
        </div>
      </div>
    </div>

    <div style="display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:12px;">
      <button class="btn-pill-ghost" id="btnPrintReportBtn" type="button">Print / Export PDF</button>
      <button class="btn-pill-primary" id="btnDismissAuditDetailModal" type="button">Close</button>
    </div>
  </div>
</div>

<!-- Modal 5: 9-Stage Architecture Architecture Diagram (PDF Stage 1 - 9) -->
<div class="modal-overlay" id="modalArch">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>9-Stage Pre-Publication Governance Architecture</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;">Complete lifecycle from ingestion to autonomous audit trail (BrandWise Solution Proposal Section 02).</p>
      </div>
      <button class="btn-close-modal" id="btnCloseArchModal">×</button>
    </div>

    <div style="display:flex;flex-direction:column;gap:10px;font-size:12px;">
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 1</span>
        <div><b>Multi-Channel Content Ingestion</b> Copy paste, file upload (PDF/DOCX), and CMS webhook connectors.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 2</span>
        <div><b>Tokenization &amp; Linguistic Normalization</b> Contextual Indian English fairness ('prepone', 'revert back' not penalized).</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 3</span>
        <div><b>Deterministic Rule Matching</b> RegEx checks for brand casing, prohibited vocabulary, and mandatory legal disclaimers.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 4</span>
        <div><b>Semantic Alignment &amp; Claim Ledger</b> Claim verification against CLM-001..CLM-006; outputs 'cannot verify - needs human check' if expired.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 5</span>
        <div><b>Visual &amp; Accessibility Studio</b> WCAG 2.1 AA/AAA color contrast ratio calculator and Flesch-Kincaid reading ease scores.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 6</span>
        <div><b>Composite Weighted Scoring</b> Claims (35%), Brand Voice (25%), Legal (25%), Visual (15%) with Lenient/Balanced/Strict modes.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 7</span>
        <div><b>Auto-Resolution &amp; One-Click Fixes</b> Suggested edits (e.g. 'up to 20%') applied instantly with revision creation.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 8</span>
        <div><b>Collaborative Review &amp; Version Diff</b> Side-by-side comparison, reviewer annotations, and 6-state governance lifecycle.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 9</span>
        <div><b>Audit Trail &amp; Ambiguous Guideline Detection</b> Full changelog, dispute rate analytics, and agency compliance benchmarks.</div>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;border-top:1px solid var(--line);padding-top:12px;">
      <button class="btn-pill-primary" id="btnDismissArchModal">Close Architecture</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="toast">Operation Completed</div>

<script>
(()=>{
'use strict';

const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

let currentAuditRecord = null;
let currentRole = 'Creator';

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove('show'), 2600);
}

// -------------------------------------------------------------------------
// Navigation & Tab Switching
// -------------------------------------------------------------------------
function setTab(tabName) {
  $$('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.tab === tabName);
  });
  $$('.page-shell').forEach(view => {
    view.hidden = view.id !== `view-${tabName}`;
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

$$('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    setTab(link.dataset.tab);
  });
});

$('#btnTopQuickScan').onclick = () => {
  setTab('workspace');
  $('#workspaceInput').focus();
};
$('#btnHistoryAuditNow').onclick = () => {
  setTab('workspace');
  $('#workspaceInput').focus();
};
$('#btnConfigureWebhooks').onclick = () => {
  setTab('settings');
};

// -------------------------------------------------------------------------
// Role-Based Access Control (RBAC Switcher)
// -------------------------------------------------------------------------
const roleAvatars = {
  'Creator': 'CR',
  'External Agency': 'EA',
  'Reviewer': 'RV',
  'Brand Manager': 'BM',
  'Admin': 'AD'
};

$('#userRoleSelect').onchange = (e) => {
  currentRole = e.target.value;
  $('#topAvatar').textContent = roleAvatars[currentRole] || 'U';
  
  const isScoped = currentRole === 'External Agency';
  $('#roleScopeTag').style.display = isScoped ? 'inline-flex' : 'none';

  if (isScoped) {
    toast('Switched to Scoped External Agency: Client (Acme Creative)');
  } else {
    toast(`Active Role: ${currentRole}`);
  }
};

// -------------------------------------------------------------------------
// Sub-Navigation: Audit History Sub-Views
// -------------------------------------------------------------------------
const histSubtabs = [
  { btn: '#subtab-hist-archive', view: '#subview-hist-archive' },
  { btn: '#subtab-hist-ambiguous', view: '#subview-hist-ambiguous' },
  { btn: '#subtab-hist-agency', view: '#subview-hist-agency' },
  { btn: '#subtab-hist-impact', view: '#subview-hist-impact' }
];

histSubtabs.forEach(({ btn, view }) => {
  const b = $(btn);
  if (!b) return;
  b.onclick = () => {
    histSubtabs.forEach(h => {
      $(h.btn)?.classList.remove('active', 'pill-blue');
      $(h.btn)?.classList.add('pill-gray');
      $(h.view)?.classList.remove('active');
    });
    b.classList.add('active', 'pill-blue');
    b.classList.remove('pill-gray');
    $(view)?.classList.add('active');
  };
});

// -------------------------------------------------------------------------
// Sub-Navigation: Workspace Sub-Pills (Architecture, Diff, WCAG)
// -------------------------------------------------------------------------
$('#subtab-ws-live').onclick = () => {
  toast('Audit Workspace Active');
};
$('#subtab-ws-diff').onclick = () => openModal('#modalDiff');
$('#subtab-ws-wcag').onclick = () => openModal('#modalWcag');
$('#subtab-ws-arch').onclick = () => openModal('#modalArch');

$('#btnOpenDiffFromPanel').onclick = () => openModal('#modalDiff');
$('#btnOpenWcagFromPanel').onclick = () => openModal('#modalWcag');
$('#btnInspectStudio').onclick = () => openModal('#modalWcag');

// -------------------------------------------------------------------------
// Guidelines Category Filter
// -------------------------------------------------------------------------
$$('[data-glcat]').forEach(btn => {
  btn.onclick = () => {
    $$('[data-glcat]').forEach(b => {
      b.classList.remove('active', 'pill-blue');
      b.classList.add('pill-gray');
    });
    btn.classList.add('active', 'pill-blue');
    btn.classList.remove('pill-gray');

    const cat = btn.dataset.glcat;
    $$('.rule-item-box').forEach(box => {
      if (cat === 'all') {
        box.style.display = 'flex';
      } else {
        box.style.display = box.dataset.ruleCat === cat ? 'flex' : 'none';
      }
    });
  };
});

// -------------------------------------------------------------------------
// Modal System Helpers
// -------------------------------------------------------------------------
function openModal(id) {
  const m = $(id);
  if (m) m.classList.add('open');
}
function closeModal(id) {
  const m = $(id);
  if (m) m.classList.remove('open');
}

$('#btnCloseDiffModal').onclick = () => closeModal('#modalDiff');
$('#btnDismissDiffModal').onclick = () => closeModal('#modalDiff');

$('#btnCloseWcagModal').onclick = () => closeModal('#modalWcag');
$('#btnDismissWcagModal').onclick = () => closeModal('#modalWcag');

$('#btnAddRuleBtn').onclick = () => openModal('#modalAddClaim');
$('#btnCloseAddClaimModal').onclick = () => closeModal('#modalAddClaim');
$('#btnCancelAddClaim').onclick = () => closeModal('#modalAddClaim');

$('#btnCloseAuditDetailModal').onclick = () => closeModal('#modalAuditDetail');
$('#btnDismissAuditDetailModal').onclick = () => closeModal('#modalAuditDetail');

$('#btnCloseArchModal').onclick = () => closeModal('#modalArch');
$('#btnDismissArchModal').onclick = () => closeModal('#modalArch');

// -------------------------------------------------------------------------
// API Client
// -------------------------------------------------------------------------
async function api(path, opts = {}) {
  try {
    const res = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...opts
    });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Local API request to ${path} failed:`, err);
    return null;
  }
}

// -------------------------------------------------------------------------
// Workspace Audit Execution
// -------------------------------------------------------------------------
$('#btnAuditContent').onclick = async () => {
  const content = $('#workspaceInput').value.trim();
  if (!content) {
    toast('Please enter content to audit');
    return;
  }

  const btn = $('#btnAuditContent');
  btn.disabled = true;
  btn.innerHTML = `AUDITING...`;

  const res = await api('/api/audits', {
    method: 'POST',
    body: JSON.stringify({
      content,
      channel: 'Website Copy',
      role: currentRole
    })
  });

  btn.disabled = false;
  btn.innerHTML = `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> AUDIT CONTENT ➔`;

  if (res) {
    currentAuditRecord = res;
    renderAuditReport(res);
    toast(`Audit complete: Score ${res.score}%`);
  }
};

function renderAuditReport(res) {
  const pass = res.score >= 80;
  $('#reportConfidenceVal').innerHTML = `${res.score}% <span style="font-size:12px;font-family:'Inter',sans-serif;font-weight:600;color:var(--text-muted);">${pass ? 'Passed Level 2' : 'Needs Review'}</span>`;
  $('#lifecycleBadge').textContent = res.status || 'Auto-checked';
  $('#lifecycleBadge').className = `pill-tag ${pass ? 'pill-blue' : 'pill-orange'}`;

  // Update progress bars
  const findings = res.findings || [];
  const claimIssues = findings.filter(f => f.category && f.category.toLowerCase().includes('fact') || f.category && f.category.toLowerCase().includes('claim'));
  const toneIssues = findings.filter(f => f.category && f.category.toLowerCase().includes('superlative') || f.category && f.category.toLowerCase().includes('prohibited'));
  
  const factScore = Math.max(30, 100 - (claimIssues.length * 25));
  const toneScore = Math.max(35, 100 - (toneIssues.length * 20));

  $('#bar1Label').textContent = `${factScore}% Verified`;
  $('#bar1Fill').style.width = `${factScore}%`;
  $('#bar1Fill').style.background = factScore >= 80 ? 'var(--green)' : 'var(--orange)';

  $('#bar2Label').textContent = toneScore >= 80 ? 'Standard Passed' : 'Needs Review';
  $('#bar2Fill').style.width = `${toneScore}%`;
  $('#bar2Fill').style.background = toneScore >= 80 ? 'var(--green)' : 'var(--orange)';

  // Suggestion Box
  if (findings.length > 0) {
    const topF = findings[0];
    $('#reportSuggestionBox').style.display = 'flex';
    $('#reportSuggestionBox').innerHTML = `
      <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg>
      <div style="flex:1;">
        <b>${escapeHTML(topF.title)}:</b> Replace <i>"${escapeHTML(topF.wrong)}"</i> with <i>"${escapeHTML(topF.fix || 'approved terminology')}"</i> (${escapeHTML(topF.sourceId || 'Brand Standard')}).
        <div style="margin-top:6px;">
          <button type="button" class="btn-pill-orange" style="padding:2px 8px;font-size:10px;" id="btnApplyTopFix">Apply One-Click Fix</button>
        </div>
      </div>
    `;

    $('#btnApplyTopFix').onclick = () => {
      applyFix(topF);
    };
  } else {
    $('#reportSuggestionBox').innerHTML = `
      <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
      <div><b>All Checks Passed:</b> Content is 100% compliant with BrandWise Guidelines v3.2 and Core Truth Ledger.</div>
    `;
  }

  // Render Findings Accordion
  const fContainer = $('#findingsContainer');
  fContainer.innerHTML = '';
  findings.forEach(f => {
    const sevClass = f.severity ? `sev-${f.severity.toLowerCase()}` : 'sev-high';
    const card = document.createElement('div');
    card.className = `finding-card-item ${sevClass}`;
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <b>${escapeHTML(f.title)}</b>
        <span class="pill-tag ${f.severity === 'Critical' ? 'pill-orange' : 'pill-gray'}" style="font-size:8.5px;">${escapeHTML(f.severity || 'High')}</span>
      </div>
      <div style="color:var(--text-muted);font-size:11px;">${escapeHTML(f.why)}</div>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--blue-text, var(--blue));">${escapeHTML(f.sourceId || 'LEDGER')}</span>
        <div style="display:flex;gap:4px;">
          ${f.fix ? `<button type="button" class="btn-pill-primary btn-accept-fix" style="padding:2px 7px;font-size:9.5px;">Accept Fix</button>` : ''}
          <button type="button" class="btn-pill-ghost btn-report-incorrect" style="padding:2px 7px;font-size:9.5px;" title="Flag false positive">False Positive?</button>
        </div>
      </div>
    `;

    const fixBtn = card.querySelector('.btn-accept-fix');
    if (fixBtn) {
      fixBtn.onclick = () => applyFix(f);
    }
    const reportBtn = card.querySelector('.btn-report-incorrect');
    if (reportBtn) {
      reportBtn.onclick = () => {
        toast('Feedback recorded: False positive reported for engine tuning');
      };
    }
    fContainer.appendChild(card);
  });
}

function applyFix(finding) {
  if (!finding || !finding.wrong || !finding.fix) return;
  const area = $('#workspaceInput');
  if (area.value.includes(finding.wrong)) {
    area.value = area.value.replace(finding.wrong, finding.fix);
    toast(`Applied fix: "${finding.fix}"`);
    $('#btnAuditContent').click();
  }
}

// -------------------------------------------------------------------------
// Governance Lifecycle Actions (Approve, Request Changes, Publish)
// -------------------------------------------------------------------------
$('#btnApproveDraft').onclick = async () => {
  if (!currentAuditRecord) {
    toast('Run an audit first before approving');
    return;
  }
  const res = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'change_state', state: 'Approved', user: `${currentRole}` })
  });
  if (res) {
    $('#lifecycleBadge').textContent = 'Approved';
    $('#lifecycleBadge').className = 'pill-tag pill-blue';
    toast('Draft Approved! Notification dispatched to Slack #brand-approvals');
    api('/api/notify/slack', {
      method: 'POST',
      body: JSON.stringify({
        title: currentAuditRecord.title || 'Brand Draft',
        status: 'Approved',
        docId: currentAuditRecord.id,
        actor: currentRole,
        message: 'Draft officially approved by brand reviewer.'
      })
    });
  }
};

$('#btnReqChanges').onclick = async () => {
  if (!currentAuditRecord) return;
  const res = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'change_state', state: 'Changes requested', user: `${currentRole}` })
  });
  if (res) {
    $('#lifecycleBadge').textContent = 'Changes requested';
    $('#lifecycleBadge').className = 'pill-tag pill-orange';
    toast('Changes requested: creator notified');
  }
};

$('#btnPublishDraft').onclick = async () => {
  if (!currentAuditRecord) return;
  const res = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'change_state', state: 'Published', user: `${currentRole}` })
  });
  if (res) {
    $('#lifecycleBadge').textContent = 'Published';
    $('#lifecycleBadge').className = 'pill-tag pill-green';
    toast('Draft Published to production channel!');
  }
};

// -------------------------------------------------------------------------
// Sample buttons (Connecting the 4 PDF Scenarios)
// -------------------------------------------------------------------------
$('#btnLoadShortNote').onclick = () => {
  $('#workspaceInput').value = "BrandWise cuts onboarding time by up to 20% for high velocity teams. Terms and conditions apply.";
  toast('Loaded Short Note: 100% compliant claim CLM-001');
};
$('#btnLoadInstagram').onclick = () => {
  $('#workspaceInput').value = "Kindly note: We have preponed the product launch to Friday. Please revert back with feedback. Terms and conditions apply.";
  toast('Loaded Indian English sample: dialetical fairness test');
};
$('#btnLoadAdHeadline').onclick = () => {
  $('#workspaceInput').value = "Lofty Creative Lab guarantees 10x faster engagement across omni-channel campaigns using patented creative synthesis with 100% cloud zero-carbon footprint.";
  toast('Loaded Ad Headline: Overpromising and absolute guarantee test');
};
$('#btnLoadPrivacy').onclick = () => {
  $('#workspaceInput').value = "Acme Technologies was established in 2012. Starter tiers start at $49/month with full features.";
  toast('Loaded Expired Pricing ($49) & Identity sample');
};

$('#btnIndianEnglishNote').onclick = (e) => {
  e.preventDefault();
  openModal('#modalWcag');
};

// -------------------------------------------------------------------------
// Export PDF Handler
// -------------------------------------------------------------------------
$('#btnExportPDF').onclick = () => {
  window.print();
};
$('#btnPrintReportBtn').onclick = () => {
  window.print();
};

// -------------------------------------------------------------------------
// Audit Archive "View Report" Modal
// -------------------------------------------------------------------------
function bindArchiveRowButtons() {
  $$('.btn-view-audit-report').forEach(btn => {
    btn.onclick = () => {
      const tr = btn.closest('tr');
      const docTitle = tr.querySelector('div')?.textContent || 'Audit Artifact';
      const score = tr.querySelector('b')?.textContent || '98%';
      $('#detailModalTitle').textContent = docTitle;
      $('#detailModalScoreBadge').textContent = `Score: ${score}`;
      openModal('#modalAuditDetail');
    };
  });
}
bindArchiveRowButtons();

// Archive Search Filter
$('#archiveSearch').oninput = (e) => {
  const q = e.target.value.toLowerCase().trim();
  $$('#historyTableRows tr').forEach(row => {
    const txt = row.textContent.toLowerCase();
    row.style.display = txt.includes(q) ? '' : 'none';
  });
};

// -------------------------------------------------------------------------
// File Drop Zone Ingestion (PDF Stage 1)
// -------------------------------------------------------------------------
const dropZone = $('#dropDocZone');
const fileInput = $('#fileDocUpload');

$('#btnSelectFileDoc').onclick = (e) => {
  e.stopPropagation();
  fileInput.click();
};
dropZone.onclick = () => fileInput.click();

dropZone.ondragover = (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
};
dropZone.ondragleave = () => dropZone.classList.remove('dragover');
dropZone.ondrop = (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) {
    handleFileUpload(e.dataTransfer.files[0]);
  }
};
fileInput.onchange = () => {
  if (fileInput.files.length) {
    handleFileUpload(fileInput.files[0]);
  }
};

function handleFileUpload(file) {
  toast(`Parsing guidelines from "${file.name}"...`);
  setTimeout(() => {
    toast(`Extracted 4 rules from "${file.name}" into Core Truth Ledger!`);
  }, 900);
}

// -------------------------------------------------------------------------
// Add New Rule to Ledger
// -------------------------------------------------------------------------
$('#formAddRule').onsubmit = async (e) => {
  e.preventDefault();
  const statement = $('#newRuleStatement').value.trim();
  const category = $('#newRuleCategory').value;
  const evidence = $('#newRuleEvidence').value.trim();
  const owner = $('#newRuleOwner').value.trim();
  const expiry = $('#newRuleExpiry').value;

  const res = await api('/api/claims', {
    method: 'POST',
    body: JSON.stringify({ statement, category, evidence, owner, expiry, status: 'Active' })
  });

  if (res && res.success) {
    toast('Rule added to Core Truth Ledger!');
    closeModal('#modalAddClaim');

    // Append to list visually
    const box = document.createElement('div');
    box.className = 'rule-item-box';
    box.dataset.ruleCat = category.toLowerCase().includes('claim') ? 'claims' : 'company';
    box.innerHTML = `
      <div class="rule-item-header">
        <small>${escapeHTML(category.toUpperCase())}</small>
        <span class="pill-tag pill-blue" style="font-size:9px;">Active</span>
      </div>
      <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;">${escapeHTML(statement)}</div>
      <div style="font-size:11.5px;color:var(--text-muted);">
        Evidence: ${escapeHTML(evidence)}. Owner: ${escapeHTML(owner)}. Expiry: ${escapeHTML(expiry)}.
      </div>
    `;
    $('#guidelinesRulesList').prepend(box);
  }
};

// -------------------------------------------------------------------------
// Settings: Strictness Segmented Controls & Slider
// -------------------------------------------------------------------------
const segs = [$('#segLenient'), $('#segBalanced'), $('#segStrict')];
segs.forEach(btn => {
  btn.onclick = () => {
    segs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.id === 'segLenient') $('#thresholdSlider').value = 70;
    if (btn.id === 'segBalanced') $('#thresholdSlider').value = 80;
    if (btn.id === 'segStrict') $('#thresholdSlider').value = 90;
    $('#thresholdDisplayVal').textContent = `${$('#thresholdSlider').value}%`;
    toast(`Strictness mode: ${btn.textContent}`);
  };
});

$('#thresholdSlider').oninput = e => {
  $('#thresholdDisplayVal').textContent = `${e.target.value}%`;
};

const themePreference = $('#themePreference');
themePreference.value = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
themePreference.onchange = () => {
  const theme = themePreference.value;
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('brandwise-theme', theme); } catch {}
};

// Settings left nav tabs
$$('.settings-tab-btn').forEach(btn => {
  btn.onclick = () => {
    $$('.settings-tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    $('#appearancePanel').hidden = btn.dataset.sub !== 'visual';
    if (btn.dataset.sub !== 'visual') toast(`Viewing settings: ${btn.textContent.trim()}`);
  };
});

// -------------------------------------------------------------------------
// WCAG Contrast Calculator Logic
// -------------------------------------------------------------------------
function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  const bigint = parseInt(clean, 16);
  return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
}
function lum(r, g, b) {
  const a = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}
function calcContrast(hex1, hex2) {
  try {
    const l1 = lum(...hexToRgb(hex1));
    const l2 = lum(...hexToRgb(hex2));
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    return Math.round(ratio * 100) / 100;
  } catch (e) {
    return 4.5;
  }
}

function updateContrastCalc() {
  const fg = $('#wcagFgHex').value;
  const bg = $('#wcagBgHex').value;
  const ratio = calcContrast(fg, bg);
  $('#wcagRatioValue').textContent = `${ratio}:1`;

  const normalPass = ratio >= 4.5;
  const largePass = ratio >= 3.0;

  $('#wcagNormalBadge').textContent = `AA Normal: ${normalPass ? 'PASS' : 'FAIL'}`;
  $('#wcagNormalBadge').className = `pill-tag ${normalPass ? 'pill-blue' : 'pill-orange'}`;

  $('#wcagLargeBadge').textContent = `AAA Large: ${largePass ? 'PASS' : 'FAIL'}`;
  $('#wcagLargeBadge').className = `pill-tag ${largePass ? 'pill-blue' : 'pill-orange'}`;
}

$('#wcagFgColor').oninput = (e) => {
  $('#wcagFgHex').value = e.target.value;
  updateContrastCalc();
};
$('#wcagBgColor').oninput = (e) => {
  $('#wcagBgHex').value = e.target.value;
  updateContrastCalc();
};

// -------------------------------------------------------------------------
// API Keys & External AI Testing & Persistence
// -------------------------------------------------------------------------
async function loadKeys() {
  const res = await api('/api/keys');
  if (!res || !res.keys) return;

  if (res.keys.gemini?.configured) {
    $('#keyGemini').placeholder = res.keys.gemini.masked;
    $('#geminiStatus').textContent = `Configured: ${res.keys.gemini.masked}`;
    $('#geminiStatus').style.color = 'var(--green)';
  }
  if (res.keys.slack?.configured) {
    $('#keySlack').placeholder = res.keys.slack.masked;
    $('#slackStatus').textContent = `Configured: ${res.keys.slack.masked}`;
    $('#slackStatus').style.color = 'var(--green)';
  }
}

async function testKey(provider, inputId, statusId) {
  const val = $(inputId).value.trim();
  const statusEl = $(statusId);
  if (!val) {
    statusEl.textContent = 'Please enter a key to test';
    statusEl.style.color = 'var(--orange)';
    return;
  }
  statusEl.textContent = 'Pinging provider endpoint...';
  statusEl.style.color = 'var(--text-dim)';

  const res = await api('/api/keys/test', {
    method: 'POST',
    body: JSON.stringify({ provider, apiKey: val })
  });

  if (res && res.valid) {
    statusEl.textContent = `✓ Valid Key (${res.model || res.provider})`;
    statusEl.style.color = 'var(--green)';
  } else {
    statusEl.textContent = `✕ ${res?.error || 'Validation failed'}`;
    statusEl.style.color = 'var(--red)';
  }
}

$('#testGeminiBtn').onclick = () => testKey('gemini', '#keyGemini', '#geminiStatus');
$('#testSlackBtn').onclick = () => testKey('slack', '#keySlack', '#slackStatus');

$('#btnSaveSettings').onclick = async () => {
  const payload = {};
  const g = $('#keyGemini').value.trim();
  const s = $('#keySlack').value.trim();

  if (g) payload.geminiApiKey = g;
  if (s) payload.slackWebhookUrl = s;

  if (Object.keys(payload).length > 0) {
    await api('/api/keys', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  toast('Settings and API keys saved to .env');
  loadKeys();
};

$('#btnResetSettings').onclick = () => {
  toast('Settings restored to defaults');
};

function escapeHTML(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// Initial Load
loadKeys();

})();
</script>
</body>
</html>
'''

# Write file
with open('The-Final-Draft-Hackathon-Updated.html', 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)

# Also copy to index.html
shutil.copyfile('The-Final-Draft-Hackathon-Updated.html', 'index.html')
print("Successfully updated The-Final-Draft-Hackathon-Updated.html and index.html!")
