// Static app views. Render before brandwise-app.js binds controls.
const BrandWiseViews = {
  profile: () => component(`
  <main class="page-shell" id="view-profile" hidden>
    <h1 class="spaced-page-title">MY PROFILE</h1>
    <p>Review and update your account details. Changing your email requires a new verification code.</p>
    <div class="workspace-split" style="align-items:start;margin-top:22px;">
      <section class="white-panel">
        <div class="panel-kicker-head"><h3>Personal details</h3><span class="pill-tag pill-blue" id="profileRoleBadge">ROLE</span></div>
        <form id="profileEditForm">
          <label>Full name<input id="editProfileName" required maxlength="500"></label>
          <label>Username<input id="editProfileUsername" required minlength="3" maxlength="32" pattern="[A-Za-z0-9_]{3,32}"></label>
          <div class="email-verification" style="grid-column:1/-1;">
            <label for="editProfileEmail">Email</label>
            <div class="email-entry-row"><input id="editProfileEmail" type="email" required maxlength="254"><button class="btn-pill-ghost" id="sendProfileEmailOtp" type="button">Verify new email</button></div>
            <div class="email-otp-panel" id="profileEmailOtpPanel" hidden><label for="profileEmailOtpCode">6-digit email code</label><div class="email-entry-row"><input id="profileEmailOtpCode" inputmode="numeric" maxlength="6" placeholder="Enter code"><button class="btn-pill-primary" id="confirmProfileEmailOtp" type="button" disabled>Confirm code</button></div></div>
            <p class="email-verification-status" id="profileEmailStatus" role="status" aria-live="polite"></p>
          </div>
          <label>Organization<input id="editProfileOrganization" required maxlength="500"></label>
          <label>Role<select id="editProfileRole" required aria-describedby="profileRoleHelp"><option value="Creator">Creator</option><option value="External Agency">External Agency</option><option value="Reviewer">Reviewer</option><option value="Brand Manager">Brand Manager</option></select></label>
          <label>Work / job title<input id="editProfileWork" required maxlength="500"></label>
          <label style="grid-column:1/-1;">Responsibilities<input id="editProfileResponsibilities" required maxlength="500"></label>
          <p id="profileRoleHelp" style="grid-column:1/-1;font-size:11px;color:var(--text-muted);margin:0;">Choose the role that best matches your work. Admin access is managed separately.</p>
          <div style="grid-column:1/-1;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <button class="btn-pill-primary" type="submit" id="saveProfileButton">Save profile</button>
            <span id="profileSaveStatus" role="status" style="font-size:12px;color:var(--text-muted);"></span>
          </div>
        </form>
        <section class="profile-password-tools" aria-labelledby="profilePasswordHeading">
          <h4 id="profilePasswordHeading">Password &amp; sign-in</h4>
          <form id="profileChangePasswordForm" class="profile-password-form">
            <label for="profileCurrentPassword">Current password</label>
            <input id="profileCurrentPassword" type="password" autocomplete="current-password" minlength="1" maxlength="128" required>
            <label for="profileNewPassword">New password</label>
            <input id="profileNewPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128" required>
            <label for="profileConfirmPassword">Confirm new password</label>
            <input id="profileConfirmPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128" required>
            <div class="profile-password-actions"><button class="btn-pill-primary" id="saveNewPassword" type="submit">Change password</button><button class="btn-pill-ghost" id="profileForgotPassword" type="button">Forgot password?</button></div>
            <p class="profile-password-status" id="profilePasswordStatus" role="status" aria-live="polite"></p>
          </form>
          <form id="profilePasswordResetForm" class="profile-password-reset" hidden>
            <p>Verify your email with a code sent via Resend, then choose a new password.</p>
            <label for="profileResetEmail">Email</label>
            <div class="email-entry-row"><input id="profileResetEmail" type="email" autocomplete="email" required maxlength="254"><button class="btn-pill-ghost" id="profileSendResetCode" type="button">Send code</button></div>
            <div id="profileResetFields" hidden>
              <label for="profileResetCode">6-digit email code</label><input id="profileResetCode" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" placeholder="Enter 6-digit code">
              <label for="profileResetNewPassword">New password</label><input id="profileResetNewPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128" placeholder="At least 12 characters">
              <label for="profileResetConfirmPassword">Confirm new password</label><input id="profileResetConfirmPassword" type="password" autocomplete="new-password" minlength="12" maxlength="128">
              <button class="btn-pill-primary" type="submit" style="margin-top:10px;width:100%;">Reset password</button>
            </div>
            <div class="profile-password-actions"><button class="btn-pill-ghost" type="button" id="cancelProfilePasswordReset">Back to change password</button></div>
            <p class="profile-password-status" id="profilePasswordResetStatus" role="status" aria-live="polite"></p>
          </form>
        </section>
      </section>
      <section class="white-panel" style="border-color:var(--red);">
        <h3 style="color:var(--red);">Delete account</h3>
        <p style="margin:10px 0 16px;">Permanently remove your sign-in and profile. Saved audit records and review history remain for workspace traceability.</p>
        <button class="btn-pill-ghost" id="deleteAccountButton" type="button" style="color:var(--red);border-color:var(--red);">Delete my account</button>
        <form id="deleteAccountConfirmation" class="delete-account-confirmation" hidden>
          <label for="deleteAccountPassword">Enter your current password to verify this deletion</label>
          <input id="deleteAccountPassword" type="password" autocomplete="current-password" maxlength="128" required>
          <p class="delete-account-status" id="deleteAccountStatus" role="status" aria-live="polite"></p>
          <div class="delete-account-actions">
            <button class="btn-pill-ghost" id="cancelAccountDeletion" type="button">Cancel</button>
            <button class="btn-pill-primary" id="confirmAccountDeletion" type="submit" style="background:var(--red);border-color:var(--red);">Permanently delete account</button>
          </div>
        </form>
      </section>
    </div>
  </main>
`),
  assets: () => component(`
  <main class="page-shell" id="view-assets" hidden>
    <div class="page-heading-row">
      <div><div class="kicker-pills"><span class="pill-tag pill-blue">BRAND LIBRARY</span><span class="pill-tag pill-gray">ASSETS &amp; VERSIONS</span></div><h1 class="spaced-page-title">BRAND ASSETS</h1><p>Keep approved logos, colors, fonts, templates, and reference files ready for every content review.</p></div>
      <button class="btn-pill-primary" id="uploadBrandAsset">＋ Add brand asset</button><input id="brandAssetFile" type="file" accept="image/*,.pdf,.doc,.docx,.ttf,.otf,.woff,.woff2" hidden>
    </div>
    <div class="brand-asset-toolbar white-panel">
      <label>Search assets<input id="brandAssetSearch" type="search" placeholder="Search names or notes"></label>
      <label>Asset type<select id="brandAssetFilter"><option value="all">All assets</option><option>Logo</option><option>Color palette</option><option>Typography</option><option>Guidelines</option><option>Template</option><option>Other</option></select></label>
      <label>New asset type<select id="brandAssetCategory"><option>Logo</option><option>Color palette</option><option>Typography</option><option>Guidelines</option><option>Template</option><option>Other</option></select></label>
      <label class="asset-notes-field">Notes<input id="brandAssetNotes" maxlength="240" placeholder="e.g. Primary logo for light backgrounds"></label>
      <div class="asset-library-count"><strong id="brandAssetCount">0</strong><span>saved assets</span></div>
    </div>
    <div class="brand-asset-grid" id="brandAssetGrid"></div>
    <div class="white-panel asset-empty-state" id="brandAssetEmpty"><span class="asset-empty-icon">▧</span><h3>Your brand library is ready</h3><p>Add approved files and reference material here. Assets are saved in this browser for this account.</p><button class="btn-pill-ghost" id="emptyUploadBrandAsset">Add your first asset</button></div>
    <p class="asset-storage-note">Supported files up to 1.5 MB. The library is stored locally in this browser and is not uploaded to a shared workspace.</p>
  </main>
`),
  calendar: () => component(`
  <main class="page-shell" id="view-calendar" hidden>
    <div class="page-heading-row">
      <div><div class="kicker-pills"><span class="pill-tag pill-blue">WORKSPACE PLANNER</span><span class="pill-tag pill-orange">REMINDERS</span></div><h1 class="spaced-page-title">CALENDAR</h1><p>Plan campaign reviews, meetings, and follow-up tasks. Turn on browser notifications for timely reminders.</p></div>
      <button class="btn-pill-ghost" id="enableCalendarNotifications" type="button">Allow notifications</button>
    </div>
    <div class="calendar-layout">
      <aside class="calendar-sidebar">
        <section class="white-panel calendar-event-form-panel">
          <h2>Add a reminder</h2>
          <p>Schedule a task, meeting, or review checkpoint.</p>
          <form id="calendarEventForm">
            <label>Title<input id="calendarEventTitle" required maxlength="100" placeholder="e.g. Review launch campaign"></label>
            <label>Type<select id="calendarEventType"><option>Task</option><option>Meeting</option><option>Review</option><option>Reminder</option></select></label>
            <div class="calendar-date-row"><label>Date<input id="calendarEventDate" type="date" required></label><label>Time<input id="calendarEventTime" type="time" required></label></div>
            <label>Notes <span class="optional-label">(optional)</span><textarea id="calendarEventNotes" rows="3" maxlength="300" placeholder="Agenda, link, or details"></textarea></label>
            <label class="calendar-notify-toggle"><input id="calendarEventNotify" type="checkbox" checked><span>Notify me at this time</span></label>
            <button class="btn-pill-primary" type="submit">Save reminder</button>
            <p id="calendarFormStatus" class="calendar-notice" role="status" aria-live="polite"></p>
          </form>
        </section>
        <section class="white-panel calendar-selected-day">
          <div class="calendar-list-heading"><h2 id="calendarDayLabel">Selected day</h2></div>
          <div id="calendarDayEvents" class="calendar-upcoming-list"></div>
        </section>
        <section class="white-panel calendar-upcoming"><div class="calendar-list-heading"><div><h2>Upcoming</h2><p>Your next scheduled tasks and meetings.</p></div><span class="pill-tag pill-blue" id="calendarUpcomingCount">0 ITEMS</span></div><div id="calendarUpcomingList" class="calendar-upcoming-list"></div></section>
      </aside>
      <section class="white-panel calendar-board">
        <div class="calendar-month-heading">
          <div><h2 id="calendarMonthLabel"></h2><div class="calendar-range" id="calendarMonthRange"></div></div>
          <div class="calendar-controls">
            <input id="calendarSearch" type="search" aria-label="Search calendar events" placeholder="Search calendar events…">
            <button class="btn-pill-ghost" id="calendarPrevMonth" type="button" aria-label="Previous month">‹</button>
            <button class="btn-pill-ghost" id="calendarToday" type="button">Today</button>
            <button class="btn-pill-ghost" id="calendarNextMonth" type="button" aria-label="Next month">›</button>
            <button class="btn-pill-primary" id="calendarAddReminder" type="button">+ Add reminder</button>
          </div>
        </div>
        <div class="calendar-filters">
          <div class="calendar-filter-buttons" role="group" aria-label="Filter calendar by type">
            <button class="btn-pill-ghost" type="button" data-calendar-type="" aria-pressed="true">All</button>
            <button class="btn-pill-ghost" type="button" data-calendar-type="Task" aria-pressed="false">Tasks</button>
            <button class="btn-pill-ghost" type="button" data-calendar-type="Meeting" aria-pressed="false">Meetings</button>
            <button class="btn-pill-ghost" type="button" data-calendar-type="Review" aria-pressed="false">Reviews</button>
            <button class="btn-pill-ghost" type="button" data-calendar-type="Reminder" aria-pressed="false">Reminders</button>
          </div>
          <span class="calendar-legend" id="calendarMatchCount" role="status"></span>
        </div>
        <div class="calendar-grid-scroll" role="region" aria-label="Month view" tabindex="0">
          <div class="calendar-weekdays" aria-hidden="true"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
          <div class="calendar-days" id="calendarDays"></div>
        </div>
        <p class="calendar-notice" id="calendarNotificationStatus" role="status" aria-live="polite">Reminders appear here while the app is open. Browser notifications need permission.</p>
      </section>
    </div>
    <p class="asset-storage-note">Reminders are shared within the active workspace. Keep BrandWise open to receive scheduled notifications.</p>
  </main>
`),
  team: () => component(`
  <main class="page-shell" id="view-team" hidden>
    <div class="page-heading-row">
      <div><div class="kicker-pills"><span class="pill-tag pill-orange">ADMIN ONLY</span><span class="pill-tag pill-blue">TEAM ACTIVITY</span></div><h1>TEAM OVERVIEW</h1><p>See each person’s role, organization, current work focus, and recent audit submissions.</p></div>
      <button class="btn-pill-ghost" type="button" id="refreshAdminTeam">Refresh team</button>
    </div>
    <div class="four-stat-cards team-role-stats" id="adminTeamRoleStats"></div>
    <section class="white-panel" style="margin-top:16px;">
      <div class="panel-kicker-head"><h3>People &amp; work focus</h3><span class="pill-tag pill-gray" id="adminTeamCount">0 PEOPLE</span></div>
      <p class="team-privacy-note">Admin visibility includes registered profile and work details plus audits attributed to each person. Passwords and authentication secrets are never shown.</p>
      <div class="table-container"><table class="styled-table"><thead><tr><th>PERSON</th><th>ROLE</th><th>ORGANIZATION</th><th>JOB / WORK</th><th>RESPONSIBILITIES</th><th>RECENT AUDITS</th></tr></thead><tbody id="adminTeamRows"></tbody></table></div>
      <p class="team-load-status" id="adminTeamStatus" role="status" aria-live="polite"></p>
    </section>
  </main>
`),
  workspace: () => component(`
  <main class="page-shell" id="view-workspace">
    <div class="kicker-pills workspace-subnav" style="justify-content:center;" id="workspaceSubnav"></div>

    <!-- Centered Hero -->
    <div class="hero-center">
      <div style="position:relative;display:inline-block;">
        <span style="position:absolute;left:-44px;top:-10px;font-size:24px;">👀</span>
        <h1>WE VERIFY<br><em>CONTENT PEOPLE</em><br><b>LOVE.</b></h1>
        <span style="position:absolute;right:-60px;top:0;font-size:12px;background:var(--card-bg);border:1px solid var(--line);border-radius:var(--radius-pill);padding:4px 9px;font-weight:700;">🌈 FAST SCAN</span>
      </div>
      <p>Every statement deserves ammo, and a foundation. Audit digital claims, typography licenses, and brand assertions in real-time with cartoon clarity.</p>
      
    </div>
    <!-- Content to Check vs Audit Report (Split Grid) -->
    <div class="workspace-split">
      <!-- 01 Content to Check -->
      <div class="white-panel" style="display:flex;flex-direction:column;gap:12px;">
        <div class="panel-kicker-head">
          <h3><span class="badge-num">01</span> Content To Check</h3>
        </div>
        <p style="font-size:12px;color:var(--text-muted);">Draft claims, advertising hooks, and hero statements for automated compliance verification.</p>
        
        <label for="auditTitleInput" style="font-size:11px;font-weight:700;">Audit name</label>
        <input id="auditTitleInput" maxlength="150" placeholder="Name this audit (optional)">
        <button type="button" class="btn-pill-ghost draft-panel-button" id="btnNewAudit" style="align-self:flex-start;margin-top:6px;">Start new audit</button>
        <label for="workspaceInput" style="font-size:11px;font-weight:700;">Draft content</label>
        <textarea class="workspace-textarea" id="workspaceInput" placeholder="Paste marketing copy here..."></textarea>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 0;">
          <input type="file" id="auditDraftFile" accept=".txt,.md,.csv,.pdf,.docx" hidden>
          <button type="button" class="btn-pill-ghost draft-panel-button" id="importAuditDraftButton">Import draft</button>
          <span id="draftImportStatus" role="status" aria-live="polite" style="font-size:11px;color:var(--text-muted);margin:0;">Paste a draft to begin. Imported text is shown here before you run checks.</span>
        </div>
        
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;color:var(--text-dim);">
          <span id="charCountLabel">⏱ 18 words · text pasted</span>
          <span>14 min</span>
        </div>

        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:10.5px;" id="btnLoadShortNote" title="Approved Claim CLM-001 with up to 20%">Short Note</button>
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:10.5px;" id="btnLoadInstagram" title="Indian English fairness test without tone penalties">Instagram Post</button>
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:10.5px;" id="btnLoadAdHeadline" title="Overpromising 10x claim with replacement">Ad Headline</button>
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:10.5px;" id="btnLoadPrivacy" title="Expired pricing claim CLM-005 ($49/mo) and corporate founding year">Privacy Review</button>
        </div>

        <div style="display:flex;gap:8px;margin-top:6px;border-top:1px dashed var(--line);padding-top:10px;">
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:11px;" id="btnOpenDiffFromPanel">⚖️ View Revision Diff</button>
          <button type="button" class="btn-pill-ghost draft-panel-button" style="padding:4px 10px;font-size:11px;" id="btnOpenWcagFromPanel">🎨 Test WCAG Contrast</button>
        </div>
      </div>

      <!-- 02 Audit Report -->
      <div class="white-panel" style="display:flex;flex-direction:column;justify-content:space-between;">
        <div>
          <div class="panel-kicker-head">
            <h3><span class="badge-num">02</span> Audit Report</h3>
            <span class="pill-tag pill-gray" id="reportHeaderBadge">NO RESULTS</span>
          </div>

          <div style="display:flex;align-items:baseline;justify-content:space-between;margin:10px 0 6px;">
            <div>
              <small style="font-size:10px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">AVERAGE FINDING CONFIDENCE</small>
              <div style="font-family:'Barlow Condensed',sans-serif;font-size:36px;font-weight:900;color:var(--navy);line-height:1;" id="reportConfidenceVal">—</div>
              <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Compliance score: <b id="reportComplianceVal">No audit results yet</b></div>
            </div>
            <div id="reportResultIcon" style="width:28px;height:28px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            </div>
          </div>

          <!-- 6-State Governance Lifecycle Controller -->
          <div id="governanceLifecycle" style="display:flex;align-items:center;justify-content:space-between;background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-pill);padding:4px 10px;margin-bottom:12px;font-size:11px;">
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-size:9.5px;font-weight:800;color:var(--text-dim);text-transform:uppercase;">STAGE:</span>
              <span class="pill-tag pill-gray" id="lifecycleBadge" style="font-size:9px;padding:2px 8px;">Not started</span>
            </div>
            <div style="display:flex;gap:4px;" id="governanceActionButtons">
              <button type="button" class="btn-pill-ghost" style="padding:2px 8px;font-size:10px;" id="btnReqChanges" disabled>Request Changes</button>
              <button type="button" class="btn-pill-primary" style="padding:2px 8px;font-size:10px;" id="btnApproveDraft" disabled>Approve</button>
              <button type="button" class="btn-pill-orange" style="padding:2px 8px;font-size:10px;" id="btnPublishDraft" disabled>Publish</button>
            </div>
          </div>

          <div style="font-size:10px;color:var(--text-dim);margin:-3px 0 5px;">Finding counts by topic (these are not pass-rate percentages)</div>
          <div class="report-breakdown-row">
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Claims &amp; facts</span><span style="color:var(--green)" id="bar1Label">0 findings</span></div>
              <div class="report-track"><div class="report-fill" id="bar1Fill" style="width:0%;background:var(--green);"></div></div>
            </div>
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Wording &amp; claims tone</span><span style="color:var(--orange)" id="bar2Label">0 findings</span></div>
              <div class="report-track"><div class="report-fill" id="bar2Fill" style="width:0%;background:var(--orange);"></div></div>
            </div>
            <div class="report-bar-item">
              <div class="report-bar-label"><span>Brand &amp; identity</span><span style="color:var(--blue-text, var(--blue))" id="bar3Label">0 findings</span></div>
              <div class="report-track"><div class="report-fill" id="bar3Fill" style="width:0%;background:var(--blue);"></div></div>
            </div>
          </div>

          <!-- Suggestion Box with One-Click Fix -->
          <div class="suggestion-box" id="reportSuggestionBox" hidden></div>

          <!-- Dynamic Findings Accordion -->
          <div class="findings-accordion" id="findingsContainer">
            <!-- Rendered dynamically -->
          </div>
          <section id="reportTrailPanel" style="margin-top:12px;" hidden>
            <div style="font-size:11px;font-weight:800;color:var(--navy);margin-bottom:6px;">Audit activity</div>
            <div id="reportAuditTrail" style="display:grid;gap:5px;"></div>
          </section>
        </div>

        <div class="audit-report-footer">
          <span id="analysisTimingLabel">⚡ Audit request timing appears after analysis</span>
          <button type="button" class="btn-pill-ghost" id="btnExportPDF" disabled>EXPORT PDF</button>
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
`),
  guidelines: () => component(`
  <main class="page-shell" id="view-guidelines" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;">
          <span class="pill-tag pill-orange">v2.4 LIVE</span>
          <span class="pill-tag pill-blue">Source of Truth</span>
          <span class="pill-tag pill-gray">Updated 2d ago</span>
        </div>
        <h1 class="spaced-page-title">OFFICIAL GUIDELINES</h1>
        <p>Your approved facts, core messaging rules, and legal guardrails in one playful spot.</p>
      </div>
      <div style="display:flex;gap:8px;">
      </div>
    </div>

    <!-- Category selector pills (Clickable category filter) -->
    <div class="kicker-pills" style="border-bottom:1px solid var(--line);padding-bottom:12px;" id="guidelineFilters"></div>

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
            <div style="font-size:15px;font-weight:800;color:var(--navy);" id="guidelineFoundationYear">From current ledger</div>
            <div style="font-size:11px;color:var(--text-muted);">Citation: Delaware Certificate of Incorporation #4829104.</div>
          </div>

          <!-- Rule 3: Approved Claims -->
          <div class="rule-item-box" data-rule-cat="claims">
            <div class="rule-item-header">
              <small>APPROVED CLAIMS · CLM-001</small>
              <span class="pill-tag pill-blue" style="font-size:9px;">Product Performance</span>
            </div>
            <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;" id="guidelinePerformanceClaim">From current ledger</div>
            <div style="font-size:11.5px;color:var(--text-muted);">
              Evidence: 2026 Enterprise Benchmark Study, Section 4.2. Owner: Sarah Jenkins (VP Product). Expiry: 2027-12-31.
            </div>
          </div>

          <div class="rule-item-box" data-rule-cat="claims">
            <div class="rule-item-header"><small id="guidelinePricingId">ACTIVE PRICING CLAIM</small><span class="pill-tag pill-blue" style="font-size:9px;">Pricing &amp; Licensing</span></div>
            <div style="font-weight:800;font-size:13.5px;color:var(--navy);margin:2px 0;" id="guidelinePricingClaim">Loading current pricing claim…</div>
            <div style="font-size:11.5px;color:var(--text-muted);" id="guidelinePricingEvidence"></div>
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
          <input type="file" id="fileDocUpload" style="display:none;" accept=".txt,.md,.csv,.pdf,.docx">
          <div style="width:40px;height:40px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
          </div>
          <div style="font-weight:700;font-size:13px;color:var(--navy);">Drop company docs here</div>
          <p style="font-size:11px;">or browse from file agent workspace</p>
          <div style="display:flex;gap:6px;font-size:9.5px;font-weight:700;color:var(--text-dim);">
            <span>TXT</span> · <span>MD</span> · <span>CSV</span> · <span>PDF</span> · <span>DOCX</span>
          </div>
          <button class="btn-pill-primary" style="padding:6px 16px;font-size:11.5px;margin-top:4px;" type="button" id="btnSelectFileDoc">Select File</button>
        </div>

        <!-- Rule Coverage -->
        <div class="white-panel" style="padding:16px 20px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <b style="font-size:12px;">Rule Coverage</b>
            <span style="font-size:10px;color:var(--text-muted);font-weight:700;">Configured rules</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;font-size:11.5px;">
            <div style="display:flex;justify-content:space-between;"><span>Company Identity</span><b>Ledger based</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Approved Claims</span><b style="color:var(--blue-text, var(--blue));" id="guidelineClaimCounts">Loading…</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Prohibited Terms</span><b style="color:var(--orange);" id="guidelineTermCount">Loading…</b></div>
            <div style="display:flex;justify-content:space-between;"><span>Legal Disclaimers</span><b style="color:var(--green);">Active &amp; Enforced</b></div>
          </div>
          <div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;font-size:10.5px;color:var(--text-dim);">
            <div style="width:16px;height:16px;border-radius:50%;border:2px solid var(--blue);border-top-color:transparent;animation:spin 1s linear infinite;"></div>
            <span>Local ledger and guideline changes are used by subsequent audits.</span>
          </div>
        </div>

        <!-- Playful Banner -->
        <div class="banner-playful">
          <small>PLAYFUL FACT</small>
          <h4>NO BORING POLICIES.</h4>
          <p>Creative freedom lives inside crystal clear boundaries.</p>
        </div>
      </div>
    </div>

    <div style="font-size:11px;color:var(--text-dim);display:flex;justify-content:space-between;">
      <span>💡 Pro-Tip: The scanner engine reads Indian English phrases ('prepone', 'revert back') contextually without penalization.</span>
      <a href="#" style="color:var(--blue-text, var(--blue));font-weight:600;" id="btnIndianEnglishNote">Read Guidance</a>
    </div>
  </main>
`),
  history: () => component(`
  <main class="page-shell" id="view-history" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;" id="historyNavigation"></div>
        <h1 class="spaced-page-title">AUDIT HISTORY &amp; INSIGHTS</h1>
        <p>Track past creative audits, monitor the compliance drift, and zap issues before campaigns launch to market.</p>
      </div>
      <div class="history-actions">
        <select class="btn-pill-ghost history-dropdown" id="historyRangeButton" aria-label="Filter audit archive by date range">
          <option value="all">📅 All time</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="year">This year</option>
        </select>
        <select class="btn-pill-ghost history-dropdown" id="historySortButton" aria-label="Sort audit archive">
          <option value="newest">⇕ Newest first</option>
          <option value="oldest">⇕ Oldest first</option>
        </select>
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
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);" id="histTotalAudits">—</strong>
          <span class="pill-tag pill-blue" style="font-size:9px;" id="histWeeklyDelta">Live data</span>
        </div>
        <p style="font-size:11px;" id="histWorkstreams">Across saved audit records</p>
      </div>

      <div class="stat-box highlight-blue">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>AVG COMPLIANCE</small>
          <span>✦</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;" id="histAverageCompliance">—</strong>
          <span style="font-size:10px;background:rgba(255,255,255,0.2);padding:2px 6px;border-radius:var(--radius-pill);" id="histTargetThreshold">Target —</span>
        </div>
        <p style="font-size:11px;" id="histAverageNote">Average of saved audit scores</p>
      </div>

      <div class="stat-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>ISSUES DETECTED</small>
          <span style="color:var(--orange)">⚠</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);" id="histIssuesDetected">—</strong>
          <span class="pill-tag pill-orange" style="font-size:9px;" id="histIssuesResolved">0 resolved</span>
        </div>
        <p style="font-size:11px;" id="histAutoFixes">Suggested fixes from saved findings</p>
      </div>

      <div class="stat-box">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <small>PASSED AUDITS</small>
          <span style="color:var(--green)">✓</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:36px;color:var(--navy);" id="histPassedAudits">—</strong>
          <span class="pill-tag pill-green" style="font-size:9px;" id="histPassRate">— Pass Rate</span>
        </div>
        <p style="font-size:11px;">Audits meeting the current passing threshold</p>
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
            <span style="color:var(--orange)" id="historyTrendThreshold">- - Passing threshold</span>
          </div>
        </div>

        <div id="historyTrendSummary" style="height:160px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);text-align:center;">Trend chart will appear after real audit records are saved.</div>
      </div>

      <!-- Impact Focus & Distribution -->
      <div class="chart-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">IMPACT FOCUS</small>
            <h3 style="font-size:16px;">Issue Distribution</h3>
          </div>
          <span class="pill-tag pill-gray" style="font-size:9px;" id="issueDistributionTotal">0 findings</span>
        </div>
        <p style="font-size:11px;">Severity distribution from saved non-sample audits.</p>

        <div id="historySeverityDistribution" style="display:flex;flex-direction:column;gap:8px;margin-top:4px;color:var(--text-muted);">No measured audit findings yet.</div>
      </div>
    </div>

    <!-- SUB-VIEW 1: Audit Archive Log (Table) -->
    <div class="white-panel history-subview active" id="subview-hist-archive" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:14px;">
        <div>
          <h3>Audit Archive Log</h3>
          <p style="font-size:11.5px;">Historical demo rows are marked as sample data; live metrics exclude them.</p>
        </div>
        <div class="archive-filters">
          <input type="text" id="archiveSearch" placeholder="Search audit name or reviewer..." aria-label="Search audit name or reviewer" style="width:230px;border-radius:var(--radius-pill);padding:6px 14px;">
          <label style="font-size:11px;color:var(--text-muted)">From <input type="date" id="archiveDateFrom" aria-label="Filter audits from date"></label>
          <label style="font-size:11px;color:var(--text-muted)">To <input type="date" id="archiveDateTo" aria-label="Filter audits through date"></label>
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
          <tbody id="historyTableRows"><tr><td colspan="7">Loading saved audits…</td></tr></tbody>
        </table>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;font-size:11px;color:var(--text-dim);">
        <span id="historyTableSummary">Audit archive is loading saved records.</span>
      </div>
    </div>

    <!-- SUB-VIEW 2: Ambiguous Rules Detection (PDF Page 10) -->
    <div class="white-panel history-subview" id="subview-hist-ambiguous" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Ambiguous Guideline Detection</h3>
          <p style="font-size:11.5px;">Counts are calculated from dismissed findings and incorrect-flag reports on saved non-sample audits.</p>
        </div>
        <span class="pill-tag pill-orange" id="ambiguousRuleCount">0 DISPUTED RULES</span>
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
          <tbody id="ambiguousRulesRows"><tr><td colspan="5">No disputed findings recorded yet.</td></tr></tbody>
        </table>
      </div>
    </div>

    <!-- SUB-VIEW 3: External Agency Benchmarks (PDF Page 9) -->
    <div class="white-panel history-subview" id="subview-hist-agency" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Agency Compliance Scorecard</h3>
          <p style="font-size:11.5px;">Scores and approval rates use saved non-sample audits. Turnaround time is not measured.</p>
        </div>
        <span class="pill-tag pill-blue" id="agencyBenchmarkCount">0 TEAMS WITH AUDITS</span>
      </div>

      <div class="table-container">
        <table class="styled-table">
          <thead>
            <tr>
              <th>AGENCY / TEAM</th>
              <th>SUBMISSIONS</th>
              <th>AVG SCORE</th>
              <th>APPROVAL RATE</th>
              <th>TURNAROUND</th>
            </tr>
          </thead>
          <tbody id="agencyStatsRows"><tr><td colspan="5">No saved team audit data yet.</td></tr></tbody>
        </table>
      </div>
    </div>

    <!-- SUB-VIEW 4: Business Impact & ROI Metrics (PDF Page 11) -->
    <div class="white-panel history-subview" id="subview-hist-impact" style="padding:24px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <div>
          <h3>Enterprise Impact &amp; Evidence Metrics</h3>
          <p style="font-size:11.5px;">Operational counts use saved non-sample audits. Accuracy rates below use the synthetic labeled set, not production traffic.</p>
        </div>
        <span class="pill-tag pill-orange">SYNTHETIC TEST SET</span>
      </div>

      <div class="four-stat-cards" style="margin-top:10px;">
        <div class="stat-box" style="border-left:4px solid var(--blue);">
          <small>REVIEW CYCLE TIME</small>
          <strong style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--blue-text, var(--blue));">Not measured</strong>
          <p style="font-size:11.5px;">No timed pilot baseline is available.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--green);">
          <small>DETECTION RATE</small>
          <strong id="impactDetectionRate" style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--green);">Calculating…</strong>
          <p style="font-size:11.5px;">Measured on the synthetic labeled rule set below, not on production traffic.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--orange);">
          <small>SOURCE-LINKED FINDINGS</small>
          <strong id="impactSourceLinked" style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--orange);">—</strong>
          <p style="font-size:11.5px;">Count in saved live audits; this does not measure whether a source supports a finding.</p>
        </div>
        <div class="stat-box" style="border-left:4px solid var(--navy);">
          <small>FALSE-FLAG RATE</small>
          <strong id="impactFalseFlagRate" style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--navy);">Calculating…</strong>
          <p style="font-size:11.5px;">Synthetic-set false-flag rate; it is not a measured production rate.</p>
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
`),
  settings: () => component(`
  <main class="page-shell" id="view-settings" hidden>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;">
      <div>
        <div class="kicker-pills" style="margin-bottom:8px;">
          <span class="pill-tag pill-orange">SETTINGS ACTIVE</span>
          <span class="pill-tag pill-blue">APPLIED TO NEXT AUDIT</span>
        </div>
        <h1 class="spaced-page-title">WORKSPACE SETTINGS</h1>
        <p>Personalize your brand intelligence workspace, strictness parameters, and audit dispatch triggers.</p>
      </div>
      <div style="display:flex;align-items:center;gap:8px;background:var(--card-bg);border:1px solid var(--line);padding:8px 16px;border-radius:var(--radius-md);">
        <div style="width:28px;height:28px;border-radius:50%;background:var(--blue-light);color:var(--blue-text, var(--blue));display:flex;align-items:center;justify-content:center;">
          <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>
        </div>
        <div>
          <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">PRIMARY TENANT</small>
          <div id="storageStatusLabel" style="font-weight:700;font-size:12px;color:var(--navy);">Checking storage…</div>
        </div>
      </div>
    </div>

    <!-- Settings Split Layout -->
    <div class="settings-split-layout">
      <!-- Left sub-nav -->
      <div class="settings-nav-pane" role="group" aria-label="Preference sections" id="settingsNavigation"></div>

      <!-- Right settings cards -->
      <div id="settingsPanelContent" style="display:flex;flex-direction:column;gap:18px;">

        <header class="white-panel settings-section-heading" id="settingsSectionHeading">
          <h2 id="settingsSectionTitle">General</h2>
          <p id="settingsSectionDescription">Choose a preference section to manage only the settings related to that area.</p>
        </header>

        <section class="white-panel settings-overview-panel" data-settings-panel="general">
          <h3>General preferences</h3>
          <p>Manage how this workspace behaves across reviews. These defaults apply to new audits unless a reviewer changes them.</p>
          <div class="settings-general-options">
            <label for="defaultChannel">Default content type
              <select id="defaultChannel">
                <option>Website Copy</option><option>Digital Ad</option><option>Marketing Email</option><option>Social Post</option>
              </select>
            </label>
            <label for="defaultAiReview">Optional AI review
              <select id="defaultAiReview"><option value="off">Ask each time</option><option value="on">Include Llama 3.2 in browser by default</option></select>
            </label>
            <label class="settings-check-row"><input id="saveAuditHistory" type="checkbox" checked> Remember unsaved draft in this browser</label>
            <small style="color:var(--text-muted)">This controls only the draft saved in this browser. Submitted audits are stored in your workspace history.</small>
          </div>
        </section>

        <section id="appearancePanel" class="white-panel" data-settings-panel="visual" aria-labelledby="appearanceTitle" hidden>
          <h2 id="appearanceTitle">Appearance</h2>
          <label for="themePreference">
            Color theme
            <select id="themePreference">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
        </section>
        <!-- Preference summaries are shown only in the section they describe. -->
        <div class="tiles-grid-2" data-settings-grid>
          <div class="white-panel" data-settings-panel="profile" style="padding:16px;">
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:0 0 4px;" id="activeWorkspaceName">Private workspace</div>
            <p id="activeWorkspaceRole" style="font-size:12px;margin:0 0 12px;">Private to you</p>
            <label for="workspaceSwitcher" style="display:block;margin-top:14px;font-weight:700;font-size:11px;">Switch company</label>
            <select id="workspaceSwitcher" aria-label="Switch company workspace"><option value="">Private workspace</option></select>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
              <input id="newWorkspaceName" placeholder="New company name" aria-label="New company name" style="flex:1;min-width:150px;">
              <button class="btn-pill-primary workspace-action-button" id="createWorkspaceButton" type="button">Create company</button>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
              <input id="workspaceInviteCode" placeholder="Invitation code" aria-label="Company invitation code" style="flex:1;min-width:150px;">
              <button class="btn-pill-ghost workspace-action-button" id="joinWorkspaceButton" type="button">Join company</button>
            </div>
            <div id="workspaceInviteAdmin" hidden style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
              <input id="workspaceInviteEmail" type="email" placeholder="Teammate's verified email" aria-label="Invitee verified email" style="flex:1;min-width:150px;">
              <select id="workspaceInviteRole" aria-label="Company role"><option>Creator</option><option>External Agency</option><option>Reviewer</option><option>Brand Manager</option></select>
              <button class="btn-pill-ghost workspace-action-button" id="createWorkspaceInviteButton" type="button">Create invitation</button>
            </div>
            <div id="workspaceInviteStatus" role="status" style="font-size:11px;margin-top:6px;"></div>
          </div>

          <div class="white-panel" data-settings-panel="profile" style="padding:16px;">
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:0 0 4px;">Workspace membership</div>
            <p style="font-size:12px;margin:0;">Invitations are linked to email. Company data is shared with workspace members.</p>
          </div>

          <div class="white-panel" data-settings-panel="visual" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">ACTIVE COLOR FLOW</small>
              <div class="theme-picker" style="display:flex;align-items:center;gap:8px;" aria-label="Choose color theme">
                <span class="theme-hint">Change theme</span>
                <button type="button" class="theme-swatch" data-theme-choice="light" aria-label="Use light colors" title="Light"></button>
                <button type="button" class="theme-swatch" data-theme-choice="dark" aria-label="Use dark colors" title="Dark"></button>
                
              </div>
            </div>
            <div style="font-size:16px;font-weight:800;color:var(--navy);margin:4px 0 8px;">Color theme</div>
            <div style="display:flex;gap:6px;font-size:10px;">
              <span class="pill-tag pill-gray">Light or dark</span>
            </div>
          </div>

          <div class="white-panel" data-settings-panel="brand" style="padding:16px;">
            <div style="font-size:14px;font-weight:750;color:var(--navy);">Auditing guidelines</div>
            <div style="font-size:11px;color:var(--text-muted);margin:4px 0 10px;">v2.4 <span aria-hidden="true">·</span> Updated 2 days ago</div>
            <button class="guidelines-review-link" id="btnReviewGuidelines" type="button">Review current rules →</button>
          </div>
        </div>

        <!-- Strictness & Passing Thresholds -->
        <div class="white-panel" data-settings-panel="strictness">
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
            These are shared workspace settings used by every signed-in role. Strictness adjusts finding penalties and Strict mode adds a check for unsupported numeric multipliers. The passing threshold marks lower scores for review.
            <span id="auditPreferenceSyncStatus" role="status" style="display:block;margin-top:5px;font-weight:700;color:var(--blue-text,var(--blue));">Loading shared settings…</span>
          </p>

          <div class="threshold-setting" style="display:flex;align-items:center;justify-content:space-between;background:var(--card-elevated);border:1px solid var(--line);border-radius:var(--radius-md);padding:14px 18px;">
            <div>
              <strong style="font-family:'Barlow Condensed',sans-serif;font-size:28px;color:var(--navy);line-height:1;" id="thresholdDisplayVal">80%</strong>
              <div style="font-size:11px;font-weight:700;color:var(--navy);">Target Passing Score</div>
              <div style="font-size:10.5px;color:var(--text-dim);" id="thresholdHelpText">Audits below this score are marked for additional review.</div>
            </div>
            <div style="display:flex;align-items:center;gap:12px;width:240px;">
              <span style="font-size:11px;color:var(--text-dim);">50%</span>
              <input type="range" id="thresholdSlider" min="50" max="95" value="80" style="flex:1;">
              <span style="font-size:11px;color:var(--text-dim);">95%</span>
            </div>
          </div>
        </div>

        <!-- Active Alerts Dispatch & Studio Preview -->
        <div class="tiles-grid-2" data-settings-grid>
          <div class="white-panel" data-settings-panel="notifications" style="padding:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:18px;">📬</span>
                <div>
                  <b style="font-size:12px;">Active Alerts Dispatch</b>
                  <div style="font-size:10.5px;color:var(--text-dim);">In-app alerts &amp; browser reminders</div>
                </div>
              </div>
              <span class="pill-tag pill-orange" id="activeAlertCount">0 active</span>
            </div>

            <div id="settingsAlertsList" role="status" style="display:flex;flex-direction:column;gap:8px;font-size:11px;margin-top:10px;">No active alerts.</div>
          </div>

          <div class="white-panel" data-settings-panel="brand" style="padding:16px;">
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
        <div class="white-panel" data-settings-panel="apikeys">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div>
              <small style="font-size:9.5px;font-weight:700;color:var(--text-dim);text-transform:uppercase;">CONNECTED SERVICES</small>
              <h3 style="font-size:17px;">AI Review Credentials</h3>
            </div>
            <span class="pill-tag pill-blue">LOCAL RULES + OPTIONAL AI</span>
          </div>

          <p style="font-size:11.5px;color:var(--text-muted);margin-bottom:16px;">
            Built-in rules run locally without an API key. Add a Google AI Studio key for optional Gemini reviews within its free-tier limits.
          </p>

          <div class="mobile-stack" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">

            <div>
              <label style="font-size:11px;font-weight:700;display:block;margin-bottom:4px;">Optional Google Gemini API Key</label>
              <div style="display:flex;gap:6px;">
                <input type="password" id="keyGemini" placeholder="AIzaSy..." style="flex:1;">
                <button class="btn-pill-ghost" style="padding:4px 10px;font-size:11px;" id="testGeminiBtn" type="button">Test</button>
              </div>
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" style="display:block;width:fit-content;margin-top:4px;font-size:11px;font-weight:700;color:var(--blue-text, var(--blue));text-decoration:underline;">Get a free-tier Gemini API key &#8599;</a>
              <span style="font-size:10px;color:var(--text-dim);" id="geminiStatus">Model configured on the server</span>
            </div>


            <div style="padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:var(--card-subtle);">
              <b style="font-size:11px;">Local Llama notifications</b>
              <p style="font-size:10.5px;color:var(--text-muted);margin:5px 0 0;">Approval and change-request alerts stay in this app. If Llama is already loaded, it writes a short summary on this device; otherwise a standard alert is shown. Nothing is sent to Slack.</p>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div data-settings-panel="apikeys" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:6px;">
          <div style="display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--text-muted);">
            <span style="color:var(--blue-text, var(--blue))">●</span>
            <span id="settingsNotificationSummary">No unread alerts.</span>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-pill-ghost" id="btnResetSettings" type="button">Reset to Defaults</button>
            <button class="btn-pill-orange" id="btnSaveSettings" type="button">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </main>
`),
};

document.getElementById("appViews").replaceChildren(...Object.values(BrandWiseViews).map(render => render()));
