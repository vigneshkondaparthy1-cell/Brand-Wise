
(()=>{
'use strict';

const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

let currentAuditRecord = null;
let currentRole = 'Creator';
let currentUserRecord = null;
let activeCompanyRole = null;
let activeCompanyId = null;

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
  if (tabName === 'team' && activeCompanyRole !== 'Admin') { toast('Only a company admin can open Team Overview.'); return; }
  $$('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.tab === tabName);
  });
  $$('.page-shell').forEach(view => {
    view.hidden = view.id !== `view-${tabName}`;
  });
  if (tabName === 'assets') renderBrandAssets();
  if (tabName === 'calendar') renderCalendar();
  if (tabName === 'team') loadAdminTeam();
  if (tabName === 'history') refreshHistoryMetrics();
  if (tabName === 'history') refreshImpactMetrics();
  if (tabName === 'settings') loadAlerts();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

const sidebar = $('.sidebar');
const sidebarToggle = $('#sidebarToggle');
try { if (localStorage.getItem('brandwise-sidebar-collapsed') === 'true') sidebar.classList.add('collapsed'); } catch {}
function syncSidebarToggle() {
  const collapsed = sidebar.classList.contains('collapsed');
  sidebarToggle.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
  sidebarToggle.setAttribute('aria-label', sidebarToggle.title);
  sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
}
syncSidebarToggle();
sidebarToggle.onclick = () => { sidebar.classList.toggle('collapsed'); syncSidebarToggle(); try { localStorage.setItem('brandwise-sidebar-collapsed', String(sidebar.classList.contains('collapsed'))); } catch {} };

const brandHeaderLink = $('#brandHeaderLink');
if (brandHeaderLink) {
  brandHeaderLink.addEventListener('click', e => {
    e.preventDefault();
    $$('.modal.open').forEach(m => m.classList.remove('open'));
    setTab('workspace');
  });
}

$$('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    setTab(link.dataset.tab);
  });
});

// Browser-local brand asset library and calendar, separated by signed-in account.
let activeAccountName = '';
let calendarMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
let calendarSelectedDate = new Date().toISOString().slice(0, 10);
let brandAssets = [];
let calendarEvents = [];
const localKey = suffix => `brandwise-${suffix}-${activeAccountName || 'guest'}`;
function readLocalList(key) {
  try { const parsed = JSON.parse(localStorage.getItem(key) || '[]'); return Array.isArray(parsed) ? parsed : []; }
  catch { return []; }
}
function saveLocalList(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; }
  catch { toast('Browser storage is full. Remove a large file and try again.'); return false; }
}
function rememberUnsavedDraft(forceClear = false) {
  if (forceClear || !$('#saveAuditHistory')?.checked) {
    try { localStorage.removeItem(localKey('unsaved-draft')); } catch {}
    return;
  }
  try { localStorage.setItem(localKey('unsaved-draft'), JSON.stringify({content:$('#workspaceInput')?.value || '', title:$('#auditTitleInput')?.value || '', savedAt:Date.now()})); } catch {}
}
$('#workspaceInput').addEventListener('input', () => rememberUnsavedDraft());
$('#auditTitleInput')?.addEventListener('input', () => rememberUnsavedDraft());
async function saveCompanyCollection(path, value) {
  try {
    await accountRequest(path, {items:value});
    return true;
  } catch (error) {
    toast(error.message || 'Could not save shared workspace data.');
    return false;
  }
}
function dateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
}
async function loadBrandAssets() {
  try { const result = await accountRequest('/api/company-data/brand-assets'); brandAssets = Array.isArray(result.items) ? result.items : []; }
  catch { brandAssets = readLocalList(localKey('brand-assets')); }
  renderBrandAssets();
}
function renderBrandAssets() {
  const grid = $('#brandAssetGrid');
  if (!grid) return;
  const query = $('#brandAssetSearch').value.trim().toLowerCase();
  const category = $('#brandAssetFilter').value;
  const visible = brandAssets.filter(asset => (category === 'all' || asset.category === category) &&
    (!query || `${asset.name} ${asset.notes} ${asset.category}`.toLowerCase().includes(query)));
  grid.replaceChildren();
  $('#brandAssetCount').textContent = String(brandAssets.length);
  const empty = $('#brandAssetEmpty');
  empty.hidden = visible.length > 0;
  empty.querySelector('h3').textContent = brandAssets.length && !visible.length ? 'No matching assets' : 'Your brand library is ready';
  empty.querySelector('p').textContent = brandAssets.length && !visible.length ? 'Try another search or asset type.' : 'Add approved files and reference material here. Assets are saved in this browser for this account.';
  visible.forEach(asset => {
    const card = document.createElement('article'); card.className = 'brand-asset-card';
    const preview = document.createElement('div'); preview.className = 'brand-asset-preview';
    if (asset.data && asset.type?.startsWith('image/')) { const img = document.createElement('img'); img.src = asset.data; img.alt = `${asset.category} preview`; preview.append(img); }
    else preview.textContent = asset.category === 'Color palette' ? '◉' : asset.category === 'Typography' ? 'Aa' : asset.category === 'Logo' ? '◇' : '▧';
    const title = document.createElement('div'); title.className = 'brand-asset-title'; title.textContent = asset.name;
    const meta = document.createElement('div'); meta.className = 'brand-asset-meta'; meta.textContent = `${asset.category} · ${asset.status || 'Needs review'}`;
    const notes = document.createElement('p'); notes.className = 'brand-asset-notes'; notes.textContent = asset.notes || 'No notes added.';
    const actions = document.createElement('div'); actions.className = 'brand-asset-actions';
    if (asset.data) { const download = document.createElement('a'); download.className = 'btn-pill-ghost'; download.href = asset.data; download.download = asset.name; download.textContent = 'Download'; actions.append(download); }
    const status = document.createElement('button'); status.type = 'button'; status.className = 'btn-pill-ghost'; status.textContent = asset.status === 'Approved' ? 'Mark for review' : 'Approve';
    status.onclick = async () => { asset.status = asset.status === 'Approved' ? 'Needs review' : 'Approved'; if (await saveCompanyCollection('/api/company-data/brand-assets', brandAssets)) renderBrandAssets(); };
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn-pill-ghost'; remove.textContent = 'Remove';
    remove.onclick = async () => { const next = brandAssets.filter(item => item.id !== asset.id); if (await saveCompanyCollection('/api/company-data/brand-assets', next)) { brandAssets = next; renderBrandAssets(); } };
    actions.append(status, remove); card.append(preview, title, meta, notes, actions); grid.append(card);
  });
}
$('#uploadBrandAsset').onclick = $('#emptyUploadBrandAsset').onclick = () => $('#brandAssetFile').click();
$('#brandAssetSearch').oninput = renderBrandAssets;
$('#brandAssetFilter').onchange = renderBrandAssets;
$('#brandAssetFile').onchange = async event => {
  const file = event.target.files?.[0]; if (!file) return;
  if (file.size > 1.5 * 1024 * 1024) { toast('Choose a file smaller than 1.5 MB.'); event.target.value=''; return; }
  const reader = new FileReader();
  reader.onerror = () => toast('This file could not be read.');
  reader.onload = async () => {
    const asset = {id:globalThis.crypto?.randomUUID?.() || String(Date.now()), name:file.name, type:file.type, size:file.size,
      category:$('#brandAssetCategory').value, notes:$('#brandAssetNotes').value.trim(), status:'Needs review', data:String(reader.result), addedAt:new Date().toISOString()};
    brandAssets.unshift(asset);
    if (await saveCompanyCollection('/api/company-data/brand-assets', brandAssets)) { $('#brandAssetNotes').value=''; $('#brandAssetFilter').value='all'; renderBrandAssets(); toast('Brand asset shared with this company workspace.'); }
    else brandAssets.shift();
    event.target.value='';
  };
  reader.readAsDataURL(file);
};

function eventDateTime(item) { return new Date(`${item.date}T${item.time || '00:00'}`); }
async function saveCalendar() { return saveCompanyCollection('/api/company-data/calendar-events', calendarEvents); }
async function loadCalendar() {
  try { const result = await accountRequest('/api/company-data/calendar-events'); calendarEvents = Array.isArray(result.items) ? result.items : []; }
  catch { calendarEvents = readLocalList(localKey('calendar-events')); }
  selectCalendarDate(new Date());
  processCalendarNotifications();
}
async function loadWorkspaceProfile() {
  try {
    const result = await accountRequest('/api/workspaces');
    const workspaces = result.workspaces || [];
    activeCompanyId = result.activeCompanyId || null;
    const active = workspaces.find(item => item.id === activeCompanyId);
    activeCompanyRole = active?.role || null;
    $('#activeWorkspaceName').textContent = active?.name || 'Private workspace';
    $('#activeWorkspaceRole').textContent = activeCompanyRole || 'Private to you';
    $('#activeWorkspaceCount').textContent = `${workspaces.length || 1} workspace${workspaces.length === 1 ? '' : 's'}`;
    const select = $('#workspaceSwitcher');
    select.replaceChildren(new Option('Private workspace', ''));
    workspaces.forEach(item => select.add(new Option(`${item.name} · ${item.role}`, item.id)));
    select.value = activeCompanyId || '';
    select.disabled = workspaces.length === 0;
    $('#workspaceInviteAdmin').hidden = activeCompanyRole !== 'Admin';
    $('#adminTeamNav').hidden = activeCompanyRole !== 'Admin';
  } catch (error) { $('#workspaceInviteStatus').textContent = error.message; }
}
async function loadAlerts() {
  const list = $('#settingsAlertsList');
  if (!list) return;
  try {
    const result = await accountRequest('/api/alerts');
    const alerts = Array.isArray(result.alerts) ? result.alerts : [];
    $('#activeAlertCount').textContent = `${alerts.length} active`;
    list.replaceChildren();
    if (!alerts.length) { list.textContent = 'No active review alerts for this company.'; return; }
    alerts.forEach(alert => {
      const item = document.createElement('button'); item.type = 'button'; item.className = 'btn-pill-ghost';
      item.style.cssText = 'text-align:left;white-space:normal';
      item.textContent = `${alert.title || 'Untitled audit'} · ${alert.status || 'Review needed'}`;
      item.onclick = () => openAuditRecord(alert.id);
      list.append(item);
    });
  } catch (error) {
    $('#activeAlertCount').textContent = 'Unavailable';
    list.textContent = error.message || 'Could not load company alerts.';
  }
}
$('#createWorkspaceButton').onclick = async () => {
  const name = $('#newWorkspaceName').value.trim();
  try { await accountRequest('/api/workspaces', {name}); location.reload(); }
  catch (error) { toast(error.message); }
};
$('#workspaceSwitcher').onchange = async event => {
  const companyId = event.target.value;
  if (!companyId || companyId === activeCompanyId) return;
  try { await accountRequest('/api/workspaces/switch', {companyId}); location.reload(); }
  catch (error) { toast(error.message); }
};
$('#joinWorkspaceButton').onclick = async () => {
  try { await accountRequest('/api/workspaces/join', {code:$('#workspaceInviteCode').value.trim()}); location.reload(); }
  catch (error) { toast(error.message); }
};
$('#createWorkspaceInviteButton').onclick = async () => {
  const status = $('#workspaceInviteStatus');
  try {
    const result = await accountRequest('/api/workspaces/invite', {email:$('#workspaceInviteEmail').value.trim(), role:$('#workspaceInviteRole').value});
    status.textContent = `Invitation code ${result.code} is bound to ${result.email}; share it with that teammate.`;
  } catch (error) { status.textContent = error.message; }
};
const calendarTypeButtons = $$('[data-calendar-type]');
let calendarSaving = false;
let lastSavedCalendarEvent = null;

function renderCalendar() {
  if (!$('#calendarDays')) return;
  const year = calendarMonth.getFullYear(), month = calendarMonth.getMonth();
  $('#calendarMonthLabel').textContent = calendarMonth.toLocaleDateString(undefined, {month:'long', year:'numeric'});
  const first = new Date(year, month, 1), offset = (first.getDay()+6)%7;
  const last = new Date(year, month+1, 0);
  const formatDate = day => day.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  $('#calendarMonthRange').textContent = `${formatDate(first)} – ${formatDate(last)}, ${year}`;
  const start = new Date(year, month, 1-offset);
  const today = dateKey(new Date());
  const type = calendarTypeButtons.find(button => button.getAttribute('aria-pressed') === 'true').dataset.calendarType;
  const query = $('#calendarSearch').value.trim().toLowerCase();
  const eventsByDate = new Map();
  const matching = calendarEvents.filter(item =>
    (!type || item.type === type) && `${item.title} ${item.notes || ''}`.toLowerCase().includes(query)
  ).sort((a,b) => eventDateTime(a)-eventDateTime(b));
  for (const item of matching) {
    if (!eventsByDate.has(item.date)) eventsByDate.set(item.date, []);
    eventsByDate.get(item.date).push(item);
  }
  const monthCount = matching.filter(item => item.date >= dateKey(first) && item.date <= dateKey(last)).length;
  $('#calendarMatchCount').textContent = `${monthCount} ${monthCount === 1 ? 'event' : 'events'} this month`;
  const days = $('#calendarDays'); days.replaceChildren();
  for (let i=0;i<Math.ceil((offset+last.getDate())/7)*7;i++) {
    const day = new Date(start.getFullYear(), start.getMonth(), start.getDate()+i), key = dateKey(day);
    const cell = document.createElement('button');
    cell.type = 'button';
    cell.className = 'calendar-day';
    cell.dataset.date = key;
    cell.setAttribute('aria-pressed', String(key === calendarSelectedDate));
    if (day.getMonth() !== month) cell.classList.add('is-outside');
    if (key === today) { cell.classList.add('is-today'); cell.setAttribute('aria-current', 'date'); }
    if (key === calendarSelectedDate) cell.classList.add('is-selected');
    const events = eventsByDate.get(key) || [];
    const visibleEvents = events.slice(0,2);
    const savedEvent = events.find(item => item.id === lastSavedCalendarEvent);
    if (savedEvent && !visibleEvents.includes(savedEvent)) visibleEvents[1] = savedEvent;
    cell.innerHTML = `<span class="calendar-day-number">${day.getDate()}</span>` + visibleEvents.map(item => {
      const time = eventDateTime(item).toLocaleTimeString(undefined, {hour:'numeric',minute:'2-digit'});
      return `<span class="calendar-event-chip" data-type="${escapeHTML(item.type)}" title="${escapeHTML(item.title)}"><span class="calendar-chip-title">${escapeHTML(item.title)}</span><span class="calendar-chip-time">${escapeHTML(time)}</span></span>`;
    }).join('') + (events.length > 2 ? `<span class="calendar-more">+${events.length-2} more</span>` : '');
    const dateLabel = day.toLocaleDateString(undefined,{dateStyle:'full'});
    cell.setAttribute('aria-label', `${dateLabel}, ${events.length} events${events.length ? ': ' + visibleEvents.map(item => item.title).join(', ') : ''}`);
    cell.onclick = () => {
      selectCalendarDate(day);
      days.querySelector(`[data-date="${key}"]`)?.focus();
      if (events.length) $('#calendarDayLabel').scrollIntoView({block:'nearest'});
    };
    days.append(cell);
  }
  const selectedDay = new Date(`${calendarSelectedDate}T12:00:00`);
  $('#calendarDayLabel').textContent = selectedDay.toLocaleDateString(undefined, {weekday:'long',month:'long',day:'numeric'});
  renderCalendarEventList($('#calendarDayEvents'), eventsByDate.get(calendarSelectedDate) || [], 'No matching events on this day.');
  renderCalendarUpcoming();
}

