import {translator} from "./i18n.js";
import {openQueue, newDraft, imageEvidence, synchronizeDraft} from "./queue.js";

const $ = selector => document.querySelector(selector);
const escape = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[char]));
const base = "/api/method/uranos_project_os.services.";
const state = {language: localStorage.getItem("uranos-language") === "ar" ? "ar" : "fr", boot: null, project: "", view: "control", contexts: new Map(), dashboards: new Map(), rows: [], queue: null, pending: new Map(), busy: false, install: null, locked: false};
let t = translator(state.language);
let csrf = $("meta[name=csrf-token]")?.content || "";
let activeForm = null;
const roles = {
  control: ["Executive", "Finance Controller", "Engineering Director", "Project Manager", "Read Only Auditor"],
  controller: ["Site Controller", "Project Manager"],
  team: ["Team Lead", "Civil Director", "Electrical Execution Manager", "Project Manager"],
  store: ["Storekeeper", "Project Manager"],
  logistics: ["Procurement Logistics", "Project Manager"],
  quality: ["QA QC", "HSE", "Project Manager"],
};
const operationRoles = {
  progress: ["Team Lead", "Site Controller", "Civil Director", "Electrical Execution Manager", "Project Manager"],
  daily_report: ["Team Lead", "Site Controller", "Project Manager"],
  kit_request: ["Team Lead", "Storekeeper", "Project Manager"],
  kit_return: ["Team Lead", "Storekeeper", "Project Manager"],
  inspection: ["Team Lead", "Site Controller", "QA QC", "Project Manager"],
};
const permitted = allowed => allowed.some(role => state.boot?.roles.includes(`URANOS ${role}`));
const views = () => Object.keys(roles).filter(view => permitted(roles[view]));
const projectAllowed = project => !!state.boot?.projects.some(row => row.name === project);
async function loadAuthorizedDrafts() {
  const queue = state.queue;
  if (!queue) return [];
  const rows = await queue.all();
  if (queue !== state.queue || !state.boot) return [];
  // Preserve ciphertext for revoked projects; never display or replay it.
  return rows.filter(row => projectAllowed(row.envelope.project));
}
const number = value => value == null || !Number.isFinite(Number(value)) ? t("noData") : new Intl.NumberFormat(state.language === "ar" ? "ar-TN" : "fr-TN", {maximumFractionDigits: 2}).format(Number(value));
const percent = value => value == null ? t("noData") : `${number(value)} %`;
const date = value => value ? new Intl.DateTimeFormat(state.language === "ar" ? "ar-TN" : "fr-TN", {dateStyle: "medium", timeStyle: "short"}).format(new Date(value.replace(" ", "T"))) : "—";
const desk = (doctype, name = "", filter = {}) => {
  const slug = doctype.toLowerCase().replaceAll(" ", "-");
  return `/app/${slug}${name ? "/" + encodeURIComponent(name) : ""}${Object.keys(filter).length ? "?" + new URLSearchParams(filter) : ""}`;
};
const link = (label, doctype, name = "", filter = {}) => `<a class="record-link" href="${escape(desk(doctype, name, filter))}" target="_blank" rel="noopener">${escape(label)} <span aria-hidden="true">↗</span></a>`;
const icon = view => ({control: "◫", controller: "✓", team: "↗", store: "▤", logistics: "⇄", quality: "◇", queue: "↻"}[view] || "•");

async function api(method, data = {}, verb = "GET") {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 25000);
  try {
    const url = base + method + (verb === "GET" && Object.keys(data).length ? "?" + new URLSearchParams(data) : "");
    const response = await fetch(url, {method: verb, credentials: "same-origin", cache: "no-store", redirect: "error", signal: controller.signal,
      headers: {Accept: "application/json", ...(verb === "POST" ? {"Content-Type": "application/json", "X-Frappe-CSRF-Token": csrf, "X-URANOS-User": state.boot?.user || ""} : {})},
      ...(verb === "POST" ? {body: JSON.stringify(data)} : {})});
    let payload;
    try { payload = await response.json(); } catch { throw Object.assign(new Error("Invalid server response"), {status: response.status}); }
    if (!response.ok || payload.exc_type) {
      if ([401,403].includes(response.status) && state.boot) lock("sessionExpired");
      throw Object.assign(new Error(payload.exc_type || "Server rejected request"), {status: response.status, type: payload.exc_type});
    }
    return payload.message;
  } finally { clearTimeout(timeout); }
}

function language(value) {
  state.language = value === "ar" ? "ar" : "fr";
  localStorage.setItem("uranos-language", state.language);
  t = translator(state.language);
  document.documentElement.lang = state.language;
  document.documentElement.dir = state.language === "ar" ? "rtl" : "ltr";
}

