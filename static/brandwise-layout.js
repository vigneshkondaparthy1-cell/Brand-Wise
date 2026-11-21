// Page structure components. Loaded before views and behavior scripts.
const BrandWiseLayout = {
  authHeader: () => component(`
<header id="authPageHeader">
  <span class="auth-brand-name">BRANDWISE</span>
  <a class="auth-overview-link" href="#accountGate">Sign in</a>
    <label class="auth-theme-control" for="authTheme"><span>Theme</span>
    <select id="authTheme" aria-label="Choose light or dark theme"><option value="light">Light</option><option value="dark">Dark</option></select>
  </label>
</header>
`),
  overview: () => component(`
<section id="authOverview" aria-labelledby="authOverviewTitle">
  <div aria-hidden="true"><span class="auth-cloud"></span><span class="auth-cloud"></span><span class="auth-cloud"></span><span class="auth-cloud"></span></div>
  <div class="auth-features auth-overview-features" aria-hidden="true">
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2"/><path d="M15.5 8.5 21 3M17 3h4v4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5h16v14zM7 15l4-4 3 3 3-5M7 8h1"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6v6H4zM14 14h6v6h-6zM7 10v7h7M14 7h6M17 4v6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4-3 7-8 9-5-2-8-5-8-9V7zM8 12l3 3 5-6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4H5v17h14V4h-3M9 3h6v4H9zM8 12l2 2 5-4M8 18h7"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4M12 15v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17a4 4 0 0 1 0-8 6 6 0 0 1 12-2 5 5 0 0 1 3 10M9 17l3 3 5-5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10v5h4l3 6h3l-3-7 10 4V4L7 10zM7 10v5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"/><path d="M4 21v-2a6 6 0 0 1 12 0v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6l2 2 2-2h6v14h-6l-2 2-2-2H4zM12 6v14"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2"/><path d="M15.5 8.5 21 3M17 3h4v4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5h16v14zM7 15l4-4 3 3 3-5M7 8h1"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6v6H4zM14 14h6v6h-6zM7 10v7h7M14 7h6M17 4v6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4-3 7-8 9-5-2-8-5-8-9V7zM8 12l3 3 5-6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4H5v17h14V4h-3M9 3h6v4H9zM8 12l2 2 5-4M8 18h7"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4M12 15v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17a4 4 0 0 1 0-8 6 6 0 0 1 12-2 5 5 0 0 1 3 10M9 17l3 3 5-5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10v5h4l3 6h3l-3-7 10 4V4L7 10zM7 10v5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"/><path d="M4 21v-2a6 6 0 0 1 12 0v2"/></svg></span>
  </div>
  <div class="auth-overview-wrap">
    <div class="auth-overview-intro">
      <div class="auth-overview-kicker">Brand governance for content teams</div>
      <h2 id="authOverviewTitle">Give every<br><strong>draft a</strong><br><strong class="auth-headline-orange">brand check.</strong></h2>
      <p>Check marketing copy against approved claims, terminology, and disclaimers. See exactly what needs review before the copy goes live.</p>
      <div class="auth-overview-actions">
        <a class="btn-pill-primary" href="#authAuditPreview">Try the sample audit</a>
        <a class="btn-pill-ghost" href="#authFeatureSummary">Explore features</a>
      </div>
    </div>
    <section class="auth-demo" id="authAuditPreview" aria-labelledby="authDemoTitle">
      <header class="auth-demo-header">
        <div class="review-desk-title">
          <h3 id="authDemoTitle">▤ &nbsp;Northstar Studio · Modular Lighting Launch</h3>
          <span class="review-desk-kind">Product Campaign · v2.1</span>
        </div>
        <button class="review-desk-apply" id="authDemoToggle" type="button" aria-pressed="false">↻ &nbsp;Apply Guideline Rules</button>
      </header>
      <div class="auth-demo-grid">
        <div class="auth-demo-panel review-desk-draft">
          <div class="review-desk-subhead">
            <div class="review-desk-meta"><h4>Launch copy draft</h4><span class="review-desk-flag"><span id="authDemoFlagCount">2</span> issues flagged</span></div>
            <div class="review-desk-legend"><span><i class="review-desk-dot"></i>Unsubstantiated superlative</span><span><i class="review-desk-dot red"></i>Unverified materials claim</span></div>
          </div>
          <blockquote class="auth-demo-copy" id="authDemoCopy" aria-label="Example draft copy specimen">Northstar Studio creates modular lighting for calm, considered spaces. Our new collection delivers <mark>groundbreaking</mark> performance in every room. Each fixture is made with <mark class="claim">carbon-neutral</mark> materials and designed to bring lasting warmth to everyday routines.</blockquote>
          <div class="review-desk-meta">
            <span>Length: <span id="authDemoWordCount">34</span> words &nbsp;·&nbsp; Reading time: <span id="authDemoReadTime">9</span> sec &nbsp;·&nbsp; Target tone: Clear &amp; Considered</span>
            <div class="review-desk-pills"><span class="review-desk-pill good">Tone: 96% Consistent</span><span class="review-desk-pill pending" id="authDemoPending">2 Flags Pending</span></div>
          </div>
        </div>
        <div class="auth-demo-panel review-desk-evaluation">
          <div class="review-desk-score">
            <div class="review-desk-score-head"><h4>Brand integrity score</h4><span id="authDemoAction">Action required</span></div>
            <div class="review-desk-score-line"><strong id="authDemoScore">81</strong><small>/100</small></div>
            <div class="review-desk-progress"><span id="authDemoProgress"></span></div>
            <p id="authDemoScoreNote">2 claims need evidence or revised wording before publishing.</p>
          </div>
          <div class="review-desk-breakdown">
            <h4>Evaluation breakdown</h4>
            <div class="review-desk-stat"><span>Voice &amp; Tone Alignment</span><strong>98%</strong></div>
            <div class="review-desk-stat"><span>Approved Language</span><strong class="mid" id="authDemoLexicon">78%</strong></div>
            <div class="review-desk-stat"><span>Materials Claim Evidence</span><strong class="low" id="authDemoEsg">62%</strong></div>
            <div class="review-desk-stat"><span>Visual Identity Match</span><strong>100%</strong></div>
          </div>
          <a class="review-desk-open" href="#accountGate">Open Northstar Review Desk &nbsp;›</a>
          <p class="review-desk-status" id="authDemoResult" role="status" aria-live="polite"></p>
        </div>
      </div>
    </section>
    <h2 class="auth-feature-heading" id="authFeatureSummary">From draft to approval</h2>
    <div class="auth-overview-grid">
      <article class="auth-overview-card"><h3>Official Guidelines</h3><p>Find approved claims, preferred terminology, and required disclaimers in one place.</p></article>
      <article class="auth-overview-card"><h3>Audit Workspace</h3><p>Paste or import copy, review flagged wording and its sources, compare revisions, and route a draft for approval.</p></article>
      <article class="auth-overview-card"><h3>Brand Assets</h3><p>Keep shared brand files in the workspace so teammates can find the right materials for their work.</p></article>
    </div>
    <div class="auth-overview-cta">
      <h2>Ready to review your own draft?</h2>
      <div class="auth-overview-actions"><a class="btn-pill-primary" href="#accountGate">Sign in to BrandWise</a></div>
    </div>
  </div>
</section>
`),
  signIn: () => component(`
<main class="auth-sign-in-stage" id="authSignInStage">
  <div class="auth-features" aria-hidden="true">
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2"/><path d="M15.5 8.5 21 3M17 3h4v4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5h16v14zM7 15l4-4 3 3 3-5M7 8h1"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6v6H4zM14 14h6v6h-6zM7 10v7h7M14 7h6M17 4v6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4-3 7-8 9-5-2-8-5-8-9V7zM8 12l3 3 5-6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4H5v17h14V4h-3M9 3h6v4H9zM8 12l2 2 5-4M8 18h7"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4M12 15v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17a4 4 0 0 1 0-8 6 6 0 0 1 12-2 5 5 0 0 1 3 10M9 17l3 3 5-5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10v5h4l3 6h3l-3-7 10 4V4L7 10zM7 10v5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"/><path d="M4 21v-2a6 6 0 0 1 12 0v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6l2 2 2-2h6v14h-6l-2 2-2-2H4zM12 6v14"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="2"/><path d="M15.5 8.5 21 3M17 3h4v4"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19V5h16v14zM7 15l4-4 3 3 3-5M7 8h1"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h6v6H4zM14 14h6v6h-6zM7 10v7h7M14 7h6M17 4v6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4-3 7-8 9-5-2-8-5-8-9V7zM8 12l3 3 5-6"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4H5v17h14V4h-3M9 3h6v4H9zM8 12l2 2 5-4M8 18h7"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4M12 15v2"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17a4 4 0 0 1 0-8 6 6 0 0 1 12-2 5 5 0 0 1 3 10M9 17l3 3 5-5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10v5h4l3 6h3l-3-7 10 4V4L7 10zM7 10v5"/></svg></span>
    <span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="7" r="4"/><path d="M4 21v-2a6 6 0 0 1 12 0v2"/></svg></span>
  </div>
<section id="accountGate" class="white-panel" aria-labelledby="accountTitle" tabindex="-1">
  <div class="auth-sky" aria-hidden="true">
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
    <span class="auth-cloud"></span>
  </div>
  <h1 id="accountTitle">Sign in</h1>
  <form id="accountForm" method="post" action="/api/auth/login">
    <label>Username or email <input name="username" required maxlength="254" autocomplete="username"></label>
    <label>Password
      <span class="password-field">
        <input name="password" id="accountPassword" type="password" required minlength="4" maxlength="128" autocomplete="current-password">
        <button class="password-toggle" id="passwordToggle" type="button" aria-label="Show password" aria-pressed="false" title="Show password">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
      </span>
    </label>
    <div id="registrationFields" hidden>
      <label>Full name <input name="name" data-registration-field maxlength="120" autocomplete="name"></label>
      <div class="email-verification">
        <label for="registrationEmail">Email</label>
        <div class="email-entry-row">
          <input id="registrationEmail" name="email" data-registration-field type="email" maxlength="254" autocomplete="email">
          <button class="btn-pill-ghost" id="sendEmailOtp" type="button">Send code</button>
        </div>
        <div class="email-otp-panel" id="emailOtpPanel" hidden>
          <label for="emailOtpCode">6-digit email code</label>
          <div class="email-entry-row">
            <input id="emailOtpCode" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" placeholder="Enter code" disabled>
            <button class="btn-pill-primary" id="confirmEmailOtp" type="button" disabled>Confirm code</button>
          </div>
        </div>
        <p class="email-verification-status" id="emailVerificationStatus" role="status" aria-live="polite"></p>
      </div>
      <label>Which role best describes your work? <select name="role" data-registration-field></select></label>
      <label><span id="orgQuestion">Organization</span> <input name="organization" data-registration-field maxlength="120" autocomplete="organization"></label>
      <label><span id="workQuestion">Job title</span> <input name="work" data-registration-field maxlength="120"></label>
      <label><span id="responsibilityQuestion">What do you do?</span> <input name="responsibilities" data-registration-field maxlength="500"></label>
    </div>
    <button class="btn-pill-primary" id="accountSubmit" type="submit" disabled>Sign in</button>
    <button class="btn-pill-ghost" id="accountMode" type="button">Create an account</button>
    <button id="forgotPasswordButton" type="button">Forgot password?</button>
    <p id="accountError" role="status"></p>
  </form>
  <form id="forgotPasswordForm" method="post" action="/api/auth/password-reset" hidden>
    <p style="margin:0 0 4px;">Enter your account email and we’ll send a password reset code via Resend.</p>
    <label for="passwordResetEmail">Email</label>
    <div class="email-entry-row">
      <input id="passwordResetEmail" type="email" required maxlength="254" autocomplete="email" placeholder="you@example.com">
      <button class="btn-pill-ghost" id="sendPasswordResetCode" type="button">Send code</button>
    </div>
    <div id="passwordResetPanel" hidden>
      <label for="passwordResetCode">Verification code</label>
      <input id="passwordResetCode" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="6-digit code">
      <label for="passwordResetNewPassword">New password</label>
      <input id="passwordResetNewPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128" placeholder="At least 12 characters">
      <label for="passwordResetConfirmPassword">Confirm new password</label>
      <input id="passwordResetConfirmPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128" placeholder="Repeat new password">
      <button class="btn-pill-primary" style="margin-top:14px;width:100%;" type="submit">Reset password</button>
    </div>
    <div class="reset-password-actions"><button class="btn-pill-ghost" id="backToSignIn" type="button">Back to sign in</button></div>
    <p id="forgotPasswordStatus" role="status" aria-live="polite"></p>
  </form>
</section>
</main>
`),
  sidebar: () => component(`
<aside class="sidebar">
  <div class="brand-header">
    <a href="#workspace" class="brand-link" id="brandHeaderLink" aria-label="Go to Audit Workspace" title="Go to Audit Workspace">
      <div class="brand-logo-circle">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 00-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
      </div>
      <div class="brand-copy">
        <div class="brand-title">BRAND WISE</div>
        <div class="brand-subtitle">BRAND INTELLIGENCE</div>
      </div>
    </a>
    <button class="brand-toggle" id="sidebarToggle" type="button" aria-label="Collapse sidebar" aria-expanded="true" title="Collapse sidebar"><svg width="17" height="17" viewBox="0 0 20 20" fill="none" aria-hidden="true"><rect x="2.5" y="3" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M7 3.5v13M12 7l-2 3 2 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
  </div>

  <div class="workspace-status-badge">
    <span>WORKSPACE STATUS</span>
    <span class="pill-val">LIVE 2.4</span>
  </div>

  <nav class="sidebar-nav" id="sidebarNavigation"></nav>

  <div class="sidebar-bottom-score">
    <div class="score-header">
      <small>LATEST AUDIT SCORE</small>
      <strong id="sidebarComplianceVal">—</strong>
    </div>
    <div class="sidebar-progress-track">
      <div class="sidebar-progress-fill"></div>
    </div>
    <div class="score-subtext" id="sidebarScoreNote">No measured audits yet</div>
  </div>
</aside>
`),
  workspaceLayout: () => component(`
<div class="main-wrapper">
  <!-- Top Bar -->
  <header class="topbar">
    <button class="topbar-left topbar-audit-action" id="topbarNewAudit" type="button" title="Start a new audit">
      <span aria-hidden="true">＋</span><span>New audit</span>
    </button>

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


      <div class="profile-menu" id="profileMenu">
        <button class="user-avatar" id="topAvatar" type="button" aria-label="Open my profile" aria-haspopup="dialog" aria-expanded="false" aria-controls="profilePopover">A</button>
        <section class="profile-popover" id="profilePopover" role="dialog" aria-label="My profile" hidden>
          <div class="profile-popover-head">
            <div><div class="profile-popover-name" id="profileName">Your profile</div><div class="profile-popover-username" id="profileUsername"></div></div>
            <span class="profile-popover-role" id="profileRole"></span>
            <button class="profile-close" id="profileClose" type="button" aria-label="Close profile">×</button>
          </div>
          <dl>
            <div><dt>Email</dt><dd id="profileEmail"></dd></div>
            <div><dt>Organization</dt><dd id="profileOrganization"></dd></div>
            <div><dt>Work</dt><dd id="profileWork"></dd></div>
          </dl>
        </section>
      </div>
      <button class="btn-pill-ghost" id="accountSignOut" type="button">Sign out</button>
    </div>
  </header>









  <!-- ========================================================================= -->
  <!-- TAB 1: AUDIT WORKSPACE (IMAGE 2)                                         -->
  <!-- ========================================================================= -->


  <div id="appViews"></div>
</div>

<!-- ========================================================================= -->
<!-- MODALS MATCHING SCREENSHOT UI DESIGN                                      -->
<!-- ========================================================================= -->
`),
  supportDialog: () => component(`
<div class="modal-overlay" id="modalSupport" role="dialog" aria-modal="true" aria-labelledby="supportTitle" aria-hidden="true">
  <div class="modal-card support-card">
    <div class="modal-header">
      <div>
        <h3 id="supportTitle">BrandWise Support</h3>
        <p style="font-size:12px;margin-top:3px;">Quick help for reviewing and managing branded content.</p>
      </div>
      <button class="btn-close-modal" id="btnCloseSupport" type="button" aria-label="Close support">×</button>
    </div>
    <div class="support-guides">
      <article><span class="support-step">01</span><div><h4>Run a content audit</h4><p>Open Audit Workspace, paste your draft, choose its content type, then select <b>Audit Content</b>.</p></div></article>
      <article><span class="support-step">02</span><div><h4>Review a finding</h4><p>Open a finding to see the matched guideline or claim and its confidence. Apply a suggested fix or report an incorrect flag.</p></div></article>
      <article><span class="support-step">03</span><div><h4>Manage your workspace</h4><p>Use Settings for role-specific preferences, brand rules, appearance, and optional AI connections. Rule checks work without an AI key.</p></div></article>
    </div>
    <div class="support-footer">
      <span>Need help? Start with Official Guidelines or review your audit history.</span>
      <button class="btn-pill-primary" id="btnSupportGuidelines" type="button">Open Guidelines</button>
    </div>
  </div>
</div>
`),
  diffDialog: () => component(`
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
      <button class="btn-pill-ghost" id="btnDismissDiffModal">Back to audit</button>
      <button class="btn-pill-primary" id="btnApproveDiffModal">Approve Revision v2</button>
    </div>
  </div>
</div>
`),
  contrastDialog: () => component(`
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
              <span class="pill-tag pill-blue" id="wcagLargeBadge">AA Large: PASS</span>
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
            <strong style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--navy);" id="readabilityGrade">Not checked yet</strong>
            <p style="font-size:11px;margin-top:2px;">Guideline limit: Grade 12. Syllable counts are estimated.</p>
            <button type="button" class="btn-pill-ghost" id="btnCheckAccessibilityCopy" style="margin-top:8px;padding:5px 9px;font-size:10px;">Check workspace copy</button>
            <p id="headingOrderStatus" role="status" style="font-size:10.5px;margin-top:7px;color:var(--text-muted);">Heading order: not checked</p>
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
      <button class="btn-pill-primary" id="btnDismissWcagModal">Back to audit</button>
    </div>
  </div>
</div>
`),
  claimDialog: () => component(`
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
`),
  auditDialog: () => component(`
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
        <span class="pill-tag pill-blue" id="detailModalScoreBadge">Score: —</span>
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
`),
  flowDialog: () => component(`
<div class="modal-overlay" id="modalArch">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>Prototype Review Flow</h3>
        <p style="font-size:11.5px;color:var(--text-muted);margin-top:2px;">Implemented workflow and current prototype boundaries.</p>
      </div>
      <button class="btn-close-modal" id="btnCloseArchModal">×</button>
    </div>

    <div style="display:flex;flex-direction:column;gap:10px;font-size:12px;">
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 1</span>
        <div><b>Text input and supported imports</b> Paste text or import TXT, Markdown, CSV, PDF, or DOCX. Google Docs, Slides, and CMS connectors are not implemented.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 2</span>
        <div><b>Text preparation</b> HTML tags and required-disclaimer text are handled for readability checks. Hindi and regional-language validation are not implemented.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 3</span>
        <div><b>Deterministic checks</b> Rule-based checks use the current claims ledger and guidelines for prohibited wording, claims, disclaimer presence, and text accessibility.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 4</span>
        <div><b>Claim ledger review</b> Checks active status and expiry. Optional Gemini citations are checked for text relevance; uncertain items are sent for human review.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 5</span>
        <div><b>Accessibility utilities</b> Text reading grade, heading order, and a manual color-contrast calculator. Artwork and logo pixels are not analyzed.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 6</span>
        <div><b>Severity-based score</b> Findings deduct points according to Lenient, Balanced, or Strict settings. This is a heuristic score, not a calibrated accuracy or legal-compliance probability.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 7</span>
        <div><b>Suggested fixes</b> A person may apply or edit a suggested replacement; accepted changes create a revision.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 8</span>
        <div><b>Review and approval</b> Revisions, comments, and role-checked review stages. Approval requires the configured threshold and no pending critical/high finding; publication requires approval and all findings dispositioned.</div>
      </div>
      <div class="architecture-stage">
        <span class="pill-tag pill-blue">Stage 9</span>
        <div><b>Stored review history</b> Actions are recorded on audit records. Insights uses non-sample saved records plus a synthetic labeled ruleset; it is not an immutable audit log or production benchmark.</div>
      </div>
    </div>

    <p style="font-size:11px;color:var(--text-muted);border-top:1px solid var(--line);padding-top:10px;">Not implemented: OCR, image/logo review, Google Docs/Canva/Figma, Hindi/regional-language support, and SSO.</p>

    <div style="display:flex;justify-content:flex-end;border-top:1px solid var(--line);padding-top:12px;">
      <button class="btn-pill-primary" id="btnDismissArchModal">Back to audit</button>
    </div>
  </div>
</div>
`),
  toast: () => component(`
<div id="toast">Operation Completed</div>
`),
};

document.body.prepend(...Object.values(BrandWiseLayout).map(render => render()));