function renderCalendarUpcoming() {
  const now=Date.now();
  const upcoming=calendarEvents.filter(item => eventDateTime(item).getTime() >= now-60000).sort((a,b)=>eventDateTime(a)-eventDateTime(b));
  $('#calendarUpcomingCount').textContent=`${upcoming.length} ITEM${upcoming.length===1?'':'S'}`;
  renderCalendarEventList($('#calendarUpcomingList'), upcoming, 'Nothing upcoming. Add a reminder or meeting above.');
}

function renderCalendarEventList(list, events, emptyMessage) {
  list.replaceChildren();
  if (!events.length) { const empty=document.createElement('div'); empty.className='calendar-event-empty'; empty.textContent=emptyMessage; list.append(empty); return; }
  events.forEach(item => {
    const row=document.createElement('article'); row.className='calendar-event-row';
    const date=document.createElement('div'); date.className='calendar-event-date'; date.textContent=eventDateTime(item).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
    const detail=document.createElement('div'); const title=document.createElement('div'); title.className='calendar-event-title'; title.textContent=item.title;
    const meta=document.createElement('div'); meta.className='calendar-event-detail'; meta.textContent=`${item.type}${item.notes ? ` · ${item.notes}`:''}${item.notify ? ' · Reminder on':''}`; detail.append(title,meta);
    const remove=document.createElement('button'); remove.type='button'; remove.className='btn-pill-ghost'; remove.textContent='Remove';
    remove.onclick = async () => {
      if (calendarSaving) return;
      calendarSaving = true;
      remove.disabled = true;
      const remaining = calendarEvents.filter(entry => entry.id !== item.id);
      try {
        await accountRequest('/api/company-data/calendar-events', {items:remaining});
        calendarEvents = remaining;
        renderCalendar();
      } catch (error) {
        toast(error.message || 'Could not remove the calendar event.');
      } finally {
        calendarSaving = false;
        remove.disabled = false;
      }
    };
    row.append(date,detail,remove); list.append(row);
  });
}
function selectCalendarDate(day) {
  calendarMonth = new Date(day.getFullYear(), day.getMonth(), 1);
  calendarSelectedDate = dateKey(day);
  $('#calendarEventDate').value = calendarSelectedDate;
  renderCalendar();
}
$('#calendarPrevMonth').onclick = () => selectCalendarDate(new Date(calendarMonth.getFullYear(),calendarMonth.getMonth()-1,1));
$('#calendarNextMonth').onclick = () => selectCalendarDate(new Date(calendarMonth.getFullYear(),calendarMonth.getMonth()+1,1));
$('#calendarToday').onclick = () => selectCalendarDate(new Date());
$('#calendarAddReminder').onclick = () => $('#calendarEventTitle').focus();
$('#calendarSearch').oninput = renderCalendar;
calendarTypeButtons.forEach(button => {
  button.onclick = () => {
    calendarTypeButtons.forEach(option => option.setAttribute('aria-pressed', String(option === button)));
    renderCalendar();
  };
});
async function requestReminderPermission() {
  if (!('Notification' in window)) { $('#calendarNotificationStatus').textContent='This browser does not support desktop notifications. In-app reminders will still be saved.'; return false; }
  const permission=Notification.permission==='default' ? await Notification.requestPermission().catch(() => 'denied') : Notification.permission;
  $('#calendarNotificationStatus').textContent=permission==='granted' ? 'Browser notifications are enabled for reminders.' : 'Notifications are blocked. Reminders will remain visible in the calendar while the app is open.';
  return permission==='granted';
}
$('#enableCalendarNotifications').onclick=()=>requestReminderPermission();
$('#calendarEventForm').onsubmit=async event=>{
  event.preventDefault();
  if (calendarSaving) return;
  const form = event.currentTarget;
  const button = form.querySelector('[type="submit"]');
  const status = $('#calendarFormStatus');
  const notify=$('#calendarEventNotify').checked;
  const item={id:globalThis.crypto?.randomUUID?.() || String(Date.now()),title:$('#calendarEventTitle').value.trim(),type:$('#calendarEventType').value,
    date:$('#calendarEventDate').value,time:$('#calendarEventTime').value,notes:$('#calendarEventNotes').value.trim(),notify,notified:false};
  if (!item.title) { status.textContent = 'Enter a reminder title.'; return; }
  if (!(eventDateTime(item).getTime() > Date.now())) { status.textContent='Choose a future date and time.'; return; }
  calendarSaving = true;
  button.disabled = true;
  status.textContent = 'Saving reminder…';
  try {
    const items = [...calendarEvents, item];
    await accountRequest('/api/company-data/calendar-events', {items});
    calendarEvents = items;
    lastSavedCalendarEvent = item.id;
    form.reset();
    const next = new Date(Date.now()+3600000);
    $('#calendarEventTime').value = `${String(next.getHours()).padStart(2,'0')}:${String(next.getMinutes()).padStart(2,'0')}`;
    $('#calendarSearch').value = '';
    calendarTypeButtons.forEach(option => option.setAttribute('aria-pressed', String(!option.dataset.calendarType)));
    selectCalendarDate(new Date(`${item.date}T12:00:00`));
    status.textContent = 'Reminder saved to the shared company calendar.';
    toast('Reminder saved');
    $('#calendarDays').querySelector(`[data-date="${item.date}"]`)?.scrollIntoView({block:'center', inline:'nearest'});
  } catch (error) {
    status.textContent = error.message || 'Could not save the reminder. Please try again.';
  } finally {
    calendarSaving = false;
    button.disabled = false;
  }
};
async function processCalendarNotifications() {
  if (calendarSaving) return;
  const now=Date.now(); let changed=false;
  calendarEvents.forEach(item=>{
    const due=eventDateTime(item).getTime();
    if (!item.notify || item.notified || due>now || now-due>30*60*1000) return;
    item.notified=true; changed=true;
    try {
      if (!('Notification' in window) || Notification.permission !== 'granted') {
        toast(`Reminder: ${item.title}`);
      } else {
        new Notification(`BrandWise ${item.type.toLowerCase()}`,{body:item.title,tag:`brandwise-${item.id}`});
      }
    } catch { toast(`Reminder: ${item.title}`); }
  });
  if (changed) {
    calendarSaving = true;
    try { await saveCalendar(); }
    finally { calendarSaving = false; }
  }
}
$('#calendarEventDate').value=calendarSelectedDate;
const initialReminderTime=new Date(Date.now()+3600000);
$('#calendarEventTime').value=`${String(initialReminderTime.getHours()).padStart(2,'0')}:${String(initialReminderTime.getMinutes()).padStart(2,'0')}`;
setInterval(processCalendarNotifications,15000);
async function loadAdminTeam() {
  const status=$('#adminTeamStatus'), rows=$('#adminTeamRows');
  if (!status || activeCompanyRole !== 'Admin') return;
  status.textContent='Loading team profiles and recent audit activity…';
  try {
    const [team, auditResult]=await Promise.all([accountRequest('/api/admin/team'), api('/api/audits')]);
    const people=(team.users || []).filter(person=>person.role!=='Admin');
    const audits=auditResult?.records || [];
    const roleNames=['Creator','External Agency','Reviewer','Brand Manager'];
    const stats=$('#adminTeamRoleStats'); stats.replaceChildren();
    roleNames.forEach(role=>{
      const count=people.filter(person=>person.role===role).length;
      const card=document.createElement('div'); card.className='stat-box';
      const label=document.createElement('small'); label.textContent=role.toUpperCase();
      const value=document.createElement('strong'); value.style.cssText="display:block;margin-top:8px;font:800 34px 'Barlow Condensed',sans-serif;color:var(--navy)"; value.textContent=String(count);
      const caption=document.createElement('p'); caption.textContent=count===1?'registered team member':'registered team members';
      card.append(label,value,caption); stats.append(card);
    });
    rows.replaceChildren();
    people.forEach(person=>{
      const personAudits=audits.filter(record=>[person.name,person.username].some(value=>value && String(record.creator||'').toLowerCase()===value.toLowerCase()));
      const tr=document.createElement('tr');
      const cell=(content,className='')=>{const td=document.createElement('td'); if(className)td.className=className; if(content instanceof Node)td.append(content);else td.textContent=content||'Not provided'; return td;};
      const identity=document.createElement('div'); const name=document.createElement('div'); name.className='team-person-name'; name.textContent=person.name||person.username;
      const email=document.createElement('div'); email.className='team-person-email'; email.textContent=`@${person.username} · ${person.email||'No email'}`; identity.append(name,email);
      const auditsCell=document.createElement('div');
      const auditCount=document.createElement('strong'); auditCount.textContent=`${personAudits.length} recent`; auditsCell.append(auditCount);
      personAudits.slice(0,2).forEach(record=>{const small=document.createElement('div');small.className='team-person-email';small.textContent=`${record.title||'Untitled audit'} · ${record.status||'In progress'}`;auditsCell.append(small);});
      tr.append(cell(identity),cell(person.role),cell(person.organization),cell(person.work,'team-work-cell'),cell(person.responsibilities,'team-work-cell'),cell(auditsCell));
      rows.append(tr);
    });
    $('#adminTeamCount').textContent=`${people.length} PEOPLE`;
    if (!people.length) { const tr=document.createElement('tr'), td=document.createElement('td'); td.colSpan=6; td.textContent='No other roles have registered yet.'; tr.append(td); rows.append(tr); }
    status.textContent='Team information updated just now.';
  } catch(error) { status.textContent=error.message; }
}
$('#refreshAdminTeam').onclick=loadAdminTeam;

$('#btnHistoryAuditNow').onclick = () => {
  setTab('workspace');
  startNewAudit();
};
$('#btnConfigureWebhooks').onclick = () => {
  setTab('settings');
};

// -------------------------------------------------------------------------
// Role-Based Access Control (RBAC Switcher)
// -------------------------------------------------------------------------
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
$('#btnReviewGuidelines').onclick = () => setTab('guidelines');

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
  if (m) {
    m.classList.add('open');
    if (m.hasAttribute('aria-hidden')) m.setAttribute('aria-hidden', 'false');
  }
}
function closeModal(id) {
  const m = $(id);
  if (m) {
    m.classList.remove('open');
    if (m.hasAttribute('aria-hidden')) m.setAttribute('aria-hidden', 'true');
  }
}

$('#btnTopSupport').onclick = () => openModal('#modalSupport');
$('#btnCloseSupport').onclick = () => closeModal('#modalSupport');
$('#modalSupport').addEventListener('click', event => {
  if (event.target === $('#modalSupport')) closeModal('#modalSupport');
});
$('#btnSupportGuidelines').onclick = () => {
  closeModal('#modalSupport');
  setTab('guidelines');
};
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && $('#modalSupport').classList.contains('open')) closeModal('#modalSupport');
});

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