function lock(message = "lockedHelp") {
  state.locked = true;
  state.queue?.close();
  state.queue = null;
  state.boot = null;
  state.contexts.clear();
  state.dashboards.clear();
  state.pending.clear();
  state.rows = [];
  activeForm = null;
  csrf = "";
  $("#app").innerHTML = `<main id="main" class="boot"><p class="eyebrow">URANOS / PROJECT OS</p><h1>${t("locked")}</h1><p>${t(message)}</p><div class="button-row"><a class="button primary" href="/login?redirect-to=%2Furanos">${t("login")}</a><button id="retry-boot">${t("retry")}</button></div><p lang="ar" dir="rtl">الاتصال مطلوب لفتح المسودات المحفوظة بأمان.</p></main>`;
  $("#retry-boot").onclick = start;
}

async function assertIdentity() {
  let current;
  try { current = await api("api.bootstrap"); }
  catch (error) { if ([401,403].includes(error.status)) lock("sessionExpired"); throw error; }
  if (!state.boot || current.user !== state.boot.user) {
    lock("changedUser");
    throw Object.assign(new Error("Session identity changed"), {status: 403});
  }
  const names = projects => projects.map(project => project.name).sort().join("\0");
  if (names(current.projects) !== names(state.boot.projects) || [...current.roles].sort().join("\0") !== [...state.boot.roles].sort().join("\0") || current.finance_allowed !== state.boot.finance_allowed) {
    lock("sessionExpired");
    throw Object.assign(new Error("Authorization scope changed"), {status:403});
  }
  if (current.csrf_token) csrf = current.csrf_token;
  state.boot.projects = current.projects;
  state.boot.roles = current.roles;
  state.boot.finance_allowed = current.finance_allowed;
}

function notify(message, bad = false) {
  let box = $("#notice");
  if (!box) return;
  box.textContent = message;
  box.hidden = false;
  box.className = `notice ${bad ? "bad" : ""}`;
  box.setAttribute("role", bad ? "alert" : "status");
}

function healthLabel() { return navigator.onLine ? t("online") : t("offline"); }
function badge(status) { return `<span class="badge ${["Red","Amber","Green"].includes(status) ? status.toLowerCase() : "unknown"}">${escape(t(status || "Unknown"))}</span>`; }
function metric(label, value, kind, caption = "") { return `<article class="metric ${kind || ""}"><p>${escape(t(label))}</p><strong>${escape(percent(value))}</strong><span>${escape(caption)}</span><div class="meter" aria-hidden="true"><i style="width:${value == null ? 0 : Math.max(0, Math.min(100, Number(value)))}%"></i></div></article>`; }

function shell() {
  if (!state.boot) return;
  const available = views();
  if (!available.includes(state.view) && state.view !== "queue") state.view = available[0] || "control";
  const queueCount = state.rows.filter(row => row.state !== "synced").length;
  $("#app").innerHTML = `<div class="layout"><aside class="sidebar"><a class="wordmark" href="/uranos"><span>URANOS</span><small>PROJECT OS</small></a><div class="side-label">${t("workspace")}</div><nav aria-label="${t("workspace")}">${available.map(view => `<button class="nav-item ${state.view === view ? "active" : ""}" data-view="${view}" ${state.view === view ? 'aria-current="page"' : ""}><span class="nav-icon" aria-hidden="true">${icon(view)}</span>${t(view)}</button>`).join("")}<button class="nav-item ${state.view === "queue" ? "active" : ""}" data-view="queue"><span class="nav-icon" aria-hidden="true">↻</span>${t("queue")}<b class="count">${queueCount}</b></button></nav><div class="sidebar-foot"><span class="status-dot"></span><span>${t("secureDevice")}</span></div></aside>
  <div class="stage"><header class="topbar"><div class="project-switch"><label for="project-select">${t("project")}</label><select id="project-select">${state.view === "control" ? `<option value="">${t("allProjects")}</option>` : ""}${state.boot.projects.map(project => `<option value="${escape(project.name)}" ${state.project === project.name ? "selected" : ""}>${escape(project.project_name || project.name)}</option>`).join("")}</select></div><div class="top-actions"><span id="connection" class="connection ${navigator.onLine ? "" : "disconnected"}"><i></i>${healthLabel()}</span><button id="language" class="language" aria-label="${state.language === "fr" ? "العربية" : "Français"}">${state.language === "fr" ? "العربية" : "FR"}</button><span class="avatar" title="${escape(state.boot.user)}" aria-label="${escape(state.boot.user)}">${escape(state.boot.user.slice(0,2).toUpperCase())}</span></div></header>
  ${state.boot.environment === "synthetic-browser-fixture" ? `<div class="test-banner">${t("testEnvironment")}</div>` : ""}<main id="main" tabindex="-1"><div id="notice" class="notice" hidden></div><div class="page-heading"><div><p class="eyebrow">${t("today")} / ${t(state.view)}</p><h1>${state.view === "control" ? t("welcome") : t(state.view)}</h1><p class="muted">${state.view === "control" ? t("focus") : t("captureHint")}</p></div><div class="button-row">${state.install ? `<button id="install">${t("install")}</button>` : ""}<button id="refresh"><span aria-hidden="true">↻</span> ${t("refresh")}</button></div></div><div id="content" aria-live="polite"></div><footer class="page-foot"><span>${t("tagline")}</span><span>${escape(state.boot.user)}</span></footer></main></div></div><dialog id="dialog" aria-labelledby="dialog-title"></dialog>`;
  document.querySelectorAll("[data-view]").forEach(button => button.onclick = () => {
    state.view = button.dataset.view;
    if (state.view !== "control" && !state.project) state.project = state.boot.projects[0]?.name || "";
    shell(); render(); loadView();
  });
  $("#project-select").onchange = event => { state.project = event.target.value; render(); loadView(); };
  $("#language").onclick = () => { language(state.language === "fr" ? "ar" : "fr"); shell(); render(); };
  $("#refresh").onclick = () => loadView(true);
  if ($("#install")) $("#install").onclick = async () => { await state.install.prompt(); state.install = null; shell(); render(); };
}

