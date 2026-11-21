// Shared navigation components rendered before app initialization.
const sidebarNavigation = () => component(`
    <a href="#workspace" class="nav-link active" data-tab="workspace">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
      <span class="nav-label">Audit Workspace</span>
    </a>
    <a href="#guidelines" class="nav-link" data-tab="guidelines">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      <span class="nav-label">Official Guidelines</span>
    </a>
    <a href="#history" class="nav-link" data-tab="history">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span class="nav-label">Audit History</span>
    </a>
    <a href="#assets" class="nav-link" data-tab="assets">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 014 15.5zM4 15.5A2.5 2.5 0 016.5 13H20M8 7h7M8 10h5"/></svg>
      <span class="nav-label">Brand Assets</span>
    </a>
    <a href="#calendar" class="nav-link" data-tab="calendar">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M7 3v3m10-3v3M4 9h16M5 5h14a1 1 0 011 1v13H4V6a1 1 0 011-1zm3 8h3m-3 4h6"/></svg>
      <span class="nav-label">Calendar</span>
    </a>
    <a href="#team" class="nav-link" data-tab="team" id="adminTeamNav" hidden>
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M16 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2m6-10a4 4 0 100-8 4 4 0 000 8zm7-3a4 4 0 010 7m5 6v-2a4 4 0 00-3-3.87"/></svg>
      <span class="nav-label">Team Overview</span>
    </a>
    <a href="#settings" class="nav-link" data-tab="settings">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
      <span class="nav-label">Settings</span>
    </a>
    <a href="#profile" class="nav-link" data-tab="profile">
      <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path stroke-linecap="round" stroke-linejoin="round" d="M4 21a8 8 0 0116 0"/></svg>
      <span class="nav-label">Profile</span>
    </a>
  `);

const workspaceSubnav = () => component(`
      <button type="button" class="pill-tag pill-blue active" id="subtab-ws-live">Live workspace</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-diff">Version diff</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-wcag">WCAG contrast</button>
      <button type="button" class="pill-tag pill-gray" id="subtab-ws-arch">Review flow</button>
    `);

const guidelineFilters = () => component(`
      <span style="font-size:10px;font-weight:800;text-transform:uppercase;color:var(--text-dim);margin-right:6px;">CATEGORIES:</span>
      <button type="button" class="pill-tag pill-blue active" data-glcat="all">All Rules</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="company">Company Identity</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="claims">Approved Claims Ledger</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="prohibited">Prohibited Words</button>
      <button type="button" class="pill-tag pill-gray" data-glcat="legal">Legal Disclaimers</button>
    `);

const settingsNavigation = () => component(`
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
        </button>`);

const historyNavigation = () => component(`<button type="button" class="pill-tag pill-blue active" id="subtab-hist-archive">● LIVE ARCHIVE</button>
          <button type="button" class="pill-tag pill-orange" id="subtab-hist-ambiguous">● AMBIGUOUS RULES</button>
          <button type="button" class="pill-tag pill-gray" id="subtab-hist-agency">● AGENCY BENCHMARKS</button>
          <button type="button" class="pill-tag pill-gray" id="subtab-hist-impact">● IMPACT METRICS</button>`);

document.getElementById("sidebarNavigation").replaceChildren(sidebarNavigation());

document.getElementById("workspaceSubnav").replaceChildren(workspaceSubnav());

document.getElementById("guidelineFilters").replaceChildren(guidelineFilters());
document.getElementById("settingsNavigation").replaceChildren(settingsNavigation());
document.getElementById("historyNavigation").replaceChildren(historyNavigation());

const browserAiReview = () => component(`<div class="browser-ai-review">
  <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
    <label style="display:flex;align-items:center;gap:6px"><input id="enableGemini" type="checkbox"> Include optional AI review</label>
    <select id="aiReviewProvider" aria-label="Choose AI review model" style="max-width:min(100%,420px)">
      <option value="browser-1b">In-browser Llama 3.2 1B (private, free, recommended)</option>
      <option value="browser-3b">In-browser Llama 3.2 3B (better quality, larger download)</option>
    </select>
  </div>
  <div id="aiModelProgressPanel" hidden style="max-width:620px;margin:8px 0 0 22px">
    <div style="display:flex;align-items:center;gap:8px"><progress id="aiModelProgress" max="100" value="0" style="flex:1;height:10px"></progress><button id="cancelAiLoad" class="btn-pill-ghost" type="button" style="margin:0;padding:3px 10px">Cancel</button></div>
    <div id="aiModelProgressText" style="margin-top:4px;color:var(--text-muted)"></div>
  </div>
  <p id="aiModelDownloadNote" style="margin:6px 0 0 22px;color:var(--text-muted)">First use downloads about 0.9 GB (1B) or 2.3 GB (3B); it is cached afterwards.</p>
  <details style="margin:6px 0 0 22px;font-size:11px">
    <summary style="cursor:pointer;color:var(--blue-text,var(--blue));font-weight:700">AI and privacy details</summary>
    <p id="aiPrivacyText" style="max-width:720px;margin:6px 0;color:var(--text-muted)">With an in-browser Llama model, the draft is processed in your browser and is not sent to any AI provider. Model weights are downloaded from the internet and cached. AI findings are subjective and need a human. Built with Llama.</p>
    <p id="geminiPrivacyText" hidden style="max-width:720px;margin:6px 0;color:var(--text-muted)">If Gemini is selected, the draft and review context are sent to Google for review.</p>
  </details>
  <p id="aiReviewStatus" role="status" aria-live="polite" style="margin:6px 0 0 22px"></p></div>`);
document.querySelector("#workspaceInput").after(browserAiReview());