async function refreshHistoryMetrics() {
  const result = await api('/api/audits');
  const audits = Array.isArray(result) ? result : result?.records;
  if (!Array.isArray(audits)) return;
  const measured = audits.filter(item => !item.sampleData);
  const total = measured.length;
  const average = total ? measured.reduce((sum, item) => sum + (Number(item.score) || 0), 0) / total : 0;
  const threshold = Number(readAuditPreferences()?.passingThreshold) || 80;
  $('#histTargetThreshold').textContent = `Target ${threshold}%`;
  const passed = measured.filter(item => Number(item.score) >= threshold).length;
  const findings = measured.flatMap(item => Array.isArray(item.findings) ? item.findings : []);
  const resolved = findings.filter(item => ['accepted','edited','dismissed','resolved'].includes(String(item.actionStatus || '').toLowerCase())).length;
  const since = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const thisWeek = measured.filter(item => Date.parse(item.date) >= since).length;
  const workstreams = new Set(measured.map(item => item.agency || item.channel || item.type).filter(Boolean)).size;
  $('#histTotalAudits').textContent = String(total);
  $('#histWeeklyDelta').textContent = `+${thisWeek} this week`;
  $('#histWorkstreams').textContent = `Across ${workstreams} active workstream${workstreams === 1 ? '' : 's'}`;
  $('#histAverageCompliance').textContent = total ? `${Math.round(average)}%` : '—';
  $('#histAverageNote').textContent = `Average score across ${total} saved audit${total === 1 ? '' : 's'}`;
  $('#historyTrendThreshold').textContent = `- - Passing threshold (${threshold}%)`;
  $('#histIssuesDetected').textContent = String(findings.length);
  $('#histIssuesResolved').textContent = `${resolved} resolved`;
  $('#histAutoFixes').textContent = `${findings.filter(item => item.fix).length} findings include suggested fixes`;
  $('#histPassedAudits').textContent = String(passed);
  $('#histPassRate').textContent = `${total ? Math.round(passed / total * 1000) / 10 : 0}% Pass Rate`;
  const latest = measured.slice().sort((a,b) => Date.parse(b.date || 0) - Date.parse(a.date || 0))[0];
  $('#sidebarComplianceVal').textContent = latest ? `${Number(latest.score) || 0}%` : '—';
  const sidebarFill = document.querySelector('.sidebar-progress-fill');
  if (sidebarFill) sidebarFill.style.width = `${Math.max(0, Math.min(100, Number(latest?.score) || 0))}%`;
  $('#sidebarScoreNote').textContent = latest ? `Latest saved audit · ${new Date(latest.date).toLocaleDateString()}` : 'No measured audits yet';
  // The history summary is optional on screens that don't render the history panel.
  const historyLatestRun = $('#historyLatestRun');
  if (historyLatestRun) {
    historyLatestRun.textContent = latest
      ? `Latest saved run: ${Number(latest.score) || 0}%`
      : 'No measured audits yet';
  }
  const trend = measured.slice().sort((a,b) => Date.parse(a.date || 0) - Date.parse(b.date || 0)).slice(-12);
  const trendNode = $('#historyTrendSummary');
  if (trendNode) {
    if (trend.length >= 2) {
      const points = trend.map((item, index) => ({ x: 24 + index * (552 / (trend.length - 1)), y: 132 - (Math.max(0, Math.min(100, Number(item.score) || 0)) * 1.12), item }));
      const path = points.map((point,index) => `${index ? 'L' : 'M'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ');
      const thresholdY = 132 - threshold * 1.12;
      const labels = [points[0], points[Math.floor((points.length - 1) / 2)], points[points.length - 1]];
      trendNode.innerHTML = `<svg role="img" aria-label="Compliance scores over the latest ${trend.length} saved audits" viewBox="0 0 600 160" width="100%" height="160" preserveAspectRatio="none"><line x1="20" y1="${thresholdY.toFixed(1)}" x2="580" y2="${thresholdY.toFixed(1)}" stroke="var(--orange)" stroke-dasharray="5 5"/><path d="${path}" fill="none" stroke="var(--blue)" stroke-width="3"/>${points.map(p=>`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="var(--blue)"/>`).join('')}${labels.map(p=>`<text x="${p.x.toFixed(1)}" y="154" text-anchor="middle" fill="var(--text-muted)" font-size="10">${escapeHTML(new Date(p.item.date).toLocaleDateString())}</text>`).join('')}</svg>`;
    } else {
      trendNode.textContent = trend.length ? 'Save one more real audit to show a score trend.' : 'Trend chart will appear after real audit records are saved.';
    }
  }
  $('#issueDistributionTotal').textContent = `${findings.length} findings`;
  const severityOrder = [['Critical','var(--red)'],['High','var(--orange)'],['Medium','var(--amber)'],['Low','var(--blue)']];
  const distribution = $('#historySeverityDistribution');
  if (findings.length) {
    distribution.innerHTML = severityOrder.map(([severity,color]) => {
      const count = findings.filter(f => f.severity === severity).length;
      const width = Math.round(count / findings.length * 100);
      return `<div><div style="display:flex;justify-content:space-between;font-size:11px;font-weight:600;"><span>${severity}</span><span>${count}</span></div><div class="report-track" style="margin-top:3px;"><div class="report-fill" style="width:${width}%;background:${color};"></div></div></div>`;
    }).join('');
  } else distribution.textContent = 'No measured audit findings yet.';
  const historyRows = $('#historyTableRows');
  if (historyRows) historyRows.innerHTML = audits.map(item => {
    const sample = item.sampleData ? ' · SAMPLE' : '';
    const issueCount = (item.findings || []).length;
    const score = Number.isFinite(Number(item.score)) ? `${Number(item.score)}%` : '—';
    const auditDate = item.date ? new Date(item.date).toISOString().slice(0,10) : '';
    const reviewer = item.reviewedBy || item.reviewer || item.approvedBy || '';
    return `<tr data-audit-id="${escapeHTML(item.id || '')}" data-audit-date="${escapeHTML(auditDate)}"><td><div style="font-weight:700;color:var(--navy);">${escapeHTML(item.title || 'Untitled audit')}</div><div style="font-size:10.5px;color:var(--text-dim);">${escapeHTML(item.channel || item.type || 'Audit')}${sample} · ${escapeHTML(item.creator || 'Unknown submitter')}${reviewer ? ` · Reviewer: ${escapeHTML(reviewer)}` : ''}</div></td><td>${escapeHTML(item.settings?.strictness || 'Deterministic')}</td><td>${item.date ? escapeHTML(new Date(item.date).toLocaleString()) : '—'}</td><td><b>${score}</b></td><td>${issueCount}</td><td>${escapeHTML(item.status || '—')}</td><td><button class="btn-pill-ghost btn-view-audit-report" data-audit-id="${escapeHTML(item.id || '')}" type="button">View Report</button></td></tr>`;
  }).join('') || '<tr><td colspan="7">No saved audits yet.</td></tr>';
  $$('.btn-view-audit-report[data-audit-id]').forEach(button => button.onclick = () => openAuditRecord(button.dataset.auditId));
  filterAuditArchive();
}

async function refreshGuidelineCounts() {
  const [claimsResult, guidelines] = await Promise.all([api('/api/claims'), api('/api/guidelines')]);
  const claims = claimsResult?.claims || [];
  const today = new Date().toISOString().slice(0,10);
  const active = claims.filter(item => item.status === 'Active' && (!item.expiry || item.expiry >= today)).length;
  const expired = claims.filter(item => item.status === 'Expired' || (item.expiry && item.expiry < today)).length;
  const termCount = guidelines?.terminology?.prohibited?.length;
  $('#guidelineClaimCounts').textContent = `${active} active / ${expired} expired`;
  $('#guidelineTermCount').textContent = Number.isInteger(termCount) ? `${termCount} terms` : 'Unavailable';
  const identity = claims.find(item => item.category === 'Company Identity' && item.status === 'Active');
  const year = identity?.statement?.match(/\b(?:18|19|20)\d{2}\b/)?.[0];
  if (year) $('#guidelineFoundationYear').textContent = year;
  const performance = claims.find(item => item.category === 'Product Performance' && item.status === 'Active');
  if (performance) $('#guidelinePerformanceClaim').textContent = performance.statement;
  const pricing = claims.find(item => /pricing/i.test(item.category || '') && item.status === 'Active' && (!item.expiry || item.expiry >= today));
  $('#guidelinePricingClaim').textContent = pricing?.statement || 'No active pricing claim';
  $('#guidelinePricingId').textContent = pricing ? `ACTIVE PRICING CLAIM · ${pricing.id}` : 'ACTIVE PRICING CLAIM';
  $('#guidelinePricingEvidence').textContent = pricing ? `${pricing.evidence || 'Evidence not recorded'} · Owner: ${pricing.owner || 'Unassigned'} · Expiry: ${pricing.expiry || 'Not recorded'}` : 'Add a current, verified price to the claims ledger to validate pricing copy.';
}

async function refreshImpactMetrics() {
  const data = await api('/api/insights');
  const evidence = data?.impactEvidence;
  if (!evidence) return;
  const evaluation = evidence.labelledEvaluation;
  $('#impactDetectionRate').textContent = evaluation?.detectionRate == null ? 'Unavailable' : `${evaluation.detectionRate}%`;
  $('#impactFalseFlagRate').textContent = evaluation?.falseFlagRate == null ? 'Unavailable' : `${evaluation.falseFlagRate}%`;
  $('#impactSourceLinked').textContent = String(evidence.sourceLinkedFindingCount ?? 0);
  const description = $('#subview-hist-impact p');
  if (description) description.textContent = `${evidence.measurementStatus} Labeled set: ${evaluation?.caseCount ?? 0} synthetic cases (${evaluation?.compliantCases ?? 0} compliant, ${evaluation?.noncompliantCases ?? 0} noncompliant).`;

  const disputed = data.ambiguousRules || [];
  $('#ambiguousRuleCount').textContent = `${disputed.length} DISPUTED RULE${disputed.length === 1 ? '' : 'S'}`;
  $('#ambiguousRulesRows').innerHTML = disputed.length ? disputed.map(item => `<tr><td><code>${escapeHTML(item.ruleId)}</code></td><td><b>${escapeHTML(item.ruleTitle)}</b></td><td>${Number(item.dismissalCount) || 0}</td><td>Not calculated</td><td>${escapeHTML(item.recommendation || 'Review feedback with a human reviewer.')}</td></tr>`).join('') : '<tr><td colspan="5">No disputed findings recorded yet.</td></tr>';

  const teams = data.agencyStats || [];
  $('#agencyBenchmarkCount').textContent = `${teams.length} TEAM${teams.length === 1 ? '' : 'S'} WITH AUDITS`;
  $('#agencyStatsRows').innerHTML = teams.length ? teams.map(item => `<tr><td>${escapeHTML(item.name)}</td><td>${Number(item.submissions) || 0}</td><td>${item.avgCompliance == null ? '—' : `${Number(item.avgCompliance)}%`}</td><td>${item.approvalRate == null ? '—' : `${Number(item.approvalRate)}%`}</td><td>Not measured</td></tr>`).join('') : '<tr><td colspan="5">No saved team audit data yet.</td></tr>';
  const archiveSummary = $('#historyTableSummary');
  if (archiveSummary) archiveSummary.textContent = `Showing saved records available to this account. Sample/demo records are labeled and excluded from live metrics.`;
}

async function refreshStorageStatus() {
  const label = $('#storageStatusLabel');
  if (!label) return;
  try {
    const response = await fetch('/api/health');
    const health = await response.json();
    const storage = health?.storage;
    label.textContent = storage?.engine === 'neon-postgres'
      ? (storage.connected ? 'Neon PostgreSQL connected' : 'Neon PostgreSQL unavailable')
      : (storage?.connected ? 'Local SQLite + JSON' : 'Storage unavailable');
  } catch {
    label.textContent = 'Storage status unavailable';
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
  const requestStarted = performance.now();
  let aiFallbackReason = '';
  try {
    await flushAndRefreshAuditPreferences();
    const auditPreferences = readAuditPreferences();
    const aiEnabled = document.querySelector('#enableGemini')?.checked ?? (document.getElementById('defaultAiReview')?.value === 'on');
    const selectedAi = document.querySelector('#aiReviewProvider')?.value || 'browser-1b';
    let aiProvider = null;
    let clientAi = null;
    if (aiEnabled && selectedAi.startsWith('browser-')) {
      const requested = selectedAi === 'browser-3b' ? AI_MODELS.llama3b : AI_MODELS.llama1b;
      if (browserAiEngine && browserAiModel && (browserAiModel.startsWith(selectedAi === 'browser-3b' ? 'Llama-3.2-3B' : 'Llama-3.2-1B'))) {
        try {
          const context = await getAiContext();
          const findings = await runBrowserAiReview(content, context, browserAiModel);
          aiProvider = 'browser';
          clientAi = {model: browserAiModel, findings};
        } catch (error) {
          aiFallbackReason = friendlyAiError(error);
        }
      } else {
        aiFallbackReason = 'The in-browser model is still downloading; this audit is running with deterministic checks now.';
        if (!browserAiLoadPromise) getOrLoadBrowserModel(requested).catch(() => {});
      }
    } else if (aiEnabled && selectedAi === 'gemini') {
      aiProvider = 'gemini';
    }

    const res = await api('/api/audits', {
      method: 'POST',
      body: JSON.stringify({
        title: document.getElementById('auditTitleInput')?.value.trim() || '',
        content,
        channel: document.getElementById('defaultChannel')?.value || 'Website Copy',
        role: currentRole,
        settings: auditPreferences,
        useAI: Boolean(aiProvider),
        aiProvider,
        clientAi
      })
    });
    if (res) {
      res.clientRoundTripMs = Math.round(performance.now() - requestStarted);
      currentAuditRecord = res;
      renderAuditReport(res);
      refreshHistoryMetrics();
      toast(`Audit complete: Score ${res.score}%`);
      if (aiFallbackReason) updateAiStatus(`${aiFallbackReason} Deterministic checks were completed.`, 'error');
      else updateAiStatus(res.aiStatus || 'Deterministic review', res.aiStatus?.includes('unavailable') ? 'error' : 'success');
      rememberUnsavedDraft(false);
    } else {
      toast('The audit could not be saved. Your draft remains in the editor; retry the check.');
    }
  } catch (error) {
    toast(error?.message || 'The audit could not be completed. Your draft remains in the editor.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> AUDIT CONTENT ➔`;
  }
};

function renderAuditReport(res) {
  $('#btnExportPDF').disabled = !res || !Array.isArray(res.findings) || !Number.isFinite(Number(res.score));
  if (Number.isFinite(Number(res.clientRoundTripMs))) {
    $('#analysisTimingLabel').textContent = `Audit API round-trip: ${Math.round(Number(res.clientRoundTripMs))} ms (browser ↔ server)`;
  } else {
    $('#analysisTimingLabel').textContent = 'Saved audit result · timing unavailable';
  }
  const requiredThreshold = Number(res.passingThreshold || $('#thresholdSlider')?.value || 80);
  const pass = typeof res.passedThreshold === 'boolean' ? res.passedThreshold : Number(res.score) >= requiredThreshold;
  const confidenceScore = res.confidence != null && Number.isFinite(Number(res.confidence)) ? Math.round(Number(res.confidence)) : null;
  $('#reportConfidenceVal').innerHTML = `${confidenceScore === null ? 'N/A' : `${confidenceScore}%`} <span style="font-size:12px;font-family:'Inter',sans-serif;font-weight:600;color:var(--text-muted);">estimated</span>`;
  const auditMode = res.settings?.strictness ? `${res.settings.strictness} mode · ` : '';
  $('#reportComplianceVal').textContent = `${Number(res.score) || 0}% (${auditMode}target ${requiredThreshold}% · ${pass ? 'threshold met' : 'additional review needed'})`;
  $('#reportHeaderBadge').textContent = pass ? 'THRESHOLD MET' : 'REVIEW NEEDED';
  $('#reportHeaderBadge').className = `pill-tag ${pass ? 'pill-blue' : 'pill-orange'}`;
  document.querySelector('#aiReviewStatus').textContent=res.aiStatus||'Deterministic review';
  $('#lifecycleBadge').textContent = res.status || 'Auto-checked';
  $('#lifecycleBadge').className = `pill-tag ${pass ? 'pill-blue' : 'pill-orange'}`;
  const reviewer = ['Reviewer', 'Brand Manager', 'Admin'].includes(currentRole);
  $('#btnReqChanges').disabled = !reviewer;
  $('#btnApproveDraft').disabled = !reviewer || !pass || findingsHaveBlocking(res.findings || []);
  $('#btnPublishDraft').disabled = !reviewer || res.status !== 'Approved' || (res.findings || []).some(f => (f.actionStatus || 'pending') === 'pending');

  // Update progress bars
  const findings = res.findings || [];
  if (res.accessibility) {
    const grade = res.accessibility.readingGrade;
    $('#readabilityGrade').textContent = grade === null ? 'Not enough text' : `${grade} (Grade ${grade <= res.accessibility.maxGrade ? 'within' : 'above'} limit)`;
    const issueCount = res.accessibility.headingIssues?.length || 0;
    $('#headingOrderStatus').textContent = res.accessibility.headingCount
      ? issueCount ? `${issueCount} heading order issue${issueCount === 1 ? '' : 's'} found` : `${res.accessibility.headingCount} headings checked; order looks good`
      : 'No structured headings found in this copy';
  }
  const categoryOf = finding => String(finding.category || '').toLowerCase();
  const claimIssues = findings.filter(f => /claim|fact|pricing|substantiation/.test(categoryOf(f)));
  const toneIssues = findings.filter(f => /prohibited|terminology|superlative|overpromis|unsupported/.test(categoryOf(f)));
  const brandIssues = findings.filter(f => /brand|trademark|asset|identity/.test(categoryOf(f)));
  [[claimIssues,'bar1Label','bar1Fill'],[toneIssues,'bar2Label','bar2Fill'],[brandIssues,'bar3Label','bar3Fill']].forEach(([items,labelId,fillId]) => {
    $(`#${labelId}`).textContent = `${items.length} finding${items.length === 1 ? '' : 's'}`;
    $(`#${fillId}`).style.width = `${Math.min(100, items.length * 20)}%`;
  });

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
      saveFindingFix(topF, 'accept_fix', topF.fix);
    };
  } else {
    $('#reportSuggestionBox').innerHTML = `
      <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
      <div><b>No findings surfaced in the configured checks.</b> This is not a guarantee of full compliance; review the source copy before publication.</div>
    `;
  }

  // Render Findings Accordion
  const fContainer = $('#findingsContainer');
  fContainer.innerHTML = '';
  findings.forEach(f => {
    const sevClass = f.severity ? `sev-${f.severity.toLowerCase()}` : 'sev-high';
    const confidence = Number.isFinite(Number(f.confidence)) ? Number(f.confidence) : null;
    const confidenceType = f.confidenceBasis === 'AI estimate; not calibrated'
      ? 'AI estimate (not calibrated)'
      : f.confidenceBasis?.startsWith('Heuristic') ? 'heuristic estimate' : 'rule match';
    const confidenceLabel = confidence === null ? '' : `${confidence}% ${confidenceType}`;
    const card = document.createElement('div');
    card.className = `finding-card-item ${sevClass}`;
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <b>${escapeHTML(f.title)}</b>
        <span class="pill-tag ${f.severity === 'Critical' ? 'pill-orange' : 'pill-gray'}" style="font-size:8.5px;">${escapeHTML(f.severity || 'High')}</span>
      </div>
      <div style="color:var(--text-muted);font-size:11px;">${escapeHTML(f.why)}</div>
      ${confidenceLabel ? `<div style="color:var(--text-dim);font-size:10px;margin-top:3px;">Confidence: ${escapeHTML(confidenceLabel)}</div>` : ''}
      <details style="margin-top:6px;font-size:10.5px;">
        <summary style="cursor:pointer;color:var(--blue-text,var(--blue));font-weight:700;">Evidence and finding details</summary>
        <div style="display:grid;gap:4px;margin-top:6px;padding:9px 10px;border-radius:8px;background:var(--card-elevated);line-height:1.45;">
          <div><b>Matched wording:</b> ${escapeHTML(f.wrong || 'Not specified')}</div>
          <div><b>Source:</b> ${escapeHTML(f.sourceId || 'No source linked')} · ${escapeHTML(f.official || 'No evidence reference supplied')}</div>
          <div><b>Owner / expiry:</b> ${escapeHTML(f.owner || 'Not specified')} / ${escapeHTML(f.expiry || 'Not specified')}</div>
          <div><b>Location / verification:</b> ${escapeHTML(f.location || 'Not specified')} · ${escapeHTML(f.state || 'Needs human review')}</div>
          <div><b>Suggested wording:</b> ${escapeHTML(f.fix || 'No automatic replacement; decide with a reviewer.')}</div>
          ${f.citationIssue ? `<div><b>Citation note:</b> ${escapeHTML(f.citationIssue)}</div>` : ''}
          ${f.reportedIncorrect ? `<div><b>Feedback:</b> Reported as potentially incorrect${f.incorrectFeedback ? ` - ${escapeHTML(f.incorrectFeedback)}` : ''}</div>` : ''}
        </div>
      </details>
      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:9.5px;color:var(--blue-text, var(--blue));">${escapeHTML(f.sourceId || 'LEDGER')}</span>
        <div style="display:flex;gap:4px;">
          ${f.actionStatus === 'accepted' ? '<span class="pill-tag pill-blue">Fix accepted</span>' : ''}
          ${f.actionStatus === 'edited' ? '<span class="pill-tag pill-blue">Fix edited</span>' : ''}
          ${f.actionStatus === 'dismissed' ? '<span class="pill-tag pill-gray">Dismissed</span>' : ''}
          ${!['accepted','edited','dismissed'].includes(f.actionStatus) ? `${f.fix ? '<button type="button" class="btn-pill-primary btn-accept-fix" style="padding:2px 7px;font-size:9.5px;">Accept</button><button type="button" class="btn-pill-ghost btn-edit-fix" style="padding:2px 7px;font-size:9.5px;">Edit</button>' : ''}<button type="button" class="btn-pill-ghost btn-dismiss-fix" style="padding:2px 7px;font-size:9.5px;">Dismiss</button>` : ''}
          <button type="button" class="btn-pill-ghost btn-report-incorrect" style="padding:2px 7px;font-size:9.5px;" title="Report a possibly incorrect finding" ${f.reportedIncorrect ? 'disabled' : ''}>${f.reportedIncorrect ? 'Reported' : 'Report incorrect'}</button>
        </div>
      </div>
    `;

    const fixBtn = card.querySelector('.btn-accept-fix');
    if (fixBtn) {
      fixBtn.onclick = () => saveFindingFix(f, 'accept_fix', f.fix);
    }
    const editBtn = card.querySelector('.btn-edit-fix');
    if (editBtn) {
      editBtn.onclick = () => {
        const wording = window.prompt('Edit the suggested replacement wording:', f.fix || '');
        if (wording?.trim()) saveFindingFix(f, 'edit_fix', wording.trim());
      };
    }
    const dismissBtn = card.querySelector('.btn-dismiss-fix');
    if (dismissBtn) {
      dismissBtn.onclick = async () => {
        const saved = await saveFindingAction({ action: 'dismiss_fix', findingId: f.id, reason: `Dismissed by ${currentRole}` });
        if (saved) toast('Dismissal saved to the audit trail');
      };
    }
    const reportBtn = card.querySelector('.btn-report-incorrect');
    if (reportBtn) {
      reportBtn.onclick = async () => {
        if (!currentAuditRecord?.id || !f.id) {
          toast('Could not save feedback for this finding');
          return;
        }
        reportBtn.disabled = true;
        const saved = await api(`/api/audits/${currentAuditRecord.id}/action`, {
          method: 'POST',
          body: JSON.stringify({
            action: 'report_incorrect_flag',
            findingId: f.id,
            feedback: 'User reported this finding as potentially incorrect.'
          })
        });
        if (saved) {
          currentAuditRecord = saved;
          renderAuditReport(saved);
          toast('Report saved to the audit trail');
        } else {
          reportBtn.disabled = false;
          toast('Could not save feedback. Please try again.');
        }
      };
    }
    fContainer.appendChild(card);
  });
  const trail = Array.isArray(res.auditTrail) ? res.auditTrail : [];
  $('#reportTrailPanel').hidden = !trail.length;
  $('#reportAuditTrail').innerHTML = trail.slice().reverse().slice(0,8).map(item => `
    <div style="display:flex;justify-content:space-between;gap:12px;padding:7px 9px;border:1px solid var(--line);border-radius:8px;background:var(--card-elevated);font-size:10px;">
      <span><b>${escapeHTML(item.action || 'Activity')}</b> · ${escapeHTML(item.user || 'System')}${item.note ? ` — ${escapeHTML(item.note)}` : ''}</span>
      <time style="flex:0 0 auto;color:var(--text-dim);">${escapeHTML(item.timestamp || '')}</time>
    </div>`).join('');
}

function findingsHaveBlocking(findings) {
  return findings.some(f => ['Critical','High'].includes(f.severity) && (f.actionStatus || 'pending') === 'pending');
}

async function openAuditRecord(auditId) {
  const record = await api(`/api/audits/${encodeURIComponent(auditId)}`);
  if (!record) { toast('Could not load this audit record.'); return; }
  currentAuditRecord = record;
  $('#workspaceInput').value = record.content || '';
  if ($('#auditTitleInput')) $('#auditTitleInput').value = record.title || '';
  renderAuditReport(record);
  setTab('workspace');
}

async function saveFindingAction(action) {
  if (!currentAuditRecord?.id || !action.findingId) {
    toast('Run an audit before changing a finding');
    return null;
  }
  const saved = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({...action, baseRevisionId: currentAuditRecord.currentRevisionId})
  });
  if (saved) {
    currentAuditRecord = saved;
    renderAuditReport(saved);
  } else {
    const latest = await api(`/api/audits/${encodeURIComponent(currentAuditRecord.id)}`);
    toast(latest && latest.currentRevisionId !== currentAuditRecord.currentRevisionId
      ? 'This audit changed since you opened it. Your editor text is unchanged; reopen the saved revision and retry.'
      : 'Could not save this action. Please try again.');
  }
  return saved;
}

async function saveFindingFix(finding, action, wording) {
  if (!finding?.id || !wording?.trim()) return;
  const phrase = String(finding.wrong || '');
  const source = String(currentAuditRecord?.content || '');
  const matches = [];
  if (phrase) for (let offset = 0, found; (found = source.toLowerCase().indexOf(phrase.toLowerCase(), offset)) !== -1; offset = found + phrase.length) matches.push(found);
  let occurrenceIndex = 0;
  if (matches.length > 1) {
    const choice = window.prompt(`This wording appears ${matches.length} times. Enter the occurrence number to replace (1–${matches.length}):`, String(matches.length));
    if (choice === null) return;
    occurrenceIndex = Number(choice) - 1;
    if (!Number.isInteger(occurrenceIndex) || occurrenceIndex < 0 || occurrenceIndex >= matches.length) { toast('Choose a valid occurrence number.'); return; }
  }
  const saved = await saveFindingAction({ action, findingId: finding.id, fixText: wording.trim(), occurrenceIndex });
  if (saved) {
    $('#workspaceInput').value = saved.content || $('#workspaceInput').value;
    toast(action === 'edit_fix' ? 'Edited wording and saved it to the audit trail' : 'Fix accepted and saved to the audit trail');
  }
}

function startNewAudit() {
  const hasUnsavedText = Boolean($('#workspaceInput').value.trim()) &&
    (!currentAuditRecord || $('#workspaceInput').value !== (currentAuditRecord.content || ''));
  if (hasUnsavedText && !confirm('Discard the current unsaved draft and start a new audit?')) return;
  $('#workspaceInput').value = '';
  $('#auditTitleInput').value = '';
  $('#draftImportStatus').textContent = 'Paste or import a draft to begin. Imported text is shown here before checks.';
  currentAuditRecord = null;
  $('#btnExportPDF').disabled = true;
  rememberUnsavedDraft(true);
  $('#reportConfidenceVal').textContent = '—';
  $('#reportComplianceVal').textContent = 'No audit results yet';
  $('#reportHeaderBadge').textContent = 'NO RESULTS';
  $('#reportHeaderBadge').className = 'pill-tag pill-gray';
  $('#lifecycleBadge').textContent = 'Not started';
  $('#lifecycleBadge').className = 'pill-tag pill-gray';
  $('#findingsContainer').textContent = 'Run an audit to see verified findings and evidence.';
  $('#reportSuggestionBox').style.display = 'none';
  $('#reportSuggestionBox').replaceChildren();
  ['btnReqChanges','btnApproveDraft','btnPublishDraft'].forEach(id => { const button=$(`#${id}`); if(button)button.disabled=true; });
  ['bar1Label','bar2Label','bar3Label'].forEach(id => { const node=$(`#${id}`); if(node)node.textContent='0 findings'; });
  ['bar1Fill','bar2Fill','bar3Fill'].forEach(id => { const node=$(`#${id}`); if(node)node.style.width='0%'; });
  $('#workspaceInput').focus();
}
$('#btnNewAudit').onclick = startNewAudit;

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
    currentAuditRecord = res;
    renderAuditReport(res);
    const alertText = await createLocalLlmAlert({
      title: currentAuditRecord.title || 'Brand draft',
      status: 'Approved',
      actor: currentRole,
      message: 'Draft officially approved by a reviewer.'
    });
    toast(alertText);
  }
};