function actionButtons(operations) {
  return `<div class="capture-actions">${operations.filter(op => permitted(operationRoles[op])).map(op => `<button class="action-card" data-capture="${op}"><span aria-hidden="true">${{progress:"↗",daily_report:"▤",kit_request:"+",kit_return:"↩",inspection:"✓"}[op]}</span><strong>${t(op)}</strong><span class="action-arrow" aria-hidden="true">→</span></button>`).join("")}</div>`;
}

function projectCard(project) {
  const dashboard = state.dashboards.get(project.name);
  return `<button class="project-card" data-project="${escape(project.name)}"><div class="card-heading"><span class="project-code">${escape(project.name)}</span>${badge(dashboard?.status)}</div><h2>${escape(project.project_name || project.name)}</h2><div class="card-progress"><strong>${escape(percent(dashboard?.physical_progress))}</strong><span>${t("verified")}</span></div><div class="meter" aria-hidden="true"><i style="width:${Math.max(0,Math.min(100,Number(dashboard?.physical_progress) || 0))}%"></i></div><div class="mini-metrics"><span>${t("planned")}<b>${escape(percent(dashboard?.planned_progress))}</b></span><span>${t("materials")}<b>${escape(percent(dashboard?.material_readiness))}</b></span></div><div class="project-card-foot"><span>${t("details")}</span><span aria-hidden="true">→</span></div></button>`;
}

function packages(dashboard, context) {
  return `<section class="panel"><div class="section-heading"><h2>${t("packages")}</h2><span class="subtle">${dashboard.work_packages?.length || 0}</span></div><div class="package-list">${(dashboard.work_packages || []).map(row => {
    const definition = context?.work_packages.find(item => item.name === row.work_package);
    return `<button class="package-row" data-package="${escape(row.work_package)}"><div><span class="project-code">${escape(definition?.code || row.work_package)}</span><h3>${escape(definition?.title || row.work_package)}</h3><span class="subtle">${t("reportedQty")} ${number(row.qty_reported)} · ${t("verifiedQty")} ${number(row.qty_verified)} / ${number(row.qty_planned)} <bdi>${escape(definition?.uom || "")}</bdi></span></div><div class="package-end"><strong>${percent(row.completion_percent)}</strong><div class="meter"><i style="width:${Math.min(100,Number(row.completion_percent) || 0)}%"></i></div></div></button>`;
  }).join("") || `<p class="empty">${t("noPackages")}</p>`}</div><p class="rule-note">${t("physicalRule")}</p></section>`;
}

function alertPanel(dashboard) {
  const records = [...(dashboard.alerts || []).filter(row => row.status !== "Resolved").map(row => ({...row, doctype: "URANOS Executive Alert", label: row.message || row.rule})), ...(dashboard.blockers || []).filter(row => !["Closed","Resolved","Cancelled"].includes(row.status)).map(row => ({...row, doctype: "URANOS Blocker", label: row.title})), ...(dashboard.ncrs || []).filter(row => row.status !== "Closed").map(row => ({...row, doctype: "URANOS NCR", label: row.defect}))];
  return `<section class="panel"><div class="section-heading"><h2>${t("alerts")}</h2><span class="subtle">${records.length}</span></div>${records.map(row => `<article class="alert-row ${row.severity === "Critical" ? "urgent" : ""}"><span class="alert-symbol" aria-hidden="true">!</span><div><p>${escape(row.label)}</p><span class="subtle">${escape(row.name)} · ${escape(row.severity === "Critical" ? t("critical") : row.severity)}</span><div>${link(t("source"), row.doctype, row.name)}</div></div></article>`).join("") || `<p class="empty">${t("noAlerts")}</p>`}</section>`;
}

function shipmentPanel(dashboard) {
  return `<section class="panel"><div class="section-heading"><h2>${t("shipments")}</h2>${link(t("purchaseOrders"), "Purchase Order", "", {project: state.project})}</div>${(dashboard.shipments || []).map(row => `<article class="shipment-row"><span class="shipment-icon" aria-hidden="true">⇄</span><div><h3>${escape(row.name)}</h3><p class="subtle">${escape(row.status)}</p><div class="shipment-dates"><span>${t("eta")}<b><bdi>${escape(row.eta_revised || row.eta_initial || t("noData"))}</bdi></b></span><span>${t("needBy")}<b><bdi>${escape(row.need_by || t("noData"))}</bdi></b></span></div>${link(t("source"), "URANOS Shipment", row.name)}</div></article>`).join("") || `<p class="empty">${t("empty")}</p>`}</section>`;
}

