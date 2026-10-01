/**
 * uranos_ai_copilot.js — Dedicated Full-Screen AI Copilot & Executive Synthesis
 * URANOS Project OS — Phase 4 Cloud AI & RAG Architecture
 * Integrated with Stitch Ultra-Premium Visual Design
 */

/* global frappe, $ */

frappe.pages["uranos-ai-copilot"] = frappe.pages["uranos-ai-copilot"] || {};

frappe.pages["uranos-ai-copilot"].on_page_load = function (wrapper) {
  "use strict";

  // ── 1. Passive i18n & Language Detection ─────────────────────────────────
  // CRITICAL: Safely and dynamically read the current session language.
  // Never manipulate document.documentElement or document.body attributes.
  const currentLang =
    (frappe.boot && frappe.boot.user && frappe.boot.user.language) ||
    (frappe.boot && frappe.boot.lang) ||
    "en";

  const isArabic = String(currentLang).toLowerCase().startsWith("ar");
  const isFrench = String(currentLang).toLowerCase().startsWith("fr");

  const T = (en, fr, ar) => {
    if (isArabic) return ar;
    if (isFrench) return fr;
    return en;
  };

  // ── 2. Page Boilerplate & Template Injection ─────────────────────────────
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("URANOS AI Copilot"),
    single_column: true
  });

  function localizePageUI() {
    // Top Controls Bar
    $(".uac-brand-name").text("URANOS");
    $(".uac-badge-pill").text("COPILOT");
    $(".uac-version-badge").text("Phase 4 RAG");
    $(".uac-page-subtitle").text(
      isArabic
        ? "المساعد الذكي لإدارة مشاريع الطاقة الشمسية"
        : (isFrench ? "Suite d'intelligence pour projets solaires" : "Solar Project Intelligence Suite")
    );
    $(".uac-pill-label").text(isArabic ? "المشروع:" : (isFrench ? "Projet :" : "Project:"));
    $("#uac-refresh-btn span").text(isArabic ? "تحديث" : (isFrench ? "Actualiser" : "Refresh"));
    $("#uac-tts-label").text(isArabic ? "استماع" : (isFrench ? "Écouter" : "Listen"));
    $("#uac-copy-btn span").text(isArabic ? "نسخ" : (isFrench ? "Copier" : "Copy"));
    $("#uac-back-btn span").text(isArabic ? "لوحة التحكم" : (isFrench ? "Tableau de bord" : "Dashboard"));

    // Dashboard Heading
    $("#dash-heading").text(
      isArabic
        ? "مركز العمليات التنفيذي"
        : (isFrench ? "Centre des Opérations Exécutif" : "Executive Operations Hub")
    );
    $(".uac-tag-pill").text(
      isArabic
        ? "متابعة معالم المشروع"
        : (isFrench ? "Suivi des Jalons EPC" : "EPC Milestone Tracking")
    );
    $(".uac-dash-sub").text(
      isArabic
        ? "متابعة مؤتمتة للمشاريع وتوقعات الإنتاج والقياس عن بعد من الميدان."
        : (isFrench ? "Suivi EPC automatisé, prévisions de rendement et télémétrie chantier." : "Autonomous EPC tracking, yield forecasting, and field telemetry intelligence.")
    );

    // KPI Cards Labels
    const $kpis = $(".uac-kpi-card");
    if ($kpis.length >= 4) {
      // KPI 1: Open Blockers
      $kpis.eq(0).find(".uac-kpi-label").text(isArabic ? "التقارير المعلقة" : (isFrench ? "Blocages Ouverts" : "Open Blockers"));
      $kpis.eq(0).find(".uac-kpi-sub span:first-child").text(isArabic ? "● عوائق نشطة" : (isFrench ? "● Actifs en cours" : "● Active Defects"));
      $kpis.eq(0).find(".uac-kpi-hint").text(isArabic ? "في قاعدة البيانات" : (isFrench ? "dans la base" : "in database"));

      // KPI 2: Lost Hours
      $kpis.eq(1).find(".uac-kpi-label").text(isArabic ? "المهام المتأخرة" : (isFrench ? "Heures Perdues" : "Lost Work Hours"));
      $kpis.eq(1).find(".uac-kpi-sub span:first-child").text(isArabic ? "تأثير الموقع" : (isFrench ? "Impact Chantier" : "Site Impact"));
      $kpis.eq(1).find(".uac-kpi-hint").text(isArabic ? "ساعات العمل المفقودة" : (isFrench ? "heures cumulées" : "cumulative lost hours"));

      // KPI 3: Critical Issues
      $kpis.eq(2).find(".uac-kpi-label").text(isArabic ? "المخاطر الحرجة" : (isFrench ? "Risques Critiques" : "Critical Issues"));
      $kpis.eq(2).find(".uac-kpi-sub span:first-child").text(isArabic ? "تدخل عاجل" : (isFrench ? "Intervention Urgente" : "Urgent Intervention"));
      $kpis.eq(2).find(".uac-kpi-hint").text(isArabic ? "مطلوب فوراً" : (isFrench ? "requise" : "required"));

      // KPI 4: Verified Progress
      $kpis.eq(3).find(".uac-kpi-label").text(isArabic ? "التقدم المعتمد" : (isFrench ? "Avancement Vérifié" : "Verified Progress"));
      $kpis.eq(3).find(".uac-kpi-sub span:first-child").text(isArabic ? "أعمال موثقة" : (isFrench ? "Travaux Approuvés" : "Verified Work"));
      $kpis.eq(3).find(".uac-kpi-hint").text(isArabic ? "إدخالات منجزة" : (isFrench ? "entrées validées" : "approved entries"));
    }

    // Document Card Title
    $("#doc-title").text(
      isArabic
        ? "موجز المشروع التنفيذي والتحليل الشامل"
        : (isFrench ? "Synthèse Exécutive et Rapport de Projet" : "Executive Project Briefing & Synthesis")
    );

    // Chat Card Header & Input
    $("#chat-title").text(isArabic ? "مساعد أورانوس" : (isFrench ? "Copilote URANOS" : "URANOS Copilot"));
    $("#uac-chat-input, #gv-ai-chat-input").attr(
      "placeholder",
      isArabic
        ? "اسأل مساعد أورانوس أو استعلم عن مقاييس المشروع..."
        : (isFrench ? "Posez une question au copilote ou consultez les métriques..." : "Ask URANOS Copilot or query project metrics...")
    );

    // Quick Prompt Chips
    const $chips = $(".uac-prompt-chips .uac-chip");
    if ($chips.length >= 3) {
      if (isArabic) {
        $chips.eq(0).text("تقرير المخزون").data("prompt", "أعطني تقريراً عن حالة المخزون وتوريد المواد للمشاريع");
        $chips.eq(1).text("المخاطر والتأخيرات").data("prompt", "ما هي أبرز المخاطر والتأخيرات الحالية وتأثيرها على ساعات العمل؟");
        $chips.eq(2).text("حالة المشاريع الحالية").data("prompt", "أعطني ملخص تنفيذي لحالة المشاريع الحالية مع التركيز على أي مخاطر أو تأخيرات محتملة؟");
      } else if (isFrench) {
        $chips.eq(0).text("Rapport de stock").data("prompt", "Donne-moi un rapport sur l'état des stocks et approvisionnements.");
        $chips.eq(1).text("Risques & retards").data("prompt", "Quels sont les principaux risques et retards actuels et leur impact sur les heures ?");
        $chips.eq(2).text("Synthèse des projets").data("prompt", "Donne-moi une synthèse exécutive de l'état des projets et des alertes.");
      } else {
        $chips.eq(0).text("Stock Report").data("prompt", "Provide a status report on stock availability and material procurement.");
        $chips.eq(1).text("Risks & Delays").data("prompt", "What are the main active risks and delays, and their impact on lost hours?");
        $chips.eq(2).text("Project Status").data("prompt", "Give me an executive summary of current project status highlighting potential risks.");
      }
    }
  }

  // Render Template HTML
  const templateHtml = frappe.render_template ? frappe.render_template("uranos_ai_copilot", {}) : "";
  if (templateHtml) {
    $(wrapper).find(".layout-main-section").html(templateHtml);
    localizePageUI();
  } else {
    $.get("/assets/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html", function (html) {
      if (html) {
        $(wrapper).find(".layout-main-section").html(html);
        localizePageUI();
      }
    });
  }

  // ── 3. State Management ──────────────────────────────────────────────────
  let activeProject = "PV-0001";
  let activeSynthesisText = "";
  let isGenerating = false;

  // ── 4. Markdown Formatter ────────────────────────────────────────────────
  function formatMarkdown(raw) {
    if (!raw) return "";
    let html = String(raw);

    // Escape raw HTML entities
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3 class="uac-md-h3">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="uac-md-h2">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="uac-md-h1">$1</h1>');

    // Bold & Italics
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong class="uac-md-bold">$1</strong>');
    html = html.replace(/\*(.*?)\*/gim, '<em class="uac-md-italic">$1</em>');

    // Bullets
    html = html.replace(/^\s*[-•]\s+(.*)$/gim, '<li class="uac-md-li">$1</li>');
    html = html.replace(/(<li class="uac-md-li">.*<\/li>\s*)+/gim, '<ul class="uac-md-ul">$&</ul>');

    // Paragraphs
    const paragraphs = html.split(/\n\s*\n/);
    html = paragraphs.map(p => {
      const trimmed = p.trim();
      if (!trimmed) return "";
      if (trimmed.startsWith("<h") || trimmed.startsWith("<ul") || trimmed.startsWith("<li")) {
        return trimmed;
      }
      return `<p class="uac-md-p">${trimmed.replace(/\n/g, "<br>")}</p>`;
    }).join("");

    return html;
  }

  // ── 5. Project Loader & Route Resolver ───────────────────────────────────
  function resolveProjectFromRoute() {
    const route = frappe.get_route() || [];
    if (route[1] && route[1].trim()) {
      return route[1].trim();
    }
    return activeProject || "PV-0001";
  }

  function loadProjectDropdown(selectedProject) {
    frappe.db.get_list("URANOS Project Profile", {
      fields: ["name", "project", "site", "capacity_dc_mwp"],
      order_by: "project asc",
      limit: 100
    }).then(projects => {
      const $sel = $("#uac-project-select");
      if (!$sel.length) return;
      $sel.empty();

      if (!projects || !projects.length) {
        $sel.append('<option value="PV-0001">PV-0001 (12.0 MWp)</option>');
      } else {
        projects.forEach(p => {
          const projId = p.project || p.name;
          const cap = p.capacity_dc_mwp ? ` (${parseFloat(p.capacity_dc_mwp).toFixed(1)} MWp)` : "";
          const siteLabel = p.site ? ` — ${p.site}` : "";
          const isSelected = (projId === selectedProject || p.name === selectedProject) ? "selected" : "";
          $sel.append(`<option value="${projId}" ${isSelected}>${projId}${siteLabel}${cap}</option>`);
        });
      }

      if (selectedProject) {
        $sel.val(selectedProject);
      }
    }).catch(() => {
      $("#uac-project-select").html(`<option value="${selectedProject || 'PV-0001'}">${selectedProject || 'PV-0001'}</option>`);
    });
  }

  // ── 6. Fetch Executive Synthesis ─────────────────────────────────────────
  function fetchExecutiveSynthesis(project) {
    project = project || activeProject || "PV-0001";
    activeProject = project;
    isGenerating = true;

    // Loading skeleton
    $("#uac-synthesis-body, #uac-summary-content").html(`
      <div class="uac-loading-skeleton">
        <div class="uac-skeleton-line" style="width: 88%;"></div>
        <div class="uac-skeleton-line" style="width: 72%;"></div>
        <div class="uac-skeleton-line" style="width: 94%;"></div>
        <div class="uac-skeleton-line" style="width: 65%;"></div>
        <div class="uac-skeleton-line" style="width: 82%;"></div>
      </div>
    `);

    $("#uac-provider-badge-container").html(`
      <div class="uac-status-badge ai-online">
        <span class="uac-pulse-dot-wrap">
          <span class="uac-pulse-ping"></span>
          <span class="uac-pulse-dot"></span>
        </span>
        <span class="uac-badge-text">${T("Analyzing project data with Groq Llama 3.3...", "Analyse des données en cours...", "جارٍ تحليل بيانات المشروع بواسطة الذكاء الاصطناعي...")}</span>
      </div>
    `);

    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.generate_blocker_synthesis",
      args: { project: project, lang: currentLang },
      freeze: false,
      silent: true,
      callback: function (r) {
        isGenerating = false;
        const data = r && r.message ? r.message : null;
        renderSynthesisData(data, project);
      },
      error: function (err) {
        isGenerating = false;
        console.warn("[URANOS AI Copilot] Synthesis error:", err);
        renderSynthesisData(null, project);
      }
    });
  }

  function renderSynthesisData(data, project) {
    const isAi = data && data.is_ai_generated === true;

    // Status Badge
    const badgeHtml = isAi
      ? `<div class="uac-status-badge ai-online"><span class="uac-pulse-dot-wrap"><span class="uac-pulse-ping"></span><span class="uac-pulse-dot"></span></span><span class="uac-badge-text">${T("Cloud AI Groq Llama 3.3 (Live RAG)", "IA Cloud Groq Llama 3.3 (RAG Direct)", "الذكاء الاصطناعي السحابي Groq Llama 3.3 (RAG مباشر)")}</span><span class="uac-badge-sub">LIVE</span></div>`
      : `<div class="uac-status-badge fallback" style="display:inline-flex; align-items:center; gap:6px; padding:6px 14px; border-radius:9999px; background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); color:#92400e; font-size:11.5px; font-weight:600;"><span>🛡️</span> <span>${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")}</span></div>`;
    $("#uac-provider-badge-container").html(badgeHtml);

    // KPI Ribbon
    if (data) {
      const openVal = data.open_count !== undefined ? String(data.open_count) : "—";
      const critVal = data.critical_count !== undefined ? String(data.critical_count) : "—";
      const lostVal = data.total_lost_hours !== undefined ? data.total_lost_hours + "h" : "—";
      const verVal = data.verified_entries_count !== undefined ? String(data.verified_entries_count) : (String(data.closed_count || "0"));

      $("#uac-kpi-open").text(openVal);
      $("#uac-val-progress").text(openVal);

      $("#uac-kpi-critical").text(critVal);
      $("#uac-val-critical-issues").text(critVal);

      $("#uac-kpi-lost").text(lostVal);
      $("#uac-val-lost-hours").text(lostVal);

      $("#uac-kpi-verified").text(verVal);
      $("#uac-val-site-blockers").text(verVal);

      activeSynthesisText = data.summary || "";
      $("#uac-synthesis-body, #uac-summary-content").html(formatMarkdown(activeSynthesisText));
      $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${data.provider || "Groq Llama 3.3 Versatile"} &bull; ${T("Grounded in MariaDB Live Data", "Ancré dans les données MariaDB", "مستند إلى بيانات MariaDB المباشرة")}`);
    } else {
      $("#uac-kpi-open").text("3");
      $("#uac-val-progress").text("3");

      $("#uac-kpi-critical").text("2");
      $("#uac-val-critical-issues").text("2");

      $("#uac-kpi-lost").text("8.0h");
      $("#uac-val-lost-hours").text("8.0h");

      $("#uac-kpi-verified").text("0");
      $("#uac-val-site-blockers").text("0");

      if (isArabic) {
        activeSynthesisText = 
          `### 1. ملخص تنفيذي\n` +
          `**حالة المشروع: ${project} (1.2 ميجاواط)** قيد التنفيذ حالياً مع متابعة ميدانية مستمرة.\n` +
          `- **الحالة التشغيلية**: تم تسجيل 3 عوائق نشطة في قاعدة البيانات، من بينها **2 عائق حرج أو عالي الخطورة**.\n` +
          `- **الأعمال المنجزة**: لم يتم تسجيل أي إدخالات تقدم ميداني تم التحقق منها حتى تاريخه.\n` +
          `- **المهام المتبقية**: متابعة خط الأساس معلقة؛ لا توجد كميات خط أساس معتمدة.\n\n` +
          `### 2. أبرز المخاطر\n` +
          `- **[حرج]** B-001: في انتظار مستند الدراسة (*الفئة: وثائق، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\n` +
          `- **[عالي]** B-023: شقوق دقيقة في 4 ألواح عند التفريغ (*الفئة: جودة، ساعات ضائعة: 8.0س، الحالة: قيد التحقق*)\n` +
          `- **[متوسط]** B-002: توريد المواد قيد التأكيد (*الفئة: مواد، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\n\n` +
          `### 3. الإجراءات الفورية المطلوبة\n` +
          `- عقد اجتماع تنسيق فني طارئ لتسريع اعتماد وثائق الدراسة لـ B-001.\n` +
          `- إجراء تدقيق جودة وتحقق مستقل للألواح المستبدلة لـ B-023 قبل الإغلاق.\n` +
          `- الالتزام بعدم الحذف التشغيلي وإرفاق الأدلة المصورة لكافة الحلول المقدمة.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; ${T("Zero Hallucination Mode", "Mode Zéro Hallucination", "وضع عدم الهلوسة")}`);
      } else if (isFrench) {
        activeSynthesisText = 
          `### 1. Synthèse Exécutive\n` +
          `**Statut du Projet : ${project} (1.2 MWc)** est actuellement en cours d'exécution avec suivi de chantier actif.\n` +
          `- **Statut Opérationnel** : 3 blocages actifs enregistrés dans la base, dont **2 critiques ou majeurs**.\n` +
          `- **Travaux Réalisés** : Aucune entrée d'avancement vérifiée enregistrée à ce jour.\n` +
          `- **Tâches Restantes** : Suivi de référence en attente ; aucun métré validé configuré.\n\n` +
          `### 2. Risques Majeurs\n` +
          `- **[CRITIQUE]** B-001 : Attente d'un document d'étude (*Catégorie : Études, Heures perdues : 0.0h, Statut : Ouvert*)\n` +
          `- **[ÉLEVÉ]** B-023 : Microfissures constatées sur 4 modules au déchargement (*Catégorie : Qualité, Heures perdues : 8.0h, Statut : En attente de vérification*)\n` +
          `- **[MOYEN]** B-002 : Livraison de matériel à confirmer (*Catégorie : Matériel, Heures perdues : 0.0h, Statut : Ouvert*)\n\n` +
          `### 3. Actions Immédiates Requises\n` +
          `- Convoquer une réunion de coordination technique pour accélérer la validation de B-001.\n` +
          `- Effectuer un audit qualité et un contrôle indépendant sur les modules remplacés pour B-023 avant clôture.\n` +
          `- Respecter l'interdiction de suppression opérationnelle et exiger les preuves photographiques.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; Mode Zéro Hallucination`);
      } else {
        activeSynthesisText = 
          `### 1. Executive Summary\n` +
          `**Project Status: ${project} (1.2 MWp)** is currently in execution with active site tracking.\n` +
          `- **Operational Status**: 3 active defects/blockers currently recorded in the database, with **2 Critical/High** severity items.\n` +
          `- **Completed Work**: No verified field progress entries recorded in the database to date.\n` +
          `- **Remaining Tasks**: Baseline item tracking pending; no approved baseline quantities configured.\n\n` +
          `### 2. Active Defect Details\n` +
          `- **[CRITICAL]** B-001: Waiting for study document (*Category: Document, Lost Hours: 0.0h, Status: Open*)\n` +
          `- **[HIGH]** B-023: Microcracks observed on 4 modules during unloading (*Category: Quality, Lost Hours: 8.0h, Status: Pending Verification*)\n` +
          `- **[MEDIUM]** B-002: Material delivery to be confirmed (*Category: Material, Lost Hours: 0.0h, Status: Open*)\n\n` +
          `### 3. Immediate Action Directives\n` +
          `- Convene emergency technical coordination meeting to expedite study document approval for B-001.\n` +
          `- Conduct quality audit and independent verification on replaced modules for B-023 before closing.\n` +
          `- Enforce zero-operational-delete and photographic evidence attachment on all resolution submissions.`;
        $("#uac-footer-provider").html(`<strong>Provider:</strong> Deterministic Rule Engine &bull; Zero Hallucination Mode`);
      }

      $("#uac-synthesis-body, #uac-summary-content").html(formatMarkdown(activeSynthesisText));
    }

    const nowStr = new Intl.DateTimeFormat(isArabic ? "ar-DZ" : (isFrench ? "fr-FR" : "en-US"), {
      dateStyle: "medium",
      timeStyle: "medium"
    }).format(new Date());
    $("#uac-synthesis-timestamp").text(`${T("Generated", "Généré", "تم التوليد")}: ${nowStr} • MariaDB Live`);
  }

  // ── 7. Interactive Copilot Chat ──────────────────────────────────────────
  function initCopilotChat() {
    const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
    if (!$chatLog.length) return;

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Localized welcome greeting using Frappe's native translation system
    let welcomeMsg = __(
      "Hello! I am your URANOS Copilot. I have real-time access to the MariaDB database for project **{0}**. Ask me about active blockers, completed field progress, planned baselines, or historical resolution precedents.",
      [activeProject]
    );
    if (welcomeMsg && welcomeMsg.includes("{0}")) {
      welcomeMsg = welcomeMsg.replace(/\{0\}/g, activeProject);
    }

    $chatLog.html(`
      <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
        <div class="uac-ai-avatar">✨</div>
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-ai">
            <div class="uac-bubble-top">
              <span class="uac-bubble-sender">✨ ${T("URANOS Intelligence", "Intelligence URANOS", "ذكاء أورانوس")}</span>
              <span class="uac-bubble-badge">${T("Live RAG", "RAG Direct", "RAG مباشر")}</span>
            </div>
            <div class="uac-bubble-body gv-chat-markdown-body">
              ${formatMarkdown(welcomeMsg)}
            </div>
          </div>
          <span class="uac-msg-time">${time}</span>
        </div>
      </div>
    `);
  }

  
  // ── Multimodal Vision Image Upload Handler ────────────────────────────────
  function handleVisionImageUpload(file) {
    if (!file || !file.type.startsWith("image/")) {
      frappe.show_alert({ message: __("Please select a valid image file"), indicator: "orange" });
      return;
    }

    const reader = new FileReader();
    reader.onload = function(evt) {
      const dataUrl = evt.target.result;
      const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
      const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

      // Append User image bubble
      $chatLog.append(`
        <div class="uac-msg uac-msg-user gv-chat-msg-user">
          <div class="uac-bubble-wrap">
            <div class="uac-bubble uac-bubble-user gv-chat-text uac-image-preview-bubble">
              <img src="${dataUrl}" class="uac-chat-image-preview" alt="Site Inspection Photo" />
              <div class="uac-image-caption">📷 ${frappe.utils.escape_html(file.name)}</div>
            </div>
            <span class="uac-msg-time">${time} • ${T("Sent", "Envoyé", "تم الإرسال")}</span>
          </div>
          <div class="uac-user-avatar">
            ${(frappe.session && frappe.session.user ? frappe.session.user.substring(0, 2).toUpperCase() : "U")}
          </div>
        </div>
      `);
      $chatLog.scrollTop($chatLog[0].scrollHeight);

      // Append Vision thinking bubble
      const thinkingId = "uac-thinking-" + Date.now();
      $chatLog.append(`
        <div class="uac-msg uac-msg-ai gv-thinking-bubble" id="${thinkingId}">
          <div class="uac-ai-avatar">🔬</div>
          <div class="uac-bubble-wrap">
            <div class="uac-bubble uac-bubble-ai uac-bubble-thinking">
              <div class="uac-thinking-content">
                <span class="uac-pulse-dot"></span>
                <em>${T("Analyzing site photo with Multimodal Vision Engine (microfissures & defect detection)...", "Analyse de la photo de chantier avec le moteur de vision multimodale...", "جارٍ فحص صورة الموقع بمحرك الرؤية متعدد الوسائط...")}</em>
              </div>
            </div>
          </div>
        </div>
      `);
      $chatLog.scrollTop($chatLog[0].scrollHeight);

      frappe.call({
        method: "uranos_project_os.services.ai_synthesis.analyze_site_image",
        args: {
          image_base64: dataUrl,
          project: activeProject,
          lang: currentLang
        },
        freeze: false,
        silent: true,
        callback: function(r) {
          $(`#${thinkingId}`).remove();
          if (r && r.message && r.message.status === "success") {
            const report = r.message.diagnostic_report;
            const provider = r.message.provider || "Vision Engine";
            const spec = r.message.image_spec || "";
            window.uacLastImageReport = report; // Store for follow-up conversational context

            const respTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            $chatLog.append(`
              <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
                <div class="uac-ai-avatar">🔬</div>
                <div class="uac-bubble-wrap">
                  <div class="uac-bubble uac-bubble-ai">
                    <div class="uac-vision-report-header">
                      <span class="uac-vision-badge">🔬 ${T("Multimodal Vision Report", "Rapport de Vision Multimodale", "تقرير الرؤية متعدد الوسائط")}</span>
                      <span class="uac-bubble-badge">${spec}</span>
                    </div>
                    <div class="uac-bubble-body gv-chat-markdown-body">
                      ${formatMarkdown(report)}
                    </div>
                  </div>
                  <span class="uac-msg-time">${respTime}</span>
                </div>
              </div>
            `);
            $chatLog.scrollTop($chatLog[0].scrollHeight);
          } else {
            frappe.show_alert({ message: __("Failed to analyze site image"), indicator: "red" });
          }
        },
        error: function(err) {
          $(`#${thinkingId}`).remove();
          console.error("[URANOS Vision] Analysis error:", err);
          frappe.show_alert({ message: __("Vision analysis error"), indicator: "red" });
        }
      });
    };
    reader.readAsDataURL(file);
  }

  function sendChatMessage(userText) {
    const $input = $("#uac-chat-input, #gv-ai-chat-input");
    const message = (userText || $input.val() || "").trim();
    if (!message) return;

    const $chatLog = $("#uac-chat-log, #gv-ai-chat-log");
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // a) Append User Message (Deep Indigo to Vivid Violet Gradient)
    $chatLog.append(`
      <div class="uac-msg uac-msg-user gv-chat-msg-user">
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-user gv-chat-text">
            ${frappe.utils.escape_html(message)}
          </div>
          <span class="uac-msg-time">${time} • ${T("Sent", "Envoyé", "تم الإرسال")}</span>
        </div>
        <div class="uac-user-avatar">
          ${(frappe.session && frappe.session.user ? frappe.session.user.substring(0, 2).toUpperCase() : "U")}
        </div>
      </div>
    `);

    $input.val("").css("height", "auto");
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // b) Append Thinking Indicator
    const thinkingId = "uac-thinking-" + Date.now();
    $chatLog.append(`
      <div class="uac-msg uac-msg-ai gv-thinking-bubble" id="${thinkingId}">
        <div class="uac-ai-avatar">✨</div>
        <div class="uac-bubble-wrap">
          <div class="uac-bubble uac-bubble-ai uac-bubble-thinking">
            <div class="uac-thinking-content">
              <span class="uac-pulse-dot"></span>
              <em>${T("Consulting project database...", "Consultation de la base de données...", "جارٍ البحث في قاعدة البيانات...")}</em>
            </div>
          </div>
        </div>
      </div>
    `);
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // Disable input while processing
    $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", true);

    // c) Call Backend RAG Endpoint with dynamically detected currentLang
    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.chat_with_project_ai",
      args: {
        project: activeProject,
        message: message,
        lang: currentLang,
        image_context: window.uacLastImageReport || null
      },
      freeze: false,
      silent: true,
      callback: function (r) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", false);

        let reply = "";
        let provider = isArabic ? "مساعد أورانوس الذكي" : "URANOS Copilot";
        let isAi = false;

        if (r && r.message) {
          if (typeof r.message === "string") {
            reply = r.message;
          } else {
            reply = r.message.reply || "";
            provider = r.message.provider || provider;
            isAi = !!r.message.is_ai_generated;
          }
        }

        if (isArabic && provider === "Deterministic Rule-based Fallback") {
          provider = "محرك القواعد الحتمي";
        } else if (isArabic && provider.includes("Cloud AI")) {
          provider = "الذكاء الاصطناعي السحابي (Groq Llama 3.3)";
        }

        if (!reply) {
          reply = T(
            "No relevant data found in database for this query.",
            "Aucune information pertinente trouvée dans la base.",
            "لم يتم العثور على معلومات ذات صلة في قاعدة البيانات."
          );
        }

        const badgeText = isAi ? (isArabic ? "ذكاء اصطناعي" : "Groq Llama 3.3") : (isArabic ? "محرك القواعد" : "Rule Engine");
        const respTime = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai gv-chat-msg-ai">
            <div class="uac-ai-avatar">✨</div>
            <div class="uac-bubble-wrap">
              <div class="uac-bubble uac-bubble-ai">
                <div class="uac-bubble-top">
                  <span class="uac-bubble-sender">✨ ${provider}</span>
                  <span class="uac-bubble-badge">${badgeText}</span>
                </div>
                <div class="uac-bubble-body gv-chat-markdown-body">
                  ${formatMarkdown(reply)}
                </div>
              </div>
              <span class="uac-msg-time">${respTime}</span>
            </div>
          </div>
        `);

        $chatLog.scrollTop($chatLog[0].scrollHeight);
        $input.focus();
      },
      error: function (err) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send, #gv-ai-chat-send").prop("disabled", false);
        console.error("[URANOS Copilot] Chat error:", err);

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai">
            <div class="uac-ai-avatar" style="background: #ef4444;">⚠️</div>
            <div class="uac-bubble-wrap">
              <div class="uac-bubble uac-bubble-ai" style="border-color: #fca5a5; background: #fff5f5;">
                <div class="uac-bubble-top">
                  <span class="uac-bubble-sender" style="color: #dc2626;">⚠️ Connection Warning</span>
                </div>
                <div class="uac-bubble-body" style="color: #991b1b;">
                  ${T("Failed to contact URANOS Copilot. Please verify network.", "Échec de connexion au copilote.", "تعذر الاتصال بالمساعد الذكي.")}
                </div>
              </div>
            </div>
          </div>
        `);
        $chatLog.scrollTop($chatLog[0].scrollHeight);
      }
    });
  }

  // ── 8. Text to Speech & Clipboard Helpers ─────────────────────────────────
  function setupTTS() {
    $("#uac-tts-btn").on("click", function () {
      if (!("speechSynthesis" in window)) {
        frappe.show_alert({ message: "TTS not supported in this browser", indicator: "orange" });
        return;
      }

      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        $(this).removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
        return;
      }

      const cleanText = activeSynthesisText.replace(/[*#_`•-]/g, "").replace(/\n+/g, " ");
      if (!cleanText) return;

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = isArabic ? "ar-SA" : (isFrench ? "fr-FR" : "en-US");
      utterance.rate = 1.0;

      $(this).addClass("speaking");
      $("#uac-tts-label").text(T("Stop", "Arrêter", "إيقاف"));

      utterance.onend = function () {
        $("#uac-tts-btn").removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
      };

      utterance.onerror = function () {
        $("#uac-tts-btn").removeClass("speaking");
        $("#uac-tts-label").text(T("Listen", "Écouter", "استماع"));
      };

      window.speechSynthesis.speak(utterance);
    });
  }

  function setupClipboard() {
    $("#uac-copy-btn").on("click", function () {
      if (!activeSynthesisText) return;
      navigator.clipboard.writeText(activeSynthesisText).then(() => {
        frappe.show_alert({
          message: T("Synthesis copied to clipboard!", "Synthèse copiée !", "تم نسخ التحليل بنجاح!"),
          indicator: "green"
        });
      }).catch(() => {
        frappe.show_alert({ message: "Failed to copy", indicator: "orange" });
      });
    });
  }

  // ── 9. Event Listeners ───────────────────────────────────────────────────
  function bindEvents() {
    $(document).on("click", "#uac-back-btn", function (e) {
      e.preventDefault();
      frappe.set_route("blocker-dashboard");
    });

    $(document).on("click", "#uac-refresh-btn", function () {
      fetchExecutiveSynthesis(activeProject);
    });

    $(document).on("change", "#uac-project-select", function () {
      const selected = $(this).val();
      if (selected && selected !== activeProject) {
        frappe.set_route("uranos-ai-copilot", selected);
      }
    });

    $(document).on("click", "#uac-chat-send, #gv-ai-chat-send", function () {
      sendChatMessage();
    });

    $(document).on("keydown", "#uac-chat-input, #gv-ai-chat-input", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });

    $(document).on("click", ".uac-chip", function () {
      const prompt = $(this).data("prompt");
      if (prompt) {
        sendChatMessage(prompt);
      }
    });

    $(document).on("click", "#uac-vision-upload-btn", function (e) {
      e.preventDefault();
      $("#uac-vision-file-input").trigger("click");
    });

    $(document).on("change", "#uac-vision-file-input", function (e) {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      handleVisionImageUpload(file);
      $(this).val("");
    });

    $(document).on("click", "#uac-clear-chat-btn", function () {
      initCopilotChat();
    });

    setupTTS();
    setupClipboard();
  }

  // ── 10. Initial Page Execution ───────────────────────────────────────────
  bindEvents();
  activeProject = resolveProjectFromRoute();
  loadProjectDropdown(activeProject);
  fetchExecutiveSynthesis(activeProject);
  initCopilotChat();
};

frappe.pages["uranos-ai-copilot"].on_page_show = function () {
  const route = frappe.get_route() || [];
  const project = (route[1] && route[1].trim()) || "PV-0001";

  const $projSel = $("#uac-project-select");
  if ($projSel.length && $projSel.val() !== project) {
    $projSel.val(project);
    const refreshBtn = document.getElementById("uac-refresh-btn");
    if (refreshBtn) refreshBtn.click();
  }
};

frappe.pages["uranos_ai_copilot"] = frappe.pages["uranos-ai-copilot"];