$('#btnReqChanges').onclick = async () => {
  if (!currentAuditRecord) return;
  const res = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'change_state', state: 'Changes requested', user: `${currentRole}` })
  });
  if (res) {
    currentAuditRecord = res;
    renderAuditReport(res);
    const alertText = await createLocalLlmAlert({
      title: currentAuditRecord.title || 'Brand draft',
      status: 'Changes requested',
      actor: currentRole,
      message: 'The creator should review the requested edits in BrandWise.'
    });
    toast(alertText);
  }
};

$('#btnPublishDraft').onclick = async () => {
  if (!currentAuditRecord) return;
  const res = await api(`/api/audits/${currentAuditRecord.id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action: 'change_state', state: 'Published', user: `${currentRole}` })
  });
  if (res) {
    currentAuditRecord = res;
    renderAuditReport(res);
    toast('Draft Published to production channel!');
  }
};

// -------------------------------------------------------------------------
// Sample buttons (Connecting the 4 PDF Scenarios)
// -------------------------------------------------------------------------
$('#btnLoadShortNote').onclick = () => {
  $('#workspaceInput').value = "BrandWise cuts onboarding time by up to 20% for high-velocity teams. Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.";
  toast('Loaded approved-claim example with the full required disclaimer');
};
$('#btnLoadInstagram').onclick = () => {
  $('#workspaceInput').value = "Kindly note: We have preponed the product launch to Friday. Please revert back with feedback. Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.";
  toast('Loaded regional-English example with the required disclaimer');
};
$('#btnLoadAdHeadline').onclick = () => {
  $('#workspaceInput').value = "Lofty Creative Lab guarantees 10x faster engagement across omni-channel campaigns using patented creative synthesis with 100% cloud zero-carbon footprint. Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.";
  toast('Loaded unsubstantiated performance and absolute-claim example');
};
$('#btnLoadPrivacy').onclick = () => {
  $('#workspaceInput').value = "Acme Technologies was established in 2012. Starter tiers start at $49/month with full features. Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.";
  toast('Loaded expired-pricing example; verify the flagged source before publication');
};

$('#btnIndianEnglishNote').onclick = (e) => {
  e.preventDefault();
  openModal('#modalWcag');
};

// -------------------------------------------------------------------------
// Export a focused, print-ready report instead of printing the whole app.
// -------------------------------------------------------------------------
function exportAuditPDF() {
  const audit = currentAuditRecord;
  if (!audit || !Array.isArray(audit.findings) || !Number.isFinite(Number(audit.score))) {
    toast('Run or open a saved audit before exporting its report.');
    return;
  }
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    toast('Allow pop-ups to open the print-ready report.');
    return;
  }
  const safe = escapeHTML;
  const findings = audit.findings;
  const findingCards = findings.length ? findings.map((finding, index) => {
    const severity = String(finding.severity || 'Needs review');
    const severityClass = /critical|high/i.test(severity) ? 'high' : /medium/i.test(severity) ? 'medium' : 'low';
    const state = finding.state || (/expired|unrelated|missing|needs human/i.test(`${finding.verification || ''} ${finding.citationIssue || ''}`) ? 'Needs human review' : 'Review evidence before publication');
    return `<article class="finding ${severityClass}">
      <div class="finding-head"><div><span class="eyebrow">FINDING ${String(index + 1).padStart(2, '0')}</span><h3>${safe(finding.title || finding.category || 'Review finding')}</h3></div><span class="severity ${severityClass}">${safe(severity)}</span></div>
      <p>${safe(finding.why || 'Review this wording against the approved brand guidance.')}</p>
      ${finding.wrong ? `<div class="label">Flagged wording</div><blockquote>${safe(finding.wrong)}</blockquote>` : ''}
      <div class="finding-meta"><div><span class="label">Source</span><b>${safe(finding.sourceId || 'No source linked')}</b></div><div><span class="label">Review status</span><b>${safe(state)}</b></div></div>
      ${finding.official ? `<div class="evidence"><span class="label">Evidence reference</span><p>${safe(finding.official)}</p></div>` : ''}
      <div class="fix"><span class="label">Suggested correction</span><p>${safe(finding.fix || 'No supported automatic correction. Confirm with a reviewer.')}</p></div>
      ${finding.actionStatus ? `<div class="disposition">Disposition: ${safe(finding.actionStatus)}</div>` : ''}
    </article>`;
  }).join('') : '<div class="empty">No findings were returned for this audit. This is not a guarantee of full compliance; a person should review the draft before publication.</div>';
  const generatedAt = new Date().toLocaleString();
  const status = audit.status || (audit.passedThreshold ? 'Threshold met' : 'Review needed');
  const channel = audit.channel || audit.type || 'Content review';
  const aiMethod = audit.aiStatus || 'Deterministic rules';
  const draft = audit.content || '';
  const title = audit.title || 'Untitled audit';
  const score = Math.max(0, Math.min(100, Number(audit.score) || 0));
  const threshold = Number(audit.passingThreshold || 80);
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${safe(title)} · BrandWise Audit</title>
    <style>
      @page{size:A4;margin:16mm 15mm 18mm}*{box-sizing:border-box}body{margin:0;color:#142b46;background:#fff;font:14px/1.55 Inter,Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
      .topline{height:8px;background:linear-gradient(90deg,#0878ce 0 72%,#f36b21 72%)}header{padding:23px 0 18px;border-bottom:1px solid #d8e1ee;display:flex;justify-content:space-between;align-items:center;gap:18px}.brand{font-size:19px;font-weight:900;letter-spacing:.13em;color:#0878ce}.brand small{display:block;color:#6b7f99;font-size:9px;letter-spacing:.16em;margin-top:2px}.report-label{text-align:right;color:#6b7f99;font-size:10px;font-weight:700;letter-spacing:.1em}
      .intro{padding:25px 0 18px}.eyebrow,.label{font-size:9px;line-height:1.3;letter-spacing:.09em;font-weight:800;color:#71839c;text-transform:uppercase}.intro h1{font-size:28px;line-height:1.12;margin:6px 0 4px;letter-spacing:-.035em}.sub{margin:0;color:#637895}.chips{display:flex;gap:7px;flex-wrap:wrap;margin-top:13px}.chip{display:inline-block;background:#eaf3fc;color:#0878ce;border-radius:999px;padding:5px 10px;font-size:10px;font-weight:800}
      .summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:3px 0 22px}.metric{border:1px solid #d8e1ee;border-radius:12px;padding:12px 14px;background:#f7f9fc;min-height:76px}.metric b{display:block;font-size:23px;line-height:1.1;margin-top:5px}.metric small{display:block;color:#6b7f99;font-size:10px;margin-top:4px}.section-title{display:flex;align-items:end;justify-content:space-between;border-bottom:2px solid #0878ce;padding-bottom:7px;margin:20px 0 11px}.section-title h2{font-size:16px;margin:0}.section-title span{font-size:10px;color:#6b7f99}
      .draft{white-space:pre-wrap;overflow-wrap:anywhere;background:#f7f9fc;border:1px solid #d8e1ee;border-left:3px solid #0878ce;border-radius:8px;padding:13px 15px;margin:0;color:#263d59;font-size:12px}.finding{break-inside:avoid;border:1px solid #d8e1ee;border-left:4px solid #0878ce;border-radius:10px;padding:13px 14px;margin:10px 0}.finding.high{border-left-color:#e75a43}.finding.medium{border-left-color:#ef9b25}.finding.low{border-left-color:#0878ce}.finding-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.finding h3{font-size:14px;line-height:1.3;margin:3px 0 5px}.finding>p{margin:4px 0 10px;color:#536b88}.severity{flex:none;border-radius:999px;padding:4px 9px;background:#eaf3fc;color:#0878ce;font-size:9px;font-weight:800;text-transform:uppercase}.severity.high{background:#fff0ed;color:#bd4033}.severity.medium{background:#fff5e4;color:#9c6200}.finding blockquote{margin:5px 0 11px;padding:8px 11px;background:#f7f9fc;border-radius:6px;border-left:2px solid #f36b21;color:#243c59}.finding-meta{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:9px 0;border-top:1px solid #edf1f6}.finding-meta b{display:block;margin-top:3px;font-size:11px}.evidence,.fix{padding:9px 10px;border-radius:7px;margin-top:7px;background:#f7f9fc}.fix{background:#eef6fd}.evidence p,.fix p{margin:4px 0 0;color:#425a78}.disposition{font-size:10px;color:#60748f;margin-top:8px}.empty{padding:18px;border:1px dashed #b9c9dc;border-radius:9px;color:#637895}
      footer{margin-top:24px;border-top:1px solid #d8e1ee;padding-top:10px;display:flex;justify-content:space-between;gap:12px;color:#71839c;font-size:9px}.no-print{position:sticky;top:0;background:#142b46;color:white;padding:10px 16px;text-align:center;font-size:12px}.no-print button{margin-left:12px;border:0;border-radius:999px;padding:8px 14px;font-weight:700;color:#142b46;background:white;cursor:pointer}@media print{.no-print{display:none}header{padding-top:0}}
    </style></head><body><div class="no-print">Print-ready audit report <button type="button">Print / Save as PDF</button></div><div class="topline"></div>
    <main><header><div class="brand">BRANDWISE<small>BRAND INTELLIGENCE</small></div><div class="report-label">AUDIT REPORT<br>${safe(generatedAt)}</div></header>
      <section class="intro"><div class="eyebrow">CONTENT COMPLIANCE REVIEW</div><h1>${safe(title)}</h1><p class="sub">A review of ${safe(channel)} against the configured BrandWise guidance.</p><div class="chips"><span class="chip">${safe(status)}</span><span class="chip">${safe(aiMethod)}</span>${audit.settings?.strictness ? `<span class="chip">${safe(audit.settings.strictness)} review</span>` : ''}</div></section>
      <section class="summary"><div class="metric"><span class="eyebrow">COMPLIANCE SCORE</span><b>${score}%</b><small>Configured passing threshold: ${safe(threshold)}%</small></div><div class="metric"><span class="eyebrow">FINDINGS</span><b>${findings.length}</b><small>${findings.filter(f => !['accepted','edited','dismissed'].includes(f.actionStatus)).length} pending disposition</small></div><div class="metric"><span class="eyebrow">REVIEW STATUS</span><b style="font-size:16px;margin-top:9px">${safe(status)}</b><small>Human review remains part of the workflow</small></div></section>
      <section><div class="section-title"><h2>Draft reviewed</h2><span>${draft.length.toLocaleString()} characters</span></div><div class="draft">${safe(draft || 'No saved draft text is available.')}</div></section>
      <section><div class="section-title"><h2>Findings and recommendations</h2><span>${findings.length} total</span></div>${findingCards}</section>
      <footer><span>BrandWise · Explainable brand review</span><span>Generated ${safe(generatedAt)} · Review findings with a qualified human before publication.</span></footer></main></body></html>`;
  printWindow.document.open();
  printWindow.document.write(html);
  printWindow.document.close();
  printWindow.document.querySelector('.no-print button').addEventListener('click', () => printWindow.print());
}
$('#btnExportPDF').onclick = exportAuditPDF;
$('#btnPrintReportBtn').onclick = exportAuditPDF;

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
let historyRange = 'all';
let historySort = 'newest';
const historyRangeOptions = [
  {key:'all',label:'All time'},
  {key:'30d',label:'Last 30 days'},
  {key:'90d',label:'Last 90 days'},
  {key:'year',label:'This year'}
];
function updateHistoryControlLabels() {
  const range = historyRangeOptions.find(option => option.key === historyRange) || historyRangeOptions[0];
  $('#historyRangeButton').textContent = `📅 ${range.label}`;
  $('#historySortButton').textContent = `⇕ ${historySort === 'newest' ? 'Newest first' : 'Oldest first'}`;
}
function filterAuditArchive() {
  const q = $('#archiveSearch').value.toLowerCase().trim();
  const from = $('#archiveDateFrom').value;
  const to = $('#archiveDateTo').value;
  const today = new Date();
  const cutoff = new Date(today);
  if (historyRange === '30d') cutoff.setDate(cutoff.getDate() - 30);
  if (historyRange === '90d') cutoff.setDate(cutoff.getDate() - 90);
  const rangeFrom = historyRange === 'year' ? `${today.getFullYear()}-01-01` : (historyRange === 'all' ? '' : cutoff.toISOString().slice(0,10));
  const rows = $$('#historyTableRows tr[data-audit-id]');
  rows.sort((a,b) => {
    const order = (a.dataset.auditDate || '').localeCompare(b.dataset.auditDate || '');
    return historySort === 'newest' ? -order : order;
  }).forEach(row => $('#historyTableRows').appendChild(row));
  let visibleCount = 0;
  rows.forEach(row => {
    const date = row.dataset.auditDate || '';
    const matchesText = row.textContent.toLowerCase().includes(q);
    const matchesDate = (!from || (date && date >= from)) && (!to || (date && date <= to)) && (!rangeFrom || (date && date >= rangeFrom));
    const visible = matchesText && matchesDate;
    row.style.display = visible ? '' : 'none';
    if (visible) visibleCount += 1;
  });
  const summary = $('#historyTableSummary');
  if (summary) summary.textContent = `Showing ${visibleCount} of ${rows.length} saved audit${rows.length === 1 ? '' : 's'} · ${historyRangeOptions.find(option => option.key === historyRange)?.label || 'All time'} · ${historySort === 'newest' ? 'Newest first' : 'Oldest first'}`;
}
$('#historyRangeButton').onclick = () => {
  const index = historyRangeOptions.findIndex(option => option.key === historyRange);
  historyRange = historyRangeOptions[(index + 1) % historyRangeOptions.length].key;
  updateHistoryControlLabels();
  filterAuditArchive();
};
$('#historySortButton').onclick = () => {
  historySort = historySort === 'newest' ? 'oldest' : 'newest';
  updateHistoryControlLabels();
  filterAuditArchive();
};
updateHistoryControlLabels();
$('#archiveSearch').oninput = filterAuditArchive;
$('#archiveDateFrom').onchange = filterAuditArchive;
$('#archiveDateTo').onchange = filterAuditArchive;

// -------------------------------------------------------------------------
// File Drop Zone Ingestion (PDF Stage 1)
// -------------------------------------------------------------------------
const dropZone = $('#dropDocZone');
const fileInput = $('#fileDocUpload');
const auditDraftFile = $('#auditDraftFile');
$('#importAuditDraftButton').onclick = () => auditDraftFile.click();
auditDraftFile.onchange = async () => {
  const file = auditDraftFile.files?.[0];
  if (!file) return;
  const status = $('#draftImportStatus');
  if (file.size > 10 * 1024 * 1024) { status.textContent = 'This file is over 10 MB. Try a smaller file. Scanned PDFs need OCR, which is not supported yet.'; auditDraftFile.value=''; return; }
  status.textContent = 'Extracting text…';
  try {
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = ''; for (let i=0;i<bytes.length;i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192));
    const response = await fetch('/api/import', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:file.name,data:btoa(binary)})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not extract this document.');
    if (!result.text?.trim()) throw new Error('No readable text was found. This may be a scanned PDF; OCR is not supported yet.');
    $('#workspaceInput').value = result.text.slice(0,250000);
    $('#auditTitleInput').value = $('#auditTitleInput').value.trim() || file.name.replace(/\.[^.]+$/,'').slice(0,150);
    $('#workspaceInput').dispatchEvent(new Event('input', {bubbles:true}));
    status.textContent = `Extracted ${Math.min(result.text.length,250000).toLocaleString()} characters from ${file.name}. Review the draft before auditing.`;
  } catch (error) { status.textContent = error.message || 'Document extraction failed. Your current draft was preserved.'; }
  finally { auditDraftFile.value=''; }
};

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

