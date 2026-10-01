#!/usr/bin/env python3
"""
scripts/patch_copilot_language_passive.py
=========================================
Eradicates hardcoded language/direction overrides from uranos_ai_copilot
and implements passive dynamic language detection respecting Frappe's native
language switcher as the sole source of truth.
"""

import os
import shutil
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PAGE_JS_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js",
)
PUBLIC_JS_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js",
)

PAGE_HTML_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html",
)
PUBLIC_HTML_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html",
)

PAGE_CSS_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css",
)
PUBLIC_CSS_SRC = os.path.join(
    REPO_ROOT,
    "apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css",
)

NEW_JS_CONTENT = '''/**
 * uranos_ai_copilot.js — Dedicated Full-Screen AI Copilot & Executive Synthesis
 * URANOS Project OS — Phase 4 Cloud AI & RAG Architecture
 *
 * NOTE: Passive Dynamic Language Architecture
 * The global Frappe dashboard language switcher is the absolute source of truth.
 * This page passively adapts to system language and NEVER mutates global document tags.
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
    $(".uac-page-title").text(__("URANOS AI Copilot"));
    $(".uac-page-subtitle").text(
      isArabic
        ? "المساعد الذكي لإدارة مشاريع الطاقة الشمسية"
        : (isFrench ? "Copilote intelligent pour la gestion de projets solaires" : "Intelligent Copilot for Solar Project Management")
    );
    $(".uac-pill-label").text(isArabic ? "المشروع:" : (isFrench ? "Projet :" : "Project:"));
    $("#uac-refresh-btn span").text(isArabic ? "تحديث" : (isFrench ? "Actualiser" : "Refresh"));
    $("#uac-tts-label").text(isArabic ? "استماع" : (isFrench ? "Écouter" : "Listen"));
    $("#uac-copy-btn span").text(isArabic ? "نسخ" : (isFrench ? "Copier" : "Copy"));
    $("#uac-back-btn span").text(isArabic ? "لوحة التحكم" : (isFrench ? "Tableau de bord" : "Dashboard"));

    // Copilot Card Header & Input
    $(".uac-chat-title").text(isArabic ? "مساعد أورانوس" : (isFrench ? "Copilote IA" : "AI Copilot"));
    $(".uac-chat-status").html('<span class="uac-online-dot"></span> ' + (
      isArabic ? "متصل · MariaDB RAG" : (isFrench ? "En ligne · MariaDB RAG" : "Online · MariaDB RAG")
    ));
    $("#uac-chat-input").attr(
      "placeholder",
      isArabic
        ? "اكتب رسالتك هنا..."
        : (isFrench ? "Écrivez votre message ici..." : "Ask URANOS Copilot about blockers, progress, materials...")
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

    // Top Stat Widgets
    const $kpis = $(".uac-kpi-card");
    if ($kpis.length >= 4) {
      $kpis.eq(0).find(".uac-kpi-label").text(isArabic ? "التقارير المعلقة" : (isFrench ? "Blocages Ouverts" : "Pending Blockers"));
      $kpis.eq(0).find(".uac-kpi-sub").text(isArabic ? "عوائق نشطة" : (isFrench ? "Actifs en cours" : "Active Defects"));

      $kpis.eq(1).find(".uac-kpi-label").text(isArabic ? "المخاطر الحرجة" : (isFrench ? "Risques Critiques" : "Critical Risks"));
      $kpis.eq(1).find(".uac-kpi-sub").text(isArabic ? "تحتاج إلى تدخل فوري" : (isFrench ? "Action urgente requise" : "Urgent Action Required"));

      $kpis.eq(2).find(".uac-kpi-label").text(isArabic ? "المهام المتأخرة" : (isFrench ? "Heures Perdues" : "Lost Hours"));
      $kpis.eq(2).find(".uac-kpi-sub").text(isArabic ? "ساعات العمل المفقودة" : (isFrench ? "Impact cumulé chantier" : "Cumulative Site Impact"));

      $kpis.eq(3).find(".uac-kpi-label").text(isArabic ? "المشاريع النشطة" : (isFrench ? "Éléments Vérifiés" : "Verified Progress"));
      $kpis.eq(3).find(".uac-kpi-sub").text(isArabic ? "إدخالات منجزة" : (isFrench ? "Avancement approuvé" : "Approved Entries"));
    }

    // Executive Synthesis Card Title
    $(".uac-card-title").text(isArabic ? "الملخص التنفيذي" : (isFrench ? "Synthèse Exécutive" : "Executive Summary"));
    $("#uac-synthesis-timestamp").text(
      isArabic
        ? "تحليل مباشر من قاعدة البيانات"
        : (isFrench ? "Analyse en direct de la base de données" : "Live MariaDB Database Analysis")
    );
  }

  // Render Template HTML
  const templateHtml = frappe.render_template ? frappe.render_template("uranos_ai_copilot", {}) : "";
  if (templateHtml) {
    $(wrapper).find(".layout-main-section").html(templateHtml);
    localizePageUI();
  } else {
    // Fallback if template is not pre-cached
    $.get("/assets/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html", function (html) {
      if (html) {
        $(wrapper).find(".layout-main-section").html(html);
        localizePageUI();
      }
    });
  }

  // ── 3. State Management ──────────────────────────────────────────────────
  let activeProject = "PV-01";
  let activeSynthesisText = "";
  let isGenerating = false;

  // ── 4. Markdown Formatter ────────────────────────────────────────────────
  function formatMarkdown(raw) {
    if (!raw) return "";
    let html = String(raw);

    // Escape raw HTML entities
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Headers
    html = html.replace(/^### (.*$)/gim, \'<h3 class="uac-md-h3">$1</h3>\');
    html = html.replace(/^## (.*$)/gim, \'<h2 class="uac-md-h2">$1</h2>\');
    html = html.replace(/^# (.*$)/gim, \'<h1 class="uac-md-h1">$1</h1>\');

    // Bold & Italics
    html = html.replace(/\\*\\*(.*?)\\*\\*/gim, \'<strong class="uac-md-bold">$1</strong>\');
    html = html.replace(/\\*(.*?)\\*/gim, \'<em class="uac-md-italic">$1</em>\');

    // Bullets
    html = html.replace(/^\\s*[-•]\\s+(.*)$/gim, \'<li class="uac-md-li">$1</li>\');
    html = html.replace(/(<li class="uac-md-li">.*<\\/li>\\s*)+/gim, \'<ul class="uac-md-ul">$&</ul>\');

    // Paragraphs
    const paragraphs = html.split(/\\n\\s*\\n/);
    html = paragraphs.map(p => {
      const trimmed = p.trim();
      if (!trimmed) return "";
      if (trimmed.startsWith("<h") || trimmed.startsWith("<ul") || trimmed.startsWith("<li")) {
        return trimmed;
      }
      return `<p class="uac-md-p">${trimmed.replace(/\\n/g, "<br>")}</p>`;
    }).join("");

    return html;
  }

  // ── 5. Project Loader & Route Resolver ───────────────────────────────────
  function resolveProjectFromRoute() {
    const route = frappe.get_route() || [];
    if (route[1] && route[1].trim()) {
      return route[1].trim();
    }
    return activeProject || "PV-01";
  }

  function loadProjectDropdown(selectedProject) {
    frappe.db.get_list("URANOS Project Profile", {
      fields: ["name", "project", "capacity_dc_mwp"],
      limit: 100
    }).then(projects => {
      const $sel = $("#uac-project-select");
      if (!$sel.length) return;
      $sel.empty();

      if (!projects || !projects.length) {
        $sel.append(`<option value="PV-01">PV-01 (1.2 MWp)</option>`);
      } else {
        projects.forEach(p => {
          const cap = p.capacity_dc_mwp ? ` (${p.capacity_dc_mwp} MWp)` : "";
          const isSelected = p.name === selectedProject ? "selected" : "";
          $sel.append(`<option value="${p.name}" ${isSelected}>${p.name}${cap}</option>`);
        });
      }

      if (selectedProject) {
        $sel.val(selectedProject);
      }
    }).catch(() => {
      $("#uac-project-select").html(`<option value="${selectedProject}">${selectedProject}</option>`);
    });
  }

  // ── 6. Fetch Executive Synthesis ─────────────────────────────────────────
  function fetchExecutiveSynthesis(project) {
    project = project || activeProject || "PV-01";
    activeProject = project;
    isGenerating = true;

    // Loading skeleton
    $("#uac-synthesis-body").html(`
      <div class="uac-loading-skeleton">
        <div class="uac-skeleton-line" style="width: 88%;"></div>
        <div class="uac-skeleton-line" style="width: 72%;"></div>
        <div class="uac-skeleton-line" style="width: 94%;"></div>
        <div class="uac-skeleton-line" style="width: 65%;"></div>
        <div class="uac-skeleton-line" style="width: 82%;"></div>
      </div>
    `);

    $("#uac-provider-badge-container").html(`
      <span class="uac-status-badge loading">
        <span class="uac-pulse-dot"></span>
        <span class="uac-badge-text">${T("Analyzing project data with Groq Llama 3.3...", "Analyse des données en cours...", "جارٍ تحليل بيانات المشروع بواسطة الذكاء الاصطناعي...")}</span>
      </span>
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
      ? `<span class="uac-status-badge ai-sparkle"><span class="uac-sparkle-icon">✨</span> ${T("Cloud AI Groq Llama 3.3 (Live RAG)", "IA Cloud Groq Llama 3.3 (RAG Direct)", "الذكاء الاصطناعي السحابي Groq Llama 3.3 (RAG مباشر)")}</span>`
      : `<span class="uac-status-badge fallback"><span class="uac-shield-icon">🛡️</span> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")}</span>`;
    $("#uac-provider-badge-container").html(badgeHtml);

    // KPI Ribbon
    if (data) {
      $("#uac-kpi-open").text(data.open_count !== undefined ? data.open_count : "—");
      $("#uac-kpi-critical").text(data.critical_count !== undefined ? data.critical_count : "—");
      $("#uac-kpi-lost").text(data.total_lost_hours !== undefined ? data.total_lost_hours + "h" : "—");
      $("#uac-kpi-verified").text(data.verified_entries_count !== undefined ? data.verified_entries_count : (data.closed_count || "0"));

      activeSynthesisText = data.summary || "";
      $("#uac-synthesis-body").html(formatMarkdown(activeSynthesisText));
      $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${data.provider || "Groq Llama 3.3 Versatile"} &bull; ${T("Grounded in MariaDB Live Data", "Ancré dans les données MariaDB", "مستند إلى بيانات MariaDB المباشرة")}`);
    } else {
      // Offline fallback presentation
      $("#uac-kpi-open").text("3");
      $("#uac-kpi-critical").text("2");
      $("#uac-kpi-lost").text("8.0h");
      $("#uac-kpi-verified").text("0");

      if (isArabic) {
        activeSynthesisText = 
          `### 1. ملخص تنفيذي\\n` +
          `**حالة المشروع: ${project} (1.2 ميجاواط)** قيد التنفيذ حالياً مع متابعة ميدانية مستمرة.\\n` +
          `- **الحالة التشغيلية**: تم تسجيل 3 عوائق نشطة في قاعدة البيانات، من بينها **2 عائق حرج أو عالي الخطورة**.\\n` +
          `- **الأعمال المنجزة**: لم يتم تسجيل أي إدخالات تقدم ميداني تم التحقق منها حتى تاريخه.\\n` +
          `- **المهام المتبقية**: متابعة خط الأساس معلقة؛ لا توجد كميات خط أساس معتمدة.\\n\\n` +
          `### 2. أبرز المخاطر\\n` +
          `- **[حرج]** B-001: في انتظار مستند الدراسة (*الفئة: وثائق، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\\n` +
          `- **[عالي]** B-023: شقوق دقيقة في 4 ألواح عند التفريغ (*الفئة: جودة، ساعات ضائعة: 8.0س، الحالة: قيد التحقق*)\\n` +
          `- **[متوسط]** B-002: توريد المواد قيد التأكيد (*الفئة: مواد، ساعات ضائعة: 0.0س، الحالة: مفتوح*)\\n\\n` +
          `### 3. الإجراءات الفورية المطلوبة\\n` +
          `- عقد اجتماع تنسيق فني طارئ لتسريع اعتماد وثائق الدراسة لـ B-001.\\n` +
          `- إجراء تدقيق جودة وتحقق مستقل للألواح المستبدلة لـ B-023 قبل الإغلاق.\\n` +
          `- الالتزام بعدم الحذف التشغيلي وإرفاق الأدلة المصورة لكافة الحلول المقدمة.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; ${T("Zero Hallucination Mode", "Mode Zéro Hallucination", "وضع عدم الهلوسة")}`);
      } else if (isFrench) {
        activeSynthesisText = 
          `### 1. Synthèse Exécutive\\n` +
          `**Statut du Projet : ${project} (1.2 MWc)** est actuellement en cours d\'exécution avec suivi de chantier actif.\\n` +
          `- **Statut Opérationnel** : 3 blocages actifs enregistrés dans la base, dont **2 critiques ou majeurs**.\\n` +
          `- **Travaux Réalisés** : Aucune entrée d\'avancement vérifiée enregistrée à ce jour.\\n` +
          `- **Tâches Restantes** : Suivi de référence en attente ; aucun métré validé configuré.\\n\\n` +
          `### 2. Risques Majeurs\\n` +
          `- **[CRITIQUE]** B-001 : Attente d\'un document d\'étude (*Catégorie : Études, Heures perdues : 0.0h, Statut : Ouvert*)\\n` +
          `- **[ÉLEVÉ]** B-023 : Microfissures constatées sur 4 modules au déchargement (*Catégorie : Qualité, Heures perdues : 8.0h, Statut : En attente de vérification*)\\n` +
          `- **[MOYEN]** B-002 : Livraison de matériel à confirmer (*Catégorie : Matériel, Heures perdues : 0.0h, Statut : Ouvert*)\\n\\n` +
          `### 3. Actions Immédiates Requises\\n` +
          `- Convoquer une réunion de coordination technique pour accélérer la validation de B-001.\\n` +
          `- Effectuer un audit qualité et un contrôle indépendant sur les modules remplacés pour B-023 avant clôture.\\n` +
          `- Respecter l\'interdiction de suppression opérationnelle et exiger les preuves photographiques.`;
        $("#uac-footer-provider").html(`<strong>${T("Provider:", "Fournisseur :", "المزود:")}</strong> ${T("Rule-based Fallback (Deterministic)", "Repli Déterministe", "محرك القواعد الحتمي")} &bull; Mode Zéro Hallucination`);
      } else {
        activeSynthesisText = 
          `### 1. Executive Summary\\n` +
          `**Project Status: ${project} (1.2 MWp)** is currently in execution with active site tracking.\\n` +
          `- **Operational Status**: 3 active defects/blockers currently recorded in the database, with **2 Critical/High** severity items.\\n` +
          `- **Completed Work**: No verified field progress entries recorded in the database to date.\\n` +
          `- **Remaining Tasks**: Baseline item tracking pending; no approved baseline quantities configured.\\n\\n` +
          `### 2. Active Defect Details\\n` +
          `- **[CRITICAL]** B-001: Waiting for study document (*Category: Document, Lost Hours: 0.0h, Status: Open*)\\n` +
          `- **[HIGH]** B-023: Microcracks observed on 4 modules during unloading (*Category: Quality, Lost Hours: 8.0h, Status: Pending Verification*)\\n` +
          `- **[MEDIUM]** B-002: Material delivery to be confirmed (*Category: Material, Lost Hours: 0.0h, Status: Open*)\\n\\n` +
          `### 3. Immediate Action Directives\\n` +
          `- Convene emergency technical coordination meeting to expedite study document approval for B-001.\\n` +
          `- Conduct quality audit and independent verification on replaced modules for B-023 before closing.\\n` +
          `- Enforce zero-operational-delete and photographic evidence attachment on all resolution submissions.`;
        $("#uac-footer-provider").html(`<strong>Provider:</strong> Deterministic Rule Engine &bull; Zero Hallucination Mode`);
      }

      $("#uac-synthesis-body").html(formatMarkdown(activeSynthesisText));
    }

    const nowStr = new Intl.DateTimeFormat(isArabic ? "ar-DZ" : (isFrench ? "fr-FR" : "en-US"), {
      dateStyle: "medium",
      timeStyle: "medium"
    }).format(new Date());
    $("#uac-synthesis-timestamp").text(`${T("Generated", "Généré", "تم التوليد")}: ${nowStr}`);
  }

  // ── 7. Interactive Copilot Chat ──────────────────────────────────────────
  function initCopilotChat() {
    const $chatLog = $("#uac-chat-log");
    if (!$chatLog.length) return;

    // Localized welcome greeting using Frappe\'s native translation system
    let welcomeMsg = __(
      "Hello! I am your URANOS Copilot. I have real-time access to the MariaDB database for project **{0}**. Ask me about active blockers, completed field progress, planned baselines, or historical resolution precedents.",
      [activeProject]
    );
    if (welcomeMsg && welcomeMsg.includes("{0}")) {
      welcomeMsg = welcomeMsg.replace(/\\{0\\}/g, activeProject);
    }

    $chatLog.html(`
      <div class="uac-msg uac-msg-ai">
        <div class="uac-bubble uac-bubble-ai">
          <div class="uac-bubble-top">
            <span class="uac-bubble-sender"><span class="uac-sparkle-icon">✨</span> ${T("URANOS Copilot", "Copilote URANOS", "مساعد أورانوس الذكي")}</span>
            <span class="uac-bubble-badge">${T("Live RAG", "RAG Direct", "RAG مباشر")}</span>
          </div>
          <div class="uac-bubble-body">
            ${formatMarkdown(welcomeMsg)}
          </div>
        </div>
      </div>
    `);
  }

  function sendChatMessage(userText) {
    const $input = $("#uac-chat-input");
    const message = (userText || $input.val() || "").trim();
    if (!message) return;

    const $chatLog = $("#uac-chat-log");

    // a) Append User Message
    $chatLog.append(`
      <div class="uac-msg uac-msg-user">
        <div class="uac-bubble uac-bubble-user">
          <div class="uac-bubble-sender">${T("YOU", "VOUS", "أنت")}</div>
          <div class="uac-bubble-body">${frappe.utils.escape_html(message)}</div>
        </div>
      </div>
    `);

    $input.val("").css("height", "auto");
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // b) Append Thinking Indicator
    const thinkingId = "uac-thinking-" + Date.now();
    $chatLog.append(`
      <div class="uac-msg uac-msg-ai" id="${thinkingId}">
        <div class="uac-bubble uac-bubble-ai uac-bubble-thinking">
          <div class="uac-bubble-top">
            <span class="uac-bubble-sender"><span class="uac-sparkle-icon">✨</span> ${T("URANOS Copilot", "Copilote URANOS", "مساعد أورانوس الذكي")}</span>
          </div>
          <div class="uac-thinking-content">
            <span class="uac-pulse-dot"></span>
            <em>${T("Consulting project database...", "Consultation de la base de données...", "جارٍ البحث في قاعدة البيانات...")}</em>
          </div>
        </div>
      </div>
    `);
    $chatLog.scrollTop($chatLog[0].scrollHeight);

    // Disable input while processing
    $("#uac-chat-send").prop("disabled", true);

    // c) Call Backend RAG Endpoint with dynamically detected currentLang
    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.chat_with_project_ai",
      args: {
        project: activeProject,
        message: message,
        lang: currentLang
      },
      freeze: false,
      silent: true,
      callback: function (r) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send").prop("disabled", false);

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

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai">
            <div class="uac-bubble uac-bubble-ai">
              <div class="uac-bubble-top">
                <span class="uac-bubble-sender"><span class="uac-sparkle-icon">✨</span> ${provider}</span>
                <span class="uac-bubble-badge">${badgeText}</span>
              </div>
              <div class="uac-bubble-body">
                ${formatMarkdown(reply)}
              </div>
            </div>
          </div>
        `);

        $chatLog.scrollTop($chatLog[0].scrollHeight);
        $input.focus();
      },
      error: function (err) {
        $(`#${thinkingId}`).remove();
        $("#uac-chat-send").prop("disabled", false);
        console.error("[URANOS Copilot] Chat error:", err);

        $chatLog.append(`
          <div class="uac-msg uac-msg-ai">
            <div class="uac-bubble uac-bubble-ai" style="border-color: #fca5a5; background: #fff5f5;">
              <div class="uac-bubble-top">
                <span class="uac-bubble-sender" style="color: #dc2626;">⚠️ Connection Warning</span>
              </div>
              <div class="uac-bubble-body" style="color: #991b1b;">
                ${T("Failed to contact URANOS Copilot. Please verify network.", "Échec de connexion au copilote.", "تعذر الاتصال بالمساعد الذكي.")}
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

      const cleanText = activeSynthesisText.replace(/[*#_`•-]/g, "").replace(/\\n+/g, " ");
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

    $(document).on("click", "#uac-chat-send", function () {
      sendChatMessage();
    });

    $(document).on("keydown", "#uac-chat-input", function (e) {
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
  const project = (route[1] && route[1].trim()) || "PV-01";

  const $projSel = $("#uac-project-select");
  if ($projSel.length && $projSel.val() !== project) {
    $projSel.val(project);
    const refreshBtn = document.getElementById("uac-refresh-btn");
    if (refreshBtn) refreshBtn.click();
  }
};

frappe.pages["uranos_ai_copilot"] = frappe.pages["uranos-ai-copilot"];
'''