function queueView() {
  return `<div class="panel queue-intro"><div><h2>${t("localQueue")}</h2><p>${t("draftRule")}</p></div><button id="sync-all" class="primary" ${state.busy || !navigator.onLine ? "disabled" : ""}>${t("syncAll")}</button></div><div class="queue-list">${state.rows.map(row => `<article class="panel queue-card"><div class="card-heading"><span class="project-code">${escape(row.envelope.project)}</span><span class="queue-state ${escape(row.state)}">${t(row.state)}</span></div><h2>${t(row.envelope.operation)}</h2><p class="subtle">${date(row.created)} · ${t("attempts")}: ${row.attempts || 0} · ${t("evidence")}: ${row.envelope.attachments.length}</p><p class="uuid"><span>${t("originalUUID")}</span><bdi>${escape(row.uuid)}</bdi></p>${row.error ? `<p class="error-code">${escape(row.error)}</p>` : ""}<div class="button-row"><button data-review="${row.uuid}">${t("review")}</button>${row.state !== "synced" ? `<button data-sync="${row.uuid}" ${state.busy || !navigator.onLine ? "disabled" : ""}>${t("sync")}</button>` : link(t("source"), row.result.doctype, row.result.name)}${row.state === "synced" && row.envelope.operation === "progress" && !row.submitted ? `<button data-submit="${row.uuid}" ${!navigator.onLine ? "disabled" : ""}>${t("submitProgress")}</button>` : ""}</div></article>`).join("") || `<section class="panel"><p class="empty">${t("noDrafts")}</p></section>`}</div>`;
}

function render() {
  if (!state.boot || !$("#content")) return;
  const context = state.contexts.get(state.project);
  const dashboard = state.dashboards.get(state.project);
  let content = "";
  if (state.view === "queue") content = queueView();
  else if (!state.boot.projects.length) content = `<div class="panel"><p>${t("noProjects")}</p></div>`;
  else if (state.view === "control" && !state.project) content = `<div class="portfolio-label"><h2>${t("portfolio")}</h2><span>${state.boot.projects.length} ${t("scope")}</span></div><div class="project-grid">${state.boot.projects.map(projectCard).join("")}</div><p class="rule-note">${t("physicalRule")}</p>`;
  else {
    if (state.view === "team") content += actionButtons(["progress","kit_request","daily_report","inspection"]);
    if (state.view === "controller") content += actionButtons(["progress","daily_report","inspection"]);
    if (state.view === "store") content += actionButtons(["kit_request","kit_return"]);
    if (state.view === "quality") content += actionButtons(["inspection"]);
    if (["team","controller","store","quality"].includes(state.view)) content += `<p class="rule-note">${t("draftRule")}</p>`;
    if (dashboard) {
      content += `<div class="project-summary"><span class="project-code">${escape(state.project)}</span>${badge(dashboard.status)}<span class="subtle">${t("lastUpdate")}: ${date(dashboard.as_of)}</span></div>`;
      if (["control","team","controller"].includes(state.view)) content += `<div class="metrics">${metric("verified",dashboard.physical_progress,"verified",t("physicalRule"))}${metric("planned",dashboard.planned_progress,"planned")}${metric("materials",dashboard.material_readiness,"materials")}</div><div class="two-columns">${packages(dashboard,context)}${alertPanel(dashboard)}</div>`;
      if (state.view === "controller" || state.view === "quality" && permitted(["QA QC","Project Manager"])) content += `<section class="panel"><div class="section-heading"><h2>${t("pending")}</h2></div>${(state.pending.get(state.project) || []).map(row => `<article class="pending-row"><div><h3>${escape(row.work_package)} · ${escape(row.zone)}</h3><p>${t("reportedQty")}: <strong>${number(row.qty_reported)}</strong> · ${t("reporter")}: ${escape(row.reported_by)}</p>${link(t("source"), "URANOS Field Progress Entry", row.name)}</div>${permitted(["Site Controller"]) && row.reported_by !== state.boot.user ? `<button data-verify="${escape(row.name)}">${t("review")}</button>` : ""}</article>`).join("") || `<p class="empty">${t("noPending")}</p>`}</section>`;
      if (state.view === "logistics") content += shipmentPanel(dashboard) + alertPanel(dashboard);
      if (state.view === "store") content += `<section class="panel"><h2>${t("stockActions")}</h2><p class="muted">${t("stockHint")}</p><div class="desk-links">${link(t("receive"),"Purchase Receipt","",{project:state.project})}${link(t("kitIssues"),"URANOS Kit Issue","",{project:state.project})}${link(t("reels"),"URANOS Cable Reel","",{project:state.project})}</div></section>${alertPanel(dashboard)}`;
      if (state.view === "quality") content += `<section class="panel"><h2>${t("documents")}</h2><p class="muted">${t("qaHint")}</p><div class="desk-links">${link(t("drawing"),"URANOS Document Register","",{project:state.project})}${link(t("ncrRegister"),"URANOS NCR","",{project:state.project})}${link(t("commissioning"),"URANOS Commissioning Dossier","",{project:state.project})}</div><p class="rule-note">${t("drawingWarning")}</p></section>${alertPanel(dashboard)}`;
      if (state.view === "control" && state.boot.finance_allowed && dashboard.costs) content += `<section class="panel"><h2>${t("costs")}</h2><div class="table-scroll"><table><thead><tr><th>${t("package")}</th><th>${t("currency")}</th><th>${t("budget")}</th><th>${t("committed")}</th><th>${t("forecast")}</th></tr></thead><tbody>${dashboard.costs.map(row => `<tr><td>${escape(row.work_package)}</td><td>${escape(row.currency)}</td><td>${number(row.budget)}</td><td>${number(row.committed)}</td><td>${number(row.forecast)}</td></tr>`).join("")}</tbody></table></div></section>`;
    } else content += `<div class="panel empty">${navigator.onLine ? t("loading") : t("unavailable")}</div>`;
  }
  $("#content").innerHTML = content;
  document.querySelectorAll("[data-project]").forEach(button => button.onclick = () => {state.project = button.dataset.project; shell(); render(); loadView();});
  document.querySelectorAll("[data-capture]").forEach(button => button.onclick = () => capture(button.dataset.capture));
  document.querySelectorAll("[data-package]").forEach(button => button.onclick = () => packageDetail(button.dataset.package));
  document.querySelectorAll("[data-sync]").forEach(button => button.onclick = () => syncRows([button.dataset.sync]));
  document.querySelectorAll("[data-review]").forEach(button => button.onclick = () => reviewDraft(button.dataset.review));
  document.querySelectorAll("[data-submit]").forEach(button => button.onclick = () => submitProgress(button.dataset.submit));
  document.querySelectorAll("[data-verify]").forEach(button => button.onclick = () => verification(button.dataset.verify));
  if ($("#sync-all")) $("#sync-all").onclick = () => syncRows(state.rows.filter(row => ["draft","queued","syncing"].includes(row.state)).map(row => row.uuid));
}