async function handleFileUpload(file) {
  if(file.size>10*1024*1024){toast('Choose a file smaller than 10 MB');return;}
  toast('Extracting document text…');
  try {
    const bytes=new Uint8Array(await file.arrayBuffer());
    let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
    const response=await fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:file.name,data:btoa(binary)})});
    const result=await response.json();if(!response.ok)throw new Error(result.error);
    $('#newRuleStatement').value=result.text;
    $('#newRuleEvidence').value='Imported document: '+file.name;
    openModal('#modalAddClaim');
    toast('Text extracted. Review wording, owner and expiry before saving approved guidance.');
  } catch(error){toast(error.message||'Document import failed');}
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
function activeStrictness() {
  return $('#segStrict')?.classList.contains('active') ? 'strict' : $('#segLenient')?.classList.contains('active') ? 'lenient' : 'balanced';
}
function readAuditPreferences() {
  return {strictness: activeStrictness(), passingThreshold: Number($('#thresholdSlider')?.value || 80)};
}
let auditPreferenceSaveTimer = null;
let auditPreferenceSavePromise = Promise.resolve(null);
function applyAuditPreferences(settings) {
  if (!settings || typeof settings !== 'object') return;
  const threshold = Number(settings.passingThreshold);
  if (Number.isFinite(threshold)) $('#thresholdSlider').value = Math.max(50, Math.min(95, threshold));
  const strictnessButton = {lenient:$('#segLenient'), balanced:$('#segBalanced'), strict:$('#segStrict')}[settings.strictness];
  if (strictnessButton) {
    segs.forEach(button => button.classList.remove('active'));
    strictnessButton.classList.add('active');
  }
  updateThresholdText();
  try { localStorage.setItem('brandwise-audit-preferences', JSON.stringify(readAuditPreferences())); } catch {}
}
async function loadAuditPreferences() {
  const settings = await api('/api/audit-preferences');
  if (settings) applyAuditPreferences(settings);
  return settings;
}
async function saveAuditPreferencesNow(snapshot = readAuditPreferences()) {
  const saved = await api('/api/audit-preferences', {method:'POST', body:JSON.stringify(snapshot)});
  const status = $('#auditPreferenceSyncStatus');
  if (saved) {
    applyAuditPreferences(saved);
    if (status) status.textContent = 'Saved for every role in this workspace';
  } else if (status) {
    status.textContent = 'Could not sync. Your local choice will retry on the next audit.';
  }
  return saved;
}
function persistAuditPreferences() {
  const snapshot = readAuditPreferences();
  try { localStorage.setItem('brandwise-audit-preferences', JSON.stringify(snapshot)); } catch {}
  const status = $('#auditPreferenceSyncStatus');
  if (status) status.textContent = 'Saving shared workspace settings…';
  if (auditPreferenceSaveTimer) clearTimeout(auditPreferenceSaveTimer);
  auditPreferenceSaveTimer = setTimeout(() => {
    auditPreferenceSaveTimer = null;
    auditPreferenceSavePromise = auditPreferenceSavePromise.catch(() => null).then(() => saveAuditPreferencesNow(snapshot));
  }, 220);
}
async function flushAndRefreshAuditPreferences() {
  if (auditPreferenceSaveTimer) {
    clearTimeout(auditPreferenceSaveTimer);
    auditPreferenceSaveTimer = null;
    const snapshot = readAuditPreferences();
    auditPreferenceSavePromise = auditPreferenceSavePromise.catch(() => null).then(() => saveAuditPreferencesNow(snapshot));
  }
  await auditPreferenceSavePromise;
  return await loadAuditPreferences();
}
function updateThresholdText() {
  const value = Number($('#thresholdSlider').value);
  $('#thresholdDisplayVal').textContent = `${value}%`;
  $('#thresholdHelpText').textContent = `Audits below ${value}% are marked for additional review.`;
}
const segs = [$('#segLenient'), $('#segBalanced'), $('#segStrict')];
try {
  const savedAuditPreferences = JSON.parse(localStorage.getItem('brandwise-audit-preferences') || 'null');
  if (savedAuditPreferences) {
    const threshold = Number(savedAuditPreferences.passingThreshold);
    if (Number.isFinite(threshold)) $('#thresholdSlider').value = Math.max(50, Math.min(95, threshold));
    const strictnessButton = {lenient:$('#segLenient'), balanced:$('#segBalanced'), strict:$('#segStrict')}[savedAuditPreferences.strictness];
    if (strictnessButton) { segs.forEach(button => button.classList.remove('active')); strictnessButton.classList.add('active'); }
  }
} catch {}
updateThresholdText();
segs.forEach(btn => {
  btn.onclick = () => {
    segs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.id === 'segLenient') $('#thresholdSlider').value = 70;
    if (btn.id === 'segBalanced') $('#thresholdSlider').value = 80;
    if (btn.id === 'segStrict') $('#thresholdSlider').value = 90;
    updateThresholdText();
    persistAuditPreferences();
    toast(`Strictness mode: ${btn.textContent}`);
  };
});

