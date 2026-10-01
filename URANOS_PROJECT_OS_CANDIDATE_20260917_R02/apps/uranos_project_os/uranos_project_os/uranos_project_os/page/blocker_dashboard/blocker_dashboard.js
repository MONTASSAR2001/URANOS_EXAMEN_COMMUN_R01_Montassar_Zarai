/**
 * blocker_dashboard.js — URANOS Blocker Dashboard controller
 *
 * Architecture:
 *   - Pure Frappe Page controller: no external JS dependencies.
 *   - All data comes from frappe.call → frappe.db.get_list (server-side ORM,
 *     permission-scoped by security.py automatically).
 *   - Two frappe.Chart instances: status donut + category bar.
 *   - Full bilingual support (FR / AR) driven by frappe.boot.lang.
 *   - RTL layout applied via dir attribute on the root wrapper.
 *   - All DOM reads/writes are mediated through id-addressed helpers to
 *     keep the controller decoupled from the HTML structure.
 */

/* global frappe */

frappe.pages["blocker-dashboard"].on_page_load = function (wrapper) {
  "use strict";

  // ── i18n ────────────────────────────────────────────────────────────────
  const ar  = String(frappe.boot.lang || "fr").startsWith("ar");
  const T   = (fr, _ar) => ar ? _ar : fr;
  const esc = v => frappe.utils.escape_html(String(v ?? ""));

  const LABELS = {
    title:      T("Blocker Dashboard", "لوحة تحكم العوائق"),
    subtitle:   T("Surveillance opérationnelle des blocages URANOS", "مراقبة تشغيلية لعوائق أورانوس"),
    allProjects:T("— Tous les projets —", "— جميع المشاريع —"),
    allSev:     T("Toutes", "جميع الخطورات"),
    createBlocker: T("+ Nouvel Obstacle", "+ عائق جديد"),
    refresh:    T("Actualiser", "تحديث"),
    loading:    T("Chargement…", "جارٍ التحميل…"),
    updatedAt:  T("Actualisé à", "تم التحديث في"),
    noData:     T("Aucun blocage actif pour ce filtre.", "لا توجد عوائق نشطة لهذا الفلتر."),

    kpiActive:  T("Blocages actifs", "عوائق نشطة"),
    kpiCritical:T("Critical / High", "حرج / عالٍ"),
    kpiPending: T("En attente vérif.", "بانتظار التحقق"),
    kpiOverdue: T("Hors délai cible", "تجاوز الموعد"),

    chartStatus:   T("Répartition par statut", "التوزيع حسب الحالة"),
    chartCategory: T("Blocages par catégorie", "العوائق حسب الفئة"),

    thTitle:    T("Titre", "العنوان"),
    thProject:  T("Projet", "المشروع"),
    thStatus:   T("Statut", "الحالة"),
    thSeverity: T("Sévérité", "الخطورة"),
    thCategory: T("Catégorie", "الفئة"),
    thResp:     T("Responsable", "المسؤول"),
    thTarget:   T("Délai cible", "الموعد المستهدف"),
    thLost:     T("H. perdues", "ساعات ضائعة"),
    thAction:   T("Action", "إجراء"),
    btnOpen:    T("Ouvrir", "فتح"),

    statusOpen:    T("Open", "مفتوح"),
    statusIP:      T("In Progress", "قيد التنفيذ"),
    statusPending: T("Pending Verification", "بانتظار التحقق"),
    statusClosed:  T("Closed", "مغلق"),

    projectLabel:  T("Projet", "المشروع"),
    severityLabel: T("Sévérité", "الخطورة"),
  };

  // ── Frappe Page boilerplate ──────────────────────────────────────────────
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title:  LABELS.title,
    single_column: true,
  });

  // Apply RTL on root wrapper
  if (ar) {
    $(wrapper).attr("dir", "rtl");
    $(wrapper).find(".uranos-bd").attr("dir", "rtl");
  }

  // Inject page HTML from the companion .html template
  $(wrapper).find(".layout-main-section").html(
    frappe.render_template("blocker_dashboard")
  );

  // ── DOM handle cache (avoids repeated querySelector calls) ──────────────
  const byId = id => document.getElementById(id);

  const DOM = {
    root:          byId("uranos-bd"),
    projectSel:    byId("bd-project-select"),
    severitySel:   byId("bd-severity-select"),
    refreshBtn:    byId("bd-refresh-btn"),
    refreshLabel:  byId("bd-refresh-label"),
    createBtn:     byId("bd-create-btn"),
    createLabel:   byId("bd-create-label"),
    refreshIcon:   document.querySelector("#bd-refresh-btn .bd-btn__icon"),
    loading:       byId("bd-loading"),
    lastUpdated:   byId("bd-last-updated"),

    kpiActiveVal:    byId("kpi-active-val"),
    kpiCriticalVal:  byId("kpi-critical-val"),
    kpiPendingVal:   byId("kpi-pending-val"),
    kpiOverdueVal:   byId("kpi-overdue-val"),
    kpiActiveTrend:  byId("kpi-active-trend"),
    kpiCritTrend:    byId("kpi-critical-trend"),
    kpiPendTrend:    byId("kpi-pending-trend"),
    kpiOverTrend:    byId("kpi-overdue-trend"),

    chartStatusEl:   byId("bd-chart-status"),
    chartCategoryEl: byId("bd-chart-category"),
    chartStatusTitle:   byId("bd-chart-status-title"),
    chartCategoryTitle: byId("bd-chart-category-title"),

    tableBody:  byId("bd-table-body"),
    tableCount: byId("bd-table-count"),
    emptyState: byId("bd-empty-state"),
    emptyText:  byId("bd-empty-text"),

    pageTitle:    byId("bd-page-title"),
    pageSubtitle: byId("bd-page-subtitle"),
    loadingText:  byId("bd-loading-text"),
    projectLabel: byId("bd-project-label"),
    severityLabel:byId("bd-severity-label"),

    thTitle:    byId("th-title"),
    thProject:  byId("th-project"),
    thStatus:   byId("th-status"),
    thSeverity: byId("th-severity"),
    thCategory: byId("th-category"),
    thResp:     byId("th-resp"),
    thTarget:   byId("th-target"),
    thLost:     byId("th-lost"),
    thAction:   byId("th-action"),
  };

  // ── Apply bilingual static labels ────────────────────────────────────────
  function applyLabels() {
    if (DOM.pageTitle)    DOM.pageTitle.textContent    = LABELS.title;
    if (DOM.pageSubtitle) DOM.pageSubtitle.textContent = LABELS.subtitle;
    if (DOM.loadingText)  DOM.loadingText.textContent  = LABELS.loading;
    if (DOM.createLabel)  DOM.createLabel.textContent  = LABELS.createBlocker;
    if (DOM.refreshLabel) DOM.refreshLabel.textContent = LABELS.refresh;
    if (DOM.emptyText)    DOM.emptyText.textContent    = LABELS.noData;

    if (DOM.projectLabel)  DOM.projectLabel.textContent  = LABELS.projectLabel;
    if (DOM.severityLabel) DOM.severityLabel.textContent = LABELS.severityLabel;

    if (DOM.kpiActiveVal)   DOM.kpiActiveVal.closest(".bd-kpi-card")
      .querySelector(".bd-kpi-card__label").textContent  = LABELS.kpiActive;
    if (DOM.kpiCriticalVal) DOM.kpiCriticalVal.closest(".bd-kpi-card")
      .querySelector(".bd-kpi-card__label").textContent  = LABELS.kpiCritical;
    if (DOM.kpiPendingVal)  DOM.kpiPendingVal.closest(".bd-kpi-card")
      .querySelector(".bd-kpi-card__label").textContent  = LABELS.kpiPending;
    if (DOM.kpiOverdueVal)  DOM.kpiOverdueVal.closest(".bd-kpi-card")
      .querySelector(".bd-kpi-card__label").textContent  = LABELS.kpiOverdue;

    if (DOM.chartStatusTitle)   DOM.chartStatusTitle.textContent   = LABELS.chartStatus;
    if (DOM.chartCategoryTitle) DOM.chartCategoryTitle.textContent = LABELS.chartCategory;

    if (DOM.thTitle)    DOM.thTitle.textContent    = LABELS.thTitle;
    if (DOM.thProject)  DOM.thProject.textContent  = LABELS.thProject;
    if (DOM.thStatus)   DOM.thStatus.textContent   = LABELS.thStatus;
    if (DOM.thSeverity) DOM.thSeverity.textContent = LABELS.thSeverity;
    if (DOM.thCategory) DOM.thCategory.textContent = LABELS.thCategory;
    if (DOM.thResp)     DOM.thResp.textContent     = LABELS.thResp;
    if (DOM.thTarget)   DOM.thTarget.textContent   = LABELS.thTarget;
    if (DOM.thLost)     DOM.thLost.textContent     = LABELS.thLost;
    if (DOM.thAction)   DOM.thAction.textContent   = LABELS.thAction;

    // First option of project select
    if (DOM.projectSel && DOM.projectSel.options[0]) {
      DOM.projectSel.options[0].textContent = LABELS.allProjects;
    }
    // First option of severity select
    if (DOM.severitySel && DOM.severitySel.options[0]) {
      DOM.severitySel.options[0].textContent = LABELS.allSev;
    }
  }

  // ── Chart instances (module-level, recreated on refresh) ────────────────
  let _chartStatus   = null;
  let _chartCategory = null;

  // ── Status → CSS class mapping ───────────────────────────────────────────
  const STATUS_CLASS = {
    "Open":                 "bd-status-pill--open",
    "In Progress":          "bd-status-pill--in-progress",
    "Pending Verification": "bd-status-pill--pending",
    "Closed":               "bd-status-pill--closed",
  };

  const SEVERITY_CLASS = {
    "Low":      "bd-severity-pill--low",
    "Medium":   "bd-severity-pill--medium",
    "High":     "bd-severity-pill--high",
    "Critical": "bd-severity-pill--critical",
  };

  // Chart colour palettes
  const STATUS_COLORS   = ["#4cc9f0", "#6c63ff", "#ffb703", "#00d4aa"];
  const CATEGORY_COLORS = [
    "#6c63ff","#4cc9f0","#00d4aa","#ffb703","#ff4d6d",
    "#f97316","#a78bfa","#34d399","#fb923c","#60a5fa","#f472b6","#94a3b8",
  ];

  // ── Utility: set loading state ───────────────────────────────────────────
  function setLoading(on) {
    if (!DOM.loading) return;
    DOM.loading.hidden = !on;
    if (DOM.refreshBtn) {
      DOM.refreshBtn.disabled = on;
      DOM.refreshBtn.classList.toggle("bd-btn--loading", on);
    }
  }

  // ── Utility: format datetime for display ────────────────────────────────
  function fmtDatetime(dt) {
    if (!dt) return "—";
    try {
      return new Intl.DateTimeFormat(ar ? "ar-DZ" : "fr-FR", {
        dateStyle: "short", timeStyle: "short",
      }).format(new Date(dt));
    } catch {
      return String(dt).slice(0, 16);
    }
  }

  // ── Utility: is a blocker overdue? ───────────────────────────────────────
  function isOverdue(doc) {
    if (!doc.target_resolution) return false;
    if (doc.status === "Closed") return false;
    return new Date(doc.target_resolution) < new Date();
  }

  // ── 1. Load projects accessible to the current user ─────────────────────
  function loadProjectFilter() {
    frappe.call({
      method: "uranos_project_os.services.api.get_accessible_projects",
      callback: function (r) {
        const projects = (r && r.message) ? r.message : [];
        if (!DOM.projectSel || !projects) return;
        DOM.projectSel.options.length = 1;
        projects.forEach(p => {
          const opt = document.createElement("option");
          opt.value       = p.name;
          opt.textContent = p.project_name || p.name;
          DOM.projectSel.appendChild(opt);
        });
      },
    });
  }

  // ── 2. Fetch URANOS Blocker records ─────────────────────────────────────
  function fetchBlockers(projectFilter, severityFilter) {
    const filters = [];
    if (projectFilter)  filters.push(["project",  "=", projectFilter]);
    if (severityFilter) filters.push(["severity", "=", severityFilter]);
    // Exclude fully closed by default — show all to give overdue visibility
    // (closed items still count towards the charts)

    return frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "URANOS Blocker",
        fields: [
          "name", "title", "project", "status", "severity", "category",
          "responsible", "target_resolution", "lost_hours",
          "opened_at", "resolved_by", "resolution_submitted_at",
        ],
        filters,
        limit: 500,
        order_by: "modified desc",
      },
    });
  }

  // ── 3. Compute KPIs from the flat record list ────────────────────────────
  function computeKPIs(docs) {
    const active   = docs.filter(d => d.status !== "Closed");
    const critical = docs.filter(d =>
      ["Critical", "High"].includes(d.severity) && d.status !== "Closed"
    );
    const pending  = docs.filter(d => d.status === "Pending Verification");
    const overdue  = docs.filter(d => isOverdue(d));

    return {
      active:   active.length,
      critical: critical.length,
      pending:  pending.length,
      overdue:  overdue.length,
    };
  }

  // ── 4. Render KPI cards ──────────────────────────────────────────────────
  function renderKPIs(kpis) {
    if (DOM.kpiActiveVal)   DOM.kpiActiveVal.textContent   = kpis.active;
    if (DOM.kpiCriticalVal) DOM.kpiCriticalVal.textContent = kpis.critical;
    if (DOM.kpiPendingVal)  DOM.kpiPendingVal.textContent  = kpis.pending;
    if (DOM.kpiOverdueVal)  DOM.kpiOverdueVal.textContent  = kpis.overdue;

    // Trend badges (simple thresholds for now)
    function trendBadge(el, val, warnAt, errAt, suffix) {
      if (!el) return;
      const isErr  = val >= errAt;
      const isWarn = val >= warnAt;
      el.textContent = suffix || "";
      el.style.background = isErr  ? "rgba(255,77,109,0.15)"
                          : isWarn ? "rgba(255,183,3,0.15)"
                                   : "rgba(0,212,170,0.12)";
      el.style.color = isErr  ? "#ff4d6d"
                     : isWarn ? "#ffb703"
                              : "#00d4aa";
    }
    trendBadge(DOM.kpiActiveTrend,  kpis.active,   5,  10, kpis.active   > 0  ? T("actif", "نشط")    : T("RAS", "لا شيء"));
    trendBadge(DOM.kpiCritTrend,    kpis.critical, 1,   3, kpis.critical > 0  ? T("⚠ priorité", "⚠ أولوية") : "✓");
    trendBadge(DOM.kpiPendTrend,    kpis.pending,  2,   5, kpis.pending  > 0  ? T("à vérifier", "للتحقق")   : "✓");
    trendBadge(DOM.kpiOverTrend,    kpis.overdue,  1,   3, kpis.overdue  > 0  ? T("en retard", "متأخر")    : "✓");
  }

  // ── 5. Render Status Donut chart ─────────────────────────────────────────
  const STATUS_ORDER = ["Open", "In Progress", "Pending Verification", "Closed"];
  const STATUS_FR    = {
    "Open": "Open", "In Progress": "In Progress",
    "Pending Verification": "Vérification", "Closed": "Clôturé",
  };

  function renderStatusChart(docs) {
    if (!DOM.chartStatusEl) return;
    DOM.chartStatusEl.innerHTML = "";

    const counts = {};
    STATUS_ORDER.forEach(s => { counts[s] = 0; });
    docs.forEach(d => { if (counts[d.status] !== undefined) counts[d.status]++; });

    const labels = STATUS_ORDER.map(s => ar ? s : (STATUS_FR[s] || s));
    const values = STATUS_ORDER.map(s => counts[s]);

    try {
      _chartStatus = new frappe.Chart(DOM.chartStatusEl, {
        type:   "donut",
        colors: STATUS_COLORS,
        data: {
          labels,
          datasets: [{ values }],
        },
        height: 240,
        tooltipOptions: { formatTooltipY: d => `${d} blocker${d !== 1 ? "s" : ""}` },
      });
    } catch (e) {
      console.warn("[URANOS BD] frappe.Chart not available:", e);
    }
  }

  // ── 6. Render Category Bar chart ─────────────────────────────────────────
  function renderCategoryChart(docs) {
    if (!DOM.chartCategoryEl) return;
    DOM.chartCategoryEl.innerHTML = "";

    const counts = {};
    const active = docs.filter(d => d.status !== "Closed");
    active.forEach(d => {
      const cat = d.category || "Other";
      counts[cat] = (counts[cat] || 0) + 1;
    });

    // Sort descending
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const labels = sorted.map(([cat]) => cat);
    const values = sorted.map(([, n]) => n);

    if (values.length === 0) {
      DOM.chartCategoryEl.innerHTML =
        `<p style="color:var(--bd-text-muted);font-size:.82rem;text-align:center;padding:60px 0">${
          T("Aucune donnée", "لا توجد بيانات")
        }</p>`;
      return;
    }

    try {
      _chartCategory = new frappe.Chart(DOM.chartCategoryEl, {
        type:   "bar",
        colors: CATEGORY_COLORS,
        data: {
          labels,
          datasets: [{ values, name: T("Blocages actifs", "عوائق نشطة") }],
        },
        height: 240,
        barOptions: { stacked: false, spaceRatio: 0.4 },
        tooltipOptions: { formatTooltipY: d => `${d}` },
        axisOptions: { xIsSeries: true },
      });
    } catch (e) {
      console.warn("[URANOS BD] frappe.Chart not available:", e);
    }
  }

  // ── 7. Render action table ───────────────────────────────────────────────
  function renderTable(docs) {
    if (!DOM.tableBody) return;
    DOM.tableBody.innerHTML = "";

    // Show only non-closed for the actionable table, but allow viewing closed
    // via the full filter
    const rows = docs;

    if (DOM.tableCount)
      DOM.tableCount.textContent = String(rows.length);

    if (rows.length === 0) {
      if (DOM.emptyState) DOM.emptyState.hidden = false;
      return;
    }
    if (DOM.emptyState) DOM.emptyState.hidden = true;

    const df = frappe.datetime.now_datetime();

    rows.forEach(doc => {
      const overdue  = isOverdue(doc);
      const statusCls  = STATUS_CLASS[doc.status]   || "";
      const sevCls     = SEVERITY_CLASS[doc.severity] || "";
      const targetTxt  = doc.target_resolution ? fmtDatetime(doc.target_resolution) : "—";
      const lostH      = doc.lost_hours ? Number(doc.lost_hours).toFixed(1) : "—";
      const resp       = doc.responsible
        ? `<span title="${esc(doc.responsible)}">${esc(doc.responsible.split("@")[0])}</span>`
        : `<span style="color:var(--bd-text-muted)">—</span>`;

      const tr = document.createElement("tr");
      if (overdue) tr.classList.add("is-overdue");

      tr.innerHTML = `
        <td class="bd-table__td bd-table__td--title" title="${esc(doc.title)}">${esc(doc.title)}</td>
        <td class="bd-table__td">${esc(doc.project)}</td>
        <td class="bd-table__td">
          <span class="bd-status-pill ${statusCls}">${esc(doc.status)}</span>
        </td>
        <td class="bd-table__td">
          <span class="bd-severity-pill ${sevCls}">${esc(doc.severity || "—")}</span>
        </td>
        <td class="bd-table__td">${esc(doc.category || "—")}</td>
        <td class="bd-table__td">${resp}</td>
        <td class="bd-table__td bd-table__td--target">${esc(targetTxt)}</td>
        <td class="bd-table__td">${esc(lostH)}</td>
        <td class="bd-table__td">
          <a class="bd-open-btn"
             href="/app/uranos-blocker/${encodeURIComponent(doc.name)}"
             target="_blank"
             rel="noopener noreferrer"
             aria-label="${T("Ouvrir", "فتح")} ${esc(doc.title)}">
            &#8599; ${T("Ouvrir", "فتح")}
          </a>
        </td>`;

      DOM.tableBody.appendChild(tr);
    });
  }

  // ── 8. Main refresh orchestrator ─────────────────────────────────────────
  async function refresh() {
    const projectFilter  = DOM.projectSel  ? DOM.projectSel.value  : "";
    const severityFilter = DOM.severitySel ? DOM.severitySel.value : "";

    setLoading(true);
    try {
      const {message: docs} = await fetchBlockers(projectFilter, severityFilter);
      const allDocs = docs || [];

      const kpis = computeKPIs(allDocs);
      renderKPIs(kpis);
      renderStatusChart(allDocs);
      renderCategoryChart(allDocs);
      renderTable(allDocs);

      // Timestamp
      if (DOM.lastUpdated) {
        const now = new Intl.DateTimeFormat(ar ? "ar-DZ" : "fr-FR", {
          timeStyle: "medium",
        }).format(new Date());
        DOM.lastUpdated.textContent = `${LABELS.updatedAt} ${now}`;
      }
    } catch (err) {
      frappe.msgprint({
        title:   T("Erreur de chargement", "خطأ في التحميل"),
        message: T(
          "Impossible de charger les données. Vérifiez vos droits d'accès.",
          "تعذّر تحميل البيانات. تحقق من صلاحيات الوصول."
        ),
        indicator: "red",
      });
      console.error("[URANOS BD] refresh error:", err);
    } finally {
      setLoading(false);
    }
  }

  // ── 9. Event listeners ────────────────────────────────────────────────────
  if (DOM.createBtn) {
    DOM.createBtn.addEventListener("click", function () {
      frappe.set_route("app", "uranos-blocker", "new");
    });
  }
  if (DOM.refreshBtn) {
    DOM.refreshBtn.addEventListener("click", refresh);
  }
  const aiBtn = byId("bd-ai-synthesis-btn");
  if (aiBtn) {
    aiBtn.addEventListener("click", function () {
      const proj = (DOM.projectSel && DOM.projectSel.value) ? DOM.projectSel.value : "PV-0001";
      frappe.set_route("uranos-ai-copilot", proj);
    });
  }
  if (DOM.projectSel) {
    DOM.projectSel.addEventListener("change", refresh);
  }
  if (DOM.severitySel) {
    DOM.severitySel.addEventListener("change", refresh);
  }

  // ── 10. Initialise ───────────────────────────────────────────────────────
  applyLabels();
  loadProjectFilter();
  refresh();
};

/**
 * on_page_show is called every time the user navigates back to this page
 * without a full reload. We refresh the data to keep KPIs current.
 */
frappe.pages["blocker-dashboard"].on_page_show = function () {
  // Trigger a silent refresh if the page was already initialised
  const refreshBtn = document.getElementById("bd-refresh-btn");
  if (refreshBtn) refreshBtn.click();
};