let loadSequence = 0;
async function loadView(recheck = false) {
  const sequence = ++loadSequence;
  if (!navigator.onLine) { render(); return; }
  try {
    if (recheck) await assertIdentity();
    if (!state.boot || state.view === "queue") { render(); return; }
    const projects = state.project ? [state.project] : state.boot.projects.map(project => project.name);
    // Four concurrent requests maximum for a portfolio, rather than 25 bursts.
    let index = 0;
    await Promise.all(Array.from({length: Math.min(4,projects.length)}, async () => {
      while (index < projects.length) {
        const project = projects[index++];
        const data = await api("api.dashboard", {project});
        if (!state.boot || sequence !== loadSequence) return;
        state.dashboards.set(project, data);
      }
    }));
    if (state.project) {
      const project = state.project;
      const context = await api("api.project_context", {project});
      if (sequence !== loadSequence || !state.boot) return;
      state.contexts.set(project, context);
      const pending = permitted(["Site Controller","QA QC","Project Manager"]) ? await api("api.pending_verifications", {project}) : [];
      if (!state.boot || sequence !== loadSequence) return;
      state.pending.set(project, pending);
    }
    if (sequence === loadSequence) render();
  } catch (error) {
    if ([401,403].includes(error.status)) lock("sessionExpired");
    else { render(); notify(t("unavailable"), true); }
  }
}

function dialog(title, content) {
  const element = $("#dialog");
  element.innerHTML = `<div class="dialog-heading"><h2 id="dialog-title">${escape(title)}</h2><button class="close-dialog" aria-label="${t("close")}">×</button></div>${content}`;
  element.querySelector(".close-dialog").onclick = () => element.close();
  element.showModal();
  return element;
}

function field(key, {type = "text", required = true, value = "", options = null, label = null, min = null, step = null} = {}) {
  return `<label class="field">${escape(label || t(key))}${required ? ' <span aria-hidden="true">*</span>' : ""}${options ? `<select name="${key}" ${required ? "required" : ""}><option value="">${t("choose")}</option>${options.map(option => `<option value="${escape(option.value)}" ${String(option.value) === String(value) ? "selected" : ""}>${escape(option.label)}</option>`).join("")}</select>` : `<input name="${key}" type="${type}" value="${escape(value)}" ${required ? "required" : ""} ${min != null ? `min="${min}"` : ""} ${step != null ? `step="${step}"` : ""} ${type === "number" ? 'inputmode="decimal" max="1000000000000"' : 'maxlength="140"'} autocomplete="off">`}</label>`;
}