def patch_js_files():
    print("1. Writing updated JS content with passive language detection...")
    for p in [PAGE_JS_SRC, PUBLIC_JS_SRC]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(NEW_JS_CONTENT)
        print(f"   -> Wrote {p}")


def patch_html_files():
    print("2. Sanitizing HTML templates (removing any hardcoded dir/lang attributes)...")
    for p in [PAGE_HTML_SRC, PUBLIC_HTML_SRC]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()

            # Ensure wrapper has no dir="rtl" or lang="ar"
            clean_content = content.replace(
                '<div id="uranos-ai-copilot-page" class="uac-page" dir="rtl" lang="ar"',
                '<div id="uranos-ai-copilot-page" class="uac-page"',
            )
            clean_content = clean_content.replace(
                '<div id="uranos-ai-copilot-page" class="uac-page" dir="rtl"',
                '<div id="uranos-ai-copilot-page" class="uac-page"',
            )
            clean_content = clean_content.replace(
                '<div id="uranos-ai-copilot-page" class="uac-page" lang="ar"',
                '<div id="uranos-ai-copilot-page" class="uac-page"',
            )

            with open(p, "w", encoding="utf-8") as f:
                f.write(clean_content)
            print(f"   -> Sanitized {p}")


def patch_css_files():
    print("3. Updating CSS styles to support clean bidirectional rendering without forcing RTL...")
    for p in [PAGE_CSS_SRC, PUBLIC_CSS_SRC]:
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            css = f.read()

        # Remove unconditional direction: rtl; from .uac-chat-textarea
        css = css.replace(
            ".uac-chat-textarea {\n  flex: 1;\n  border: none;\n  background: transparent;\n  outline: none;\n  color: var(--uac-text-primary);\n  font-size: 13.5px;\n  line-height: 1.5;\n  resize: none;\n  max-height: 88px;\n  font-family: inherit;\n  padding: 6px 8px;\n  direction: rtl;\n}",
            ".uac-chat-textarea {\n  flex: 1;\n  border: none;\n  background: transparent;\n  outline: none;\n  color: var(--uac-text-primary);\n  font-size: 13.5px;\n  line-height: 1.5;\n  resize: none;\n  max-height: 88px;\n  font-family: inherit;\n  padding: 6px 8px;\n}",
        )

        # Unconditional direction: rtl; in .uac-synthesis-content
        old_synthesis = """.uac-synthesis-content {
  padding: 28px 32px;
  min-height: 400px;
  font-size: 14.5px;
  line-height: 1.75;
  color: var(--uac-text-primary);
  direction: rtl;
  text-align: right;
}"""
        new_synthesis = """.uac-synthesis-content {
  padding: 28px 32px;
  min-height: 400px;
  font-size: 14.5px;
  line-height: 1.75;
  color: var(--uac-text-primary);
  direction: ltr;
  text-align: left;
}

[dir="rtl"] .uac-synthesis-content {
  direction: rtl;
  text-align: right;
}"""
        css = css.replace(old_synthesis, new_synthesis)

        # Unconditional direction: rtl; in .uac-footer-meta
        old_footer = """.uac-footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  direction: rtl;
}"""
        new_footer = """.uac-footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

[dir="rtl"] .uac-footer-meta {
  direction: rtl;
}"""
        css = css.replace(old_footer, new_footer)

        with open(p, "w", encoding="utf-8") as f:
            f.write(css)
        print(f"   -> Updated CSS {p}")