$('#thresholdSlider').oninput = e => {
  updateThresholdText();
  persistAuditPreferences();
};

const themePreference = $('#themePreference');
themePreference.value = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
themePreference.onchange = () => {
  const theme = themePreference.value;
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('brandwise-theme', theme); } catch {}
};
const generalPrefs = ['defaultChannel', 'defaultAiReview', 'saveAuditHistory'];
generalPrefs.forEach(id => {
  const control = document.getElementById(id);
  try {
    const saved = JSON.parse(localStorage.getItem(`brandwise-pref-${id}`));
    if (saved !== null) control.type === 'checkbox' ? control.checked = saved : control.value = saved;
  } catch {}
  control.addEventListener('change', () => {
    const value = control.type === 'checkbox' ? control.checked : control.value;
    try { localStorage.setItem(`brandwise-pref-${id}`, JSON.stringify(value)); } catch {}
  });
});
$$('[data-theme-choice]').forEach(button => {
  button.setAttribute('aria-pressed', String(button.dataset.themeChoice === themePreference.value));
  button.onclick = () => {
    themePreference.value = button.dataset.themeChoice;
    themePreference.dispatchEvent(new Event('change'));
    $$('[data-theme-choice]').forEach(swatch => swatch.setAttribute('aria-pressed', String(swatch === button)));
  };
});

// Settings navigation: show only the preference content selected on the left.
const settingsDescriptions = {
  general: ['General', 'Choose a preference section to manage only the settings related to that area.'],
  profile: ['Workspace Profile', 'Workspace identity and connected partner details.'],
  strictness: ['Audit Preferences', 'Set review strictness and the passing threshold for content checks.'],
  brand: ['Brand Configuration', 'Review the active brand guidelines and visual configuration.'],
  visual: ['Appearance', 'Choose the workspace color theme.'],
  notifications: ['Notifications', 'Review alert and notification settings.'],
  apikeys: ['Data & Privacy / Keys', 'Manage connected service credentials used by this local workspace.']
};
function showSettingsPanel(sub, announce = false) {
  const selected = settingsDescriptions[sub] ? sub : 'general';
  $$('.settings-tab-btn').forEach(btn => {
    const active = btn.dataset.sub === selected;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-pressed', String(active));
  });
  $$('#settingsPanelContent [data-settings-panel]').forEach(panel => {
    panel.hidden = panel.dataset.settingsPanel !== selected;
  });
  $$('#settingsPanelContent [data-settings-grid]').forEach(grid => {
    const visibleCount = [...grid.children].filter(child => !child.hidden).length;
    grid.hidden = visibleCount === 0;
    grid.classList.toggle('settings-grid-single', visibleCount === 1);
  });
  $('#settingsSectionTitle').textContent = settingsDescriptions[selected][0];
  $('#settingsSectionDescription').textContent = settingsDescriptions[selected][1];
  if (announce) toast(`Viewing settings: ${settingsDescriptions[selected][0]}`);
}
$$('.settings-tab-btn').forEach(btn => {
  btn.onclick = () => showSettingsPanel(btn.dataset.sub, true);
});
showSettingsPanel(document.querySelector('.settings-tab-btn.active')?.dataset.sub || 'general');

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

  const normalPass = ratio >= contrastThresholds.normal;
  const largePass = ratio >= contrastThresholds.large;

  $('#wcagNormalBadge').textContent = `AA Normal: ${normalPass ? 'PASS' : 'FAIL'}`;
  $('#wcagNormalBadge').className = `pill-tag ${normalPass ? 'pill-blue' : 'pill-orange'}`;

  $('#wcagLargeBadge').textContent = `AA Large: ${largePass ? 'PASS' : 'FAIL'}`;
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

let contrastThresholds = { normal: 4.5, large: 3.0 };