function capture(operation) {
  if (!permitted(operationRoles[operation])) return;
  const context = state.contexts.get(state.project);
  if (!context || !state.queue) { notify(t("captureUnavailable"), true); return; }
  const packagesOptions = context.work_packages.map(row => ({value: row.name, label: `${row.code || row.name} · ${row.title} (${row.uom})`}));
  const warehouses = context.warehouses.map(row => ({value:row.name,label:row.warehouse_name || row.name}));
  const workPackage = () => field("work_package", {label:t("package"),options:packagesOptions});
  const postingDate = () => field("posting_date",{type:"date",value:new Date(Date.now() - new Date().getTimezoneOffset()*60000).toISOString().slice(0,10)});
  let fields = "";
  if (operation === "progress") fields = workPackage() + field("activity") + field("zone") + field("crew") + postingDate() + field("qty_reported",{type:"number",min:"0.000000001",step:"any"});
  if (operation === "daily_report") fields = postingDate() + field("site") + field("manpower",{type:"number",min:0,step:1,required:false}) + field("equipment",{required:false}) + field("weather",{required:false});
  if (operation === "kit_request") fields = workPackage() + field("kit_template",{options:context.kit_templates.map(row => ({value:row.name,label:`${row.kit_code} · ${row.kit_version}`}))}) + field("qty_kits",{type:"number",min:"0.000000001",step:"any"}) + field("from_warehouse",{options:warehouses}) + field("to_warehouse",{options:warehouses}) + field("activity") + field("crew") + field("zone",{required:false});
  if (operation === "kit_return") fields = field("kit_issue") + field("to_warehouse",{options:warehouses});
  if (operation === "inspection") fields = workPackage() + field("zone") + field("inspection_type") + postingDate();
  activeForm = {operation, project:state.project, context};
  const element = dialog(t(operation), `<form id="capture-form"><section id="step-one"><p class="step-label">${t("firstStep")}</p><div class="form-grid">${fields}</div>${["kit_return","inspection"].includes(operation) ? `<div id="rows"></div><button id="add-row" type="button">+ ${t("addRow")}</button>` : ""}<p id="baseline-hint" class="rule-note"></p><div class="dialog-actions"><button type="button" id="next" class="primary">${t("next")} <span aria-hidden="true">→</span></button></div></section><section id="step-two" hidden><p class="step-label">${t("secondStep")}</p><label class="field">${t("notes")}<textarea name="notes" rows="3" maxlength="8000"></textarea></label><label class="field">${t("evidence")}<input type="file" name="evidence" accept="image/png,image/jpeg" multiple capture="environment"></label><p class="rule-note">${t("privateEvidence")}</p><p class="rule-note">${t("draftRule")}</p><p id="form-error" role="alert"></p><div class="dialog-actions"><button type="button" id="back">${t("back")}</button><button type="submit" name="save" class="primary">${t("saveDraft")}</button><button type="submit" name="send" ${!navigator.onLine ? "disabled" : ""}>${t("sendDraft")}</button></div></section></form>`);
  const form = $("#capture-form");
  if (operation === "progress") $("#step-two .step-label").insertAdjacentHTML("afterend", '<div id="allocation-fields"></div>');
  $("#next").onclick = () => {
    const invalid = [...$("#step-one").querySelectorAll("input,select")].find(input => !input.checkValidity());
    if (invalid) { invalid.reportValidity(); return; }
    if (operation === "progress") {
      const selectedPackage = form.elements.work_package.value;
      const prior = activeForm.allocationPackage === selectedPackage ? {kit:form.elements.kit_issue?.value || "",reel:form.elements.cable_reel?.value || ""} : {kit:"",reel:""};
      const issues = (context.kit_issues || []).filter(row => row.work_package === selectedPackage);
      $("#allocation-fields").innerHTML = `<p class="rule-note">${t("allocationHint")}</p><div class="form-grid">${field("kit_issue",{label:t("allocationKit"),required:false,options:issues.map(row => ({value:row.name,label:[row.name,row.activity,row.zone,row.crew,row.status].filter(Boolean).join(" · ")}))})}${field("cable_reel",{label:t("allocationReel"),required:false,options:(context.cable_reels || []).map(row => ({value:row.name,label:[row.reel_id || row.name,row.item_code,row.status].filter(Boolean).join(" · ")}))})}</div>`;
      form.elements.kit_issue.onchange = () => { form.elements.cable_reel.disabled = !!form.elements.kit_issue.value; };
      form.elements.cable_reel.onchange = () => { form.elements.kit_issue.disabled = !!form.elements.cable_reel.value; };
      form.elements.kit_issue.value = prior.kit;
      form.elements.cable_reel.value = prior.reel;
      form.elements.kit_issue.onchange();
      form.elements.cable_reel.onchange();
      activeForm.allocationPackage = selectedPackage;
    }
    $("#step-one").hidden = true; $("#step-two").hidden = false; $("#step-two textarea").focus();
  };
  $("#back").onclick = () => { $("#step-two").hidden = true; $("#step-one").hidden = false; };
  const select = form.elements.work_package;
  if (select) select.onchange = () => {
    const wp = context.work_packages.find(row => row.name === select.value);
    $("#baseline-hint").textContent = wp ? `${t("baseline")}: ${wp.baseline_version || t("noData")} · ${t("unit")}: ${wp.uom}` : "";
  };
  if ($("#add-row")) { $("#add-row").onclick = () => addRow(operation); addRow(operation); }
  form.onsubmit = async event => {
    event.preventDefault();
    if (!$("#step-one").hidden) { $("#next").click(); return; }
    const submitter = event.submitter;
    form.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = true);
    try {
      const payload = {};
      for (const [key,value] of new FormData(form).entries()) if (typeof value === "string" && value.trim() && !key.startsWith("row_")) payload[key] = value.trim();
      const wp = context.work_packages.find(row => row.name === payload.work_package);
      if (operation === "progress") {
        if (form.elements.kit_issue.value && form.elements.cable_reel.value) throw new Error("allocationExclusive");
        if (!wp?.baseline_version) throw new Error("captureUnavailable");
        if (payload.kit_issue && !(context.kit_issues || []).some(row => row.name === payload.kit_issue && row.work_package === payload.work_package)) throw new Error("allocationInvalid");
        if (payload.cable_reel && !(context.cable_reels || []).some(row => row.name === payload.cable_reel)) throw new Error("allocationInvalid");
        payload.baseline_version = wp.baseline_version;
      }
      if (operation === "inspection") payload.checks = [...form.querySelectorAll(".form-row")].map(row => ({check:row.querySelector('[name="row_check"]').value.trim(), result:row.querySelector('[name="row_result"]').value}));
      if (operation === "kit_return") payload.returns = [...form.querySelectorAll(".form-row")].map(row => ({item_code:row.querySelector('[name="row_item_code"]').value.trim(),qty:row.querySelector('[name="row_qty"]').value,uom:row.querySelector('[name="row_uom"]').value.trim()}));
      if (payload.manpower) payload.manpower = Number(payload.manpower);
      const attachments = await imageEvidence([...form.elements.evidence.files]);
      const envelope = newDraft(activeForm.project, operation, payload, attachments, wp?.modified || null);
      const row = {uuid:envelope.uuid,envelope,state:"draft",created:new Date().toISOString(),attempts:0};
      await state.queue.add(row);
      state.rows = await loadAuthorizedDrafts();
      element.close(); activeForm = null;
      state.view = "queue"; shell(); render(); notify(t("saved"));
      if (submitter?.name === "send") await syncRows([row.uuid]);
    } catch (error) {
      if ($("#form-error")) $("#form-error").textContent = t(error.message);
      form.querySelectorAll('button[type="submit"]').forEach(button => button.disabled = button.name === "send" && !navigator.onLine);
    }
  };
}