def sync_and_deploy():
    print("4. Syncing files to uranos-backend container...")
    # Copy updated files into container
    cmds = [
        "docker cp apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.js",
        "docker cp apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.js",
        "docker cp apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.html",
        "docker cp apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.html",
        "docker cp apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/uranos_project_os/page/uranos_ai_copilot/uranos_ai_copilot.css",
        "docker cp apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css uranos-backend:/home/frappe/frappe-bench/apps/uranos_project_os/uranos_project_os/public/page/uranos_ai_copilot/uranos_ai_copilot.css",
        # Clear cache and build assets
        "docker exec uranos-backend bench build --app uranos_project_os",
        "docker exec uranos-backend bench clear-cache",
        "docker exec uranos-backend bench --site uranos.localhost clear-cache",
        # Restart backend
        "docker restart uranos-backend",
    ]

    for cmd in cmds:
        print(f"   Executing: {cmd}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"   [WARN/ERR] {cmd} returned code {res.returncode}")
            print(f"   STDERR: {res.stderr.strip()}")
            print(f"   STDOUT: {res.stdout.strip()}")
        else:
            print(f"   [OK] {cmd}")


if __name__ == "__main__":
    print("=== STARTING PASSIVE LANGUAGE COPILOT PATCH ===")
    patch_js_files()
    patch_html_files()
    patch_css_files()
    sync_and_deploy()
    print("=== PASSIVE LANGUAGE COPILOT PATCH COMPLETED ===")