$('#btnCheckAccessibilityCopy').onclick = async () => {
  const content = $('#workspaceInput').value.trim();
  if (!content) {
    toast('Enter copy in the workspace first');
    return;
  }
  const result = await api('/api/accessibility', {
    method: 'POST',
    body: JSON.stringify({ content })
  });
  if (!result) {
    toast('Accessibility check could not be completed');
    return;
  }
  $('#readabilityGrade').textContent = result.readingGrade === null
    ? 'Not enough text'
    : `${result.readingGrade} (Grade ${result.readabilityPass ? 'within' : 'above'} limit)`;
  const issues = result.headingIssues?.length || 0;
  $('#headingOrderStatus').textContent = result.headingCount
    ? issues ? `${issues} heading order issue${issues === 1 ? '' : 's'} found` : `${result.headingCount} headings checked; order looks good`
    : 'No structured headings found in this copy';
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

$('#btnSaveSettings').onclick = async () => {
  const payload = {};
  const g = $('#keyGemini').value.trim();
  if (g) payload.geminiApiKey = g;

  if (Object.keys(payload).length > 0) {
    await api('/api/keys', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  toast('Settings and API keys saved to .env');
  loadKeys();
};

$('#btnResetSettings').onclick = async () => {
  const defaults = {strictness:'balanced', passingThreshold:80};
  try { localStorage.setItem('brandwise-audit-preferences', JSON.stringify(defaults)); } catch {}
  applyAuditPreferences(defaults);
  $('#defaultChannel').value = 'Website Copy';
  $('#defaultAiReview').value = 'off';
  $('#saveAuditHistory').checked = true;
  generalPrefs.forEach(id => { try { localStorage.setItem(`brandwise-pref-${id}`, JSON.stringify(id === 'defaultChannel' ? 'Website Copy' : id === 'saveAuditHistory')); } catch {} });
  if (themePreference) { themePreference.value='light'; themePreference.dispatchEvent(new Event('change')); }
  rememberUnsavedDraft();
  const saved = await saveAuditPreferencesNow(defaults);
  toast(saved ? 'Workspace preferences reset to defaults.' : 'Local preferences reset. Shared audit defaults could not be saved.');
};

function escapeHTML(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}


// Scatter decorative icons in open space around each section's content.
function arrangeAuthIcons() {
  const overview = document.getElementById('authOverview');
  const stage = document.getElementById('authSignInStage');
  const gate = document.getElementById('accountGate');
  const header = document.getElementById('authPageHeader');

  for (const section of [overview, stage]) {
    const layer = section.querySelector('.auth-features');
    const bounds = layer.getBoundingClientRect();
    if (!bounds.width || !bounds.height) continue;

    const panels = section === stage ? [gate] : section.querySelectorAll(
      '.auth-overview-intro, .auth-demo, #authFeatureSummary, .auth-overview-grid, .auth-overview-cta'
    );
    const panelBounds = [...panels].map(panel => panel.getBoundingClientRect());
    const size = parseFloat(getComputedStyle(layer.firstElementChild).width);
    const clearance = 22;
    const topInset = section === overview ? header.getBoundingClientRect().height + 18 : 36;
    const bottomInset = section === overview ? 36 : 24;
    const clearsPanels = ({ x, y }) => !panelBounds.some(panel =>
      bounds.left + x < panel.right + clearance &&
      bounds.left + x + size > panel.left - clearance &&
      bounds.top + y < panel.bottom + clearance &&
      bounds.top + y + size > panel.top - clearance
    );

    // Fixed, staggered side placements match the reference screenshots.
    const overviewSlots = [
      [.035,.105],[.17,.135],[.83,.12],[.965,.095],
      [.075,.205],[.94,.225],[.025,.315],[.16,.345],[.84,.325],[.975,.355],
      [.07,.435],[.93,.455],[.025,.545],[.17,.565],[.83,.535],[.975,.575],
      [.07,.655],[.94,.675],[.025,.765],[.16,.785],[.84,.755],[.975,.795],
      [.07,.875],[.93,.895],[.025,.955],[.17,.965],[.83,.945],[.975,.97]
    ];
    const signInSlots = [
      [.035,.075],[.17,.11],[.83,.09],[.965,.07],
      [.07,.22],[.94,.24],[.025,.36],[.17,.39],[.83,.35],[.975,.38],
      [.07,.52],[.94,.54],[.025,.66],[.17,.69],[.83,.65],[.975,.68],
      [.07,.82],[.94,.84],[.025,.94],[.17,.96],[.83,.92],[.975,.95],
      [.27,.075],[.73,.075],[.27,.975],[.73,.975]
    ];
    const referenceSlots = section === overview ? overviewSlots : signInSlots;
    [...layer.children].forEach((icon, index) => {
      const anchor = referenceSlots[index];
      const point = anchor && {
        x: Math.round(anchor[0] * bounds.width - size / 2),
        y: Math.round(anchor[1] * bounds.height - size / 2)
      };
      const slot = point && clearsPanels(point) ? point : null;
      icon.classList.toggle('is-positioned', Boolean(slot));
      if (!slot) return;
      icon.style.left = Math.max(0, Math.min(bounds.width - size, slot.x)) + 'px';
      icon.style.top = Math.max(0, Math.min(bounds.height - size, slot.y)) + 'px';
      icon.style.setProperty('--icon-rot', `${Math.round(Math.sin(index * 2.4) * 12)}deg`);
    });


  }
}

const authIconObserver = new ResizeObserver(arrangeAuthIcons);
for (const id of ['authOverview', 'authSignInStage', 'accountGate', 'authPageHeader']) {
  authIconObserver.observe(document.getElementById(id));
}
arrangeAuthIcons();

const authDemoCopy = $('#authDemoCopy');
const authDemoResult = $('#authDemoResult');
const authDemoOriginalCopy = authDemoCopy.innerHTML;
const updateDemoMetrics = () => {
  const text = authDemoCopy.innerText.trim();
  const words = text ? text.split(/\s+/).length : 0;
  $('#authDemoWordCount').textContent = words;
  $('#authDemoReadTime').textContent = Math.max(1, Math.ceil(words / 4));
};
updateDemoMetrics();
$('#authDemoToggle').onclick = event => {
  const revised = event.currentTarget.getAttribute('aria-pressed') !== 'true';
  event.currentTarget.setAttribute('aria-pressed', String(revised));
  if (revised) {
    const originalText = authDemoCopy.innerText;
    const cleaned = originalText
      .replace(/\bgroundbreaking\b/gi, 'thoughtfully designed')
      .replace(/\bcarbon-neutral\b/gi, 'made with lower-impact')
      .replace(/\bguarantees?\b/gi, 'is designed to support');
    authDemoCopy.textContent = cleaned;
    const remaining = (cleaned.match(/\b(groundbreaking|carbon-neutral|guarantees?)\b/gi) || []).length;
    const score = remaining ? 88 : 96;
    $('#authDemoFlagCount').textContent = String(remaining);
    $('#authDemoPending').textContent = remaining ? `${remaining} Flags Pending` : 'Ready to recheck';
    $('#authDemoScore').textContent = String(score);
    $('#authDemoProgress').style.width = `${score}%`;
    $('#authDemoAction').textContent = remaining ? 'Review required' : 'Ready to recheck';
    $('#authDemoScoreNote').textContent = remaining ? 'Some flagged wording remains. Review the draft before publishing.' : 'Guideline edits applied. Run a fresh audit before publishing.';
    $('#authDemoLexicon').textContent = remaining ? '88%' : '100%';
    $('#authDemoLexicon').className = remaining ? 'mid' : '';
    $('#authDemoEsg').textContent = remaining ? '78%' : '93%';
    $('#authDemoEsg').className = 'mid';
    authDemoResult.textContent = remaining ? `${remaining} flagged phrase(s) remain for your review.` : 'Guideline edits applied · run a fresh audit before publishing.';
    event.currentTarget.textContent = '↻  Restore sample findings';
  } else {
    authDemoCopy.innerHTML = authDemoOriginalCopy;
    $('#authDemoFlagCount').textContent = '2';
    $('#authDemoPending').textContent = '2 Flags Pending';
    $('#authDemoScore').textContent = '81';
    $('#authDemoProgress').style.width = '81%';
    $('#authDemoAction').textContent = 'Action required';
    $('#authDemoScoreNote').textContent = '2 claims need evidence or revised wording before publishing.';
    $('#authDemoLexicon').textContent = '78%';
    $('#authDemoLexicon').className = 'mid';
    $('#authDemoEsg').textContent = '62%';
    $('#authDemoEsg').className = 'low';
    authDemoResult.textContent = '';
    event.currentTarget.textContent = '↻  Apply Guideline Rules';
  }
  updateDemoMetrics();
};

const accountForm = $('#accountForm');
const registrationFields = $('#registrationFields');
const roleField = accountForm.elements.role;
const accountError = $('#accountError');
const accountPassword = $('#accountPassword');
const passwordToggle = $('#passwordToggle');
const authTheme = $('#authTheme');
authTheme.value = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
authTheme.onchange = () => {
  const theme = authTheme.value;
  document.documentElement.dataset.theme = theme;
  themePreference.value = theme;
  try { localStorage.setItem('brandwise-theme', theme); } catch {}
};
passwordToggle.onclick = () => {
  const show = accountPassword.type === 'password';
  accountPassword.type = show ? 'text' : 'password';
  passwordToggle.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
  passwordToggle.title = show ? 'Hide password' : 'Show password';
  passwordToggle.setAttribute('aria-pressed', String(show));
  accountPassword.focus();
};
let registration = false;
let roleQuestions = {};
let verifiedEmail = '';
const registrationEmail = $('#registrationEmail');
const emailOtpPanel = $('#emailOtpPanel');
const emailOtpCode = $('#emailOtpCode');
const emailVerificationStatus = $('#emailVerificationStatus');
const sendEmailOtpButton = $('#sendEmailOtp');
const confirmEmailOtpButton = $('#confirmEmailOtp');

async function accountRequest(path, data) {
  const response = await fetch(path, data === undefined ? {credentials:'same-origin'} : {
    method: 'POST', credentials:'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
  });
  const responseText = await response.text();
  let result;
  try {
    result = responseText ? JSON.parse(responseText) : {};
  } catch {
    const detail = responseText.trimStart().startsWith('<')
      ? `The app returned a webpage instead of the account API (HTTP ${response.status}). Refresh the page and try again.`
      : `The account API returned an unreadable response (HTTP ${response.status}).`;
    throw new Error(detail);
  }
  if (!response.ok) {
    const error = new Error(result.error || 'Account request failed.');
    error.status = response.status;
    throw error;
  }
  return result;
}

function resetEmailVerification() {
  verifiedEmail = '';
  emailOtpPanel.hidden = true;
  emailOtpCode.value = '';
  emailOtpCode.disabled = true;
  confirmEmailOtpButton.disabled = true;
  sendEmailOtpButton.disabled = false;
  sendEmailOtpButton.textContent = 'Verify';
  emailVerificationStatus.textContent = '';
  emailVerificationStatus.removeAttribute('data-state');
}

registrationEmail.addEventListener('input', () => {
  if (verifiedEmail && registrationEmail.value.trim().toLowerCase() !== verifiedEmail) resetEmailVerification();
});

emailOtpCode.addEventListener('input', () => {
  confirmEmailOtpButton.disabled = !/^\d{6}$/.test(emailOtpCode.value.trim());
});

sendEmailOtpButton.onclick = async () => {
  if (!registrationEmail.reportValidity()) return;
  const email = registrationEmail.value.trim().toLowerCase();
  sendEmailOtpButton.disabled = true;
  emailVerificationStatus.textContent = 'Sending a verification code via Resend…';
  emailVerificationStatus.dataset.state = 'pending';
  try {
    const res = await accountRequest('/api/auth/send-otp', { email });
    if (registrationEmail.value.trim().toLowerCase() !== email) {
      emailVerificationStatus.textContent = 'The email changed. Verify the current address.';
      emailVerificationStatus.dataset.state = 'error';
      return;
    }
    emailOtpPanel.hidden = false;
    emailOtpCode.disabled = false;
    sendEmailOtpButton.textContent = 'Resend code';
    if (res && res.dev_code) {
      emailOtpCode.value = res.dev_code;
      confirmEmailOtpButton.disabled = false;
      emailVerificationStatus.textContent = `Local mode: code is ${res.dev_code} (auto-filled). Click Confirm to verify.`;
      confirmEmailOtpButton.focus();
    } else {
      confirmEmailOtpButton.disabled = true;
      emailVerificationStatus.textContent = `A 6-digit code was sent to ${email} via Resend. It expires in 10 minutes.`;
      emailOtpCode.focus();
    }
    emailVerificationStatus.dataset.state = 'success';
  } catch (error) {
    emailVerificationStatus.textContent = error.message;
    emailVerificationStatus.dataset.state = 'error';
  } finally {
    sendEmailOtpButton.disabled = false;
  }
};

confirmEmailOtpButton.onclick = async () => {
  const email = registrationEmail.value.trim().toLowerCase();
  const code = emailOtpCode.value.trim();
  confirmEmailOtpButton.disabled = true;
  try {
    await accountRequest('/api/auth/verify-otp', { email, code });
    verifiedEmail = email;
    emailVerificationStatus.textContent = 'Email verified. You can finish creating your account.';
    emailVerificationStatus.dataset.state = 'success';
    sendEmailOtpButton.textContent = 'Verified ✓';
    sendEmailOtpButton.disabled = true;
  } catch (error) {
    emailVerificationStatus.textContent = error.message;
    emailVerificationStatus.dataset.state = 'error';
    confirmEmailOtpButton.disabled = !/^\d{6}$/.test(emailOtpCode.value.trim());
  }
};

function updateRegistrationQuestions() {
  const questions = roleQuestions[roleField.value];
  if (!questions) return;
  ['#orgQuestion', '#workQuestion', '#responsibilityQuestion'].forEach((selector, i) => {
    $(selector).textContent = questions[i];
  });
}
roleField.onchange = updateRegistrationQuestions;

function setRegistration(enabled) {
  registration = enabled;
  const identifierLabel = accountForm.querySelector('label:has(input[name="username"])');
  if (identifierLabel) identifierLabel.firstChild.textContent = enabled ? 'Username ' : 'Username or email ';
  if (enabled && accountForm.elements.username.value.includes('@')) {
    const emailName = accountForm.elements.username.value.split('@')[0];
    const suggested = emailName.toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 32);
    accountForm.elements.username.value = suggested.length >= 3 ? suggested : '';
  }
  $('#accountGate').toggleAttribute('data-registering', enabled);
  registrationFields.hidden = !enabled;
  registrationFields.querySelectorAll('[data-registration-field]').forEach(field => {
    field.disabled = !enabled;
    field.required = enabled;
  });
  accountForm.elements.password.autocomplete = enabled ? 'new-password' : 'current-password';
  accountForm.elements.password.minLength = enabled ? 4 : 0;
  resetEmailVerification();
  $('#accountTitle').textContent = enabled ? 'Create an account' : 'Sign in';
  $('#accountSubmit').textContent = enabled ? 'Register' : 'Sign in';
  $('#accountMode').textContent = enabled ? 'Back to sign in' : 'Create an account';
  $('#forgotPasswordButton').hidden = enabled;
  accountError.textContent = '';
}
setRegistration(false);

const forgotPasswordForm = $('#forgotPasswordForm');
const passwordResetEmail = $('#passwordResetEmail');
const passwordResetStatus = $('#forgotPasswordStatus');
const passwordResetPanel = $('#passwordResetPanel');
const passwordResetCode = $('#passwordResetCode');
const passwordResetNewPassword = $('#passwordResetNewPassword');
const passwordResetConfirmPassword = $('#passwordResetConfirmPassword');

$('#forgotPasswordButton').onclick = () => {
  setRegistration(false);
  accountForm.hidden = true;
  forgotPasswordForm.hidden = false;
  forgotPasswordForm.reset();
  passwordResetPanel.hidden = true;
  passwordResetStatus.textContent = '';
  passwordResetStatus.removeAttribute('data-state');
  $('#accountTitle').textContent = 'Reset password';
  passwordResetEmail.focus();
};

$('#backToSignIn').onclick = () => {
  forgotPasswordForm.hidden = true;
  accountForm.hidden = false;
  setRegistration(false);
  $('#accountTitle').textContent = 'Sign in';
  accountForm.elements.username.focus();
};

$('#sendPasswordResetCode').onclick = async () => {
  if (!passwordResetEmail.reportValidity()) return;
  const button = $('#sendPasswordResetCode');
  button.disabled = true;
  passwordResetStatus.textContent = 'Sending a reset code via Resend…';
  passwordResetStatus.dataset.state = 'pending';
  try {
    const email = passwordResetEmail.value.trim().toLowerCase();
    const result = await accountRequest('/api/auth/password-reset/send', { email });
    passwordResetPanel.hidden = false;
    if (result && result.dev_code) {
      passwordResetCode.value = result.dev_code;
      passwordResetStatus.textContent = `Local mode: reset code is ${result.dev_code} (auto-filled).`;
      passwordResetNewPassword.focus();
    } else {
      passwordResetStatus.textContent = result.message || `If an account uses that email, a 6-digit reset code has been sent via Resend.`;
      passwordResetCode.focus();
    }
    passwordResetStatus.dataset.state = 'success';
  } catch (error) {
    passwordResetStatus.textContent = error.message;
    passwordResetStatus.dataset.state = 'error';
  } finally { button.disabled = false; }
};

forgotPasswordForm.onsubmit = async event => {
  event.preventDefault();
  const code = passwordResetCode.value.trim();
  const newPassword = passwordResetNewPassword.value;
  const confirmPassword = passwordResetConfirmPassword.value;
  if (!/^\d{6}$/.test(code)) {
    passwordResetStatus.textContent = 'Enter the six-digit code from your email.';
    passwordResetStatus.dataset.state = 'error';
    return;
  }
  if (newPassword !== confirmPassword) {
    passwordResetStatus.textContent = 'The new passwords do not match.';
    passwordResetStatus.dataset.state = 'error';
    return;
  }
  const button = forgotPasswordForm.querySelector('button[type="submit"]');
  button.disabled = true;
  passwordResetStatus.textContent = 'Updating password…';
  passwordResetStatus.dataset.state = 'pending';
  try {
    const email = passwordResetEmail.value.trim().toLowerCase();
    await accountRequest('/api/auth/password-reset', { email, code, newPassword });
    passwordResetStatus.textContent = 'Password reset successfully. Return to sign in and use your new password.';
    passwordResetStatus.dataset.state = 'success';
    passwordResetPanel.hidden = true;
    forgotPasswordForm.reset();
  } catch (error) {
    passwordResetStatus.textContent = error.message;
    passwordResetStatus.dataset.state = 'error';
  } finally { button.disabled = false; }
};
$('#accountMode').onclick = async () => {
  if (registration) return setRegistration(false);
  try {
    roleQuestions = await accountRequest('/api/auth/roles');
    roleField.replaceChildren(...Object.keys(roleQuestions).map(role => new Option(role, role)));
    updateRegistrationQuestions();
    setRegistration(true);
  } catch (error) { accountError.textContent = error.message; }
};
accountForm.onsubmit = async event => {
  event.preventDefault();
  const button = $('#accountSubmit');
  button.disabled = true;
  try {
    const formData = Object.fromEntries(new FormData(accountForm));
    if (registration && verifiedEmail !== String(formData.email || '').trim().toLowerCase()) {
      throw new Error('Verify your email address before creating an account.');
    }
    if (registration) {
      if (formData.username.includes('@')) {
        const emailName = formData.username.split('@')[0];
        formData.username = emailName.toLowerCase().replace(/[^a-z0-9_]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 32);
      }
      if (!/^[A-Za-z0-9_]{3,32}$/.test(formData.username)) throw new Error('Choose a username with 3 to 32 letters, numbers, or underscores.');
      await accountRequest('/api/auth/register', formData);
      setRegistration(false);
      accountForm.elements.password.value = '';
      await initializeAccount();
      setTab('profile');
    } else {
      await accountRequest('/api/auth/login', formData);
      await initializeAccount();
    }
  } catch (error) {
    accountError.textContent = error.message;
  } finally { button.disabled = false; }
};
const profileMenu = $('#profileMenu');
const profileButton = $('#topAvatar');
const profilePopover = $('#profilePopover');
let profileVerifiedEmail = '';
function fillProfileEditor(user) {
  $('#editProfileName').value = user.name || '';
  $('#editProfileUsername').value = user.username || '';
  $('#editProfileEmail').value = user.email || '';
  $('#editProfileOrganization').value = user.organization || '';
  const roleSelect = $('#editProfileRole');
  let adminOption = roleSelect.querySelector('option[value="Admin"]');
  if (user.role === 'Admin' && !adminOption) {
    adminOption = new Option('Admin (managed)', 'Admin');
    adminOption.disabled = true;
    roleSelect.add(adminOption);
  } else if (user.role !== 'Admin' && adminOption) {
    adminOption.remove();
  }
  roleSelect.value = user.role || '';
  $('#editProfileWork').value = user.work || '';
  $('#editProfileResponsibilities').value = user.responsibilities || '';
  $('#profileRoleBadge').textContent = user.role || 'ROLE';
  profileVerifiedEmail = '';
}
const profileEmail = $('#editProfileEmail');
const profileEmailCode = $('#profileEmailOtpCode');
function clearProfileEmailVerification() {
  profileVerifiedEmail = '';
  $('#profileEmailOtpPanel').hidden = true;
  profileEmailCode.value = '';
  $('#confirmProfileEmailOtp').disabled = true;
  $('#profileEmailStatus').textContent = '';
  $('#profileEmailStatus').removeAttribute('data-state');
}
profileEmail.addEventListener('input', clearProfileEmailVerification);
profileEmailCode.addEventListener('input', () => { $('#confirmProfileEmailOtp').disabled = !/^\d{6}$/.test(profileEmailCode.value.trim()); });
$('#sendProfileEmailOtp').onclick = async () => {
  if (!profileEmail.reportValidity()) return;
  const email = profileEmail.value.trim().toLowerCase();
  try {
    const res = await accountRequest('/api/auth/send-otp', {email});
    $('#profileEmailOtpPanel').hidden = false;
    profileEmailCode.disabled = false;
    if (res && res.dev_code) {
      profileEmailCode.value = res.dev_code;
      $('#confirmProfileEmailOtp').disabled = false;
      $('#profileEmailStatus').textContent = `Local mode: code is ${res.dev_code} (auto-filled). Click Confirm to verify.`;
      $('#confirmProfileEmailOtp').focus();
    } else {
      $('#confirmProfileEmailOtp').disabled = true;
      $('#profileEmailStatus').textContent = `A 6-digit code was sent to ${email} via Resend. It expires in 10 minutes.`;
      profileEmailCode.focus();
    }
    $('#profileEmailStatus').dataset.state = 'success';
  } catch (error) {
    $('#profileEmailStatus').textContent = error.message;
    $('#profileEmailStatus').dataset.state = 'error';
  }
};
$('#confirmProfileEmailOtp').onclick = async () => {
  const email = profileEmail.value.trim().toLowerCase();
  try {
    await accountRequest('/api/auth/verify-otp', {email, code:profileEmailCode.value.trim()});
    profileVerifiedEmail = email;
    $('#profileEmailStatus').textContent = 'New email verified. Save your profile to apply it.';
    $('#profileEmailStatus').dataset.state = 'success';
  } catch (error) {
    $('#profileEmailStatus').textContent = error.message;
    $('#profileEmailStatus').dataset.state = 'error';
  }
};
$('#profileEditForm').onsubmit = async event => {
  event.preventDefault();
  const button = $('#saveProfileButton');
  button.disabled = true;
  $('#profileSaveStatus').textContent = '';
  const payload = {
    username: $('#editProfileUsername').value.trim(),
    email: profileEmail.value.trim(),
    name: $('#editProfileName').value.trim(),
    role: $('#editProfileRole').value,
    organization: $('#editProfileOrganization').value.trim(),
    work: $('#editProfileWork').value.trim(),
    responsibilities: $('#editProfileResponsibilities').value.trim()
  };
  try {
    const oldEmail = $('#profileEmail').textContent.trim().toLowerCase();
    if (payload.email.toLowerCase() !== oldEmail && profileVerifiedEmail !== payload.email.toLowerCase()) {
      throw new Error('Verify the new email address before saving.');
    }
    const user = await accountRequest('/api/auth/profile', payload);
    currentRole = user.role;
    fillProfileEditor(user);
    $('#userRoleSelect').value = user.role;
    $('#topAvatar').textContent = (user.name || user.username).slice(0,2).toUpperCase();
    $('#topAvatar').title = user.name || user.username;
    $('#profileName').textContent = user.name || user.username;
    $('#profileUsername').textContent = `@${user.username}`;
    $('#profileRole').textContent = user.role;
    $('#profileEmail').textContent = user.email || 'Not provided';
    $('#profileOrganization').textContent = user.organization || 'Not provided';
    $('#profileWork').textContent = user.work || 'Not provided';
    $('#profileSaveStatus').textContent = 'Profile saved.';
    toast('Profile updated');
  } catch (error) {
    $('#profileSaveStatus').textContent = error.message;
  } finally { button.disabled = false; }
};
const deleteAccountConfirmation = $('#deleteAccountConfirmation');
const deleteAccountPassword = $('#deleteAccountPassword');
const deleteAccountStatus = $('#deleteAccountStatus');
$('#deleteAccountButton').onclick = () => {
  deleteAccountConfirmation.hidden = false;
  deleteAccountStatus.textContent = '';
  deleteAccountPassword.value = '';
  deleteAccountPassword.focus();
};
$('#cancelAccountDeletion').onclick = () => {
  deleteAccountConfirmation.hidden = true;
  deleteAccountPassword.value = '';
  deleteAccountStatus.textContent = '';
};
deleteAccountConfirmation.onsubmit = async event => {
  event.preventDefault();
  const password = deleteAccountPassword.value;
  const confirmButton = $('#confirmAccountDeletion');
  confirmButton.disabled = true;
  $('#cancelAccountDeletion').disabled = true;
  deleteAccountStatus.textContent = 'Verifying password and deleting your profile…';
  try {
    await accountRequest('/api/auth/delete', {password});
    deleteAccountPassword.value = '';
    location.reload();
  } catch (error) {
    deleteAccountStatus.textContent = error.message;
    deleteAccountPassword.value = '';
    deleteAccountPassword.focus();
  } finally {
    confirmButton.disabled = false;
    $('#cancelAccountDeletion').disabled = false;
  }
};

const profileChangePasswordForm = $('#profileChangePasswordForm');
const profilePasswordStatus = $('#profilePasswordStatus');
profileChangePasswordForm.onsubmit = async event => {
  event.preventDefault();
  const currentPassword = $('#profileCurrentPassword').value;
  const newPassword = $('#profileNewPassword').value;
  const confirmation = $('#profileConfirmPassword').value;
  if (newPassword !== confirmation) {
    profilePasswordStatus.textContent = 'The new passwords do not match.';
    return;
  }
  const button = $('#saveNewPassword');
  button.disabled = true;
  profilePasswordStatus.textContent = 'Updating password…';
  try {
    await accountRequest('/api/auth/change-password', {currentPassword, newPassword});
    profileChangePasswordForm.reset();
    profilePasswordStatus.textContent = 'Password changed successfully.';
  } catch (error) {
    profilePasswordStatus.textContent = error.message;
  } finally { button.disabled = false; }
};

const profilePasswordResetForm = $('#profilePasswordResetForm');
const profilePasswordResetStatus = $('#profilePasswordResetStatus');
$('#profileForgotPassword').onclick = () => {
  $('#profileResetEmail').value = $('#editProfileEmail').value.trim();
  profilePasswordResetStatus.textContent = '';
  profileChangePasswordForm.hidden = true;
  profilePasswordResetForm.hidden = false;
};
$('#cancelProfilePasswordReset').onclick = () => {
  profilePasswordResetForm.reset();
  profilePasswordResetForm.hidden = true;
  profileChangePasswordForm.hidden = false;
  profilePasswordResetStatus.textContent = '';
};
$('#profileSendResetCode').onclick = async () => {
  const email = $('#profileResetEmail');
  if (!email.reportValidity()) return;
  const button = $('#profileSendResetCode');
  button.disabled = true;
  profilePasswordResetStatus.textContent = 'Sending a reset code via Resend…';
  try {
    const address = email.value.trim().toLowerCase();
    const result = await accountRequest('/api/auth/password-reset/send', {email:address});
    $('#profileResetFields').hidden = false;
    if (result && result.dev_code) {
      $('#profileResetCode').value = result.dev_code;
      profilePasswordResetStatus.textContent = `Local mode: reset code is ${result.dev_code} (auto-filled).`;
      $('#profileResetNewPassword').focus();
    } else {
      profilePasswordResetStatus.textContent = result.message || `If an account uses that email, a 6-digit reset code has been sent via Resend.`;
      $('#profileResetCode').focus();
    }
  } catch (error) {
    profilePasswordResetStatus.textContent = error.message;
  } finally { button.disabled = false; }
};
profilePasswordResetForm.onsubmit = async event => {
  event.preventDefault();
  const code = $('#profileResetCode').value.trim();
  const newPassword = $('#profileResetNewPassword').value;
  if (!/^\d{6}$/.test(code)) {
    profilePasswordResetStatus.textContent = 'Enter the six-digit code from your email.';
    return;
  }
  if (newPassword !== $('#profileResetConfirmPassword').value) {
    profilePasswordResetStatus.textContent = 'The new passwords do not match.';
    return;
  }
  const button = profilePasswordResetForm.querySelector('button[type="submit"]');
  button.disabled = true;
  profilePasswordResetStatus.textContent = 'Updating password…';
  try {
    await accountRequest('/api/auth/password-reset', {
      email: $('#profileResetEmail').value.trim().toLowerCase(),
      code,
      newPassword
    });
    profilePasswordResetForm.reset();
    profilePasswordResetStatus.textContent = 'Password reset successfully. Sign out and sign in with your new password.';
  } catch (error) {
    profilePasswordResetStatus.textContent = error.message;
  } finally { button.disabled = false; }
};
function setProfileOpen(open) {
  profilePopover.hidden = !open;
  if (open) {
    const buttonRect = profileButton.getBoundingClientRect();
    const panelHeight = profilePopover.getBoundingClientRect().height;
    profilePopover.style.top = `${Math.max(12, Math.min(buttonRect.bottom + 10, window.innerHeight - panelHeight - 12))}px`;
  }
  profileButton.setAttribute('aria-expanded', String(open));
}
async function refreshProfileSummary() {
  const user = await api('/api/auth/me');
  if (!user) return;
  $('#profileName').textContent = user.name || user.username || 'Your profile';
  $('#profileUsername').textContent = `@${user.username || ''}`;
  $('#profileRole').textContent = user.role || '';
  $('#profileRoleBadge').textContent = user.role || 'ROLE';
  $('#profileEmail').textContent = user.email || 'Not provided';
  $('#profileOrganization').textContent = user.organization || 'Not provided';
  $('#profileWork').textContent = user.work || 'Not provided';
  setProfileOpen(true);
}
profileButton.onclick = () => {
  const opening = profilePopover.hidden;
  setProfileOpen(opening);
  if (opening) refreshProfileSummary();
};
$('#profileClose').onclick = () => { setProfileOpen(false); profileButton.focus(); };
document.addEventListener('click', event => {
  if (!profilePopover.hidden && !profileMenu.contains(event.target)) setProfileOpen(false);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !profilePopover.hidden) {
    setProfileOpen(false);
    profileButton.focus();
  }
});
window.addEventListener('resize', () => {
  if (!profilePopover.hidden) setProfileOpen(true);
});
$('#accountSignOut').onclick = async () => {
  try {
    await accountRequest('/api/auth/logout', {});
    location.reload();
  } catch (error) { toast(error.message); }
};
async function initializeAccount() {
  const user = await accountRequest('/api/auth/me');
  currentUserRecord = user;
  activeAccountName = (user.username || '').toLowerCase();
  currentRole = user.role;
  activeCompanyId = user.activeCompanyId || null;
  await loadWorkspaceProfile();
  const currentGuidelines = await api('/api/guidelines');
  if (currentGuidelines?.accessibility) {
    contrastThresholds = {
      normal: Number(currentGuidelines.accessibility.contrastNormalText) || 4.5,
      large: Number(currentGuidelines.accessibility.contrastLargeText) || 3.0
    };
    updateContrastCalc();
  }
  $('#userRoleSelect').value = user.role;
  $('#userRoleSelect').disabled = true;
  $('#topAvatar').textContent = user.name.slice(0, 2).toUpperCase();
  $('#topAvatar').title = user.name;
  $('#profileName').textContent = user.name || user.username;
  $('#profileUsername').textContent = `@${user.username}`;
  $('#profileRole').textContent = user.role;
  $('#profileEmail').textContent = user.email || 'Not provided';
  $('#profileOrganization').textContent = user.organization || 'Not provided';
  $('#profileWork').textContent = user.work || 'Not provided';
  fillProfileEditor(user);
  await Promise.all([refreshGuidelineCounts(), refreshHistoryMetrics(), refreshStorageStatus()]);
  await Promise.all([loadBrandAssets(), loadCalendar(), loadAlerts()]);
  $('#roleScopeTag').style.display = 'none';
  $('#view-settings').querySelector('#keyGemini').closest('.white-panel').hidden = user.role !== 'Admin';
  document.documentElement.dataset.signedIn = 'true';
  window.scrollTo(0, 0);
  accountForm.reset();
  await loadAuditPreferences();
  if (user.role === 'Admin') loadKeys();
  if (activeCompanyRole === 'Admin') loadAdminTeam();
  try {
    const savedDraft = JSON.parse(localStorage.getItem(localKey('unsaved-draft')) || 'null');
    if (savedDraft && !$('#workspaceInput').value.trim() && (savedDraft.content || savedDraft.title) && confirm('Restore the unsaved draft saved in this browser?')) {
      $('#workspaceInput').value = savedDraft.content || '';
      $('#auditTitleInput').value = savedDraft.title || '';
      const status = $('#auditDraftStatus'); if (status) status.textContent = 'Unsaved draft restored from this browser.';
    }
  } catch {}
}
initializeAccount().catch(() => {});


})();