function addRow(operation) {
  const container = $("#rows");
  if (container.children.length >= 20) return;
  const wrapper = document.createElement("div"); wrapper.className = "form-row";
  wrapper.innerHTML = operation === "kit_return" ? field("row_item_code",{label:t("item_code")}) + field("row_qty",{label:t("qty"),type:"number",min:"0.000000001",step:"any"}) + field("row_uom",{label:t("uom")}) : field("row_check",{label:t("check")}) + field("row_result",{label:t("result"),options:["Pass","Fail","Not Applicable","Not Checked"].map(value => ({value,label:t(value)}))});
  const remove = document.createElement("button"); remove.type = "button"; remove.textContent = t("removeRow"); remove.onclick = () => { if (container.children.length > 1) wrapper.remove(); };
  wrapper.append(remove); container.append(wrapper);
}

async function syncRows(uuids) {
  if (state.busy || !navigator.onLine || !state.queue) return;
  state.busy = true; render();
  try {
    const queue = state.queue;
    for (const uuid of uuids) {
      if (!state.boot || !state.queue) break;
      const row = await queue.get(uuid);
      if (row && projectAllowed(row.envelope.project)) await synchronizeDraft(queue,row,api,assertIdentity);
    }
    if (state.queue) state.rows = await loadAuthorizedDrafts();
  } catch (error) { notify(t("unavailable"), true); }
  finally { state.busy = false; if (state.boot) { shell(); render(); if (state.rows.some(row => uuids.includes(row.uuid) && row.state === "synced")) notify(t("syncedNotice")); } }
}

function reviewDraft(uuid) {
  const row = state.rows.find(item => item.uuid === uuid);
  if (!row) return;
  dialog(t(row.envelope.operation), `<p class="queue-state ${row.state}">${t(row.state)}</p><dl class="detail-list"><dt>${t("project")}</dt><dd><bdi>${escape(row.envelope.project)}</bdi></dd><dt>${t("originalUUID")}</dt><dd><bdi>${row.uuid}</bdi></dd>${Object.entries(row.envelope.payload).map(([key,value]) => `<dt>${escape(t(key))}</dt><dd>${escape(typeof value === "object" ? JSON.stringify(value) : value)}</dd>`).join("")}</dl><h3>${t("evidence")}</h3><ul>${row.envelope.attachments.map(file => `<li><bdi>${escape(file.filename)}</bdi> · ${escape(file.mime_type)}<small class="digest">SHA256: ${file.sha256}</small></li>`).join("")}</ul><p class="rule-note">${t(["rejected","conflict"].includes(row.state) ? "conflictHelp" : "draftRule")}</p>`);
}

function packageDetail(name) {
  const row = state.dashboards.get(state.project)?.work_packages.find(item => item.work_package === name);
  const definition = state.contexts.get(state.project)?.work_packages.find(item => item.name === name);
  if (!row) return;
  dialog(definition?.title || name, `<p class="project-code">${escape(name)}</p><div class="detail-quantities"><div>${t("plannedQty")}<strong>${number(row.qty_planned)}</strong></div><div>${t("reportedQty")}<strong>${number(row.qty_reported)}</strong></div><div>${t("verifiedQty")}<strong>${number(row.qty_verified)}</strong></div></div><p>${t("unit")}: <bdi>${escape(definition?.uom || t("noData"))}</bdi></p><p class="rule-note">${t("physicalRule")}</p><div class="desk-links">${link(t("source"),"URANOS Field Progress Entry","",{project:state.project,work_package:name})}${link(t("drawing"),"URANOS Document Register","",{project:state.project})}</div>`);
}

async function submitProgress(uuid) {
  const row = state.rows.find(item => item.uuid === uuid);
  if (!row || !projectAllowed(row.envelope.project) || row.state !== "synced" || row.envelope.operation !== "progress") return;
  try {
    await assertIdentity();
    await api("operations.submit_progress",{name:row.result.name},"POST");
    row.submitted = true; await state.queue.update(row); render(); notify(t("submitSuccess"));
  } catch (error) { notify(`${t("error")} · ${error.type || t("unavailable")}`,true); }
}

function verification(name) {
  const row = (state.pending.get(state.project) || []).find(item => item.name === name);
  if (!permitted(["Site Controller"]) || !row || row.reported_by === state.boot.user) return;
  const element = dialog(t("pending"), `<p>${escape(row.work_package)} · ${escape(row.zone)} · ${escape(row.activity)}</p><p>${t("reportedQty")}: ${number(row.qty_reported)}</p>${link(t("source"),"URANOS Field Progress Entry",row.name)}<p class="rule-note">${t("verifyHint")}</p><form id="verify-form">${field("qty_verified",{type:"number",min:0,step:"any"})}<p id="verify-error" role="alert"></p><div class="dialog-actions"><button class="primary" type="submit" ${!navigator.onLine ? "disabled" : ""}>${t("verify")}</button></div></form>`);
  $("#verify-form").onsubmit = async event => {
    event.preventDefault();
    const button = event.submitter; button.disabled = true;
    try { await assertIdentity(); await api("operations.verify_progress",{name:row.name,qty_verified:event.target.elements.qty_verified.value},"POST"); element.close(); await loadView(); notify(t("verifySuccess")); }
    catch (error) { if ($("#verify-error")) $("#verify-error").textContent = `${t("error")} · ${error.type || t("unavailable")}`; button.disabled = !navigator.onLine; }
  };
}

async function start() {
  const savedLanguage = localStorage.getItem("uranos-language");
  language(state.language);
  try {
    const boot = await api("api.bootstrap");
    if (!boot?.user || boot.user === "Guest") { lock(); return; }
    if (boot.csrf_token) csrf = boot.csrf_token;
    state.boot = boot; state.locked = false;
    if (!savedLanguage && boot.language === "ar") language("ar");
    state.queue?.close();
    state.queue = null;
    state.rows = [];
    let localError = false;
    try {
      const key = await api("offline.encryption_key",{},"POST");
      state.queue = await openQueue(boot.user,key.key_base64);
      key.key_base64 = null;
      state.rows = await loadAuthorizedDrafts();
      channel?.postMessage({scope:state.queue.scope});
    } catch (error) {
      state.queue?.close();
      state.queue = null;
      state.rows = [];
      if ([401,403].includes(error.status)) { lock("sessionExpired"); return; }
      localError = true;
    }
    const available = views();
    state.view = available[0] || "control";
    state.project = state.view === "control" ? "" : boot.projects[0]?.name || "";
    shell(); render(); await loadView();
    if (localError) notify(t("captureUnavailable"),true);
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/assets/uranos_project_os/field/sw.js",{scope:"/assets/uranos_project_os/field/"}).catch(() => notify(t("unavailable"),true));
  } catch { lock(); }
}

addEventListener("online", () => { if ($("#connection")) { $("#connection").className = "connection"; $("#connection").innerHTML = `<i></i>${healthLabel()}`; } if (state.boot) { render(); assertIdentity().catch(() => {}); } });
addEventListener("offline", () => { if ($("#connection")) { $("#connection").className = "connection disconnected"; $("#connection").innerHTML = `<i></i>${healthLabel()}`; } if (state.boot) render(); });
addEventListener("beforeinstallprompt", event => { event.preventDefault(); state.install = event; if (state.boot) { shell(); render(); } });
// Another authenticated browser tab broadcasts a login identity change. Only
// a SHA256 identity fingerprint is exchanged, never a key or draft content.
const channel = "BroadcastChannel" in window ? new BroadcastChannel("uranos-field-session") : null;
if (channel) channel.onmessage = event => { if (event.data?.scope && state.queue && event.data.scope !== state.queue.scope) lock("changedUser"); };
addEventListener("focus", () => { if (state.boot && navigator.onLine) assertIdentity().catch(() => {}); });
start();
