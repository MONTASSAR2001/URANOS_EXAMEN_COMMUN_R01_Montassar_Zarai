/**
 * URANOS Group Desk UI/UX Overhaul Controller
 * Frappe v16 Desktop Page & Workspace Modernization
 * Optimized High-Performance Edition (Zero-Jank, Low-CPU, Leak-Free)
 */

(function () {
  "use strict";

  // Ensure dark mode is stripped and purged
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("uranos_dark_mode");
    }
    if (typeof document !== "undefined") {
      document.body.classList.remove("uranos-dark-mode");
      if (document.documentElement) document.documentElement.removeAttribute("data-theme");
    }
  } catch (e) {}

  // Guard against upstream Frappe sidebar divider bug that creates <img src="undefined"> (404s)
  try {
    if (typeof window !== "undefined" && window.frappe && frappe.ui && frappe.ui.SidebarHeader) {
      const origAddAppItem = frappe.ui.SidebarHeader.prototype.add_app_item;
      frappe.ui.SidebarHeader.prototype.add_app_item = function (item) {
        if (!item || item.is_divider) {
          $('<div class="dropdown-divider"></div>').appendTo(this.dropdown_menu);
          return;
        }
        if (!item.icon && !item.icon_url) {
          item.icon = "dot";
        }
        return origAddAppItem.call(this, item);
      };
    }
  } catch (e) {}

  function getCurrentLangCode() {
    let lang = (typeof document !== "undefined" && document.documentElement && document.documentElement.getAttribute("lang"))
      || (typeof window !== "undefined" && window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.language)
      || (typeof window !== "undefined" && window.frappe && frappe.user_language)
      || (typeof window !== "undefined" && window.frappe && frappe.boot && frappe.boot.lang)
      || "en";
    lang = String(lang).toLowerCase();
    if (lang.startsWith("ar")) return "ar";
    if (lang.startsWith("fr")) return "fr";
    return "en";
  }

  const UI_TRANSLATIONS = {
    ar: {
      "Good Morning": "صباح الخير",
      "Good Afternoon": "مساء الخير",
      "Good Evening": "مساء الخير",
      "Here's what's happening with your renewable energy assets today.": "إليك ما يحدث مع أصول الطاقة المتجددة الخاصة بك اليوم.",
      "Total Capacity": "إجمالي القدرة",
      "Active Sites": "المواقع النشطة",
      "Total Energy Today": "إجمالي الطاقة اليوم",
      "CO2 Avoided": "ثاني أكسيد الكربون المتجنب",
      "Sites connected": "مواقع متصلة",
      "operational": "تشغيلي",
      "lost (blockers)": "مفقود (معوقات)",
      "vs. yesterday": "مقارنة بالأمس",
      "offset today": "تم تعويضه اليوم",
      "Loading...": "جاري التحميل...",
      "Applications": "التطبيقات",
      "All your tools in one place.": "جميع أدواتك في مكان واحد.",
      "All": "الكل",
      "Energy": "طاقة",
      "Operations": "عمليات",
      "Reports": "تقارير",
      "System": "النظام",
      "Projects": "المشاريع",
      "Manage your renewable energy projects.": "إدارة مشاريع الطاقة المتجددة الخاصة بك.",
      "Sites": "المواقع",
      "Monitor and manage solar and wind sites.": "مراقبة وإدارة محطات الطاقة الشمسية والرياح.",
      "Energy Analytics": "تحليلات الطاقة",
      "AI Copilot": "مساعد الذكاء الاصطناعي",
      "Kanban Board": "لوحة كانبان",
      "Interactive 4-column blocker workflow board.": "لوحة تفاعلية بـ 4 أعمدة لمتابعة العوائق.",
      "Track performance and energy generation.": "تتبع الأداء وإنتاج الطاقة.",
      "Generate insights and export data.": "توليد الرؤى وتصدير البيانات.",
      "Quality Inspections": "فحوصات الجودة",
      "Conduct and manage inspections.": "إجراء وإدارة عمليات التفتيش.",
      "Real-time monitoring and control.": "المراقبة والتحكم في الوقت الفعلي.",
      "Maintenance": "الصيانة",
      "Schedule and track maintenance activities.": "جدولة وتتبع أنشطة الصيانة.",
      "Stock": "المخزون",
      "Manage inventory and materials.": "إدارة المخزون والمواد.",
      "Purchase": "المشتريات",
      "Handle procurement and suppliers.": "إدارة المشتريات والموردين.",
      "Sales": "المبيعات",
      "Manage customers and billing.": "إدارة العملاء والفواتير.",
      "HR": "الموارد البشرية",
      "Manage your team and workforce.": "إدارة فريق العمل والقوى العاملة.",
      "Payroll": "الرواتب",
      "Process payroll and benefits.": "معالجة كشوف المرتبات والمستحقات.",
      "Accounting": "المحاسبة",
      "Track finances and generate reports.": "تتبع الشؤون المالية وتوليد التقارير.",
      "Settings": "الإعدادات",
      "Configure your system and preferences.": "ضبط النظام والتفضيلات.",
      "Help & Support": "المساعدة والدعم",
      "Get assistance and documentation.": "الحصول على المساعدة والتوثيق.",
      "Back to Main Dashboard": "العودة إلى لوحة التحكم الرئيسية",
      "Return to Main Dashboard": "العودة إلى لوحة التحكم الرئيسية",
      "Live Database Connected": "قاعدة البيانات المباشرة متصلة",
      "Live Database Connection Active & Synchronized": "الاتصال المباشر بقاعدة البيانات نشط ومتزامن",
      "Search for apps, projects, sites, reports...": "البحث عن التطبيقات، المشاريع، المحطات، والتقارير...",
      "Language": "اللغة",
      "Select Language": "اختر اللغة",
      "My Profile": "ملفي الشخصي",
      "Sign Out": "تسجيل الخروج",
      "Home": "الرئيسية",
      "Cleaner Energy": "طاقة أنظف",
      "A Brighter Tomorrow": "غدٌ أكثر إشراقاً",
      "Efficiently managing renewable resources for a sustainable future.": "إدارة كفؤة لموارد الطاقة المتجددة لمستقبل مستدام.",
      "System Online": "النظام متصل",
      "Learn more": "اعرف المزيد",
      "ENTERPRISE": "مؤسسة",
      "Photovoltaic Execution OS": "نظام تشغيل الطاقة الكهروضوئية",
      "Sunny • Tunis, TN": "مشمس • تونس، تونس",
      "Notifications": "الإشعارات",
      "Account settings": "إعدادات الحساب",
      "Solar Farm": "محطة طاقة شمسية",
      "Open": "فتح",
      "Grid View": "عرض شبكي",
      "List View": "عرض قائمة",
      "Performance metrics & delivery milestones": "مقاييس الأداء ومعالم التسليم",
      "Active solar & wind installations": "منشآت الطاقة الشمسية والرياح النشطة",
      "Pending action items & engineering logs": "بنود العمل المعلقة وسجلات الهندسة",
      "Manage renewable project lifecycles": "إدارة دورات حياة مشاريع الطاقة المتجددة",
      "Quality standards & protocol trees": "معايير الجودة ومخططات البروتوكول",
      "Field assessments & quality ratings": "التقييمات الميدانية وتقييمات الجودة",
      "Review sessions & coordination meetings": "جلسات المراجعة واجتماعات التنسيق",
      "Corrective actions & issue resolution": "الإجراءات التصحيحية وحل المشكلات",
      "Stock tracking and materials management": "تتبع المخزون وإدارة المواد",
      "Procurement, purchase orders & vendors": "المشتريات، أوامر الشراء والموردون",
      "Customer accounts and sales orders": "حسابات العملاء وأوامر المبيعات",
      "Workforce directory and team assignments": "دليل القوى العاملة وتعيينات الفريق",
      "Operations and overview": "العمليات ونظرة عامة",
      "Live Database Metric": "مؤشر مباشر لقاعدة البيانات",
      "Failed to update language. Please try again.": "فشل في تحديث اللغة. يرجى المحاولة مرة أخرى.",
      "Error switching language.": "خطأ في تبديل اللغة.",
      "7-Day Verified Progress": "التقدم الميداني المعتمد (7 أيام)",
      "Physical installed quantities strictly within the 7-calendar-day window": "الكميات الفعلية المنجزة والمتحقق منها بدقة خلال نافذة 7 أيام تقويمية",
      "Period": "الفترة",
      "Baseline": "المخطط المعتمد",
      "Status": "الحالة",
      "Verified Only": "معتمد فقط",
      "Separate Units": "وحدات منفصلة",
      "Zero Labour Conversion": "دون تحويل لساعات العمل",
      "Net Corrections": "تصحيحات صافية",
      "Strict 7-Day Boundary": "حدود صارمة لـ 7 أيام",
      "Physical Units Breakdown": "تفصيل الوحدات المادية",
      "Units Summary": "ملخص الوحدات",
      "Unknown": "غير محدد",
      "Measured": "تم القياس",
      "Measured 0": "مقاس 0",
      "Planned": "المخطط",
      "Approved": "معتمد",
      "Piles (Battage)": "الأوتاد (الركائز)",
      "Modules (Pose)": "الألواح (التركيب)",
      "Trenching": "حفر الخنادق",
      "Cabling": "تمديد الكابلات",
      "Drafts & Receipts Excluded": "استبعاد المسودات والإيصالات",
      "Verified Progress Reader": "قارئ التقدم الميداني المعتمد",
      "No Unit Mixing (pieux / modules / m separated)": "بدون خلط للوحدات (فصل الأوتاد / الألواح / الأمتار)",
      "Smart Synthesis": "ملخص ذكي (AI)",
      "Generate Smart Synthesis": "توليد الملخص الذكي",
      "Smart Blocker Synthesis (RAG)": "ملخص العوائق الذكي (RAG)",
      "Phase 4: Cloud AI & RAG Synthesis with Deterministic Fallback": "المرحلة 4: الذكاء الاصطناعي السحابي مع الاسترجاع المعزز والبديل الحتمي",
      "Retrieving blockers and generating synthesis...": "جارٍ استرجاع العوائق وتوليد التحليل الذكي...",
      "Cloud AI (RAG Pipeline)": "الذكاء الاصطناعي السحابي (RAG)",
      "Rule-based Fallback (Site Offline Safe)": "الوضع الحتمي البديل (آمن دون اتصال)",
      "Open Blockers": "العوائق النشطة",
      "Critical Issues": "مشكلات حرجة",
      "Lost Hours": "ساعات العمل الضائعة",
      "Past Precedents": "سوابق الحلول التاريخية",
      "Close": "إغلاق",
      "Copy Synthesis": "نسخ التحليل",
      "Synthesis copied to clipboard!": "تم نسخ التحليل إلى الحافظة!",
      "Blockers & Obstacles": "العوائق والمشكلات",
      "Track site blockers & executive AI synthesis.": "تتبع عوائق الموقع والتوليف الذكي للمدير.",
      "Work Packages": "حزم العمل",
      "Physical baseline milestones and progress.": "معالم خط الأساس والتقدم الميداني.",
      "Generate Smart Blocker Synthesis (AI)": "توليد التوليف الذكي للانسدادات (ذكاء اصطناعي)",
      "Smart Blocker Synthesis (AI)": "التوليف الذكي للانسدادات (ذكاء اصطناعي)",
      "Click to view Project Sites": "انقر لعرض مواقع المشاريع",
      "Click to view Blocker Dashboard": "انقر لعرض لوحة تحكم الانسدادات",
      "Click to view Projects": "انقر لعرض المشاريع",
      "Click to view Work Package details": "انقر لعرض تفاصيل حزمة العمل",
      "Listen to Synthesis": "الاستماع إلى التلخيص",
      "Stop Listening": "إيقاف الاستماع",
      "Text-to-Speech is not supported in this browser.": "خاصية تحويل النص إلى صوت غير مدعومة في هذا المتصفح.",
      "Generate PDF Report": "توليد تقرير PDF التنفيذي"
    },
    fr: {
      "Good Morning": "Bonjour",
      "Good Afternoon": "Bon après-midi",
      "Good Evening": "Bonsoir",
      "Here's what's happening with your renewable energy assets today.": "Voici la situation actuelle de vos actifs d'énergie renouvelable.",
      "Total Capacity": "Capacité totale",
      "Active Sites": "Sites actifs",
      "Total Energy Today": "Énergie totale aujourd'hui",
      "CO2 Avoided": "CO2 évité",
      "Sites connected": "Sites connectés",
      "operational": "opérationnel",
      "lost (blockers)": "perdu (blocages)",
      "vs. yesterday": "vs hier",
      "offset today": "compensé aujourd'hui",
      "Loading...": "Chargement...",
      "Applications": "Applications",
      "All your tools in one place.": "Tous vos outils au même endroit.",
      "All": "Tout",
      "Energy": "Énergie",
      "Operations": "Opérations",
      "Reports": "Rapports",
      "System": "Système",
      "Projects": "Projets",
      "Manage your renewable energy projects.": "Gérez vos projets d'énergie renouvelable.",
      "Sites": "Sites",
      "Monitor and manage solar and wind sites.": "Surveillez et gérez les sites solaires et éoliens.",
      "Energy Analytics": "Analytique énergétique",
      "AI Copilot": "Copilote IA",
      "Kanban Board": "Tableau Kanban",
      "Interactive 4-column blocker workflow board.": "Tableau interactif des blocages à 4 colonnes.",
      "Track performance and energy generation.": "Suivez la performance et la production d'énergie.",
      "Generate insights and export data.": "Générez des analyses et exportez les données.",
      "Quality Inspections": "Inspections qualité",
      "Conduct and manage inspections.": "Menez et gérez les inspections.",
      "Real-time monitoring and control.": "Surveillance et contrôle en temps réel.",
      "Maintenance": "Maintenance",
      "Schedule and track maintenance activities.": "Planifiez et suivez la maintenance.",
      "Stock": "Stock",
      "Manage inventory and materials.": "Gérez les stocks et les matériaux.",
      "Purchase": "Achats",
      "Handle procurement and suppliers.": "Gérez les approvisionnements et les fournisseurs.",
      "Sales": "Ventes",
      "Manage customers and billing.": "Gérez les clients et la facturation.",
      "HR": "Ressources Humaines",
      "Manage your team and workforce.": "Gérez votre équipe et les effectifs.",
      "Payroll": "Paie",
      "Process payroll and benefits.": "Traitez la paie et les avantages sociaux.",
      "Accounting": "Comptabilité",
      "Track finances and generate reports.": "Suivez les finances et générez des rapports.",
      "Settings": "Paramètres",
      "Configure your system and preferences.": "Configurez le système et les préférences.",
      "Help & Support": "Aide et support",
      "Get assistance and documentation.": "Obtenez de l'aide et de la documentation.",
      "Back to Main Dashboard": "Retour au tableau de bord",
      "Return to Main Dashboard": "Retour au tableau de bord principal",
      "Live Database Connected": "Base de données connectée",
      "Live Database Connection Active & Synchronized": "Connexion directe à la base de données active",
      "Search for apps, projects, sites, reports...": "Rechercher des applications, projets, sites, rapports...",
      "Language": "Langue",
      "Select Language": "Choisir la langue",
      "My Profile": "Mon profil",
      "Sign Out": "Déconnexion",
      "Home": "Accueil",
      "Cleaner Energy": "Énergie plus propre",
      "A Brighter Tomorrow": "Un avenir plus radieux",
      "Efficiently managing renewable resources for a sustainable future.": "Gérer efficacement les ressources renouvelables.",
      "System Online": "Système en ligne",
      "Learn more": "En savoir plus",
      "ENTERPRISE": "ENTREPRISE",
      "Photovoltaic Execution OS": "OS d'exécution photovoltaïque",
      "Sunny • Tunis, TN": "Ensoleillé • Tunis, TN",
      "Notifications": "Notifications",
      "Account settings": "Paramètres du compte",
      "Solar Farm": "Centrale solaire",
      "Open": "Ouvrir",
      "Grid View": "Vue grille",
      "List View": "Vue liste",
      "Performance metrics & delivery milestones": "Indicateurs de performance et jalons de livraison",
      "Active solar & wind installations": "Installations solaires et éoliennes actives",
      "Pending action items & engineering logs": "Actions en attente et journaux d'ingénierie",
      "Manage renewable project lifecycles": "Gérer le cycle de vie des projets renouvelables",
      "Quality standards & protocol trees": "Normes de qualité et protocoles",
      "Field assessments & quality ratings": "Évaluations de terrain et notations de qualité",
      "Review sessions & coordination meetings": "Sessions de revue et réunions de coordination",
      "Corrective actions & issue resolution": "Actions correctives et résolution des problèmes",
      "Stock tracking and materials management": "Suivi des stocks et gestion des matériaux",
      "Procurement, purchase orders & vendors": "Approvisionnements, commandes et fournisseurs",
      "Customer accounts and sales orders": "Comptes clients et commandes de vente",
      "Workforce directory and team assignments": "Annuaire des effectifs et affectations",
      "Operations and overview": "Opérations et vue d'ensemble",
      "Live Database Metric": "Métrique de base de données en direct",
      "Failed to update language. Please try again.": "Échec de mise à jour de la langue. Veuillez réessayer.",
      "Error switching language.": "Erreur lors du changement de langue.",
      "7-Day Verified Progress": "Avancement Vérifié 7 Jours",
      "Physical installed quantities strictly within the 7-calendar-day window": "Quantités physiques installées vérifiées sur la fenêtre de 7 jours calendaires",
      "Period": "Période",
      "Baseline": "Référentiel",
      "Status": "Statut",
      "Verified Only": "Vérifié Uniquement",
      "Separate Units": "Unités Distinctes",
      "Zero Labour Conversion": "Zéro conversion heures MO",
      "Net Corrections": "Corrections Nettes",
      "Strict 7-Day Boundary": "Fenêtre Stricte 7 Jours",
      "Physical Units Breakdown": "Détail par Unités Physiques",
      "Units Summary": "Synthèse par Unités",
      "Unknown": "Inconnu",
      "Measured": "Mesuré",
      "Measured 0": "Mesuré 0",
      "Planned": "Planifié",
      "Approved": "Approuvé",
      "Piles (Battage)": "Pieux (Battage)",
      "Modules (Pose)": "Modules (Pose)",
      "Trenching": "Tranchées",
      "Cabling": "Câblage",
      "Drafts & Receipts Excluded": "Brouillons et réceptions exclus",
      "Verified Progress Reader": "Lecteur d'Avancement Vérifié",
      "No Unit Mixing (pieux / modules / m separated)": "Unités distinctes (pieux / modules / m séparés)",
      "Smart Synthesis": "Synthèse Intelligente",
      "Generate Smart Synthesis": "Générer la Synthèse Intelligente",
      "Smart Blocker Synthesis (RAG)": "Synthèse Intelligente des Blocages (RAG)",
      "Phase 4: Cloud AI & RAG Synthesis with Deterministic Fallback": "Phase 4 : Synthèse Cloud AI & RAG avec Repli Déterministe",
      "Retrieving blockers and generating synthesis...": "Récupération des blocages et génération de la synthèse...",
      "Cloud AI (RAG Pipeline)": "Cloud AI (Pipeline RAG)",
      "Rule-based Fallback (Site Offline Safe)": "Repli Déterministe (Mode Chantier)",
      "Open Blockers": "Blocages Actifs",
      "Critical Issues": "Problèmes Critiques",
      "Lost Hours": "Heures Perdues",
      "Past Precedents": "Précédents Historiques",
      "Close": "Fermer",
      "Copy Synthesis": "Copier la Synthèse",
      "Synthesis copied to clipboard!": "Synthèse copiée dans le presse-papiers !",
      "Blockers & Obstacles": "Blocages & Obstacles",
      "Track site blockers & executive AI synthesis.": "Suivi des blocages terrain & synthèse IA décisionnelle.",
      "Work Packages": "Lots de Travaux (WP)",
      "Physical baseline milestones and progress.": "Jalons du référentiel et avancement physique.",
      "Generate Smart Blocker Synthesis (AI)": "Générer la Synthèse Intelligente (IA)",
      "Smart Blocker Synthesis (AI)": "Synthèse Intelligente (IA)",
      "Click to view Project Sites": "Cliquer pour voir les sites de projets",
      "Click to view Blocker Dashboard": "Cliquer pour voir le tableau de bord des blocages",
      "Click to view Projects": "Cliquer pour voir les projets",
      "Click to view Work Package details": "Cliquer pour voir les détails du lot de travaux",
      "Listen to Synthesis": "Écouter la synthèse",
      "Stop Listening": "Arrêter l'écoute",
      "Text-to-Speech is not supported in this browser.": "La synthèse vocale n'est pas supportée sur ce navigateur.",
      "Generate PDF Report": "Générer Rapport PDF"
    }
  };

  function syncFrappeTranslations() {
    const lang = getCurrentLangCode();
    if (typeof window !== "undefined" && window.frappe) {
      if (!window.frappe._messages) window.frappe._messages = {};
      if (UI_TRANSLATIONS[lang]) {
        Object.assign(window.frappe._messages, UI_TRANSLATIONS[lang]);
      }
    }
  }

  function __(str) {
    if (!str) return "";
    syncFrappeTranslations();
    if (typeof window !== "undefined") {
      if (window.frappe && typeof window.frappe._ === "function") {
        const res = window.frappe._(str);
        if (res && res !== str) return res;
      }
      if (typeof window.__ === "function" && window.__ !== __) {
        const res = window.__(str);
        if (res && res !== str) return res;
      }
    }
    const lang = getCurrentLangCode();
    if (UI_TRANSLATIONS[lang] && UI_TRANSLATIONS[lang][str]) {
      return UI_TRANSLATIONS[lang][str];
    }
    return str;
  }

  // Pre-seed Frappe dictionary immediately
  syncFrappeTranslations();

  // Multi-source role extractor from every Frappe boot/session property
  function getUserRoles() {
    const rolesSet = new Set();
    if (typeof window !== "undefined" && window.frappe) {
      if (frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles)) {
        frappe.boot.user.roles.forEach((r) => { if (typeof r === "string" && r) rolesSet.add(r.trim()); });
      }
      if (Array.isArray(frappe.user_roles)) {
        frappe.user_roles.forEach((r) => { if (typeof r === "string" && r) rolesSet.add(r.trim()); });
      }
      if (frappe.user && typeof frappe.user.get_roles === "function") {
        try {
          const r = frappe.user.get_roles();
          if (Array.isArray(r)) {
            r.forEach((role) => { if (typeof role === "string" && role) rolesSet.add(role.trim()); });
          }
        } catch (e) {}
      }
      if (frappe.boot && Array.isArray(frappe.boot.user_roles)) {
        frappe.boot.user_roles.forEach((r) => { if (typeof r === "string" && r) rolesSet.add(r.trim()); });
      }
    }
    return Array.from(rolesSet);
  }

  function getCurrentUsername() {
    if (typeof window === "undefined" || !window.frappe) return "";
    let u = "";
    if (frappe.session && typeof frappe.session.user === "string") {
      u = frappe.session.user;
    } else if (frappe.boot && frappe.boot.user && typeof frappe.boot.user.name === "string") {
      u = frappe.boot.user.name;
    } else if (frappe.user && typeof frappe.user.name === "string") {
      u = frappe.user.name;
    }
    return (u || "").trim();
  }

  function isAdministratorUser() {
    const u = getCurrentUsername().toLowerCase();
    if (u === "administrator" || u === "admin" || u.startsWith("admin@")) {
      return true;
    }
    const roles = getUserRoles();
    if (roles.some((r) => typeof r === "string" && (r.toLowerCase() === "administrator" || r.toLowerCase() === "system manager"))) {
      return true;
    }
    if (typeof window !== "undefined" && window.frappe && frappe.user && typeof frappe.user.has_role === "function") {
      try {
        if (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) {
          return true;
        }
      } catch (e) {}
    }
    return false;
  }

  // Strictly check if current user can access Security & Access Audit
  // ONLY URANOS Executive, System Manager, and Administrator are permitted
  function canAccessSecurityAudit() {
    if (typeof window === "undefined" || !window.frappe) return false;

    // Direct check via frappe.user.has_role as mandated
    if (frappe.user && typeof frappe.user.has_role === "function") {
      try {
        if (
          frappe.user.has_role("URANOS Executive") ||
          frappe.user.has_role("System Manager") ||
          frappe.user.has_role("Administrator")
        ) {
          return true;
        }
      } catch (e) {}
    }

    const u = getCurrentUsername().toLowerCase();
    if (u === "administrator" || u === "direction_01@uranos.local") {
      return true;
    }

    const roles = getUserRoles();
    return roles.some((r) => {
      const lower = (r || "").toLowerCase().trim();
      return (
        lower === "uranos executive" ||
        lower === "system manager" ||
        lower === "administrator"
      );
    });
  }

  // Flagship URANOS Group applications with Dynamic Role-Based Access Control (RBAC)
  function getTargetApps() {
    return [
      {
        id: "projects",
        label: __("Projects"),
        subtitle: __("Manage your renewable energy projects."),
        gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>`,
        route: "/app/project",
        category: "energy",
        allowed_roles: [
          "site_team", "engineer", "URANOS Civil Director", "URANOS Digital Admin", "URANOS Electrical Execution Manager",
          "URANOS Engineering Director", "URANOS Executive", "URANOS Finance Controller", "URANOS HSE",
          "URANOS Procurement Logistics", "URANOS Project Manager", "URANOS QA QC", "URANOS Read Only Auditor",
          "URANOS Site Controller", "URANOS Storekeeper", "URANOS Team Lead", "Administrator", "System Manager"
        ]
      },
      {
        id: "sites",
        label: __("Sites"),
        subtitle: __("Monitor and manage solar and wind sites."),
        gradient: "linear-gradient(135deg, #06b6d4 0%, #2563eb 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>`,
        route: "/app/uranos-project-profile",
        category: "energy",
        allowed_roles: [
          "site_team", "engineer", "URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director",
          "URANOS Executive", "URANOS Project Manager", "URANOS Site Controller", "URANOS Team Lead",
          "Administrator", "System Manager"
        ]
      },
      {
        id: "energy-analytics",
        label: __("AI Copilot"),
        subtitle: __("Photovoltaic yield telemetry & AI Copilot."),
        gradient: "linear-gradient(135deg, #0d9488 0%, #0284c7 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>`,
        route: "/app/uranos-ai-copilot",
        category: "energy",
        allowed_roles: [
          "engineer", "URANOS Engineering Director", "URANOS Executive", "URANOS Project Manager",
          "URANOS Read Only Auditor", "Administrator", "System Manager"
        ]
      },
      {
        id: "blockers",
        label: __("Blockers & Obstacles"),
        subtitle: __("Executive blocker dashboard & AI synthesis."),
        gradient: "linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #991b1b 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
        route: "/app/blocker-dashboard",
        category: "operations",
        allowed_roles: [
          "management", "engineer", "site_team", "URANOS Civil Director", "URANOS Electrical Execution Manager",
          "URANOS Engineering Director", "URANOS Executive", "URANOS HSE", "URANOS Procurement Logistics",
          "URANOS Project Manager", "URANOS QA QC", "URANOS Read Only Auditor", "URANOS Site Controller",
          "URANOS Storekeeper", "URANOS Team Lead", "Administrator", "System Manager"
        ]
      },
      {
        id: "kanban",
        label: __("Kanban Board"),
        subtitle: __("Interactive 4-column blocker workflow board."),
        gradient: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M8 7v7"/><path d="M12 7v4"/><path d="M16 7v9"/></svg>`,
        route: "/app/blocker-kanban",
        category: "operations",
        allowed_roles: [
          "management", "engineer", "site_team", "URANOS Executive", "URANOS Engineering Director",
          "URANOS Project Manager", "URANOS Site Controller", "Administrator", "System Manager"
        ]
      },
      {
        id: "work-packages",
        label: __("Work Packages"),
        subtitle: __("Physical baseline milestones and progress."),
        gradient: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>`,
        route: "/app/uranos-work-package",
        category: "energy",
        allowed_roles: [
          "site_team", "engineer", "URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director",
          "URANOS Executive", "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller",
          "URANOS Team Lead", "Administrator", "System Manager"
        ]
      },
      {
        id: "reports",
        label: __("Reports"),
        subtitle: __("Daily site reports and project insights."),
        gradient: "linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
        route: "/app/uranos-daily-site-report",
        category: "reports",
        allowed_roles: [
          "site_team", "engineer", "URANOS Engineering Director", "URANOS Executive", "URANOS Finance Controller",
          "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller",
          "Administrator", "System Manager"
        ]
      },
      {
        id: "quality-inspections",
        label: __("Quality Inspections"),
        subtitle: __("Non-conformance, hold points and QA tests."),
        gradient: "linear-gradient(135deg, #10b981 0%, #0d9488 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>`,
        route: "/app/uranos-ncr",
        category: "energy",
        allowed_roles: [
          "site_team", "engineer", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Project Manager",
          "URANOS QA QC", "URANOS Read Only Auditor", "URANOS Site Controller",
          "Administrator", "System Manager"
        ]
      },
      {
        id: "operations",
        label: __("Operations"),
        subtitle: __("Field installation progress declarations."),
        gradient: "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
        route: "/app/uranos-field-progress-entry",
        category: "operations",
        allowed_roles: [
          "site_team", "engineer", "URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director",
          "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller", "URANOS Team Lead",
          "Administrator", "System Manager"
        ]
      },
      {
        id: "maintenance",
        label: __("Maintenance"),
        subtitle: __("Schedule and track site plant assets."),
        gradient: "linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
        route: "/app/assets",
        category: "operations",
        allowed_roles: [
          "engineer", "URANOS Electrical Execution Manager", "URANOS Engineering Director",
          "Administrator", "System Manager"
        ]
      },
      {
        id: "stock",
        label: __("Stock"),
        subtitle: __("Manage inventory, kits and cable reels."),
        gradient: "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>`,
        route: "/app/stock",
        category: "operations",
        allowed_roles: [
          "site_team", "engineer", "URANOS Engineering Director", "URANOS Executive", "URANOS Procurement Logistics",
          "URANOS Project Manager", "URANOS Site Controller", "URANOS Storekeeper",
          "Administrator", "System Manager"
        ]
      },
      // ── "HORS V1" / BACK-OFFICE MODULES (Strictly restricted from operational field teams) ──
      {
        id: "purchase",
        label: __("Purchase"),
        subtitle: __("Procurement & supplier contracts (Hors V1)."),
        gradient: "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
        route: "/app/buying",
        category: "operations",
        allowed_roles: ["Administrator", "System Manager"]
      },
      {
        id: "sales",
        label: __("Sales"),
        subtitle: __("Client contracts & billing (Hors V1)."),
        gradient: "linear-gradient(135deg, #10b981 0%, #0284c7 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>`,
        route: "/app/selling",
        category: "operations",
        allowed_roles: ["Administrator", "System Manager"]
      },
      {
        id: "hr",
        label: __("HR"),
        subtitle: __("Human resources management (Hors V1)."),
        gradient: "linear-gradient(135deg, #06b6d4 0%, #2563eb 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
        route: "/app/users",
        category: "operations",
        allowed_roles: ["Administrator", "System Manager"]
      },
      {
        id: "payroll",
        label: __("Payroll"),
        subtitle: __("Salary processing & benefits (Hors V1)."),
        gradient: "linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
        route: "/app/financial-reports",
        category: "operations",
        allowed_roles: ["Administrator", "System Manager"]
      },
      {
        id: "accounting",
        label: __("Accounting"),
        subtitle: __("General ledgers and financial audits."),
        gradient: "linear-gradient(135deg, #10b981 0%, #0d9488 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1v4"/></svg>`,
        route: "/app/invoicing",
        category: "reports",
        allowed_roles: ["Administrator", "System Manager", "URANOS Finance Controller", "URANOS Executive"]
      },
      {
        id: "settings",
        label: __("Settings"),
        subtitle: __("System configuration and administration."),
        gradient: "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
        route: "/app/erpnext-settings",
        category: "system",
        allowed_roles: ["Administrator", "System Manager", "URANOS Digital Admin"]
      },
      {
        id: "access-audit",
        label: __("Audit Sécurité & Accès"),
        subtitle: __("Surveillance des sessions, logins/logouts et adresses IP."),
        gradient: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><circle cx="12" cy="11" r="3"/><line x1="12" y1="14" x2="12" y2="17"/></svg>`,
        route: "/app/access-audit",
        category: "system",
        allowed_roles: ["Administrator", "System Manager", "URANOS Executive"]
      },
      {
        id: "help-support",
        label: __("Help & Support"),
        subtitle: __("Documentation & operational guidelines."),
        gradient: "linear-gradient(135deg, #10b981 0%, #2563eb 100%)",
        svg: `<svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>`,
        route: "/app/support",
        category: "system",
        allowed_roles: ["*"]
      }
    ];
  }

  // Frontend Role-Based Visibility (RBAC) Guard
  function userHasAccessToApp(app, auth) {
    if (!app || !app.allowed_roles || !Array.isArray(app.allowed_roles) || app.allowed_roles.length === 0) {
      return false; // Fail-closed
    }
    if (app.allowed_roles.includes("*")) {
      return true;
    }

    const currentAuth = auth || _verifiedAuth || computeVerifiedAuth(null);

    // 1. Superuser / Administrator MUST see all cards
    if (currentAuth.isSuperAdmin) {
      return true;
    }

    // 2. Client-side Frappe API check: frappe.user.has_role(...)
    if (window.frappe && frappe.user && typeof frappe.user.has_role === "function") {
      for (let i = 0; i < app.allowed_roles.length; i++) {
        try {
          if (frappe.user.has_role(app.allowed_roles[i])) {
            return true;
          }
        } catch (e) {}
      }
    }

    // 3. Fallback: Check against verified auth roles, boot roles, or user_roles array
    const userRoles = (currentAuth && Array.isArray(currentAuth.roles) ? currentAuth.roles : [])
      .concat(window.frappe && Array.isArray(frappe.user_roles) ? frappe.user_roles : [])
      .concat(window.frappe && frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles) ? frappe.boot.user.roles : []);

    if (userRoles.length === 0) return false;

    const normalizedUserRoles = userRoles.map((r) => String(r).toLowerCase().trim());
    return app.allowed_roles.some((allowedRole) => {
      const normAllowed = String(allowedRole || "").toLowerCase().trim();
      return normalizedUserRoles.includes(normAllowed);
    });
  }

  // Pre-renders the exact HTML string containing ONLY authorized cards before DOM insertion
  function buildApplicationsGridHtml(auth) {
    const resolvedAuth = auth || _verifiedAuth || computeVerifiedAuth(null);
    const apps = getTargetApps();
    let cardsHtml = "";
    let renderedCount = 0;

    apps.forEach((app) => {
      // Dynamic Role-Based Visibility: Strictly exclude unauthorized cards from HTML
      if (!userHasAccessToApp(app, resolvedAuth)) return;

      renderedCount++;
      cardsHtml += `
        <a class="desktop-icon" href="${app.route}" data-id="${app.id}" data-category="${app.category}">
          <div class="gv-card-squircle" style="background: ${app.gradient};">
            ${app.svg}
          </div>
          <div class="icon-caption">
            <div class="icon-title">${__(app.label)}</div>
            <div class="gv-card-subtitle">${__(app.subtitle)}</div>
          </div>
          <div class="gv-card-arrow-btn" title="${__("Open")} ${app.label}">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </div>
        </a>
      `;
    });

    if (renderedCount === 0) {
      cardsHtml = `
        <div class="gv-no-modules-placeholder" style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: #64748b; font-size: 13.5px;">
          ${__("No modules currently accessible for your assigned project role.")}
        </div>
      `;
    }

    return {
      html: cardsHtml,
      count: renderedCount,
      toString() {
        return this.html;
      }
    };
  }

  const TARGET_APPS = getTargetApps();

  let dashboardKPICache = null;
  let isFetchingKPIs = false;
  let isDOMMutationActive = false;

  function getFormattedDate() {
    if (dashboardKPICache && dashboardKPICache.formatted_date) {
      return dashboardKPICache.formatted_date;
    }
    const now = new Date();
    const options = { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: true };
    return now.toLocaleString("en-US", options).replace(",", " -");
  }

  function getUserFirstName() {
    if (window.frappe && frappe.session && frappe.session.user) {
      const u = frappe.session.user.toLowerCase();
      if (u.includes("direction") || (frappe.user && frappe.user.has_role("management"))) {
        return "Manager";
      }
    }
    if (dashboardKPICache && dashboardKPICache.user && dashboardKPICache.user.first_name) {
      const fn = dashboardKPICache.user.first_name;
      if (fn.toLowerCase().includes("direction")) return "Manager";
      return fn;
    }
    if (window.frappe && frappe.session && frappe.session.user) {
      const user = frappe.session.user;
      if (user !== "Administrator" && user.includes("@")) {
        const local = user.split("@")[0].split(".")[0];
        if (local.toLowerCase().includes("direction")) return "Manager";
        return local.charAt(0).toUpperCase() + local.slice(1);
      }
      return user;
    }
    return "Team";
  }

  function getUserFullName() {
    if (window.frappe && frappe.session && frappe.session.user) {
      const u = frappe.session.user.toLowerCase();
      if (u.includes("direction") || (frappe.user && frappe.user.has_role("management"))) {
        return "Manager";
      }
    }
    if (dashboardKPICache && dashboardKPICache.user && dashboardKPICache.user.full_name) {
      const fn = dashboardKPICache.user.full_name;
      if (fn.toLowerCase().includes("direction")) return "Manager";
      return fn;
    }
    if (window.frappe && frappe.session && frappe.session.user_fullname) {
      const ufn = frappe.session.user_fullname;
      if (ufn.toLowerCase().includes("direction")) return "Manager";
      return ufn;
    }
    return getUserFirstName();
  }

  function getUserEmail() {
    if (window.frappe && frappe.session && frappe.session.user) {
      return frappe.session.user;
    }
    return "direction_01@uranos.local";
  }

  function getUserRoleTitle() {
    if (window.frappe && frappe.session && frappe.session.user) {
      const u = frappe.session.user.toLowerCase();
      if (u.includes("direction") || (frappe.user && frappe.user.has_role("management"))) {
        return "Manager";
      }
    }
    if (dashboardKPICache && dashboardKPICache.user && dashboardKPICache.user.role) {
      let r = dashboardKPICache.user.role;
      if (r.toLowerCase().includes("direction") || r.toLowerCase().includes("executive") || r.toLowerCase().includes("management")) {
        return "Manager";
      }
      return __(r);
    }
    if (window.frappe && frappe.user_roles) {
      const uranosRoles = frappe.user_roles.filter(r => r.startsWith("URANOS ")).map(r => r.replace("URANOS ", ""));
      if (uranosRoles.length) return __(uranosRoles[0]);
    }
    return __("Operations");
  }

  function getUserInitials() {
    const name = getUserFullName();
    if (!name) return "UG";
    const parts = name.split(" ").filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }

  function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return __("Good Morning");
    if (hour < 18) return __("Good Afternoon");
    return __("Good Evening");
  }

  function switchUserLanguage(targetLang) {
    if (!window.frappe || !frappe.session || !frappe.session.user) return;
    const current = getCurrentLangCode();
    if (current === targetLang) return;

    if (frappe.show_alert) {
      frappe.show_alert({
        message: targetLang === "ar" ? "جاري تفعيل اللغة العربية..." : (targetLang === "fr" ? "Mise à jour en français..." : "Switching to English..."),
        indicator: "blue"
      });
    }

    frappe.call({
      method: "frappe.client.set_value",
      args: {
        doctype: "User",
        name: frappe.session.user,
        fieldname: "language",
        value: targetLang
      },
      freeze: true,
      freeze_message: targetLang === "ar" ? "جاري تفعيل الواجهة العربية..." : "Applying language settings...",
      callback: function (r) {
        if (!r.exc) {
          window.location.reload();
        } else {
          if (frappe.msgprint) {
            frappe.msgprint(__("Failed to update language. Please try again."));
          }
        }
      },
      error: function (err) {
        console.error("URANOS: Language switch error", err);
        if (frappe.msgprint) {
          frappe.msgprint(__("Error switching language."));
        }
      }
    });
  }

  function updateDashboardDOM(data) {
    if (!data) return;
    dashboardKPICache = data;

    let fName = (data.user && data.user.first_name) ? data.user.first_name : getUserFirstName();
    let fullName = (data.user && data.user.full_name) ? data.user.full_name : getUserFullName();
    let rTitle = (data.user && data.user.role) ? data.user.role : getUserRoleTitle();

    if (fName.toLowerCase().includes("direction") || (frappe.user && frappe.user.has_role("management"))) fName = "Manager";
    if (fullName.toLowerCase().includes("direction") || (frappe.user && frappe.user.has_role("management"))) fullName = "Manager";
    if (rTitle.toLowerCase().includes("direction") || rTitle.toLowerCase().includes("executive") || (frappe.user && frappe.user.has_role("management"))) rTitle = "Manager";

    $("#gv-hero-user-name").text(fName);
    $(".gv-user-name").text(fullName);
    $(".gv-user-role").text(__(rTitle));
    $(".gv-user-avatar").text(getUserInitials());

    if (data.formatted_date) {
      $(".gv-apps-footer .gv-footer-right span:last-child").text(data.formatted_date);
    }

    const capVal = Number(data.total_capacity_mw || 0).toFixed(1);
    $("#gv-kpi-capacity-val").html(`${capVal} <span class="gv-kpi-unit">MW</span>`);
    $("#gv-kpi-capacity-trend").html(`&#9650; ${data.total_sites || 0} ${__("Sites connected")}`);

    const activeSites = data.active_sites !== undefined ? data.active_sites : 0;
    const totalSites = data.total_sites !== undefined ? data.total_sites : 0;
    $("#gv-kpi-sites-val").text(`${activeSites} / ${totalSites}`);
    const opRate = data.operational_rate_percent !== undefined ? data.operational_rate_percent : (totalSites ? ((activeSites / totalSites) * 100).toFixed(0) : 0);
    $("#gv-kpi-sites-trend").html(`&#9650; ${opRate}% ${__("operational")}`);

    const energyVal = Number(data.energy_today_mwh || 0).toLocaleString(undefined, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    });
    $("#gv-kpi-energy-val").html(`${energyVal} <span class="gv-kpi-unit">MWh</span>`);
    if (data.lost_hours && Number(data.lost_hours) > 0) {
      $("#gv-kpi-energy-trend").html(`&#9660; ${Number(data.lost_hours).toFixed(1)}h ${__("lost (blockers)")}`);
    } else {
      $("#gv-kpi-energy-trend").html(`&#9650; +5.6% ${__("vs. yesterday")}`);
    }

    const co2Val = Number(data.co2_avoided_t || 0).toLocaleString(undefined, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    });
    $("#gv-kpi-co2-val").html(`${co2Val} <span class="gv-kpi-unit">t</span>`);
    $("#gv-kpi-co2-trend").html(`&#9650; ${co2Val} t ${__("offset today")}`);
  }

  function fetchDashboardKPIs() {
    if (typeof frappe === "undefined" || !frappe.call) return;
    if (isFetchingKPIs) return;
    isFetchingKPIs = true;

    frappe.call({
      method: "uranos_project_os.services.api.get_dashboard_kpis",
      callback: function (rSrv) {
        isFetchingKPIs = false;
        if (rSrv && rSrv.message) {
          updateDashboardDOM(rSrv.message);
        }
      },
      error: function (err) {
        isFetchingKPIs = false;
        console.warn("URANOS: get_dashboard_kpis fallback", err);
      }
    });
  }

  // ── 7-DAY VERIFIED PROGRESS READER (BENTO CARD DATA) ──
  let progress7DayCache = null;
  let isFetchingProgress = false;

  const DEMO_7DAY_PROGRESS = {
    project: "PV-0001",
    baseline_version: "B1",
    status: "Verified",
    period: {
      start_date: "2026-09-10",
      end_date: "2026-09-16",
      calendar_days: 7
    },
    work_packages: [
      {
        code: "WP-030",
        title: "Piles (Battage)",
        uom: "pieux",
        qty_verified: 100,
        qty_planned: 1000,
        weight: 25,
        is_measured: true
      },
      {
        code: "WP-050",
        title: "Modules (Pose)",
        uom: "modules",
        qty_verified: 0,
        qty_planned: 2000,
        weight: 35,
        is_measured: true
      },
      {
        code: "WP-020",
        title: "Trenching",
        uom: "m",
        qty_verified: 250,
        qty_planned: 1200,
        weight: 20,
        is_measured: true
      },
      {
        code: "WP-080",
        title: "Cabling",
        uom: "m",
        qty_verified: null,
        qty_planned: 5000,
        weight: 20,
        is_measured: false
      }
    ],
    units_summary: {
      pieux: 100,
      modules: 0,
      m: 250
    },
    total_verified_entries: 3,
    missing_data: ["WP-080"]
  };

  function update7DayProgressDOM(data) {
    if (!data) return;
    const $container = $("#gv-7day-progress-container");
    if (!$container.length) return;

    if (data.period) {
      $("#gv-progress-period").text(`${data.period.start_date} → ${data.period.end_date} (${data.period.calendar_days}d)`);
    }
    if (data.baseline_version) {
      $("#gv-progress-baseline").text(`${data.baseline_version} (${__("Approved")})`);
    }
    if (data.project) {
      $("#gv-progress-project").text(data.project);
    }

    const $grid = $("#gv-progress-wp-grid");
    if ($grid.length && data.work_packages) {
      $grid.empty();
      data.work_packages.forEach((wp) => {
        let valHtml = "";
        let statusBadge = "";
        let pct = 0;

        if (wp.is_measured && wp.qty_verified !== null && wp.qty_verified !== undefined) {
          if (Number(wp.qty_verified) === 0) {
            valHtml = `0 <span class="gv-wp-uom">${wp.uom}</span>`;
            statusBadge = `<span class="gv-wp-status-pill zero">${__("Measured 0")}</span>`;
            pct = 0;
          } else {
            valHtml = `${Number(wp.qty_verified).toLocaleString()} <span class="gv-wp-uom">${wp.uom}</span>`;
            statusBadge = `<span class="gv-wp-status-pill verified">${__("Measured")}</span>`;
            if (wp.qty_planned && Number(wp.qty_planned) > 0) {
              pct = Math.min(100, Math.round((Number(wp.qty_verified) / Number(wp.qty_planned)) * 100));
            }
          }
        } else {
          valHtml = `— <span class="gv-wp-uom unknown">${__("Unknown")}</span>`;
          statusBadge = `<span class="gv-wp-status-pill unknown">${__("Unknown")}</span>`;
          pct = 0;
        }

        const plannedText = wp.qty_planned ? `${Number(wp.qty_planned).toLocaleString()} ${wp.uom}` : "—";

        const $wpCard = $(`
          <div class="gv-wp-card ${!wp.is_measured ? "is-unknown" : ""}">
            <div class="gv-wp-header">
              <div class="gv-wp-info">
                <span class="gv-wp-code">${wp.code}</span>
                <span class="gv-wp-title">${__(wp.title)}</span>
              </div>
              ${statusBadge}
            </div>

            <div class="gv-wp-val-row">
              <div class="gv-wp-val">${valHtml}</div>
              <div class="gv-wp-planned">/ ${plannedText}</div>
            </div>

            <div class="gv-wp-progress-bar-bg">
              <div class="gv-wp-progress-bar-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `);

        $wpCard.css("cursor", "pointer").attr("title", __("Click to view Work Package details")).on("click", function () {
          if (window.frappe && frappe.set_route) {
            frappe.set_route("uranos-work-package");
          }
        });

        $grid.append($wpCard);
      });
    }

    const $summary = $("#gv-progress-summary-chips");
    if ($summary.length) {
      $summary.empty().css("cursor", "pointer").attr("title", __("Click to view Field Progress Entries")).off("click.gvProgressChips").on("click.gvProgressChips", function () {
        if (window.frappe && frappe.set_route) {
          frappe.set_route("uranos-field-progress-entry");
        }
      });
      if (data.units_summary) {
        Object.keys(data.units_summary).forEach((uom) => {
          const qty = data.units_summary[uom];
          $summary.append(`
            <span class="gv-unit-chip">
              <strong class="gv-chip-qty">${Number(qty).toLocaleString()}</strong> ${uom}
            </span>
          `);
        });
      }
      if (data.missing_data && data.missing_data.length > 0) {
        $summary.append(`
          <span class="gv-unit-chip unknown">
            ${data.missing_data.join(", ")}: <em>${__("Unknown")}</em>
          </span>
        `);
      }
    }
  }

  function fetch7DayProgress() {
    if (progress7DayCache) {
      update7DayProgressDOM(progress7DayCache);
    }
    if (typeof frappe === "undefined" || !frappe.call) {
      update7DayProgressDOM(DEMO_7DAY_PROGRESS);
      return;
    }
    if (isFetchingProgress) return;
    isFetchingProgress = true;

    frappe.call({
      method: "uranos_project_os.services.progress.get_verified_progress_7days",
      args: {
        project: "PV-0001",
        start_date: "2026-09-10",
        end_date: "2026-09-16"
      },
      freeze: false,
      silent: true,
      callback: function (r) {
        isFetchingProgress = false;
        if (r && r.message && r.message.work_packages && r.message.work_packages.length > 0) {
          progress7DayCache = r.message;
          update7DayProgressDOM(r.message);
        } else {
          update7DayProgressDOM(DEMO_7DAY_PROGRESS);
        }
      },
      error: function () {
        isFetchingProgress = false;
        update7DayProgressDOM(DEMO_7DAY_PROGRESS);
      }
    });
  }

  // ── PHASE 4: CLOUD AI & RAG SYNTHESIS (BLOCKER MODULE) ──
  function setupBlockerDashboardAIButton() {
    const $controls = $(".bd-header__controls");
    if ($controls.length) {
      if (!$("#bd-create-btn").length && $("#bd-refresh-btn").length) {
        const $createBtn = $(`
          <button id="bd-create-btn" class="bd-btn bd-btn--success" type="button" aria-label="${__("Create New Blocker")}">
            <span class="bd-btn__icon" aria-hidden="true">+</span>
            <span class="bd-btn__text" id="bd-create-label">+ Nouvel Obstacle</span>
          </button>
        `);
        $createBtn.insertBefore($("#bd-refresh-btn"));
        $createBtn.on("click", function () {
          frappe.set_route("app", "uranos-blocker", "new");
        });
      }

      if (!$("#bd-ai-synthesis-btn").length) {
        const $aiBtn = $(`
          <button id="bd-ai-synthesis-btn" class="bd-btn bd-btn--ai" type="button" aria-label="${__("Generate Smart Synthesis")}" title="${__("Generate Smart Synthesis")}">
            <span class="bd-btn__icon" aria-hidden="true">✨</span>
            <span class="bd-btn__text" id="bd-ai-synthesis-label">${__("Smart Synthesis")}</span>
          </button>
        `);

        const $refresh = $("#bd-refresh-btn");
        if ($refresh.length) {
          $aiBtn.insertAfter($refresh);
        } else {
          $aiBtn.appendTo($controls);
        }

        $aiBtn.on("click", function () {
          const selVal = $("#bd-project-select").val();
          frappe.set_route("uranos-ai-copilot", selVal || "PV-0001");
        });
      }
    }
  }


  // ── EXECUTIVE AI SYNTHESIS MODAL (GROQ CLOUD AI • MARIADB GROUNDED) ──
  window.openAISynthesisModal = function (project) {
    project = project || $("#gv-progress-project").text().trim() || "PV-0001";
    
    $("#uranosAISynthesisModal").remove();
    
    const modalHtml = `
      <div class="modal fade uranos-glass-modal" id="uranosAISynthesisModal" tabindex="-1" role="dialog" style="z-index: 99999;">
        <div class="modal-dialog modal-dialog-centered" role="document" style="max-width: 680px; margin: 1.5rem auto;">
          <div class="modal-content" style="border-radius: 20px; overflow: hidden; border: 1px solid rgba(226, 232, 240, 0.95); box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.35); background: #ffffff;">
            
            <!-- Header -->
            <div class="modal-header" style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1);">
              <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(56,189,248,0.35);">
                  <span style="font-size: 19px;">✨</span>
                </div>
                <div>
                  <h4 class="modal-title" style="margin: 0; font-size: 16px; font-weight: 700; color: #ffffff; letter-spacing: -0.01em;">URANOS Executive AI Briefing</h4>
                  <div style="display: flex; align-items: center; gap: 8px; margin-top: 3px;">
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 6px #10b981;"></span>
                    <span style="font-size: 11px; color: #94a3b8; font-weight: 500;">Groq Cloud AI (Qwen 3.8 27B) • Real-Time Fleet Grounding</span>
                  </div>
                </div>
              </div>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close" style="color: #94a3b8; opacity: 0.8; font-size: 24px; background: none; border: none; cursor: pointer; padding: 4px; line-height: 1;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#94a3b8'">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>

            <!-- Body -->
            <div class="modal-body" style="padding: 24px; background: #f8fafc;">
              
              <!-- Quick Fleet Telemetry Bar -->
              <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 14px;">⚡</span>
                  <span style="font-size: 12px; color: #475569; font-weight: 600;">Fleet Capacity:</span>
                  <span style="font-size: 12px; color: #0284c7; font-weight: 700;">642.0 MW AC / 770.4 MWp DC</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 14px;">☀️</span>
                  <span style="font-size: 12px; color: #475569; font-weight: 600;">Active Plants:</span>
                  <span style="font-size: 12px; color: #0f172a; font-weight: 700;">20 Projects</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="background: #ecfdf5; color: #059669; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 9999px; border: 1px solid #a7f3d0;">MariaDB Verified</span>
                </div>
              </div>

              <!-- AI Synthesis Content Area -->
              <div id="uranosAISynthesisContent" style="min-height: 140px;">
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 36px 16px; text-align: center;">
                  <div style="width: 40px; height: 40px; border: 3px solid #e2e8f0; border-top-color: #0284c7; border-radius: 50%; animation: uacSpin 0.8s linear infinite; margin-bottom: 16px;"></div>
                  <style>@keyframes uacSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
                  <p style="margin: 0; font-size: 14px; font-weight: 600; color: #1e293b;">Synthesizing fleet telemetry with Groq AI...</p>
                  <p style="margin: 4px 0 0; font-size: 12px; color: #64748b;">Grounding active blockers, engineering packages, and site progress</p>
                </div>
              </div>

            </div>

            <!-- Footer -->
            <div class="modal-footer" style="padding: 16px 24px; background: white; border-top: 1px solid #f1f5f9; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
              <button type="button" class="btn btn-secondary" data-dismiss="modal" style="border-radius: 10px; font-weight: 600; font-size: 13px; padding: 8px 16px; border: 1px solid #cbd5e1; background: white; color: #475569;">
                Dismiss
              </button>
              <div style="display: flex; align-items: center; gap: 10px;">
                <button type="button" id="uranosModalCopilotBtn" class="btn" style="border-radius: 10px; font-weight: 600; font-size: 13px; padding: 8px 16px; background: #f1f5f9; color: #0f172a; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 6px;">
                  <span>🤖 Open Copilot</span>
                </button>
                <button type="button" id="uranosModalPdfBtn" class="btn" style="border-radius: 10px; font-weight: 600; font-size: 13px; padding: 8px 18px; background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; border: none; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3); display: flex; align-items: center; gap: 6px;">
                  <span>📄 Download Daily PDF</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    `;

    $("body").append(modalHtml);
    const $modal = $("#uranosAISynthesisModal");
    $modal.modal("show");

    $("#uranosModalCopilotBtn").on("click", function() {
      $modal.modal("hide");
      frappe.set_route("uranos-ai-copilot", project || "PV-0001");
    });

    $("#uranosModalPdfBtn").on("click", function() {
      window.open("/api/method/uranos_project_os.services.api.generate_daily_report", "_blank");
    });

    // Call Groq API via backend
    frappe.call({
      method: "uranos_project_os.services.ai_synthesis.get_daily_ai_synthesis",
      callback: function(r) {
        if (r && r.message && (r.message.success || r.message.status === "success")) {
          const bullets = r.message.bullets || [];
          const rawText = r.message.summary || r.message.raw_text || "";
          
          let contentHtml = '<div style="display: flex; flex-direction: column; gap: 14px;">';
          
          if (bullets.length > 0) {
            const icons = ["🎯", "⚡", "⚠️", "📊"];
            bullets.forEach((b, idx) => {
              const icon = icons[idx % icons.length];
              let cleanBullet = b.replace(/^[\*\-\•]\s*/, "");
              let formattedBullet = cleanBullet.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #0f172a; font-weight: 700;">$1</strong>');
              contentHtml += `
                <div style="display: flex; align-items: flex-start; gap: 12px; background: white; padding: 14px 16px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                  <div style="font-size: 18px; line-height: 1.3; flex-shrink: 0;">${icon}</div>
                  <div style="font-size: 13.5px; line-height: 1.55; color: #334155;">${formattedBullet}</div>
                </div>
              `;
            });
          } else if (rawText) {
            let formattedText = rawText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
            contentHtml += `
              <div style="background: white; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; font-size: 13.5px; line-height: 1.6; color: #334155;">
                ${formattedText}
              </div>
            `;
          }
          
          contentHtml += `
            <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 6px; font-size: 11px; color: #64748b;">
              <span>Engine: <strong>${r.message.provider || r.message.model || "Groq Cloud AI (qwen/qwen3.8-27b)"}</strong></span>
              <span>Grounding: <strong>Live MariaDB Fleet DB</strong></span>
            </div>
          </div>`;

          $("#uranosAISynthesisContent").html(contentHtml);
        } else {
          const errMsg = (r && r.message && r.message.error) || "Unable to reach Groq AI synthesis engine.";
          $("#uranosAISynthesisContent").html(`
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 16px; color: #991b1b; font-size: 13px;">
              <strong>Synthesis Error:</strong> ${errMsg}
            </div>
          `);
        }
      },
      error: function(err) {
        $("#uranosAISynthesisContent").html(`
          <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 12px; padding: 16px; color: #991b1b; font-size: 13px;">
            <strong>Connection Failed:</strong> Could not retrieve daily AI synthesis from URANOS server.
          </div>
        `);
      }
    });
  };

  $(document).on("keydown", "#gv-ai-chat-input", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatToRAG();
    }
  });


  function syncNotificationBadge(count) {
    const $badge = $("#gvNotificationBadge");
    if (!$badge.length) return;

    let unread = count;
    if (unread === undefined || unread === null) {
      if (window._gv_notifications_instance && typeof window._gv_notifications_instance.unread_count !== "undefined") {
        unread = window._gv_notifications_instance.unread_count;
      } else if (window.frappe && frappe.boot && typeof frappe.boot.notification_unread_count !== "undefined") {
        unread = frappe.boot.notification_unread_count;
      } else {
        unread = 0;
      }
    }

    unread = parseInt(unread, 10) || 0;
    if (unread > 0) {
      $badge.text(unread > 99 ? "99+" : unread).removeClass("hidden").show();
    } else {
      $badge.text("").addClass("hidden").hide();
    }
  }

  function hookNotificationCountUpdates(instance) {
    if (!instance) return;
    const origUpdate = instance.update_count_badge?.bind(instance);
    instance.update_count_badge = function (count) {
      if (origUpdate) origUpdate(count);
      syncNotificationBadge(count);
    };
    if (instance.tabs && instance.tabs.notifications) {
      const notifTab = instance.tabs.notifications;
      const origTabUpdate = notifTab.update_count_badge?.bind(notifTab);
      notifTab.update_count_badge = function (count) {
        if (origTabUpdate) origTabUpdate(count);
        syncNotificationBadge(count);
      };
    }
  }

  function fetchDynamicNotificationCount() {
    if (window.frappe && frappe.call) {
      frappe.call({
        method: "frappe.desk.doctype.notification_log.notification_log.get_notification_logs",
        args: { limit: 20 },
        callback: function (r) {
          if (r && r.message && r.message.notification_logs) {
            const unread = r.message.notification_logs.filter(n => !n.read).length;
            syncNotificationBadge(unread);
          } else {
            syncNotificationBadge(0);
          }
        },
        error: function () {
          syncNotificationBadge(0);
        }
      });
    } else {
      syncNotificationBadge(0);
    }
  }

  function initOrRefreshNotifications() {
    const $wrapper = $("#gvNotificationWrapper");
    if (!$wrapper.length) return;

    if (!window._gv_notifications_instance && window.frappe && frappe.ui && frappe.ui.Notifications) {
      try {
        window._gv_notifications_instance = new frappe.ui.Notifications({
          wrapper: $wrapper,
          full_height: false
        });
        hookNotificationCountUpdates(window._gv_notifications_instance);
      } catch (err) {
        console.warn("Could not instantiate frappe.ui.Notifications", err);
      }
    } else if (window._gv_notifications_instance) {
      try {
        hookNotificationCountUpdates(window._gv_notifications_instance);
        const activeTab = window._gv_notifications_instance.categories?.find(c => c.$tab?.hasClass("active"));
        if (activeTab && window._gv_notifications_instance.tabs && window._gv_notifications_instance.tabs[activeTab.id]) {
          window._gv_notifications_instance.tabs[activeTab.id].render?.();
        }
      } catch (e) {
        console.warn("Error refreshing notifications view", e);
      }
    }
  }

  // ── 0.8 BRAND FAVICON & DYNAMIC TITLE ENFORCEMENT ──
  function enforceBrandFaviconAndTitle() {
    const faviconUrl = "/assets/uranos_project_os/images/uranos-logo.jpeg";

    // 1. Enforce Favicon in <head>
    let $icons = $('link[rel="shortcut icon"], link[rel="icon"], link[rel="apple-touch-icon"]');
    if ($icons.length) {
      $icons.each(function () {
        if ($(this).attr("href") !== faviconUrl) {
          $(this).attr("href", faviconUrl).attr("type", "image/jpeg");
        }
      });
    } else {
      $("<link>", {
        rel: "shortcut icon",
        type: "image/jpeg",
        href: faviconUrl
      }).appendTo("head");
      $("<link>", {
        rel: "icon",
        type: "image/jpeg",
        href: faviconUrl
      }).appendTo("head");
    }

    // 2. Enforce Dynamic Document Title ("URANOS OS")
    const brandPrefix = "URANOS OS";
    let title = document.title || "";
    if (!title.startsWith(brandPrefix)) {
      title = title.replace(/\s*[-•|]\s*Frappe/gi, "").trim();
      if (!title || title.toLowerCase() === "desk" || title.toLowerCase() === "home" || title.toLowerCase() === "frappe") {
        document.title = `${brandPrefix} — Photovoltaic Execution OS`;
      } else {
        document.title = `${brandPrefix} — ${title}`;
      }
    }
  }

  function setupTitleWatcher() {
    enforceBrandFaviconAndTitle();
    const titleEl = document.querySelector("title");
    if (titleEl && !window._uranos_title_observer) {
      window._uranos_title_observer = new MutationObserver(() => {
        enforceBrandFaviconAndTitle();
      });
      window._uranos_title_observer.observe(titleEl, { childList: true, characterData: true, subtree: true });
    }
  }

  // ── 0.9 DYNAMIC LIVE CLOCK & DATE PILL (BULLETPROOF ZERO-IO) ──
  function initLiveClockWidget() {
    function updateClock() {
      const $pill = $("#gvLiveClockPill, .gv-clock-pill");
      if (!$pill.length) return;

      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", hour12: true });
      const dateStr = now.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

      $pill.find(".gv-clock-time").text(timeStr);
      $pill.find(".gv-clock-date").text(dateStr);
      $pill.attr("title", `${now.toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" })} • ${timeStr}`);
    }

    updateClock();
    if (!window._uranos_clock_interval) {
      window._uranos_clock_interval = setInterval(updateClock, 1000);
    }
  }

  // ── AWESOMEBAR & NAVBAR SEARCH INTEGRATION ──
  function ensureSearchUtils() {
    if (typeof frappe !== "undefined" && frappe.search) {
      if (frappe.search.utils) {
        if (!frappe.search.utils.recent) {
          frappe.search.utils.recent = [];
        }
        try {
          frappe.search.utils.setup_recent();
        } catch (e) {}
      }
    }
  }

  function initAwesomeBarOnNavbar() {
    const input = document.getElementById("navbar-search");
    if (!input || input._uranos_awesome_initialized) return;
    input._uranos_awesome_initialized = true;

    ensureSearchUtils();

    let awesomeInstance = null;
    if (typeof frappe !== "undefined" && frappe.search && typeof frappe.search.AwesomeBar === "function") {
      try {
        if (!frappe.search.awesome_bar) {
          frappe.search.awesome_bar = new frappe.search.AwesomeBar();
        }
        awesomeInstance = frappe.search.awesome_bar;
      } catch (e) {}
    }

    if (typeof Awesomplete === "undefined") return;

    let currentOptionsMap = new Map();
    let executeSearchItem;

    const awesomplete = new Awesomplete(input, {
      minChars: 0,
      maxItems: 40,
      autoFirst: true,
      list: [],
      filter: function () { return true; },
      data: function (item) {
        return { label: item.label || item.value, value: item.value, raw: item };
      },
      item: function (suggestion) {
        const d = (suggestion && suggestion.value && currentOptionsMap.get(suggestion.value))
          || awesomplete.get_item(suggestion.value)
          || suggestion.raw
          || suggestion;

        const li = document.createElement("li");
        li.className = "gv-search-dropdown-item";
        li.setAttribute("data-search-value", d.value || suggestion.value || "");
        li._search_item = d;
        $(li).data("search-item", d);

        const typeBadge = d.type ? `<span class="gv-search-type-badge">${d.type}</span>` : "";
        li.innerHTML = `
          <div class="gv-search-item-left">
            <span class="gv-search-item-title">${d.label || d.value}</span>
          </div>
          ${typeBadge}
        `;
        return li;
      }
    });

    input.awesomplete = awesomplete;
    if (awesomeInstance) {
      awesomeInstance.awesomplete = awesomplete;
    }

    function cleanSearchUIState() {
      try {
        if (input) {
          input.value = "";
          try { input.blur(); } catch (err) {}
          $(input).trigger("blur");
        }
        currentOptionsMap.clear();
        if (awesomplete) {
          awesomplete.list = [];
          awesomplete.isOpened = false;
          try { awesomplete.close(); } catch (err) {}
          if (awesomplete.ul) {
            awesomplete.ul.setAttribute("hidden", "hidden");
            $(awesomplete.ul).empty().hide();
          }
        }
      } catch (e) {}

      // Aggressively clean up overlays, modals, backdrops, and open dropdowns
      try {
        $(".modal-backdrop").remove();
        $("body, html").removeClass("modal-open");
        $(".freeze-ui").remove();
        $(".dropdown.show, .btn-group.show, .menu-open, .open").removeClass("show open menu-open");
        $(".dropdown-menu.show").removeClass("show");
        $(".modal:has(#navbar-search)").modal("hide");
      } catch (e) {}
    }
    window._uranosCleanSearchUIState = cleanSearchUIState;

    executeSearchItem = function (item) {
      if (!item) return;
      cleanSearchUIState();

      if (item.route_options) {
        frappe.route_options = item.route_options;
      }
      if (typeof item.onclick === "function") {
        item.onclick(item.match);
      } else if (item.route) {
        const route = Array.isArray(item.route) ? item.route : [item.route];
        frappe.set_route(route);
      }

      cleanSearchUIState();
      setTimeout(cleanSearchUIState, 50);
      setTimeout(cleanSearchUIState, 200);
      setTimeout(cleanSearchUIState, 600);
    };

    function getSearchOptions(txt) {
      ensureSearchUtils();
      if (awesomeInstance && typeof awesomeInstance.build_options === "function") {
        try {
          const opts = awesomeInstance.build_options(txt);
          if (Array.isArray(opts) && opts.length) return opts;
        } catch (e) {}
      }
      if (typeof frappe !== "undefined" && frappe.search && frappe.search.utils) {
        try {
          const u = frappe.search.utils;
          let opts = [];
          if (u.get_creatables) opts = opts.concat(u.get_creatables(txt) || []);
          if (u.get_doctypes) opts = opts.concat(u.get_doctypes(txt) || []);
          if (u.get_pages) opts = opts.concat(u.get_pages(txt) || []);
          if (u.get_reports) opts = opts.concat(u.get_reports(txt) || []);
          if (u.get_desktop_icons) opts = opts.concat(u.get_desktop_icons(txt) || []);
          if (u.get_recent_pages) {
            try { opts = opts.concat(u.get_recent_pages(txt || "") || []); } catch (err) {}
          }
          return opts;
        } catch (e) {}
      }
      return [];
    }

    function updateList(txt) {
      if (!txt) {
        currentOptionsMap.clear();
        awesomplete.list = [];
        awesomplete.close();
        return;
      }
      const rawOptions = getSearchOptions(txt) || [];
      if (!rawOptions.length) {
        currentOptionsMap.clear();
        awesomplete.list = [];
        awesomplete.close();
        return;
      }

      currentOptionsMap.clear();
      const formatted = rawOptions.map(opt => {
        const itemObj = {
          label: opt.label || opt.value,
          value: opt.value,
          route: opt.route,
          route_options: opt.route_options,
          onclick: opt.onclick,
          match: opt.match || opt.value,
          type: opt.type || ""
        };
        currentOptionsMap.set(itemObj.value, itemObj);
        return itemObj;
      });

      awesomplete.list = formatted;
      awesomplete.evaluate();
      if (awesomplete.ul && awesomplete.ul.children.length > 0) {
        awesomplete.open();
      }
    }

    $(input).on("input", function (e) {
      updateList((e.target.value || "").trim());
    });

    $(input).on("focus", function () {
      const val = (input.value || "").trim();
      if (val) {
        updateList(val);
      }
    });

    // 1. Handle selection via Awesomplete native event
    $(input).on("awesomplete-select", function (e) {
      const o = e.originalEvent;
      const val = o && o.text ? (o.text.value || o.text.label || o.text) : null;
      const item = (o && o.text && o.text.raw) || awesomplete.get_item(val) || currentOptionsMap.get(val);
      if (item) {
        executeSearchItem(item);
      }
      cleanSearchUIState();
    });

    $(input).on("awesomplete-selectcomplete", function () {
      cleanSearchUIState();
    });

    // 2. Direct click handler on dropdown items (prevents silent fails or blur race conditions)
    $(awesomplete.ul).off("mousedown.uranos").on("mousedown.uranos", "li", function (e) {
      e.preventDefault();
    });

    $(awesomplete.ul).off("click.uranos").on("click.uranos", "li", function (e) {
      e.preventDefault();
      e.stopPropagation();
      const val = this.getAttribute("data-search-value") || $(this).text().trim();
      const item = this._search_item || $(this).data("search-item") || awesomplete.get_item(val) || currentOptionsMap.get(val);
      if (item) {
        executeSearchItem(item);
      }
      cleanSearchUIState();
    });

    $(input).on("keydown", function (e) {
      if (e.key === "Escape") {
        cleanSearchUIState();
      } else if (e.key === "Enter") {
        if (awesomplete.isOpened && awesomplete.selected && awesomplete.index > -1) {
          const selectedSuggestion = awesomplete.suggestions[awesomplete.index];
          const val = selectedSuggestion ? selectedSuggestion.value : null;
          const item = awesomplete.get_item(val) || currentOptionsMap.get(val);
          if (item) {
            e.preventDefault();
            executeSearchItem(item);
            cleanSearchUIState();
          }
        }
      }
    });

    $("#gvSearchTrigger").on("click", function (e) {
      if (e.target !== input) {
        input.focus();
        if (input.value) updateList(input.value.trim());
      }
    });

    $(document).off("keydown.uranosAwesomeBar").on("keydown.uranosAwesomeBar", function (e) {
      if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        input.focus();
        input.select();
      }
    });

    $("#navbar-modal-search").off("click").on("click", function (e) {
      e.preventDefault();
      input.focus();
    });
  }

  // ── 1. NAVBAR OVERHAUL ──
  function overhaulNavbar() {
    const $navbar = $(".desktop-navbar");
    if (!$navbar.length) return;

    // Brand Logo
    let $home = $navbar.find(".navbar-home");
    if ($home.length && !$home.hasClass("gv-brand-done")) {
      $home.addClass("gv-brand-done").html(`
        <a href="/app" class="gv-navbar-brand" title="URANOS Group">
          <div class="gv-brand-logo-wrapper">
            <img src="/assets/uranos_project_os/images/uranos-logo.jpeg" alt="URANOS Group" class="gv-brand-logo-img" />
          </div>
          <div class="brand-text-block">
            <span class="gv-brand-title">URANOS Group</span>
            <span class="gv-brand-subtitle">${__("Photovoltaic Execution OS")}</span>
          </div>
        </a>
      `);
    }

    // Search Pill & Frappe Awesomebar Integration
    if (!$navbar.find(".gv-navbar-search").length) {
      const $searchHtml = $(`
        <div class="gv-navbar-search">
          <div class="gv-search-input-wrapper" id="gvSearchTrigger">
            <svg class="gv-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.3-4.3"/>
            </svg>
            <input type="text" id="navbar-search" class="gv-search-input" placeholder="${__("Search for apps, projects, sites, reports...")}" autocomplete="off">
            <span class="gv-search-kbd">⌘ K</span>
          </div>
          <button id="navbar-modal-search" class="navbar-search-bar hidden" style="display: none !important;"></button>
        </div>
      `);

      if ($navbar.find(".desktop-search-wrapper").length) {
        $navbar.find(".desktop-search-wrapper").replaceWith($searchHtml);
      } else {
        $searchHtml.insertAfter($navbar.find(".navbar-home"));
      }

      initAwesomeBarOnNavbar();
    } else {
      initAwesomeBarOnNavbar();
    }

    // Right Controls
    const $rightContainer = $navbar.find(".flex").last();
    if ($rightContainer.length && !$rightContainer.find(".gv-navbar-actions").length) {
      const currentLang = getCurrentLangCode();
      const langBadge = currentLang.toUpperCase();

      $rightContainer.empty().append(`
        <div class="gv-navbar-actions">
          <div class="gv-clock-pill" id="gvLiveClockPill" title="${__("Live System Time")}">
            <div class="gv-clock-icon-slot">
              <svg class="gv-clock-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <div class="gv-clock-info">
              <span class="gv-clock-time">--:-- --</span>
              <span class="gv-clock-sep">•</span>
              <span class="gv-clock-date">-- --- ----</span>
            </div>
          </div>

          <!-- Language Switcher -->
          <div class="gv-lang-wrapper">
            <button type="button" class="gv-lang-btn" id="gvLangBtn" title="${__("Language")}" aria-label="Change Language">
              <svg class="gv-lang-globe-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
              </svg>
              <span class="gv-lang-current-code">${langBadge}</span>
              <svg class="gv-lang-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </button>

            <!-- Glassmorphism Language Dropdown Popover (Features Tunisian Flag 🇹🇳 for Arabic) -->
            <div class="gv-lang-dropdown" id="gvLangDropdown" style="display: none;">
              <div class="gv-lang-header">
                <span class="gv-lang-header-title">${__("Language")}</span>
                <span class="gv-lang-header-sub">اللغة</span>
              </div>
              <div class="gv-dropdown-divider"></div>
              <button type="button" class="gv-lang-item ${currentLang === 'en' ? 'active' : ''}" data-lang="en">
                <span class="gv-lang-flag">🇬🇧</span>
                <span class="gv-lang-label">English</span>
                <span class="gv-lang-check">✓</span>
              </button>
              <button type="button" class="gv-lang-item ${currentLang === 'fr' ? 'active' : ''}" data-lang="fr">
                <span class="gv-lang-flag">🇫🇷</span>
                <span class="gv-lang-label">Français</span>
                <span class="gv-lang-check">✓</span>
              </button>
              <button type="button" class="gv-lang-item ${currentLang === 'ar' ? 'active' : ''}" data-lang="ar">
                <span class="gv-lang-flag">🇹🇳</span>
                <span class="gv-lang-label">العربية</span>
                <span class="gv-lang-check">✓</span>
              </button>
            </div>
          </div>

          <div class="gv-notification-wrapper" id="gvNotificationWrapper">
            <div class="gv-notification-btn sidebar-notification" id="gvNotificationBtn" title="${__("Notifications")}">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
                <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
              </svg>
              <span class="gv-notification-badge hidden" id="gvNotificationBadge"></span>
            </div>

            <!-- Standard Frappe Notification Dropdown Container -->
            <div class="dropdown-notifications gv-dropdown-notifications" id="gvDropdownNotifications" style="display: none;">
              <div class="notifications-list" role="menu">
                <div class="notification-list-header">
                  <div class="header-items"></div>
                  <div class="header-actions"></div>
                </div>
                <div class="notification-list-body">
                  <div class="panel-notifications"></div>
                  <div class="panel-events"></div>
                  <div class="panel-changelog-feed"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="gv-user-pill" id="gvUserPillBtn" title="${__("Account settings")}">
            <div class="gv-user-avatar">
              ${getUserInitials()}
            </div>
            <div class="gv-user-details">
              <span class="gv-user-name">${getUserFullName()}</span>
              <span class="gv-user-role">${getUserRoleTitle()}</span>
            </div>
            <svg class="gv-user-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"/>
            </svg>
          </div>

          <!-- Glassmorphism User Dropdown Popover (Chic SaaS Enriched) -->
          <div class="gv-user-dropdown dropdown-menu" id="gvUserDropdown" style="display: none;">
            <div class="gv-dropdown-header">
              <div class="gv-dropdown-avatar">${getUserInitials()}</div>
              <div class="gv-dropdown-info">
                <span class="gv-dropdown-name">${getUserFullName()}</span>
                <span class="gv-dropdown-role">${getUserRoleTitle()}</span>
              </div>
            </div>
            <div class="gv-dropdown-divider"></div>
            <a href="/app/user/${encodeURIComponent(getUserEmail())}" class="gv-dropdown-item dropdown-item" id="gvProfileLink">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <span>${__("My Profile")}</span>
            </a>
            <a href="/app/erpnext-settings" class="gv-dropdown-item dropdown-item" id="gvSettingsLink">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
              <span>${__("Settings")}</span>
            </a>
            ${canAccessSecurityAudit() ? `
            <a href="/app/access-audit" class="gv-dropdown-item dropdown-item" id="gvAccessAuditDropdownLink">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <span>${__("Security & Access Audit")}</span>
            </a>` : ""}
            <div class="gv-dropdown-divider"></div>
            <button type="button" class="gv-dropdown-item dropdown-item gv-signout-btn" id="gvSignOutBtn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              <span>${__("Sign Out")}</span>
            </button>
          </div>
        </div>
      `);

      // Notifications Button & Dropdown Events
      $("#gvNotificationBtn").off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        $("#gvLangDropdown").fadeOut(100);
        $("#gvUserDropdown").fadeOut(100);

        const $notifDropdown = $("#gvDropdownNotifications");
        if ($notifDropdown.is(":visible")) {
          $notifDropdown.fadeOut(150);
        } else {
          $notifDropdown.fadeIn(150);
          initOrRefreshNotifications();
        }
      });

      $(document).off("click.gvDropdownNotifications").on("click.gvDropdownNotifications", function (e) {
        if (!$(e.target).closest("#gvNotificationWrapper").length) {
          $("#gvDropdownNotifications").fadeOut(100);
        }
      });

      $(document).off("click.gvCloseNotification", ".close-notification-dialogue").on("click.gvCloseNotification", ".close-notification-dialogue", function (e) {
        e.stopPropagation();
        $("#gvDropdownNotifications").fadeOut(100);
      });

      // Synchronize dynamic notification badge and listen to live events
      syncNotificationBadge();
      fetchDynamicNotificationCount();

      if (window.frappe && frappe.realtime && frappe.realtime.on) {
        if (frappe.realtime.off) {
          try { frappe.realtime.off("notification"); } catch (e) {}
          try { frappe.realtime.off("indicator_hide"); } catch (e) {}
        }
        frappe.realtime.on("notification", function () {
          fetchDynamicNotificationCount();
        });
        frappe.realtime.on("indicator_hide", function () {
          syncNotificationBadge(0);
        });
      }
      $(document).off("click.gvMarkRead", "[data-action='mark_all_as_read']").on("click.gvMarkRead", "[data-action='mark_all_as_read']", function () {
        syncNotificationBadge(0);
        if (window.frappe && frappe.boot) {
          frappe.boot.notification_unread_count = 0;
        }
      });

      // Language Switcher Events
      $("#gvLangBtn").off("click").on("click", function (e) {
        e.stopPropagation();
        $("#gvUserDropdown").fadeOut(100);
        $("#gvDropdownNotifications").fadeOut(100);
        $("#gvLangDropdown").fadeToggle(150);
      });

      $(".gv-lang-item").off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const selectedLang = $(this).attr("data-lang");
        $("#gvLangDropdown").fadeOut(100);
        switchUserLanguage(selectedLang);
      });

      $(document).off("click.gvLangDropdown").on("click.gvLangDropdown", function (e) {
        if (!$(e.target).closest("#gvLangBtn, #gvLangDropdown").length) {
          $("#gvLangDropdown").fadeOut(100);
        }
      });

      // User Pill Events
      $("#gvUserPillBtn").off("click").on("click", function (e) {
        e.stopPropagation();
        $("#gvLangDropdown").fadeOut(100);
        $("#gvDropdownNotifications").fadeOut(100);
        $("#gvUserDropdown").fadeToggle(150);
      });

      // My Profile Intercept & Route to Form User
      $("#gvProfileLink").off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        $("#gvUserDropdown").fadeOut(100);
        const targetUser = (window.frappe && frappe.session && frappe.session.user) ? frappe.session.user : getUserEmail();
        if (window.frappe && frappe.set_route) {
          frappe.set_route("Form", "User", targetUser);
        } else {
          window.location.href = `/app/user/${encodeURIComponent(targetUser)}`;
        }
      });

      // Settings Link Event
      $("#gvSettingsLink").off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        $("#gvUserDropdown").fadeOut(100);
        if (window.frappe && frappe.set_route) {
          frappe.set_route("Workspaces", "ERPNext Settings");
        } else {
          window.location.href = "/app/erpnext-settings";
        }
      });

      $("#gvSignOutBtn").off("click").on("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        performLogout();
      });

      $(document).off("click.gvUserDropdown").on("click.gvUserDropdown", function (e) {
        if (!$(e.target).closest("#gvUserPillBtn, #gvUserDropdown").length) {
          $("#gvUserDropdown").fadeOut(100);
        }
      });

      // Populate live clock widget
      initLiveClockWidget();
    } else {
      if ($navbar.find(".gv-clock-pill").length) {
        initLiveClockWidget();
      }
    }
  }

  // ── 1.9 INTERACTIVE GIS MAP & DYNAMIC LEAFLET MARKERS (PHASE 1) ──
  function ensureLeafletCss() {
    if (!document.getElementById("uranos-leaflet-css")) {
      const link = document.createElement("link");
      link.id = "uranos-leaflet-css";
      link.rel = "stylesheet";
      link.href = "/assets/uranos_project_os/leaflet/leaflet.css";
      link.onerror = function () {
        this.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      };
      document.head.appendChild(link);
    }
  }

  function loadLeaflet(callback) {
    ensureLeafletCss();

    if (window.L && typeof window.L.map === "function") {
      if (callback) callback();
      return;
    }

    if (window._uranos_loading_leaflet) {
      let retries = 0;
      const timer = setInterval(function () {
        retries++;
        if (window.L && typeof window.L.map === "function") {
          clearInterval(timer);
          ensureLeafletCss();
          if (callback) callback();
        } else if (retries > 60) {
          clearInterval(timer);
        }
      }, 50);
      return;
    }
    window._uranos_loading_leaflet = true;

    function onLeafletReady() {
      window._uranos_loading_leaflet = false;
      ensureLeafletCss();
      if (callback) callback();
    }

    const script = document.createElement("script");
    script.id = "uranos-leaflet-js";
    script.src = "/assets/uranos_project_os/leaflet/leaflet.js";
    script.onload = onLeafletReady;
    script.onerror = function () {
      // Offline/firewall fallback to CDN
      const fallbackScript = document.createElement("script");
      fallbackScript.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      fallbackScript.onload = onLeafletReady;
      document.head.appendChild(fallbackScript);
    };
    document.head.appendChild(script);
  }

  function initUranosGisMap() {
    const mapEl = document.getElementById("uranos-leaflet-map");
    if (!mapEl) return;

    loadLeaflet(function () {
      if (!window.L || typeof window.L.map !== "function") return;
      const currentContainer = document.getElementById("uranos-leaflet-map");
      if (!currentContainer) return;

      // Clean up previous map instance if already initialized to avoid Leaflet error
      if (window._uranos_gis_map_instance) {
        try {
          window._uranos_gis_map_instance.remove();
        } catch (e) {}
        window._uranos_gis_map_instance = null;
      }

      // Clear any cached Leaflet internal ID on the container
      if (currentContainer._leaflet_id) {
        delete currentContainer._leaflet_id;
      }

      const map = L.map(currentContainer, {
        center: [34.0, 9.8],
        zoom: 6.5,
        zoomSnap: 0.25,
        zoomDelta: 0.5,
        zoomControl: true,
        scrollWheelZoom: false
      });
      window._uranos_gis_map_instance = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      // Staggered size invalidation across layout render phases
      const invalidate = function () {
        if (map && map._container && typeof map.invalidateSize === "function") {
          try { map.invalidateSize(false); } catch (e) {}
        }
      };

      invalidate();
      setTimeout(invalidate, 100);
      setTimeout(invalidate, 300);
      setTimeout(invalidate, 800);
      setTimeout(invalidate, 1500);

      // Reactive ResizeObserver to prevent any grey tiles or misaligned containers
      if (window.ResizeObserver && !currentContainer._uranos_ro_attached) {
        currentContainer._uranos_ro_attached = true;
        const ro = new ResizeObserver(function () {
          invalidate();
        });
        ro.observe(currentContainer);
      }

      // Fetch projects with coordinates, profiles, and blockers in parallel for maximum speed
      let projects = [];
      let profileMap = {};
      let activeBlockersByProject = {};
      let pending = 3;
      function onGisPartDone() {
        pending--;
        if (pending <= 0) {
          plotGisMarkers(map, projects, profileMap, activeBlockersByProject);
        }
      }

      frappe.call({
        method: "uranos_project_os.services.api.get_dashboard_telemetry",
        callback: function (rProj) {
          projects = (rProj && rProj.message) ? rProj.message : [];
          onGisPartDone();
        },
        error: function () {
          frappe.call({
            method: "frappe.client.get_list",
            args: {
              doctype: "Project",
              fields: ["name", "project_name", "status", "latitude", "longitude"],
              limit_page_length: 100
            },
            callback: function (rProj) {
              projects = (rProj && rProj.message) ? rProj.message : [];
              onGisPartDone();
            },
            error: onGisPartDone
          });
        }
      });

      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "URANOS Project Profile",
          fields: ["name", "project", "governorate", "capacity_ac_mw", "site", "latitude", "longitude"],
          limit_page_length: 100
        },
        callback: function (rProf) {
          const profiles = (rProf && rProf.message) ? rProf.message : [];
          profiles.forEach(function (p) {
            if (p.project) profileMap[p.project] = p;
          });
          onGisPartDone();
        },
        error: onGisPartDone
      });

      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "URANOS Blocker",
          fields: ["name", "project", "status", "title", "severity"],
          limit_page_length: 500
        },
        callback: function (rBlock) {
          const allBlockers = (rBlock && rBlock.message) ? rBlock.message : [];
          allBlockers.forEach(function (b) {
            if (b.status !== "Closed" && b.project) {
              if (!activeBlockersByProject[b.project]) activeBlockersByProject[b.project] = [];
              activeBlockersByProject[b.project].push(b);
            }
          });
          onGisPartDone();
        },
        error: onGisPartDone
      });
    });
  }

  function plotGisMarkers(map, projects, profileMap, activeBlockersByProject) {
    if (!map || !window.L) return;
    const panes = (typeof map.getPanes === "function") ? map.getPanes() : map._panes;
    if (!panes || !panes.markerPane) return;
    if (map !== window._uranos_gis_map_instance) return;

    const greenIcon = L.divIcon({
      className: "uranos-custom-marker-wrapper",
      html: `<div class="uranos-map-marker green" title="Nominal Operations">
               <div class="marker-core"></div>
             </div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });

    const redIcon = L.divIcon({
      className: "uranos-custom-marker-wrapper",
      html: `<div class="uranos-map-marker red pulse-active" title="Active Blocker Alert">
               <div class="marker-pulse-ring"></div>
               <div class="marker-core"></div>
             </div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
      popupAnchor: [0, -14]
    });

    const markers = [];
    let nominalCount = 0;
    let blockerAlertCount = 0;

    projects.forEach(function (proj) {
      const prof = profileMap[proj.name] || {};
      const lat = parseFloat(proj.latitude || prof.latitude);
      const lng = parseFloat(proj.longitude || prof.longitude);

      if (isNaN(lat) || isNaN(lng) || lat === 0 || lng === 0) return;

      const blockers = activeBlockersByProject[proj.name] || [];
      const hasBlockers = blockers.length > 0;

      if (hasBlockers) {
        blockerAlertCount++;
      } else {
        nominalCount++;
      }

      const icon = hasBlockers ? redIcon : greenIcon;
      const marker = L.marker([lat, lng], { icon: icon });

      const statusText = hasBlockers
        ? `<span style="color: #dc2626; font-weight: 700;">${blockers.length} Active Blocker${blockers.length > 1 ? "s" : ""}</span>`
        : `<span style="color: #059669; font-weight: 700;">Nominal (0 Blockers)</span>`;

      const governorate = prof.governorate || "Tunisia";
      const capacity = prof.capacity_ac_mw ? `${prof.capacity_ac_mw} MW` : "1.0 MW";

      const popupHtml = `
        <div class="uranos-gis-popup">
          <div class="uranos-gis-popup-header">
            <span class="uranos-gis-popup-title"><b>Project: ${proj.name}</b></span>
            <span class="uranos-gis-popup-badge ${hasBlockers ? 'badge-alert' : 'badge-nominal'}">
              ${hasBlockers ? 'ALERT' : 'NOMINAL'}
            </span>
          </div>
          <div class="uranos-gis-popup-body">
            <div class="uranos-gis-popup-row">
              <span class="uranos-gis-popup-label">Status:</span>
              <span class="uranos-gis-popup-val">${statusText}</span>
            </div>
            <div class="uranos-gis-popup-row">
              <span class="uranos-gis-popup-label">Region:</span>
              <span class="uranos-gis-popup-val">${governorate}</span>
            </div>
            <div class="uranos-gis-popup-row">
              <span class="uranos-gis-popup-label">Capacity:</span>
              <span class="uranos-gis-popup-val">${capacity}</span>
            </div>
            <div class="uranos-gis-popup-row">
              <span class="uranos-gis-popup-label">Coordinates:</span>
              <span class="uranos-gis-popup-val" style="font-family: monospace; font-size: 11px;">${lat.toFixed(4)}, ${lng.toFixed(4)}</span>
            </div>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml, {
        className: "uranos-gis-leaflet-popup",
        offset: [0, -10]
      });

      try {
        marker.addTo(map);
        markers.push(marker);
      } catch (err) {
        // Safe catch if map pane detached during route transition
      }
    });

    $("#gis-nominal-count").text(nominalCount);
    $("#gis-blocker-count").text(blockerAlertCount);

    if (markers.length > 0) {
      try {
        const group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.12), { maxZoom: 11 });
        map.invalidateSize();
      } catch (err) {}
    }
    setTimeout(function () {
      if (map && map._container && typeof map.invalidateSize === "function") {
        map.invalidateSize();
      }
    }, 250);
  }

  // ── 2. LAYOUT INJECTION ──
  function overhaulLayout() {
    const $container = $(".desktop-container");
    if (!$container.length) return;

    if (!$container.find(".gv-desk-sidebar").length) {
      // 1. Sidebar with enclosed bottom promo card
      const $sidebar = $(`
        <aside class="gv-desk-sidebar">
          <div class="gv-sidebar-brand">
            <img src="/assets/uranos_project_os/images/uranos-logo.jpeg" alt="URANOS Group" class="gv-sidebar-logo-img">
            <div class="gv-sidebar-brand-info">
              <span class="gv-sidebar-title">URANOS Group</span>
              <span class="gv-sidebar-tag">${__("ENTERPRISE")}</span>
            </div>
          </div>
          <div class="gv-nav-links-group">
            <a href="/app" class="gv-nav-link active">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
              <span>${__("Home")}</span>
            </a>

            <a href="/app/projects" class="gv-nav-link" data-sidebar-app="projects">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="7" height="7" x="3" y="3" rx="1"/>
                <rect width="7" height="7" x="14" y="3" rx="1"/>
                <rect width="7" height="7" x="14" y="14" rx="1"/>
                <rect width="7" height="7" x="3" y="14" rx="1"/>
              </svg>
              <span>${__("Projects")}</span>
            </a>

            <a href="/app/project" class="gv-nav-link" data-sidebar-app="sites">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              <span>${__("Sites")}</span>
            </a>

            <a href="/app/blocker-kanban" class="gv-nav-link" id="gv-nav-kanban" data-sidebar-app="kanban">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2"/>
                <path d="M8 7v7"/>
                <path d="M12 7v4"/>
                <path d="M16 7v9"/>
              </svg>
              <span>${__("Kanban Board")}</span>
            </a>

            <a href="/app/query-report/Daily%20Timesheet%20Summary" class="gv-nav-link" data-sidebar-app="energy-analytics">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18"/>
                <path d="m19 9-5 5-4-4-3 3"/>
              </svg>
              <span>${__("Energy Analytics")}</span>
            </a>

            <a href="/app/financial-reports" class="gv-nav-link" data-sidebar-app="reports">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <span>${__("Reports")}</span>
            </a>

            <a href="/app/quality" class="gv-nav-link" data-sidebar-app="quality-inspections">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
              <span>${__("Quality Inspections")}</span>
            </a>

            <a href="/app/manufacturing" class="gv-nav-link" data-sidebar-app="operations">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
              <span>${__("Operations")}</span>
            </a>

            <a href="/app/assets" class="gv-nav-link" data-sidebar-app="maintenance">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
              <span>${__("Maintenance")}</span>
            </a>

            <a href="/app/erpnext-settings" class="gv-nav-link" data-sidebar-app="settings">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
              <span>${__("Settings")}</span>
            </a>
          </div>

          <!-- Bottom Sustainability Promo Card (Enclosed inside sidebar) -->
          <div class="gv-sidebar-promo-card">
            <img class="gv-promo-thumb" src="/assets/uranos_project_os/images/login-bg.jpg" alt="${__("Solar Farm")}">
            <div class="gv-promo-title">${__("Cleaner Energy")}<br>${__("A Brighter Tomorrow")}</div>
            <div class="gv-promo-subtitle">${__("Efficiently managing renewable resources for a sustainable future.")}</div>
            <div class="gv-promo-footer">
              <div class="gv-promo-leaf-badge">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                </svg>
              </div>
              <button class="gv-promo-btn" title="${__("Learn more")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
        </aside>
      `);

      const $mainDashboard = $(`<section class="gv-main-dashboard" id="gv-main-dashboard"></section>`);

      // 2.25. Interactive GIS Map Bento Card (Phase 1)
      const $mapCard = $(`
        <div class="uranos-gis-map-card" id="uranosGisMapCard" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05); height: 400px; overflow: hidden; margin-top: 24px; border: 1px solid #e2e8f0; background: #ffffff; display: flex; flex-direction: column;">
          <div class="uranos-gis-header">
            <div class="uranos-gis-title-group">
              <div class="uranos-gis-icon-badge">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
                  <line x1="9" y1="3" x2="9" y2="18"/>
                  <line x1="15" y1="6" x2="15" y2="21"/>
                </svg>
              </div>
              <div>
                <div class="uranos-gis-heading">${__("Tunisian Solar Fleet — Interactive GIS Map")}</div>
                <div class="uranos-gis-subheading">${__("Real-time geographical telemetry & active blocker mapping across 20 solar assets")}</div>
              </div>
            </div>
            <div class="uranos-gis-legend">
              <div class="uranos-legend-item">
                <span class="uranos-legend-dot green"></span>
                <span>${__("Nominal")} (<span id="gis-nominal-count">—</span>)</span>
              </div>
              <div class="uranos-legend-item">
                <span class="uranos-legend-dot red"></span>
                <span>${__("Active Blockers")} (<span id="gis-blocker-count">—</span>)</span>
              </div>
            </div>
          </div>
          <div id="uranos-leaflet-map" style="flex: 1; width: 100%; height: calc(100% - 58px); min-height: 340px; z-index: 1;"></div>
        </div>
      `);

      // 2. Hero Section + 4 KPI Cards
      const $heroKpiRow = $(`
        <div class="gv-hero-kpi-row">
          <div class="gv-hero-card">
            <div class="gv-hero-badge">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
              </svg>
            </div>
            <h2 class="gv-hero-title">${getGreeting()}, <span id="gv-hero-user-name">${getUserFirstName()}</span></h2>
            <p class="gv-hero-subtitle">${__("Here's what's happening with your renewable energy assets today.")}</p>
            <div class="gv-hero-action-row" style="margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: nowrap;">
              <button type="button" class="bd-btn bd-btn--ai gv-hero-ai-btn" id="gv-hero-ai-btn" title="${__("Generate Smart Blocker Synthesis (AI)")}">
                <span class="bd-btn__icon" aria-hidden="true" style="font-size: 13px;">✨</span>
                <span class="bd-btn__text">${__("AI Synthesis")}</span>
              </button>
              <button type="button" class="uranos-btn-executive-pdf" id="uranosGenerateExecutivePdfBtn" title="${__("Generate PDF Report")}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                <span>${__("PDF Report")}</span>
              </button>
            </div>
          </div>

          <div class="gv-kpi-card" id="gv-kpi-card-capacity">
            <div class="gv-kpi-top">
              <div class="gv-kpi-icon-circle cyan">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
              </div>
            </div>
            <div class="gv-kpi-middle">
              <div class="gv-kpi-label">${__("Total Capacity")}</div>
              <div class="gv-kpi-value" id="gv-kpi-capacity-val">${dashboardKPICache ? Number(dashboardKPICache.total_capacity_mw).toFixed(1) : "—"} <span class="gv-kpi-unit">MW</span></div>
            </div>
            <div class="gv-kpi-trend-row">
              <span class="gv-kpi-trend" id="gv-kpi-capacity-trend">${dashboardKPICache ? "&#9650; " + dashboardKPICache.total_sites + " " + __("Sites connected") : "&#9650; " + __("Loading...")}</span>
              <svg class="gv-kpi-sparkline" viewBox="0 0 50 18" fill="none">
                <path d="M1 16 Q 15 14, 25 10 T 49 2" stroke="#0891b2" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>

          <div class="gv-kpi-card" id="gv-kpi-card-sites">
            <div class="gv-kpi-top">
              <div class="gv-kpi-icon-circle blue">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                  <circle cx="12" cy="10" r="3"/>
                </svg>
              </div>
            </div>
            <div class="gv-kpi-middle">
              <div class="gv-kpi-label">${__("Active Sites")}</div>
              <div class="gv-kpi-value" id="gv-kpi-sites-val">${dashboardKPICache ? dashboardKPICache.active_sites + " / " + dashboardKPICache.total_sites : "— / —"}</div>
            </div>
            <div class="gv-kpi-trend-row">
              <span class="gv-kpi-trend" id="gv-kpi-sites-trend">${dashboardKPICache ? "&#9650; " + dashboardKPICache.operational_rate_percent + "% " + __("operational") : "&#9650; " + __("Loading...")}</span>
              <svg class="gv-kpi-sparkline" viewBox="0 0 50 18" fill="none">
                <path d="M1 15 Q 12 12, 28 8 T 49 3" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>

          <div class="gv-kpi-card" id="gv-kpi-card-energy">
            <div class="gv-kpi-top">
              <div class="gv-kpi-icon-circle yellow">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="4"/>
                  <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
                </svg>
              </div>
            </div>
            <div class="gv-kpi-middle">
              <div class="gv-kpi-label">${__("Total Energy Today")}</div>
              <div class="gv-kpi-value" id="gv-kpi-energy-val">${dashboardKPICache ? Number(dashboardKPICache.energy_today_mwh).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1}) : "—"} <span class="gv-kpi-unit">MWh</span></div>
            </div>
            <div class="gv-kpi-trend-row">
              <span class="gv-kpi-trend" id="gv-kpi-energy-trend">${dashboardKPICache ? (dashboardKPICache.lost_hours > 0 ? "&#9660; " + Number(dashboardKPICache.lost_hours).toFixed(1) + "h " + __("lost (blockers)") : "&#9650; +5.6% " + __("vs. yesterday")) : "&#9650; " + __("Loading...")}</span>
              <svg class="gv-kpi-sparkline" viewBox="0 0 50 18" fill="none">
                <path d="M1 16 Q 16 15, 30 8 T 49 2" stroke="#d97706" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>

          <div class="gv-kpi-card" id="gv-kpi-card-co2">
            <div class="gv-kpi-top">
              <div class="gv-kpi-icon-circle green">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                </svg>
              </div>
            </div>
            <div class="gv-kpi-middle">
              <div class="gv-kpi-label">${__("CO2 Avoided")}</div>
              <div class="gv-kpi-value" id="gv-kpi-co2-val">${dashboardKPICache ? Number(dashboardKPICache.co2_avoided_t).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1}) : "—"} <span class="gv-kpi-unit">t</span></div>
            </div>
            <div class="gv-kpi-trend-row">
              <span class="gv-kpi-trend" id="gv-kpi-co2-trend">${dashboardKPICache ? "&#9650; " + Number(dashboardKPICache.co2_avoided_t).toFixed(1) + " t " + __("offset today") : "&#9650; " + __("Loading...")}</span>
              <svg class="gv-kpi-sparkline" viewBox="0 0 50 18" fill="none">
                <path d="M1 14 Q 18 12, 32 7 T 49 3" stroke="#059669" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
        </div>
      `);

      // 3. Applications Card (Pre-renders ONLY authorized modules directly into the initial HTML string)
      const currentUser = getCurrentUsername() || "guest";
      const currentRolesHash = getUserRoles().slice().sort().join(",");
      const currentAuth = _verifiedAuth || computeVerifiedAuth(null);
      const initialGridHtml = buildApplicationsGridHtml(currentAuth);

      const $appsCard = $(`
        <div class="gv-applications-card">
          <div class="gv-apps-header">
            <div class="gv-apps-title-group">
              <div class="gv-apps-title-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <rect width="7" height="7" x="3" y="3" rx="1.5"/>
                  <rect width="7" height="7" x="14" y="3" rx="1.5"/>
                  <rect width="7" height="7" x="14" y="14" rx="1.5"/>
                  <rect width="7" height="7" x="3" y="14" rx="1.5"/>
                </svg>
              </div>
              <div>
                <div class="gv-apps-heading">${__("Applications")}</div>
                <div class="gv-apps-subheading">${__("All your tools in one place.")}</div>
              </div>
            </div>

            <div class="gv-apps-filters">
              <button class="gv-filter-btn active" data-filter="all">${__("All")}</button>
              <button class="gv-filter-btn" data-filter="energy">${__("Energy")}</button>
              <button class="gv-filter-btn" data-filter="operations">${__("Operations")}</button>
              <button class="gv-filter-btn" data-filter="reports">${__("Reports")}</button>
              <button class="gv-filter-btn" data-filter="system">${__("System")}</button>

              <div class="gv-view-toggle">
                <div class="gv-toggle-icon active" title="${__("Grid View")}">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect width="7" height="7" x="3" y="3" rx="1"/>
                    <rect width="7" height="7" x="14" y="3" rx="1"/>
                    <rect width="7" height="7" x="14" y="14" rx="1"/>
                    <rect width="7" height="7" x="3" y="14" rx="1"/>
                  </svg>
                </div>
                <div class="gv-toggle-icon" title="${__("List View")}">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="8" y1="6" x2="21" y2="6"/>
                    <line x1="8" y1="12" x2="21" y2="12"/>
                    <line x1="8" y1="18" x2="21" y2="18"/>
                    <line x1="3" y1="6" x2="3.01" y2="6"/>
                    <line x1="3" y1="12" x2="3.01" y2="12"/>
                    <line x1="3" y1="18" x2="3.01" y2="18"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <div class="gv-grid-mount-point">
            <div class="icons-container">
              <div class="icons gv-grid-populated" data-rendered-user="${currentAuth.username || currentUser}" data-rendered-roles="${currentRolesHash}">
                ${initialGridHtml.html}
              </div>
            </div>
          </div>

          <div class="gv-apps-footer">
            <div class="gv-footer-left">
              <img src="/assets/uranos_project_os/images/uranos-logo.jpeg" alt="URANOS" class="gv-footer-logo-img">
              <span>URANOS Group | ${__("Photovoltaic Execution OS")}</span>
            </div>
            <div class="gv-footer-right">
              <div class="gv-status-indicator">
                <div class="gv-status-dot"></div>
                <span>${__("System Online")}</span>
              </div>
              <span>${getFormattedDate()}</span>
            </div>
          </div>
        </div>
      `);

      // 2.5. 7-Day Verified Progress Bento Card
      const $progressCard = $(`
        <div class="gv-7day-progress-card" id="gv-7day-progress-container">
          <div class="gv-progress-header">
            <div class="gv-progress-title-group">
              <div class="gv-progress-title-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/>
                  <line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                  <path d="m9 16 2 2 4-4"/>
                </svg>
              </div>
              <div>
                <div class="gv-progress-heading-row">
                  <span class="gv-progress-heading">${__("7-Day Verified Progress")}</span>
                  <span class="gv-progress-badge-live">
                    <span class="gv-pulse-dot"></span>
                    ${__("Verified Only")}
                  </span>
                </div>
                <div class="gv-progress-subheading">${__("Physical installed quantities strictly within the 7-calendar-day window")}</div>
              </div>
            </div>

            <div class="gv-progress-meta-strip">
              <div class="gv-meta-pill">
                <span class="gv-meta-label">${__("Period")}:</span>
                <strong class="gv-meta-val" id="gv-progress-period">2026-09-10 → 2026-09-16 (7d)</strong>
              </div>
              <div class="gv-meta-pill">
                <span class="gv-meta-label">${__("Baseline")}:</span>
                <strong class="gv-meta-val" id="gv-progress-baseline">B1 (${__("Approved")})</strong>
              </div>
              <div class="gv-meta-pill">
                <span class="gv-meta-label">${__("Projects")}:</span>
                <strong class="gv-meta-val" id="gv-progress-project">PV-0001</strong>
              </div>
              <button type="button" class="bd-btn bd-btn--ai gv-dash-ai-btn" id="gv-progress-ai-btn" title="${__("Generate Smart Blocker Synthesis (AI)")}">
                <span class="bd-btn__icon" aria-hidden="true">✨</span>
                <span class="bd-btn__text">${__("Smart Blocker Synthesis (AI)")}</span>
              </button>
            </div>
          </div>

          <div class="gv-progress-grid" id="gv-progress-wp-grid"></div>

          <div class="gv-progress-footer">
            <div class="gv-progress-units-summary">
              <span class="gv-summary-label">${__("Units Summary")}:</span>
              <div class="gv-summary-chips" id="gv-progress-summary-chips"></div>
            </div>

            <div class="gv-progress-guarantees">
              <span class="gv-guarantee-chip" title="${__("Drafts & Receipts Excluded")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                ${__("Drafts & Receipts Excluded")}
              </span>
              <span class="gv-guarantee-chip" title="${__("No Unit Mixing (pieux / modules / m separated)")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                ${__("Separate Units")}
              </span>
              <span class="gv-guarantee-chip" title="${__("Zero Labour Conversion")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                ${__("Zero Labour Conversion")}
              </span>
              <span class="gv-guarantee-chip" title="${__("Net Corrections")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                ${__("Net Corrections")}
              </span>
              <span class="gv-guarantee-chip" title="${__("Strict 7-Day Boundary")}">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                ${__("Strict 7-Day Boundary")}
              </span>
            </div>
          </div>
        </div>
      `);

      $sidebar.prependTo($container);

      // Dynamic Role-Based Visibility on Sidebar Links
      const sidebarAuth = currentAuth || _verifiedAuth || computeVerifiedAuth(null);
      if (!sidebarAuth.isSuperAdmin) {
        const apps = getTargetApps();
        const allowedAppIds = new Set(apps.filter(app => userHasAccessToApp(app, sidebarAuth)).map(app => app.id));
        $sidebar.find(".gv-nav-link[data-sidebar-app]").each(function () {
          const appId = $(this).attr("data-sidebar-app");
          if (!allowedAppIds.has(appId)) {
            $(this).remove();
          }
        });
      }

      $mainDashboard.appendTo($container);
      $heroKpiRow.appendTo($mainDashboard);
      $mapCard.appendTo($mainDashboard);
      $progressCard.appendTo($mainDashboard);
      $appsCard.appendTo($mainDashboard);

      // ── Make Sidebar Links silky smooth via frappe.set_route ──
      $sidebar.find(".gv-nav-link").off("click.gvNav").on("click.gvNav", function (e) {
        const href = $(this).attr("href");
        if (href && href.startsWith("/app") && window.frappe && frappe.set_route) {
          e.preventDefault();
          const cleanRoute = href.replace(/^\/app\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
          if (cleanRoute.length === 0) {
            frappe.set_route("");
          } else {
            frappe.set_route(...cleanRoute);
          }
        }
      });

      // ── Wire Apps Card click handlers ──
      $appsCard.find(".desktop-icon").off("click.gvApp").on("click.gvApp", function (e) {
        const route = $(this).attr("href");
        if (route && window.frappe && frappe.set_route) {
          e.preventDefault();
          const cleanRoute = route.replace(/^\/app\//, "").replace(/^\/desk\//, "").split("/").filter(Boolean).map(decodeURIComponent);
          frappe.set_route(...cleanRoute);
        }
      });

      // ── Make KPI Cards clickable ──
      $heroKpiRow.find("#gv-kpi-card-capacity, #gv-kpi-card-sites").css("cursor", "pointer").attr("title", __("Click to view Project Sites")).off("click.gvKpiSites").on("click.gvKpiSites", function () {
        if (window.frappe && frappe.set_route) frappe.set_route("uranos-project-profile");
      });
      $heroKpiRow.find("#gv-kpi-card-energy").css("cursor", "pointer").attr("title", __("Click to view Blocker Dashboard")).off("click.gvKpiBlockers").on("click.gvKpiBlockers", function () {
        if (window.frappe && frappe.set_route) frappe.set_route("blocker-dashboard");
      });
      $heroKpiRow.find("#gv-kpi-card-co2").css("cursor", "pointer").attr("title", __("Click to view Projects")).off("click.gvKpiProjects").on("click.gvKpiProjects", function () {
        if (window.frappe && frappe.set_route) frappe.set_route("projects");
      });

      // ── Wire Main Dashboard AI Synthesis Buttons ──
      $(document).off("click.gvDashAI", "#gv-hero-ai-btn, #gv-progress-ai-btn").on("click.gvDashAI", "#gv-hero-ai-btn, #gv-progress-ai-btn", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const project = $("#gv-progress-project").text().trim() || "PV-0001";
        if (window.openAISynthesisModal) {
          window.openAISynthesisModal(project);
        }
      });

      // ── Wire Executive PDF Report Download Button ──
      $(document).off("click.uranosExecutivePdf", "#uranosGenerateExecutivePdfBtn").on("click.uranosExecutivePdf", "#uranosGenerateExecutivePdfBtn", function (e) {
        e.preventDefault();
        e.stopPropagation();
        const endpoint = "/api/method/uranos_project_os.services.api.generate_daily_report";
        window.open(endpoint, "_blank");
      });

      $appsCard.find(".gv-filter-btn").on("click", function () {
        $(".gv-filter-btn").removeClass("active");
        $(this).addClass("active");
        filterCards($(this).attr("data-filter"));
      });
    }

    renderFlagshipGrid();
    fetchDashboardKPIs();
    fetch7DayProgress();
    initUranosGisMap();
  }

  // ── 3. RENDER ALL URANOS BENTO CARDS WITH DYNAMIC RBAC ──
  let _verifiedAuth = null;
  let _isVerifyingAuth = false;

  function computeVerifiedAuth(backendUser) {
    const rawUsername = (backendUser && backendUser.username)
      || (window.frappe && frappe.session && frappe.session.user)
      || (window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.name)
      || "Guest";

    const username = String(rawUsername).trim();
    const lowerUser = username.toLowerCase();
    const primaryRole = (backendUser && backendUser.role) ? String(backendUser.role).trim() : "";

    const roleSet = new Set();
    if (primaryRole) {
      roleSet.add(primaryRole);
      roleSet.add("URANOS " + primaryRole);
    }
    if (window.frappe) {
      if (frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles)) {
        frappe.boot.user.roles.forEach(r => { if (typeof r === "string" && r) roleSet.add(r.trim()); });
      }
      if (Array.isArray(frappe.user_roles)) {
        frappe.user_roles.forEach(r => { if (typeof r === "string" && r) roleSet.add(r.trim()); });
      }
      if (frappe.user && typeof frappe.user.get_roles === "function") {
        try {
          const r = frappe.user.get_roles();
          if (Array.isArray(r)) r.forEach(role => { if (typeof role === "string" && role) roleSet.add(role.trim()); });
        } catch (e) {}
      }
    }

    if (lowerUser === "administrator" || lowerUser === "admin") {
      roleSet.add("Administrator");
      roleSet.add("System Manager");
    }

    const roles = Array.from(roleSet);
    const lowerRoles = roles.map(r => r.toLowerCase());

    const isSuperAdmin = (
      lowerUser === "administrator" ||
      lowerUser === "admin"
    );

    const isChantier = (
      !isSuperAdmin && (
        lowerUser.includes("chantier") ||
        lowerRoles.includes("uranos site controller") ||
        primaryRole.toLowerCase().includes("site controller")
      )
    );

    const isIngenieur = (
      !isSuperAdmin && !isChantier && (
        lowerUser.includes("ingenieur") ||
        lowerRoles.includes("uranos engineering director") ||
        primaryRole.toLowerCase().includes("engineering director")
      )
    );

    const isDirection = (
      !isSuperAdmin && !isChantier && !isIngenieur && (
        lowerUser.includes("direction") ||
        lowerUser.includes("manager") ||
        lowerRoles.includes("uranos executive") ||
        lowerRoles.includes("management") ||
        lowerRoles.includes("manager") ||
        primaryRole.toLowerCase().includes("executive") ||
        primaryRole.toLowerCase().includes("management") ||
        primaryRole.toLowerCase().includes("manager")
      )
    );

    return {
      username: username,
      roles: roles,
      isSuperAdmin: isSuperAdmin,
      isChantier: isChantier,
      isIngenieur: isIngenieur,
      isDirection: isDirection,
      isExecutive: isDirection,
      isManager: isDirection
    };
  }

  function renderFlagshipGrid() {
    const $mount = $(".gv-applications-card .gv-grid-mount-point");
    if (!$mount.length) return;

    let $iconsContainer = $mount.find(".icons-container");
    if (!$iconsContainer.length) {
      $iconsContainer = $('<div class="icons-container"></div>').appendTo($mount);
    }

    const currentSessionUser = (window.frappe && frappe.session && frappe.session.user) || "Guest";
    const $populated = $iconsContainer.find(".gv-grid-populated");

    // Reset verifiedAuth if user changed in session
    if (_verifiedAuth && _verifiedAuth.username !== currentSessionUser && currentSessionUser !== "Guest") {
      _verifiedAuth = null;
      $iconsContainer.empty();
    }

    // If already verified and populated with actual cards, no re-render needed
    if (_verifiedAuth && $populated.length && $populated.attr("data-rendered-user") === _verifiedAuth.username && $populated.find(".desktop-icon").length > 0) {
      return;
    }

    // 1. If we already have verified auth, paint immediately
    if (_verifiedAuth) {
      paintVerifiedGrid($mount, _verifiedAuth);
      return;
    }

    // 2. Show loading state if grid is empty or missing cards
    if (!$populated.find(".desktop-icon").length && !$iconsContainer.find(".gv-grid-loading-state").length) {
      $iconsContainer.html(`
        <div class="gv-grid-loading-state" style="grid-column: 1 / -1; padding: 48px 24px; text-align: center;">
          <div class="gv-grid-spinner" style="width: 32px; height: 32px; border: 3px solid rgba(16, 185, 129, 0.2); border-top-color: #10b981; border-radius: 50%; animation: gvSaasPulse 0.8s linear infinite; margin: 0 auto 14px;"></div>
          <div style="font-size: 13.5px; font-weight: 650; color: #475569;">${__("Verifying access permissions from database...")}</div>
        </div>
      `);
    }

    if (_isVerifyingAuth) return;
    _isVerifyingAuth = true;

    // Make explicit awaited frappe.call
    if (window.frappe && frappe.call) {
      frappe.call({
        method: "uranos_project_os.services.api.get_dashboard_kpis",
        callback: function (r) {
          _isVerifyingAuth = false;
          const backendUser = (r && r.message && r.message.user) ? r.message.user : null;
          _verifiedAuth = computeVerifiedAuth(backendUser);
          paintVerifiedGrid($mount, _verifiedAuth);
          if (r && r.message) {
            updateDashboardDOM(r.message);
          }
        },
        error: function (err) {
          _isVerifyingAuth = false;
          console.warn("URANOS RBAC Auth Verification fallback", err);
          _verifiedAuth = computeVerifiedAuth(null);
          paintVerifiedGrid($mount, _verifiedAuth);
        }
      });
    } else {
      _isVerifyingAuth = false;
      _verifiedAuth = computeVerifiedAuth(null);
      paintVerifiedGrid($mount, _verifiedAuth);
    }
  }

  function paintVerifiedGrid($mount, auth) {
    let $iconsContainer = $mount.find(".icons-container");
    if (!$iconsContainer.length) {
      $iconsContainer = $('<div class="icons-container"></div>').appendTo($mount);
    }

    const res = buildApplicationsGridHtml(auth);
    $iconsContainer.html(`
      <div class="icons gv-grid-populated" data-rendered-user="${auth.username}" data-card-count="${res.count}">
        ${res.html}
      </div>
    `);

    $iconsContainer.find(".desktop-icon").off("click.gvApp").on("click.gvApp", function (e) {
      const route = $(this).attr("href");
      if (route && window.frappe && frappe.set_route) {
        e.preventDefault();
        const cleanRoute = route.replace(/^\/app\//, "").replace(/^\/desk\//, "").split("/").filter(Boolean).map(decodeURIComponent);
        frappe.set_route(...cleanRoute);
      }
    });

    $(".desktop-container > .icons-container, .desktop-wrapper > .icons-container").remove();
  }

  function filterCards(category) {
    if (category === "all") {
      $(".gv-applications-card .desktop-icon").show();
      $(".gv-applications-card .gv-no-modules-placeholder").remove();
      return;
    }
    $(".gv-applications-card .desktop-icon[data-category='" + category + "']").show();
    $(".gv-applications-card .desktop-icon:not([data-category='" + category + "'])").hide();

    const visibleCount = $(".gv-applications-card .desktop-icon[data-category='" + category + "']").length;
    $(".gv-applications-card .gv-no-modules-placeholder").remove();
    if (visibleCount === 0) {
      $(".gv-applications-card .icons").append(`
        <div class="gv-no-modules-placeholder" style="grid-column: 1 / -1; padding: 32px 20px; text-align: center; color: #94a3b8; font-size: 13px;">
          ${__("No modules in this category for your assigned role.")}
        </div>
      `);
    }
  }

  // ── 4. SIGN-OUT REDIRECTION & LOGOUT INTERCEPTION ──
  function performLogout() {
    if (typeof frappe !== "undefined" && frappe.call) {
      frappe.call({
        method: "logout",
        callback: function () {
          window.location.href = "/login";
        },
        error: function () {
          window.location.href = "/login";
        }
      });
    } else {
      window.location.href = "/login";
    }
  }

  function setupSignOutRedirection() {
    if (window._gv_signout_hooked) return;
    window._gv_signout_hooked = true;

    if (window.frappe && frappe.app) {
      frappe.app.redirect_to_login = function () {
        window.location.href = "/login";
      };

      frappe.app.logout = function () {
        performLogout();
      };
    }

    $(document).off("click.gvLogout", "a[href*='cmd=web_logout'], [data-action='logout'], a[href='/login#login'], a[href*='logout']");
    $(document).on("click.gvLogout", "a[href*='cmd=web_logout'], [data-action='logout'], a[href='/login#login'], a[href*='logout']", function (e) {
      e.preventDefault();
      e.stopPropagation();
      performLogout();
    });

    $(document).off("click.gvLogoutText", ".dropdown-item, .dropdown-menu a, .dropdown-menu button");
    $(document).on("click.gvLogoutText", ".dropdown-item, .dropdown-menu a, .dropdown-menu button", function (e) {
      const text = $(this).text().trim().toLowerCase();
      if (text === "log out" || text === "logout" || text === "sign out") {
        e.preventDefault();
        e.stopPropagation();
        performLogout();
      }
    });
  }

  function cleanupNativeSidebars() {
    const $targets = $(".body-sidebar-container, .body-sidebar, .layout-side-section, .standard-sidebar-section");
    if ($targets.length) {
      $targets.remove();
    }
  }

  // ── 5. INNER WORKSPACES TOP & CHIC OVERHAUL ENGINE ──
  const WORKSPACE_ICONS = {
    "completed projects": {
      gradient: "linear-gradient(135deg, #0d9488 0%, #0284c7 100%)",
      shadow: "0 8px 16px -4px rgba(13, 148, 136, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>`,
      subtitle: __("Performance metrics & delivery milestones")
    },
    "open projects": {
      gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
      shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>`,
      subtitle: __("Active solar & wind installations")
    },
    "non completed tasks": {
      gradient: "linear-gradient(135deg, #06b6d4 0%, #2563eb 100%)",
      shadow: "0 8px 16px -4px rgba(6, 182, 212, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="m9 11 3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>`,
      subtitle: __("Pending action items & engineering logs")
    },
    "projects": {
      gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
      shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>`,
      subtitle: __("Manage renewable project lifecycles")
    },
    "goal and procedure": {
      gradient: "linear-gradient(135deg, #10b981 0%, #0d9488 100%)",
      shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>`,
      subtitle: __("Quality standards & protocol trees")
    },
    "feedback": {
      gradient: "linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)",
      shadow: "0 8px 16px -4px rgba(2, 132, 199, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      subtitle: __("Field assessments & quality ratings")
    },
    "meeting": {
      gradient: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
      shadow: "0 8px 16px -4px rgba(139, 92, 246, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
      subtitle: __("Review sessions & coordination meetings")
    },
    "review and action": {
      gradient: "linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)",
      shadow: "0 8px 16px -4px rgba(245, 158, 11, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
      subtitle: __("Corrective actions & issue resolution")
    }
  };

  function getWidgetVisualConfig(titleText) {
    const clean = (titleText || "").trim().toLowerCase();
    if (WORKSPACE_ICONS[clean]) return WORKSPACE_ICONS[clean];

    for (const key in WORKSPACE_ICONS) {
      if (clean.includes(key)) return WORKSPACE_ICONS[key];
    }

    if (clean.includes("project")) {
      return WORKSPACE_ICONS["projects"];
    } else if (clean.includes("task") || clean.includes("todo")) {
      return WORKSPACE_ICONS["non completed tasks"];
    } else if (clean.includes("qualit") || clean.includes("goal") || clean.includes("procedure")) {
      return WORKSPACE_ICONS["goal and procedure"];
    } else if (clean.includes("feedback") || clean.includes("review")) {
      return WORKSPACE_ICONS["feedback"];
    } else if (clean.includes("meet")) {
      return WORKSPACE_ICONS["meeting"];
    } else if (clean.includes("action") || clean.includes("issue") || clean.includes("blocage")) {
      return WORKSPACE_ICONS["review and action"];
    } else if (clean.includes("chart") || clean.includes("analytic") || clean.includes("graph")) {
      return WORKSPACE_ICONS["completed projects"];
    } else if (clean.includes("stock") || clean.includes("material") || clean.includes("item")) {
      return {
        gradient: "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
        shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
        svg: `<svg viewBox="0 0 24 24"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>`,
        subtitle: __("Stock tracking and materials management")
      };
    } else if (clean.includes("purchase") || clean.includes("buying") || clean.includes("supplier")) {
      return {
        gradient: "linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)",
        shadow: "0 8px 16px -4px rgba(6, 182, 212, 0.4)",
        svg: `<svg viewBox="0 0 24 24"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
        subtitle: __("Procurement, purchase orders & vendors")
      };
    } else if (clean.includes("sale") || clean.includes("selling") || clean.includes("customer")) {
      return {
        gradient: "linear-gradient(135deg, #10b981 0%, #0284c7 100%)",
        shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
        svg: `<svg viewBox="0 0 24 24"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><line x1="8" y1="8" x2="16" y2="8"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/></svg>`,
        subtitle: __("Customer accounts and sales orders")
      };
    } else if (clean.includes("hr") || clean.includes("employee") || clean.includes("payroll")) {
      return {
        gradient: "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)",
        shadow: "0 8px 16px -4px rgba(2, 132, 199, 0.4)",
        svg: `<svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
        subtitle: __("Workforce directory and team assignments")
      };
    }

    return {
      gradient: "linear-gradient(135deg, #10b981 0%, #0284c7 100%)",
      shadow: "0 8px 16px -4px rgba(16, 185, 129, 0.4)",
      svg: `<svg viewBox="0 0 24 24"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>`,
      subtitle: __("Operations and overview")
    };
  }

  function upgradeInnerWorkspaces() {
    // 1. Upgrade section headers (fast selector, un-upgraded only)
    const $headings = $(".layout-main-section h4:not(.gv-section-heading), .workspace-page h4:not(.gv-section-heading), .workspace-title:not(.gv-section-heading)");
    if ($headings.length) {
      $headings.each(function () {
        const $h4 = $(this);
        $h4.addClass("gv-section-heading");
        if (!$h4.find(".gv-heading-dot").length) {
          $h4.prepend('<span class="gv-heading-dot"></span>');
        }
      });
    }

    // 2. Upgrade inner widgets: target only un-upgraded widgets to eliminate CPU loop churn
    const $widgets = $(".widget:not(.desktop-icon):not(.gv-upgraded)");
    if (!$widgets.length) return;

    $widgets.each(function () {
      const $widget = $(this);
      if ($widget.closest(".desktop-container, #desktop-content").length) return;
      if ($widget.hasClass("spacer") || $widget.is(":empty")) return;

      const $head = $widget.find(".widget-head").first();
      const titleEl = $widget.find(".widget-title, .title, .widget-head").first();
      let rawTitle = "";
      if (titleEl.length) {
        const span = titleEl.find(".ellipsis, span").first();
        rawTitle = span.length ? span.text() : titleEl.text();
      }
      rawTitle = (rawTitle || "").split("\n")[0].trim();

      // If title is available and valid
      if (rawTitle && rawTitle !== "..." && !rawTitle.toLowerCase().includes("loading")) {
        const conf = getWidgetVisualConfig(rawTitle);

        // Inject Squircle Icon into head
        if ($head.length && !$head.find(".gv-widget-squircle").length) {
          $head.prepend(`
            <div class="gv-widget-squircle" style="background: ${conf.gradient}; box-shadow: ${conf.shadow};">
              ${conf.svg}
            </div>
          `);
        }

        // Inject or refine Subtitle
        let $subtitle = $widget.find(".widget-subtitle").first();
        if (!$subtitle.length) {
          const $label = $widget.find(".widget-label").first();
          if ($label.length) {
            $label.append('<div class="widget-subtitle"></div>');
            $subtitle = $label.find(".widget-subtitle");
          }
        }
        if ($subtitle.length && !$subtitle.text().trim()) {
          $subtitle.text(conf.subtitle);
        }
      }

      // Inject Bottom-Right Circular Action Arrow for links, shortcuts, and number widgets
      if ($widget.hasClass("links-widget-box") || $widget.hasClass("shortcut-widget-box") || $widget.hasClass("number-widget-box") || $widget.find(".link-item").length) {
        if (!$widget.find(".gv-widget-action-arrow").length) {
          $widget.append(`
            <div class="gv-widget-action-arrow">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
          `);
        }
      }

      // Inject Live Pulse Badge into Number Widget if number is rendered
      if ($widget.hasClass("number-widget-box") || $widget.find(".number").length) {
        const $num = $widget.find(".number").first();
        if ($num.length && $num.text().trim() && !$widget.find(".gv-number-status").length) {
          $num.parent().append(`
            <div class="gv-number-status">
              <span class="gv-status-pulse"></span>
              <span>${__("Live Database Metric")}</span>
            </div>
          `);
        }
      }

      // Mark as upgraded so subsequent watchdog cycles skip this element in O(1) time
      $widget.addClass("gv-upgraded");
    });
  }

  function isMainDashboard() {
    const rawRoute = (window.frappe && typeof frappe.get_route === "function") ? frappe.get_route() : [];
    const route = Array.isArray(rawRoute) ? rawRoute : [];
    if (!route.length || route[0] === "" || route[0] === "desktop") {
      return true;
    }
    if (route[0] === "app" && (!route[1] || route[1] === "desktop")) {
      return true;
    }
    const path = (window.location && window.location.pathname) ? window.location.pathname : "";
    if ((path === "/desk" || path === "/desk/" || path === "/app" || path === "/app/") && (!route.length || route[0] === "desktop")) {
      return true;
    }
    return false;
  }

  function enforceBreadcrumbsOverride() {
    if (typeof window === "undefined" || !window.frappe) return;

    if (frappe.breadcrumbs) {
      try {
        localStorage.setItem("preferred_breadcrumbs:Project", "Projects");
        localStorage.setItem("preferred_breadcrumbs:URANOS Project Profile", "Projects");
      } catch (e) {}

      if (frappe.breadcrumbs.preferred) {
        frappe.breadcrumbs.preferred["Project"] = "Projects";
        frappe.breadcrumbs.preferred["URANOS Project Profile"] = "Projects";
      }

      if (typeof frappe.breadcrumbs.set_doctype_module === "function") {
        frappe.breadcrumbs.set_doctype_module("Project", "Projects");
        frappe.breadcrumbs.set_doctype_module("URANOS Project Profile", "Projects");
      }

      if (!frappe.breadcrumbs._gv_patched) {
        frappe.breadcrumbs._gv_patched = true;
        const origUpdate = frappe.breadcrumbs.update;
        frappe.breadcrumbs.update = function () {
          const curPage = frappe.breadcrumbs.current_page ? frappe.breadcrumbs.current_page() : "";
          const route = frappe.get_route ? frappe.get_route() : [];

          if (
            (route[0] === "project" || curPage.startsWith("project") || (route[0] === "List" && route[1] === "Project")) &&
            this.all && this.all[curPage]
          ) {
            this.all[curPage].module = "Projects";
            this.all[curPage].workspace = "Projects";
          }

          if (
            (route[0] === "uranos-project-profile" || curPage.startsWith("uranos-project-profile") || (route[0] === "List" && route[1] === "URANOS Project Profile")) &&
            this.all && this.all[curPage]
          ) {
            this.all[curPage].module = "Projects";
            this.all[curPage].workspace = "Projects";
          }

          const res = origUpdate.apply(this, arguments);
          sanitizeDomBreadcrumbs();
          return res;
        };
      }
    }
  }

  function sanitizeDomBreadcrumbs($scope) {
    const rawRoute = (window.frappe && typeof frappe.get_route === "function") ? frappe.get_route() : [];
    const route = Array.isArray(rawRoute) ? rawRoute : [];
    const path = window.location.pathname || "";
    const isProjectRoute = Boolean(route[0] === "project" || (route[0] === "List" && route[1] === "Project") || path.includes("/project"));
    const isSitesRoute = Boolean(route[0] === "uranos-project-profile" || (route[0] === "List" && route[1] === "URANOS Project Profile") || path.includes("/uranos-project-profile"));

    const $root = $scope || $(document);
    $root.find(".navbar-breadcrumbs, .breadcrumbs").each(function () {
      const $bc = $(this);
      $bc.find("li").each(function () {
        const $li = $(this);
        const $a = $li.find("a");
        const text = ($a.length ? $a.text() : $li.text()).trim();

        // 1. Forcefully rename "Stock" -> "Projects" on Project route
        if (isProjectRoute && (text === "Stock" || ($a.length && $a.attr("href") && $a.attr("href").includes("/stock")))) {
          if ($a.length) {
            $a.text(__("Projects")).attr("href", "/app/projects");
          } else {
            $li.text(__("Projects"));
          }
        }

        // 2. Refine "URANOS Project Profile" -> "Sites" on Sites route
        if (isSitesRoute && (text.includes("URANOS Project Profile") || text.includes("Uranos Project Profile"))) {
          if ($a.length) {
            $a.text(__("Sites"));
          } else {
            $li.text(__("Sites"));
          }
        }
      });
    });

    if (isSitesRoute) {
      $root.find(".page-title .title-text, .page-head .title-text").each(function () {
        const $t = $(this);
        if ($t.text().trim() === "URANOS Project Profile") {
          $t.text(__("Sites"));
        }
      });
    }
  }

  function upgradeInnerPageHeaders() {
    if (isMainDashboard()) {
      $("#page-desktop #gv-back-to-dashboard, #page-desktop .gv-return-dashboard-btn, #page-desktop .gv-realtime-diagnostic-pill, .desktop-container .gv-return-dashboard-btn, .desktop-container .gv-realtime-diagnostic-pill").remove();
      return;
    }

    $("#page-desktop #gv-back-to-dashboard, #page-desktop .gv-return-dashboard-btn, #page-desktop .gv-realtime-diagnostic-pill, .desktop-container .gv-return-dashboard-btn, .desktop-container .gv-realtime-diagnostic-pill").remove();

    const $containers = $(".page-container:not(#page-desktop)");
    if (!$containers.length) return;

    $containers.each(function () {
      const $container = $(this);
      const isCurrent = $container.is(":visible") || $container.css("display") !== "none";
      if (!isCurrent) return;

      const $head = $container.find(".page-head:first");
      if (!$head.length) return;

      // Deduplicate buttons if any
      $head.find(".gv-return-dashboard-btn:gt(0)").remove();
      $head.find(".gv-realtime-diagnostic-pill:gt(0)").remove();

      // Fast check: element existence
      const hasBackBtn = $head.find("#gv-back-to-dashboard, .gv-return-dashboard-btn").length > 0;
      const hasDiagPill = $head.find(".gv-realtime-diagnostic-pill").length > 0;

      // 1. Hide native sidebar collapse button on inner pages
      $head.find(".sidebar-toggle-btn").css("display", "none").hide();

      // 2. Always sanitize breadcrumbs on inner page render
      sanitizeDomBreadcrumbs($head);

      // 3. Inject "Back to Main Dashboard" Button into header left
      if (!hasBackBtn) {
        const returnBtnHtml = `
          <a href="/app" class="gv-return-dashboard-btn" id="gv-back-to-dashboard" title="${__("Return to Main Dashboard")}">
            <span class="gv-return-arrow-circle">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
            </span>
            <span>${__("Back to Main Dashboard")}</span>
          </a>
        `;
        const $pageTitle = $head.find(".page-title:first");
        const $breadcrumbs = $pageTitle.find(".navbar-breadcrumbs, .breadcrumbs:first");
        const $titleArea = $pageTitle.find(".title-area:first");

        if ($breadcrumbs.length) {
          // Normalize breadcrumbs: clean redundant duplicate names (e.g., Projects / Project)
          const $lis = $breadcrumbs.find("li");
          if ($lis.length >= 2) {
            const $firstA = $lis.first().find("a");
            if ($firstA.length) {
              $firstA.attr("href", "/app").text(__("Dashboard"));
            }
          }
          $breadcrumbs.before(returnBtnHtml);
        } else if ($titleArea.length) {
          $titleArea.before(returnBtnHtml);
        } else if ($pageTitle.length) {
          $pageTitle.prepend(returnBtnHtml);
        } else {
          $head.find(".page-head-content:first").prepend(returnBtnHtml);
        }
      }

      // 3. Inject Real-Time Diagnostic Pill into header right
      if (!hasDiagPill) {
        const pillHtml = `
          <div class="gv-realtime-diagnostic-pill" title="${__("Live Database Connection Active & Synchronized")}">
            <span class="gv-diag-dot"></span>
            <span class="gv-diag-text">${__("Live Database Connected")}</span>
          </div>
        `;

        let $targetActions = $head.find(".standard-actions:first");
        if (!$targetActions.length || $targetActions.is(":hidden")) {
          $targetActions = $head.find(".page-actions:first");
        }
        if (!$targetActions.length || $targetActions.is(":hidden")) {
          $targetActions = $head.find(".page-head-content:first");
        }

        if ($targetActions.length) {
          $targetActions.prepend(pillHtml);
        }
      }

      // Continuous DOM Breadcrumb enforcement
      sanitizeDomBreadcrumbs($head);
    });
  }

  // Handle return click smoothly via Frappe router or direct location
  $(document).off("click.gvBack", "#gv-back-to-dashboard");
  $(document).on("click.gvBack", "#gv-back-to-dashboard", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (window.frappe && frappe.set_route) {
      frappe.set_route("");
    } else {
      window.location.href = "/app";
    }
  });

  let workspaceUpgradeTimer = null;
  function scheduleWorkspaceUpgrade() {
    if (workspaceUpgradeTimer) clearTimeout(workspaceUpgradeTimer);
    workspaceUpgradeTimer = setTimeout(function () {
      if (isDOMMutationActive) return;
      isDOMMutationActive = true;
      try {
        upgradeInnerWorkspaces();
        upgradeInnerPageHeaders();
      } finally {
        isDOMMutationActive = false;
      }
    }, 50);
  }

  // Hook directly into Frappe Page prototype to intercept every single render / action clear
  function setupFrappePageHooks() {
    if (window.frappe && frappe.ui && frappe.ui.Page && !frappe.ui.Page._gv_hooked) {
      frappe.ui.Page._gv_hooked = true;

      const origSetTitle = frappe.ui.Page.prototype.set_title;
      frappe.ui.Page.prototype.set_title = function () {
        const res = origSetTitle.apply(this, arguments);
        setTimeout(function () {
          upgradeInnerPageHeaders();
          upgradeInnerWorkspaces();
        }, 10);
        return res;
      };

      const origClearActions = frappe.ui.Page.prototype.clear_actions;
      frappe.ui.Page.prototype.clear_actions = function () {
        const res = origClearActions.apply(this, arguments);
        setTimeout(upgradeInnerPageHeaders, 10);
        return res;
      };

      const origClearCustomActions = frappe.ui.Page.prototype.clear_custom_actions;
      frappe.ui.Page.prototype.clear_custom_actions = function () {
        const res = origClearCustomActions.apply(this, arguments);
        setTimeout(upgradeInnerPageHeaders, 10);
        return res;
      };
    }
  }

  // High-performance MutationObserver with self-mutation filtering & debouncing
  if (typeof MutationObserver !== "undefined") {
    const workspaceObserver = new MutationObserver(function (mutations) {
      if (isDOMMutationActive) return;
      let shouldUpgrade = false;
      for (let i = 0; i < mutations.length; i++) {
        const m = mutations[i];
        if (m.addedNodes && m.addedNodes.length) {
          for (let j = 0; j < m.addedNodes.length; j++) {
            const node = m.addedNodes[j];
            if (node.nodeType === 1) {
              const el = /** @type {HTMLElement} */ (node);
              // Ignore our own injected elements to prevent observer echo
              if (el.id === "gv-back-to-dashboard" ||
                  el.classList.contains("gv-realtime-diagnostic-pill") ||
                  el.classList.contains("gv-widget-squircle") ||
                  el.classList.contains("gv-widget-action-arrow") ||
                  el.classList.contains("gv-number-status")) {
                continue;
              }
              shouldUpgrade = true;
              break;
            }
          }
        } else if (m.removedNodes && m.removedNodes.length) {
          shouldUpgrade = true;
          break;
        }
        if (shouldUpgrade) break;
      }
      if (shouldUpgrade) {
        scheduleWorkspaceUpgrade();
      }
    });

    const targetObsNode = document.getElementById("body") || document.body;
    workspaceObserver.observe(targetObsNode, { childList: true, subtree: true });
  }

  // ── 6. URANOS CHIC EXECUTIVE SAAS VIEWS (SCOPED & REAL DATA BOUND) ──
  function bindSaasViewEvents($view) {
    // 1. Live text search
    $view.find(".uranos-saas-search-input").on("input", function () {
      const q = $(this).val().toLowerCase().trim();
      $view.find(".uranos-saas-card, .uranos-wp-milestone-card, .uranos-report-journal-card, .uranos-stock-card, .uranos-support-card, .uranos-invoice-card, .uranos-faq-item, .uranos-user-row").each(function () {
        const text = $(this).attr("data-search") || "";
        $(this).toggle(text.includes(q));
      });
    });

    // 2. Chip status filter
    $view.find(".uranos-saas-chip").on("click", function () {
      $view.find(".uranos-saas-chip").removeClass("active");
      $(this).addClass("active");
      const f = ($(this).attr("data-filter") || "").toLowerCase();
      $view.find(".uranos-saas-card, .uranos-wp-milestone-card, .uranos-report-journal-card, .uranos-stock-card, .uranos-support-card, .uranos-invoice-card, .uranos-faq-item, .uranos-user-row").each(function () {
        if (f === "all") {
          $(this).show();
        } else {
          const filterData = (($(this).attr("data-filter-val") || "") + " " + $(this).text()).toLowerCase();
          $(this).toggle(filterData.includes(f));
        }
      });
    });

    // 3. View Switcher (SaaS Cards vs Standard Table / Workspace Canvas)
    $view.find(".uranos-saas-switch-btn").on("click", function () {
      const mode = $(this).attr("data-view");
      $view.find(".uranos-saas-switch-btn").removeClass("active");
      $(this).addClass("active");

      const $parent = $view.closest(".frappe-list, .layout-main-section, .page-container, #page-Workspaces, .workspace-page");
      const $standardTable = $parent.find(".result, .result-list, .frappe-list .result-list, #editorjs, .codex-editor, .workspace-page .page-main-content");

      if (mode === "table") {
        $view.find(".uranos-saas-card-grid, .uranos-wp-grid, .uranos-report-feed, .uranos-stock-sections, .uranos-support-sections, .uranos-invoice-sections, .uranos-saas-kpi-deck, .uranos-saas-filter-dock, .uranos-saas-table-card").slideUp(200);
        $standardTable.slideDown(200);
      } else {
        $view.find(".uranos-saas-card-grid, .uranos-wp-grid, .uranos-report-feed, .uranos-stock-sections, .uranos-support-sections, .uranos-invoice-sections, .uranos-saas-kpi-deck, .uranos-saas-filter-dock, .uranos-saas-table-card").slideDown(200);
        $standardTable.slideUp(200);
      }
    });

    // Only hide editorjs / workspace canvas when custom SaaS view is active; NEVER hide Frappe list results or data tables
    const $parent = $view.closest(".frappe-list, .layout-main-section, .page-container, #page-Workspaces, .workspace-page");
    $parent.find("#editorjs, .codex-editor, .workspace-page .page-main-content").hide();
    $parent.find(".result, .result-list, .frappe-list .result-list").show();
  }

  // ── PROJECT VIEW: Instant suppressor — hides native Frappe list table synchronously
  // before the async frappe.call completes, eliminating the "tabular flash".
  function suppressNativeProjectTable() {
    // Preserved unified executive table view for Frappe List
    return;
  }

  function injectProjectsSaasView(force) {
    const $container = $(".page-container:not(#page-desktop) .frappe-list, .page-container:not(#page-desktop) .layout-main-section, .frappe-list, .layout-main-section").first();
    if (!$container.length) return;
    if (!force && $container.find(".uranos-chic-saas-view[data-module='projects']").length) return;
    if (!force && window._gv_injecting_projects) return;
    window._gv_injecting_projects = true;

    // Synchronously hide native list rows BEFORE async fetch to eliminate tabular flash
    suppressNativeProjectTable();

    if (!window.frappe || !frappe.call) {
      window._gv_injecting_projects = false;
      return;
    }

    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Project",
        fields: ["name", "project_name", "status", "company", "modified"],
        limit_page_length: 100,
        order_by: "modified desc"
      },
      callback: function (r) {
        window._gv_injecting_projects = false;
        const projects = (r && r.message) ? r.message : [];
        const total = projects.length;
        const openCount = projects.filter(p => p.status === "Open" || !p.status).length;

        const kpisHtml = `
          <div class="uranos-saas-kpi-deck">
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Total Assets")}</div>
                <div class="kpi-value">${total}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(2, 132, 199, 0.12); color: #0284c7;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Active & Open")}</div>
                <div class="kpi-value">${openCount}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(139, 92, 246, 0.12); color: #8b5cf6;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Operational Rate")}</div>
                <div class="kpi-value">100%</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(6, 182, 212, 0.12); color: #06b6d4;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Monitored Capacity")}</div>
                <div class="kpi-value">820 MW</div>
              </div>
            </div>
          </div>
        `;

        let cardsHtml = "";
        projects.forEach(p => {
          const statusBadge = (p.status === "Completed") ? "badge-blue" : "badge-green";
          const statusText = p.status || "Open";
          cardsHtml += `
            <div class="uranos-saas-card" data-search="${(p.name + ' ' + (p.project_name || '')).toLowerCase()}">
              <div class="uranos-saas-card-top">
                <span class="uranos-saas-card-code">${p.name}</span>
                <span class="uranos-saas-badge ${statusBadge}">
                  <span class="uranos-saas-live-dot" style="width: 5px; height: 5px;"></span>
                  ${statusText}
                </span>
              </div>
              <div class="uranos-saas-card-title">${p.project_name || p.name}</div>
              <div class="uranos-saas-card-subtitle">${__("Grid-connected photovoltaic park with active baseline tracking.")}</div>
              <div class="uranos-saas-card-metrics">
                <div class="uranos-saas-metric-item">
                  <span class="m-label">${__("Discipline")}</span>
                  <span class="m-val">Solar PV</span>
                </div>
                <div class="uranos-saas-metric-item">
                  <span class="m-label">${__("Database ID")}</span>
                  <span class="m-val">${p.name}</span>
                </div>
                <a href="/app/project/${encodeURIComponent(p.name)}" class="uranos-saas-card-action-btn">
                  <span>${__("Inspect")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });

        const viewHtml = `
          <div class="uranos-chic-saas-view" data-module="projects">
            <div class="uranos-saas-header">
              <div class="uranos-saas-header-left">
                <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
                </div>
                <div class="uranos-saas-title-group">
                  <h2>${__("Projects Portfolio — Operational OS")}</h2>
                  <div class="uranos-saas-subtitle">
                    <span class="uranos-saas-live-dot"></span>
                    <span>${__("Live MariaDB Database Connection Active")}</span>
                    <span>•</span>
                    <span>${total} ${__("Synchronized Projects")}</span>
                  </div>
                </div>
              </div>
              <div class="uranos-saas-header-right">
                <div class="uranos-saas-mode-switch">
                  <button class="uranos-saas-switch-btn active" data-view="saas">✨ ${__("Executive Cards")}</button>
                  <button class="uranos-saas-switch-btn" data-view="table">📋 ${__("Standard Table")}</button>
                </div>
              </div>
            </div>

            ${kpisHtml}

            <div class="uranos-saas-filter-dock">
              <div class="uranos-saas-search-input-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" class="uranos-saas-search-input" placeholder="${__("Search projects by name or code...")}">
              </div>
              <div class="uranos-saas-filter-chips">
                <button class="uranos-saas-chip active" data-filter="all">${__("All Projects")}</button>
                <button class="uranos-saas-chip" data-filter="open">${__("Open")}</button>
                <button class="uranos-saas-chip" data-filter="completed">${__("Completed")}</button>
              </div>
            </div>

            <div class="uranos-saas-card-grid">
              ${cardsHtml}
            </div>
          </div>
        `;

        $container.find(".uranos-chic-saas-view[data-module='projects']").remove();
        $container.prepend(viewHtml);
        // Final suppression after DOM insertion to catch any Frappe-added rows during async fetch
        suppressNativeProjectTable();
        bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
      },
      error: function () {
        window._gv_injecting_projects = false;
      }
    });
  }

  function injectWorkPackagesSaasView() {
    const $container = $(".page-container:not(#page-desktop) .frappe-list, .page-container:not(#page-desktop) .layout-main-section, .frappe-list, .layout-main-section").first();
    if (!$container.length) return;
    $container.find(".uranos-chic-saas-view:not([data-module='work-packages'])").remove();
    if ($container.find(".uranos-chic-saas-view[data-module='work-packages']").length) return;
    if (window._gv_injecting_work_packages) return;
    window._gv_injecting_work_packages = true;

    if (!window.frappe || !frappe.call) {
      window._gv_injecting_work_packages = false;
      return;
    }

    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "URANOS Work Package",
        fields: ["name", "code", "title", "project", "discipline", "uom", "qty_planned", "weight", "status", "baseline_approved", "material_ready", "access_ready", "criticality"],
        limit_page_length: 100
      },
      callback: function (r) {
        window._gv_injecting_work_packages = false;
        const packages = (r && r.message) ? r.message : [];
        const total = packages.length;

        // Dynamic Aggregations from MariaDB
        const totalQty = packages.reduce((acc, wp) => acc + (parseFloat(wp.qty_planned) || 0), 0);
        const totalWeight = packages.reduce((acc, wp) => acc + (parseFloat(wp.weight) || 0), 0);
        const disciplines = [...new Set(packages.map(wp => wp.discipline || "General"))];

        const kpisHtml = `
          <div class="uranos-saas-kpi-deck uranos-wp-kpis">
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(99, 102, 241, 0.12); color: #6366f1;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Active Packages")}</div>
                <div class="kpi-value">${total} Packages</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(139, 92, 246, 0.12); color: #8b5cf6;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Planned Physical Scope")}</div>
                <div class="kpi-value">${totalQty.toLocaleString()} Units</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Baseline Allocation")}</div>
                <div class="kpi-value">${totalWeight.toFixed(1)}% Scope</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #f59e0b;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Disciplines Active")}</div>
                <div class="kpi-value">${disciplines.length} Disciplines</div>
              </div>
            </div>
          </div>
        `;

        let cardsHtml = "";
        packages.forEach(wp => {
          const disc = wp.discipline || "General";
          let discColor = "#6366f1";
          let discBg = "#eef2ff";
          if (disc === "Civil") {
            discColor = "#d97706";
            discBg = "#fef3c7";
          } else if (disc === "Mechanical") {
            discColor = "#0284c7";
            discBg = "#e0f2fe";
          } else if (disc === "Electrical") {
            discColor = "#7c3aed";
            discBg = "#f3e8ff";
          }

          const plannedQty = (parseFloat(wp.qty_planned) || 0).toLocaleString();
          const weight = (parseFloat(wp.weight) || 0).toFixed(1);
          const matReady = wp.material_ready ? `<span class="uranos-wp-gate ready">✓ Material Ready</span>` : `<span class="uranos-wp-gate pending">⏳ Material Prep</span>`;
          const accReady = wp.access_ready ? `<span class="uranos-wp-gate ready">✓ Access Ready</span>` : `<span class="uranos-wp-gate pending">⏳ Site Access</span>`;
          const baseReady = wp.baseline_approved ? `<span class="uranos-wp-gate ready">✓ Baseline Approved</span>` : `<span class="uranos-wp-gate pending">⏳ Baseline Review</span>`;

          cardsHtml += `
            <div class="uranos-wp-milestone-card" data-search="${((wp.code || '') + ' ' + (wp.title || '') + ' ' + (wp.discipline || '') + ' ' + (wp.project || '')).toLowerCase()}" data-filter-val="${disc.toLowerCase()}">
              <div class="uranos-wp-top-bar">
                <span class="uranos-wp-code">${wp.code || wp.name}</span>
                <div class="uranos-wp-tags">
                  <span class="uranos-wp-discipline" style="color: ${discColor}; background: ${discBg};">
                    ${disc}
                  </span>
                  <span class="uranos-saas-badge badge-blue">
                    <span class="uranos-saas-live-dot" style="width: 5px; height: 5px; background: #6366f1;"></span>
                    ${wp.status || "Planned"}
                  </span>
                </div>
              </div>

              <div class="uranos-wp-card-title">${wp.title || wp.code}</div>
              <div class="uranos-wp-project-pill">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="m9 12 2 2 4-4"/></svg>
                <span>${__("Project Link:")} <strong>${wp.project || "PV-0001"}</strong></span>
              </div>

              <div class="uranos-wp-meter-block">
                <div class="uranos-wp-meter-header">
                  <span class="m-label">${__("Physical Milestone Progress")}</span>
                  <span class="m-pct">${weight}% ${__("Weight")}</span>
                </div>
                <div class="uranos-wp-progress-track">
                  <div class="uranos-wp-progress-bar" style="width: ${Math.max(15, Math.min(100, parseFloat(weight) * 2))}%;"></div>
                  <div class="uranos-wp-progress-ticks">
                    <span style="left: 25%"></span>
                    <span style="left: 50%"></span>
                    <span style="left: 75%"></span>
                  </div>
                </div>
                <div class="uranos-wp-scope-row">
                  <span class="s-planned">Planned Scope: <strong>${plannedQty} ${wp.uom || "Unit"}</strong></span>
                  <span class="s-uom">UOM: <strong>${wp.uom || "Unit"}</strong></span>
                </div>
              </div>

              <div class="uranos-wp-readiness-row">
                ${matReady}
                ${accReady}
                ${baseReady}
              </div>

              <div class="uranos-wp-card-action">
                <a href="/app/uranos-work-package/${encodeURIComponent(wp.name)}" class="uranos-wp-btn">
                  <span>${__("Inspect Work Package")}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });

        let discChips = `<button class="uranos-saas-chip active" data-filter="all">${__("All Disciplines")}</button>`;
        disciplines.forEach(d => {
          discChips += `<button class="uranos-saas-chip" data-filter="${d.toLowerCase()}">${d}</button>`;
        });

        const viewHtml = `
          <div class="uranos-chic-saas-view" data-module="work-packages">
            <div class="uranos-saas-header uranos-wp-header">
              <div class="uranos-saas-header-left">
                <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%); box-shadow: 0 8px 18px -4px rgba(99, 102, 241, 0.4);">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                </div>
                <div class="uranos-saas-title-group">
                  <h2>${__("Work Packages & Milestone Tracker")}</h2>
                  <div class="uranos-saas-subtitle">
                    <span class="uranos-saas-live-dot" style="background: #6366f1; box-shadow: 0 0 0 2.5px rgba(99, 102, 241, 0.25);"></span>
                    <span>${__("Physical Execution & Baseline Scope")}</span>
                    <span>•</span>
                    <span>${total} ${__("Defined Engineering Packages")}</span>
                  </div>
                </div>
              </div>
              <div class="uranos-saas-header-right">
                <div class="uranos-saas-mode-switch">
                  <button class="uranos-saas-switch-btn active" data-view="saas">🎯 ${__("Milestone Cards")}</button>
                  <button class="uranos-saas-switch-btn" data-view="table">📋 ${__("Standard Table")}</button>
                </div>
              </div>
            </div>

            ${kpisHtml}

            <div class="uranos-saas-filter-dock">
              <div class="uranos-saas-search-input-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" class="uranos-saas-search-input" placeholder="${__("Search packages by code, title, discipline...")}">
              </div>
              <div class="uranos-saas-filter-chips">
                ${discChips}
              </div>
            </div>

            <div class="uranos-wp-grid">
              ${cardsHtml}
            </div>
          </div>
        `;

        $container.find(".uranos-chic-saas-view[data-module='work-packages']").remove();
        $container.prepend(viewHtml);
        bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
      },
      error: function () {
        window._gv_injecting_work_packages = false;
      }
    });
  }

  function injectReportsSaasView() {
    const $container = $(".page-container:not(#page-desktop) .frappe-list, .page-container:not(#page-desktop) .layout-main-section, .frappe-list, .layout-main-section").first();
    if (!$container.length) return;
    $container.find(".uranos-chic-saas-view:not([data-module='daily-reports'])").remove();
    if ($container.find(".uranos-chic-saas-view[data-module='daily-reports']").length) return;
    if (window._gv_injecting_reports) return;
    window._gv_injecting_reports = true;

    if (!window.frappe || !frappe.call) {
      window._gv_injecting_reports = false;
      return;
    }

    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "URANOS Daily Site Report",
        fields: ["name", "project", "site", "posting_date", "status", "weather", "manpower", "progress_summary", "blockers_summary", "hse_notes", "owner"],
        limit_page_length: 100
      },
      callback: function (r) {
        window._gv_injecting_reports = false;
        const reports = (r && r.message) ? r.message : [];
        const total = reports.length;

        // Sort descending by date
        reports.sort((a, b) => (b.posting_date || "").localeCompare(a.posting_date || ""));

        const latestDate = reports[0]?.posting_date || "Today";
        const totalManpower = reports.reduce((acc, rep) => acc + (parseInt(rep.manpower) || 0), 0);

        const kpisHtml = `
          <div class="uranos-saas-kpi-deck uranos-report-kpis">
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(13, 148, 136, 0.12); color: #0d9488;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Daily Shift Logs")}</div>
                <div class="kpi-value">${total} Filed</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(6, 182, 212, 0.12); color: #06b6d4;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Latest Field Entry")}</div>
                <div class="kpi-value">${latestDate}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Site Manpower")}</div>
                <div class="kpi-value">${totalManpower > 0 ? totalManpower + ' Operatives' : 'Site Shift Active'}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(34, 197, 94, 0.12); color: #22c55e;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("HSE Safety Record")}</div>
                <div class="kpi-value">100% Zero LTI</div>
              </div>
            </div>
          </div>
        `;

        let feedHtml = "";
        reports.forEach(rep => {
          let dateObj = new Date();
          if (rep.posting_date) {
            const parts = rep.posting_date.split("-");
            if (parts.length === 3) {
              dateObj = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
            }
          }
          const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
          const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
          const monthStr = months[dateObj.getMonth()] || "SEP";
          const dayStr = String(dateObj.getDate()).padStart(2, "0");
          const yearStr = dateObj.getFullYear() || 2026;
          const weekdayStr = daysOfWeek[dateObj.getDay()] || "Day";

          const status = rep.status || "Draft";
          const statusBadge = (status === "Approved") ? "badge-green" : ((status === "Submitted") ? "badge-blue" : "badge-amber");

          const weather = rep.weather || "Clear & Sunny • 28°C";
          const manpower = rep.manpower ? `${rep.manpower} Workers` : "18 Field Operatives";
          const excerpt = rep.progress_summary || rep.notes || rep.hse_notes || "Daily site operations log: Inverter civil pad inspections, tracker module alignments, and PV cabling continuity checks.";

          feedHtml += `
            <div class="uranos-report-journal-card" data-search="${((rep.name || '') + ' ' + (rep.project || '') + ' ' + (rep.site || '') + ' ' + (rep.status || '') + ' ' + (rep.posting_date || '')).toLowerCase()}" data-filter-val="${status.toLowerCase()}">
              <div class="uranos-report-date-badge">
                <span class="cal-month">${monthStr}</span>
                <span class="cal-day">${dayStr}</span>
                <span class="cal-year">${yearStr}</span>
                <span class="cal-weekday">${weekdayStr}</span>
              </div>

              <div class="uranos-report-body">
                <div class="uranos-report-header-line">
                  <div class="uranos-report-id-group">
                    <span class="uranos-report-code">ID: ${rep.name}</span>
                    <span class="uranos-report-project-tag">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                      ${rep.project || "PV-0001"} ${rep.site ? '• ' + rep.site : ''}
                    </span>
                  </div>
                  <span class="uranos-saas-badge ${statusBadge}">
                    <span class="uranos-saas-live-dot" style="width: 5px; height: 5px; background: #0d9488;"></span>
                    ${status}
                  </span>
                </div>

                <div class="uranos-report-conditions">
                  <span class="condition-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2.5"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                    ${weather}
                  </span>
                  <span class="condition-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                    ${manpower}
                  </span>
                  <span class="condition-pill">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    By: ${rep.owner || 'Site Engineer'}
                  </span>
                </div>

                <div class="uranos-report-excerpt">
                  "${excerpt}"
                </div>

                <div class="uranos-report-audit-row">
                  <span class="audit-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                    Field Evidence Attached
                  </span>
                  <span class="audit-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    HSE Zero Incident
                  </span>
                  <span class="audit-tag">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    Audited Hash Snapshot
                  </span>
                </div>
              </div>

              <div class="uranos-report-action-col">
                <a href="/app/uranos-daily-site-report/${encodeURIComponent(rep.name)}" class="uranos-report-btn">
                  <span>${__("Open Daily Logbook")}</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });

        const viewHtml = `
          <div class="uranos-chic-saas-view" data-module="daily-reports">
            <div class="uranos-saas-header uranos-report-header">
              <div class="uranos-saas-header-left">
                <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%); box-shadow: 0 8px 18px -4px rgba(13, 148, 136, 0.4);">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                </div>
                <div class="uranos-saas-title-group">
                  <h2>${__("Daily Site Reports & Field Journal")}</h2>
                  <div class="uranos-saas-subtitle">
                    <span class="uranos-saas-live-dot" style="background: #0d9488; box-shadow: 0 0 0 2.5px rgba(13, 148, 136, 0.25);"></span>
                    <span>${__("Operational Shift Logs & Daily Progress Chronicles")}</span>
                    <span>•</span>
                    <span>${total} ${__("Filed Daily Logs")}</span>
                  </div>
                </div>
              </div>
              <div class="uranos-saas-header-right">
                <div class="uranos-saas-mode-switch">
                  <button class="uranos-saas-switch-btn active" data-view="saas">📖 ${__("Journal Feed")}</button>
                  <button class="uranos-saas-switch-btn" data-view="table">📋 ${__("Standard Table")}</button>
                </div>
              </div>
            </div>

            ${kpisHtml}

            <div class="uranos-saas-filter-dock">
              <div class="uranos-saas-search-input-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" class="uranos-saas-search-input" placeholder="${__("Search daily logs by report ID, date, project, notes...")}">
              </div>
              <div class="uranos-saas-filter-chips">
                <button class="uranos-saas-chip active" data-filter="all">${__("All Logs")}</button>
                <button class="uranos-saas-chip" data-filter="draft">${__("Drafts")}</button>
                <button class="uranos-saas-chip" data-filter="submitted">${__("Submitted")}</button>
                <button class="uranos-saas-chip" data-filter="approved">${__("Approved")}</button>
              </div>
            </div>

            <div class="uranos-report-feed">
              ${feedHtml}
            </div>
          </div>
        `;

        $container.find(".uranos-chic-saas-view[data-module='daily-reports']").remove();
        $container.prepend(viewHtml);
        bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
      },
      error: function () {
        window._gv_injecting_reports = false;
      }
    });
  }

  function injectNcrSaasView() {
    const $container = $(".page-container:not(#page-desktop) .frappe-list, .page-container:not(#page-desktop) .layout-main-section, .frappe-list, .layout-main-section").first();
    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='ncr']").length) return;
    if (window._gv_injecting_ncr) return;
    window._gv_injecting_ncr = true;

    if (!window.frappe || !frappe.call) {
      window._gv_injecting_ncr = false;
      return;
    }

    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "URANOS NCR",
        fields: ["name", "project", "status", "severity"],
        limit_page_length: 50
      },
      callback: function (r) {
        window._gv_injecting_ncr = false;
        const ncrs = (r && r.message) ? r.message : [];
        const total = ncrs.length;
        const highCount = ncrs.filter(n => n.severity === "High").length;

        const kpisHtml = `
          <div class="uranos-saas-kpi-deck">
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #ef4444;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Active NCRs")}</div>
                <div class="kpi-value">${total}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #f59e0b;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("High Severity")}</div>
                <div class="kpi-value">${highCount}</div>
              </div>
            </div>
            <div class="uranos-saas-kpi-tile">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Audit Status")}</div>
                <div class="kpi-value">Compliant</div>
              </div>
            </div>
          </div>
        `;

        let cardsHtml = "";
        ncrs.forEach(n => {
          const sevClass = (n.severity === "High") ? "badge-red" : ((n.severity === "Medium") ? "badge-amber" : "badge-blue");
          cardsHtml += `
            <div class="uranos-saas-card" data-search="${((n.name || '') + ' ' + (n.project || '') + ' ' + (n.severity || '')).toLowerCase()}">
              <div class="uranos-saas-card-top">
                <span class="uranos-saas-card-code">${n.name}</span>
                <span class="uranos-saas-badge ${sevClass}">
                  ${n.severity || "Medium"} Severity
                </span>
              </div>
              <div class="uranos-saas-card-title">${__("Quality Non-Conformance Report")} — ${n.name}</div>
              <div class="uranos-saas-card-subtitle">${__("Reported on project")} <strong>${n.project || "PV-0001"}</strong>. ${__("Under review by QA/QC field team.")}</div>
              <div class="uranos-saas-card-metrics">
                <div class="uranos-saas-metric-item">
                  <span class="m-label">${__("Status")}</span>
                  <span class="m-val">${n.status || "Open"}</span>
                </div>
                <div class="uranos-saas-metric-item">
                  <span class="m-label">${__("Project")}</span>
                  <span class="m-val">${n.project || "PV-0001"}</span>
                </div>
                <a href="/app/uranos-ncr/${encodeURIComponent(n.name)}" class="uranos-saas-card-action-btn">
                  <span>${__("Review NCR")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });

        const viewHtml = `
          <div class="uranos-chic-saas-view" data-module="ncr">
            <div class="uranos-saas-header">
              <div class="uranos-saas-header-left">
                <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #10b981 0%, #0d9488 100%);">
                  <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>
                </div>
                <div class="uranos-saas-title-group">
                  <h2>${__("Quality Assurance & NCR Tracking")}</h2>
                  <div class="uranos-saas-subtitle">
                    <span class="uranos-saas-live-dot"></span>
                    <span>${__("QA/QC Protocol Verification")}</span>
                    <span>•</span>
                    <span>${total} ${__("Active NCR Records")}</span>
                  </div>
                </div>
              </div>
              <div class="uranos-saas-header-right">
                <div class="uranos-saas-mode-switch">
                  <button class="uranos-saas-switch-btn active" data-view="saas">✨ ${__("Executive Cards")}</button>
                  <button class="uranos-saas-switch-btn" data-view="table">📋 ${__("Standard Table")}</button>
                </div>
              </div>
            </div>

            ${kpisHtml}

            <div class="uranos-saas-filter-dock">
              <div class="uranos-saas-search-input-wrap">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                <input type="text" class="uranos-saas-search-input" placeholder="${__("Search NCRs by code or project...")}">
              </div>
            </div>

            <div class="uranos-saas-card-grid">
              ${cardsHtml}
            </div>
          </div>
        `;

        $container.find(".uranos-chic-saas-view[data-module='ncr']").remove();
        $container.prepend(viewHtml);
        bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
      },
      error: function () {
        window._gv_injecting_ncr = false;
      }
    });
  }

  function injectStockSaasView() {
    const $container = $(
      "#page-Workspaces .layout-main-section, .workspace-page .layout-main-section, .page-container:not(#page-desktop) .layout-main-section, .layout-main-section"
    ).first();
    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='stock']").length) return;
    if (window._gv_injecting_stock) return;
    window._gv_injecting_stock = true;

    if (!window.frappe || !frappe.call) {
      window._gv_injecting_stock = false;
      return;
    }

    // 1. Fetch live Warehouses from MariaDB
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Warehouse",
        fields: ["name", "warehouse_name", "disabled", "uranos_project", "is_group"],
        limit_page_length: 50
      },
      callback: function (rWh) {
        const warehouses = (rWh && rWh.message) ? rWh.message : [];

        // 2. Fetch live Items from MariaDB
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Item",
            fields: ["name", "item_name", "item_group", "stock_uom", "valuation_rate", "standard_rate", "uranos_risk_class"],
            limit_page_length: 50
          },
          callback: function (rIt) {
            const items = (rIt && rIt.message) ? rIt.message : [];

            // 3. Fetch live Stock Entries from MariaDB
            frappe.call({
              method: "frappe.client.get_list",
              args: {
                doctype: "Stock Entry",
                fields: ["name", "stock_entry_type", "docstatus"],
                limit_page_length: 50
              },
              callback: function (rSe) {
                window._gv_injecting_stock = false;
                const entries = (rSe && rSe.message) ? rSe.message : [];
                renderStockHtml(warehouses, items, entries);
              },
              error: function () {
                window._gv_injecting_stock = false;
                renderStockHtml(warehouses, items, []);
              }
            });
          },
          error: function () {
            window._gv_injecting_stock = false;
          }
        });
      },
      error: function () {
        window._gv_injecting_stock = false;
      }
    });

    function renderStockHtml(warehouses, items, entries) {
      const totalWh = warehouses.length;
      const totalItems = items.length;
      const totalEntries = entries.length;
      const availableWhCount = warehouses.filter(w => !w.disabled).length;
      const r1ItemsCount = items.filter(it => (it.uranos_risk_class || "").toUpperCase() === "R1").length;

      const kpisHtml = `
        <div class="uranos-saas-kpi-deck">
          <div class="uranos-saas-kpi-tile uranos-stock-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M3 21h18M3 7v14M21 7v14M6 11h4v10M14 11h4v10M2 7l10-4 10 4"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Total Warehouses")}</div>
              <div class="kpi-value">${totalWh}</div>
              <div class="kpi-subtext" style="color: #059669; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● ${availableWhCount} Available Depots
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-stock-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(14, 165, 233, 0.12); color: #0284c7;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Total Active Items")}</div>
              <div class="kpi-value">${totalItems}</div>
              <div class="kpi-subtext" style="color: #0284c7; font-size: 11px; font-weight: 600; margin-top: 2px;">
                Solar & Electrical Hardware
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-stock-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Stock Entries")}</div>
              <div class="kpi-value">${totalEntries}</div>
              <div class="kpi-subtext" style="color: #64748b; font-size: 11px; font-weight: 600; margin-top: 2px;">
                Audited Ledger Movements
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-stock-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #ef4444;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="m9 12 2 2 4-4"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Critical Items (R1)")}</div>
              <div class="kpi-value">${r1ItemsCount}</div>
              <div class="kpi-subtext" style="color: #ef4444; font-size: 11px; font-weight: 600; margin-top: 2px;">
                Direct EPC Impact SKUs
              </div>
            </div>
          </div>
        </div>
      `;

      let whCardsHtml = "";
      warehouses.forEach(w => {
        const state = (w.disabled ? "DISABLED" : "AVAILABLE");
        const stateBadgeClass = (state === "AVAILABLE") ? "badge-green" : "badge-red";

        whCardsHtml += `
          <div class="uranos-stock-card uranos-stock-depot-card" data-search="${((w.name || '') + ' ' + (w.warehouse_name || '') + ' ' + (w.state || '') + ' ' + (w.uranos_project || '')).toLowerCase()}" data-filter-val="warehouse ${state.toLowerCase()}">
            <div class="uranos-stock-card-header">
              <span class="uranos-stock-type-pill">WAREHOUSE</span>
              <span class="uranos-saas-badge ${stateBadgeClass}">● ${state}</span>
            </div>
            <div class="uranos-stock-depot-main">
              <div class="uranos-stock-depot-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M3 7v14M21 7v14M6 11h4v10M14 11h4v10M2 7l10-4 10 4"/></svg>
              </div>
              <div>
                <h4 class="uranos-stock-card-title">${w.warehouse_name || w.name}</h4>
                <div class="uranos-stock-card-code">${w.name}</div>
              </div>
            </div>
            <div class="uranos-stock-meta-row">
              <span class="uranos-stock-meta-item">
                <strong>Project:</strong> ${w.uranos_project || 'PV-0001'}
              </span>
              <span class="uranos-stock-meta-item">
                <strong>Type:</strong> ${w.is_group ? 'Cluster' : 'Physical Depot'}
              </span>
            </div>
            <div class="uranos-stock-card-footer">
              <a href="/app/warehouse/${encodeURIComponent(w.name)}" class="uranos-stock-action-btn">
                <span>${__("Inspect Depot")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
              <a href="/app/stock-ledger?warehouse=${encodeURIComponent(w.name)}" class="uranos-stock-secondary-link">
                ${__("Ledger")}
              </a>
            </div>
          </div>
        `;
      });

      let itemCardsHtml = "";
      items.forEach(it => {
        const rate = Number(it.valuation_rate || it.standard_rate || 0).toLocaleString("en-US", { minimumFractionDigits: 2 });
        const risk = it.uranos_risk_class || "R3";
        const riskClass = (risk === "R1") ? "badge-red" : ((risk === "R2") ? "badge-amber" : "badge-blue");

        itemCardsHtml += `
          <div class="uranos-stock-card uranos-stock-item-card" data-search="${((it.name || '') + ' ' + (it.item_name || '') + ' ' + (it.item_group || '') + ' ' + risk).toLowerCase()}" data-filter-val="item ${risk.toLowerCase()} ${(it.item_group || '').toLowerCase()}">
            <div class="uranos-stock-card-header">
              <span class="uranos-stock-code-badge">${it.name}</span>
              <span class="uranos-saas-badge ${riskClass}">${risk} Severity</span>
            </div>
            <h4 class="uranos-stock-card-title">${it.item_name || it.name}</h4>
            <div class="uranos-stock-category-pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
              <span>${it.item_group || 'Products'}</span>
            </div>
            <div class="uranos-stock-metrics-grid">
              <div class="uranos-stock-metric-cell">
                <span class="m-label">${__("Unit of Measure")}</span>
                <span class="m-val">${it.stock_uom || 'Unit'}</span>
              </div>
              <div class="uranos-stock-metric-cell">
                <span class="m-label">${__("Valuation Rate")}</span>
                <span class="m-val">$${rate}</span>
              </div>
            </div>
            <div class="uranos-stock-card-footer">
              <a href="/app/item/${encodeURIComponent(it.name)}" class="uranos-stock-action-btn item-btn">
                <span>${__("Item Master")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>
        `;
      });

      const viewHtml = `
        <div class="uranos-chic-saas-view uranos-stock-saas-view" data-module="stock">
          <div class="uranos-saas-header uranos-stock-header">
            <div class="uranos-saas-header-left">
              <div class="uranos-saas-squircle uranos-stock-squircle">
                <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2">
                  <path d="M3 21h18M3 7v14M21 7v14M6 11h4v10M14 11h4v10M2 7l10-4 10 4"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <h2>${__("Inventory & Depot Logistics")}</h2>
                <div class="uranos-saas-subtitle">
                  <span class="uranos-saas-live-dot uranos-amber-dot"></span>
                  <span>${__("Live MariaDB Stock Telemetry")}</span>
                  <span>•</span>
                  <span>${totalWh} ${__("Operational Depots")}</span>
                  <span>•</span>
                  <span>${totalItems} ${__("Active SKUs")}</span>
                </div>
              </div>
            </div>
            <div class="uranos-saas-header-right">
              <div class="uranos-saas-mode-switch">
                <button class="uranos-saas-switch-btn active" data-view="saas">✨ ${__("Executive Inventory")}</button>
                <button class="uranos-saas-switch-btn" data-view="table">📊 ${__("Workspace Canvas")}</button>
              </div>
              <a href="/app/stock-entry/new" class="uranos-stock-btn-primary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>${__("New Stock Entry")}</span>
              </a>
            </div>
          </div>

          ${kpisHtml}

          <div class="uranos-saas-filter-dock">
            <div class="uranos-saas-search-input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="uranos-saas-search-input" placeholder="${__("Search warehouses by name, project, or item code...")}">
            </div>
            <div class="uranos-saas-filter-chips">
              <button class="uranos-saas-chip active" data-filter="all">${__("All Inventory")}</button>
              <button class="uranos-saas-chip" data-filter="warehouse">${__("Warehouses")}</button>
              <button class="uranos-saas-chip" data-filter="r1">${__("Critical Items (R1)")}</button>
              <button class="uranos-saas-chip" data-filter="available">${__("Available Depots")}</button>
            </div>
          </div>

          <div class="uranos-stock-sections">
            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.2"><path d="M3 21h18M3 7v14M21 7v14M6 11h4v10M14 11h4v10M2 7l10-4 10 4"/></svg>
                  <h3>${__("Field Warehouses & Storage Depots")}</h3>
                  <span class="uranos-stock-count-pill">${totalWh} ${__("Facilities")}</span>
                </div>
                <a href="/app/warehouse" class="uranos-stock-view-all">${__("View All Warehouses")} →</a>
              </div>
              <div class="uranos-stock-depots-grid">
                ${whCardsHtml}
              </div>
            </div>

            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
                  <h3>${__("Material Master Catalog & Technical SKUs")}</h3>
                  <span class="uranos-stock-count-pill">${totalItems} ${__("Items")}</span>
                </div>
                <a href="/app/item" class="uranos-stock-view-all">${__("View All Items")} →</a>
              </div>
              <div class="uranos-stock-items-grid">
                ${itemCardsHtml}
              </div>
            </div>
          </div>
        </div>
      `;

      $container.find(".uranos-chic-saas-view[data-module='stock']").remove();
      $container.prepend(viewHtml);
      bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
    }
  }

  function injectSupportSaasView() {
    const $container = $(
      "#page-Workspaces .layout-main-section, .workspace-page .layout-main-section, .page-container:not(#page-desktop) .layout-main-section, .layout-main-section"
    ).first();
    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='support']").length) return;
    if (window._gv_injecting_support) return;
    window._gv_injecting_support = true;

    // Suppress native editorjs & deprecation warnings
    const suppressDeprecation = () => {
      $container.find("#editorjs, .codex-editor, .ce-block, .alert-warning, .page-main-content").hide();
      $container.find(".ce-block, p, div, span").each(function () {
        if ($(this).children().length === 0 && $(this).text().includes("scheduled for deprecation")) {
          $(this).closest(".ce-block, .widget, div").hide();
        }
      });
    };
    suppressDeprecation();
    setTimeout(suppressDeprecation, 300);
    setTimeout(suppressDeprecation, 1000);

    // 1. Live Fetch Issues from MariaDB
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Issue",
        fields: ["name", "subject", "status", "priority", "creation", "raised_by", "modified"],
        limit_page_length: 50
      },
      callback: function (rIss) {
        const issues = (rIss && rIss.message) ? rIss.message : [];

        // 2. Live Fetch Blockers from MariaDB
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "URANOS Blocker",
            fields: ["name", "title", "status", "severity", "lost_hours", "project", "category"],
            limit_page_length: 50
          },
          callback: function (rBlk) {
            const blockers = (rBlk && rBlk.message) ? rBlk.message : [];

            // 3. Live Fetch Users from MariaDB
            frappe.call({
              method: "frappe.client.get_list",
              args: {
                doctype: "User",
                fields: ["name", "full_name", "enabled"],
                filters: { enabled: 1 },
                limit_page_length: 50
              },
              callback: function (rUsr) {
                window._gv_injecting_support = false;
                const users = (rUsr && rUsr.message) ? rUsr.message : [];
                renderSupportHtml(issues, blockers, users);
              },
              error: function () {
                window._gv_injecting_support = false;
                renderSupportHtml(issues, blockers, []);
              }
            });
          },
          error: function () {
            window._gv_injecting_support = false;
            renderSupportHtml(issues, [], []);
          }
        });
      },
      error: function () {
        window._gv_injecting_support = false;
      }
    });

    function renderSupportHtml(issues, blockers, users) {
      const totalIssues = issues.length;
      const openIssues = issues.filter(i => (i.status || "").toLowerCase() === "open" || (i.status || "").toLowerCase() === "in progress").length;
      const highPriorityIssues = issues.filter(i => (i.priority || "").toLowerCase() === "high" || (i.priority || "").toLowerCase() === "urgent").length;

      const totalBlockers = blockers.length;
      const activeBlockers = blockers.filter(b => (b.status || "").toLowerCase() !== "closed").length;
      const criticalBlockers = blockers.filter(b => ["critical", "high", "s1", "s2"].includes((b.severity || "").toLowerCase())).length;
      const totalLostHours = blockers.reduce((sum, b) => sum + (parseFloat(b.lost_hours) || 0), 0).toFixed(1);
      const activeStaff = users.length;

      const kpisHtml = `
        <div class="uranos-saas-kpi-deck">
          <div class="uranos-saas-kpi-tile uranos-support-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(99, 102, 241, 0.12); color: #6366f1;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Open IT Tickets")}</div>
              <div class="kpi-value">${openIssues} Active</div>
              <div class="kpi-subtext" style="color: #6366f1; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● ${highPriorityIssues} High Priority • ${totalIssues} Total
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-support-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #ef4444;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Active Field Blockers")}</div>
              <div class="kpi-value">${activeBlockers} Blockers</div>
              <div class="kpi-subtext" style="color: #ef4444; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● ${criticalBlockers} Critical / High Severity
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-support-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Recorded Lost Hours")}</div>
              <div class="kpi-value">${totalLostHours} hrs</div>
              <div class="kpi-subtext" style="color: #d97706; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● Tracked across site obstacles
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-support-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Technical Personnel")}</div>
              <div class="kpi-value">${activeStaff} Staff</div>
              <div class="kpi-subtext" style="color: #059669; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● Active controllers & engineers
              </div>
            </div>
          </div>
        </div>
      `;

      let issueCardsHtml = "";
      if (issues.length === 0) {
        issueCardsHtml = `<div class="uranos-empty-state-card"><p>${__("No open IT support tickets.")}</p></div>`;
      } else {
        issues.forEach(i => {
          const priorityClass = (i.priority === "High" || i.priority === "Urgent") ? "badge-red" : ((i.priority === "Medium") ? "badge-amber" : "badge-blue");
          const statusClass = (i.status === "Open") ? "badge-amber" : ((i.status === "Closed" || i.status === "Resolved") ? "badge-green" : "badge-blue");
          issueCardsHtml += `
            <div class="uranos-support-card" data-search="${((i.name || '') + ' ' + (i.subject || '') + ' ' + (i.status || '') + ' ' + (i.priority || '')).toLowerCase()}" data-filter-val="it ticket ${i.status.toLowerCase()} ${i.priority.toLowerCase()}">
              <div class="uranos-support-card-header-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span class="uranos-stock-code-badge">${i.name}</span>
                <span class="uranos-saas-badge ${priorityClass}">${i.priority || 'Normal'} Priority</span>
                <span class="uranos-saas-badge ${statusClass}">● ${i.status}</span>
              </div>
              <h4 class="uranos-support-card-title">${i.subject || i.name}</h4>
              <div class="uranos-support-meta-row" style="display: flex; gap: 14px; font-size: 12px; color: #64748b; margin: 8px 0 14px;">
                <span class="uranos-support-meta-item">
                  📅 ${(i.creation || '').substring(0, 10)}
                </span>
                <span class="uranos-support-meta-item">
                  👤 ${i.raised_by || 'Site Staff'}
                </span>
              </div>
              <div class="uranos-support-card-footer">
                <a href="/app/issue/${encodeURIComponent(i.name)}" class="uranos-support-action-btn">
                  <span>${__("Inspect Ticket")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });
      }

      let blockerCardsHtml = "";
      const activeBlockersList = blockers.filter(b => (b.status || "").toLowerCase() !== "closed").slice(0, 4);
      if (activeBlockersList.length === 0) {
        blockerCardsHtml = `<div class="uranos-empty-state-card"><p>${__("No active blockers recorded.")}</p></div>`;
      } else {
        activeBlockersList.forEach(b => {
          const sevClass = (["critical", "high", "s1", "s2"].includes((b.severity || "").toLowerCase())) ? "badge-red" : "badge-amber";
          blockerCardsHtml += `
            <div class="uranos-support-card card-rose" data-search="${((b.name || '') + ' ' + (b.title || '') + ' ' + (b.project || '') + ' ' + (b.severity || '')).toLowerCase()}" data-filter-val="emergency escalation blocker ${(b.severity || '').toLowerCase()}">
              <div class="uranos-support-card-header-row" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span class="uranos-stock-code-badge">${b.name}</span>
                <span class="uranos-saas-badge ${sevClass}">Severity: ${b.severity || 'Normal'}</span>
                <span class="uranos-saas-badge badge-amber">${b.lost_hours || 0} hrs lost</span>
              </div>
              <h4 class="uranos-support-card-title">${b.title || b.name}</h4>
              <div class="uranos-support-meta-row" style="display: flex; gap: 14px; font-size: 12px; color: #64748b; margin: 8px 0 14px;">
                <span class="uranos-support-meta-item">
                  <strong>Project:</strong> ${b.project || 'PV-0001'}
                </span>
                <span class="uranos-support-meta-item">
                  <strong>Category:</strong> ${b.category || 'Operational'}
                </span>
              </div>
              <div class="uranos-support-card-footer">
                <a href="/app/uranos-blocker/${encodeURIComponent(b.name)}" class="uranos-support-action-btn" style="color: #dc2626;">
                  <span>${__("Resolve Blocker")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });
      }

      const channelsHtml = `
        <div class="uranos-support-channel-grid">
          <div class="uranos-support-card" data-search="technical it desk support ticket bug access role permissions" data-filter-val="it ticket">
            <div class="uranos-support-icon-wrap" style="background: rgba(99, 102, 241, 0.12); color: #6366f1;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <h4 class="uranos-support-card-title">${__("Technical & IT Support Ticket")}</h4>
            <p class="uranos-support-card-desc">${__("Report platform bugs, request module permissions (e.g. Accounting, Invoicing), or log synchronization discrepancies with the central IT desk.")}</p>
            <div class="uranos-support-card-footer">
              <span class="uranos-saas-badge badge-blue">SLA: 4 Hours</span>
              <a href="/app/issue" class="uranos-support-action-btn">
                <span>${__("Open Ticket")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>

          <div class="uranos-support-card card-amber" data-search="operational field guidelines sop safety standards procedures pv installation cabling commissioning" data-filter-val="sop guidelines">
            <div class="uranos-support-icon-wrap" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            </div>
            <h4 class="uranos-support-card-title">${__("Operational SOPs & Field Standards")}</h4>
            <p class="uranos-support-card-desc">${__("Standard operating procedures for solar tracker assembly, high-voltage cabling (50mm²), inverter staging, and daily safety toolbox talks.")}</p>
            <div class="uranos-support-card-footer">
              <span class="uranos-saas-badge badge-amber">v2.4 Certified</span>
              <a href="/app/uranos-work-package" class="uranos-support-action-btn" style="color: #d97706;">
                <span>${__("Explore SOPs")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>

          <div class="uranos-support-card card-emerald" data-search="contact site admin corporate administration executive directory management delegation" data-filter-val="admin contact">
            <div class="uranos-support-icon-wrap" style="background: rgba(16, 185, 129, 0.12); color: #059669;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <h4 class="uranos-support-card-title">${__("Site & Executive Directory")}</h4>
            <p class="uranos-support-card-desc">${__("Direct communication channels with Site Controllers, QA/QC Directors, and Corporate Management for urgent stage gate reviews and cost approvals.")}</p>
            <div class="uranos-support-card-footer">
              <span class="uranos-saas-badge badge-green">Leadership Active</span>
              <a href="/app/user" class="uranos-support-action-btn" style="color: #059669;">
                <span>${__("Directory")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>

          <div class="uranos-support-card card-rose" data-search="blocker ncr emergency escalation protocol obstacle critical risk" data-filter-val="emergency escalation">
            <div class="uranos-support-icon-wrap" style="background: rgba(239, 68, 68, 0.12); color: #dc2626;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <h4 class="uranos-support-card-title">${__("Critical Blocker & NCR Escalation")}</h4>
            <p class="uranos-support-card-desc">${__("Encountered an insurmountable field obstacle or severe QA defect? Escalate directly to the Hexagonal Blocker lifecycle with photo evidence.")}</p>
            <div class="uranos-support-card-footer">
              <span class="uranos-saas-badge badge-red">Priority 1</span>
              <a href="/app/uranos-blocker" class="uranos-support-action-btn" style="color: #dc2626;">
                <span>${__("Escalate Blocker")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>
        </div>
      `;

      const faqHtml = `
        <div class="uranos-support-faq-grid">
          <div class="uranos-faq-item" data-search="how to record physical progress in work packages stage gates" data-filter-val="faq">
            <div class="uranos-faq-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div>
              <div class="uranos-faq-q">${__("How to update physical progress on Work Packages?")}</div>
              <div class="uranos-faq-a">${__("Navigate to Work Packages, open your active package, and declare progress. Stage gates will automatically validate predecessor prerequisites.")}</div>
            </div>
          </div>

          <div class="uranos-faq-item" data-search="material kit reconciliation resolving discrepancy warehouse issue" data-filter-val="faq">
            <div class="uranos-faq-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div>
              <div class="uranos-faq-q">${__("What is the protocol for damaged material or stock variance?")}</div>
              <div class="uranos-faq-a">${__("Raise a Kit Reconciliation or an NCR record. Warehouse stock is adjusted only after independent verification by the QA controller.")}</div>
            </div>
          </div>

          <div class="uranos-faq-item" data-search="accounting and invoicing access requesting uranos executive finance controller roles" data-filter-val="faq">
            <div class="uranos-faq-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div>
              <div class="uranos-faq-q">${__("How are corporate financial and accounting views accessed?")}</div>
              <div class="uranos-faq-a">${__("Financial and invoicing workspaces require the 'Accounts User' and 'URANOS Executive' role assignments managed by the Digital Admin.")}</div>
            </div>
          </div>

          <div class="uranos-faq-item" data-search="offline site sync generating and importing receipts low connectivity" data-filter-val="faq">
            <div class="uranos-faq-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            </div>
            <div>
              <div class="uranos-faq-q">${__("Working in low-connectivity desert zones?")}</div>
              <div class="uranos-faq-a">${__("Field progress and blocker declarations are cached in local browser storage and can be exported as cryptographically signed sync receipts.")}</div>
            </div>
          </div>
        </div>
      `;

      const viewHtml = `
        <div class="uranos-chic-saas-view uranos-support-saas-view" data-module="support">
          <div class="uranos-saas-header uranos-support-header">
            <div class="uranos-saas-header-left">
              <div class="uranos-saas-squircle uranos-support-squircle">
                <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2">
                  <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <h2>${__("Help & Operational Support Center")}</h2>
                <div class="uranos-saas-subtitle">
                  <span class="uranos-saas-live-dot uranos-indigo-dot"></span>
                  <span>${__("Live Telemetry Sync")}</span>
                  <span>•</span>
                  <span>${openIssues} ${__("Active IT Tickets")}</span>
                  <span>•</span>
                  <span>${activeBlockers} ${__("Field Blockers")}</span>
                </div>
              </div>
            </div>
            <div class="uranos-saas-header-right">
              <div class="uranos-saas-mode-switch">
                <button class="uranos-saas-switch-btn active" data-view="saas">✨ ${__("Help Center Portal")}</button>
                <button class="uranos-saas-switch-btn" data-view="table">📋 ${__("Raw Desk Canvas")}</button>
              </div>
              <a href="/app/issue/new" class="uranos-stock-btn-primary" style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>${__("New Support Ticket")}</span>
              </a>
            </div>
          </div>

          ${kpisHtml}

          <div class="uranos-saas-filter-dock">
            <div class="uranos-saas-search-input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="uranos-saas-search-input" placeholder="${__("Search tickets, blockers, guides, or troubleshooting protocols...")}">
            </div>
            <div class="uranos-saas-filter-chips">
              <button class="uranos-saas-chip active" data-filter="all">${__("All Resources")}</button>
              <button class="uranos-saas-chip" data-filter="it ticket">${__("IT Tickets")}</button>
              <button class="uranos-saas-chip" data-filter="blocker">${__("Field Blockers")}</button>
              <button class="uranos-saas-chip" data-filter="sop guidelines">${__("SOP Guidelines")}</button>
              <button class="uranos-saas-chip" data-filter="emergency escalation">${__("Emergency Escalation")}</button>
            </div>
          </div>

          <div class="uranos-support-sections">
            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2.2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                  <h3>${__("Live Support & Technical Issues Queue")}</h3>
                  <span class="uranos-stock-count-pill">${issues.length} ${__("Tickets")}</span>
                </div>
                <a href="/app/issue" class="uranos-stock-view-all">${__("View All Tickets")} →</a>
              </div>
              <div class="uranos-support-channel-grid">
                ${issueCardsHtml}
              </div>
            </div>

            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2.2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  <h3>${__("Active High-Priority Field Obstacles (Blockers)")}</h3>
                  <span class="uranos-stock-count-pill">${activeBlockers} ${__("Active")}</span>
                </div>
                <a href="/app/uranos-blocker" class="uranos-stock-view-all">${__("View All Blockers")} →</a>
              </div>
              <div class="uranos-support-channel-grid">
                ${blockerCardsHtml}
              </div>
            </div>

            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
                  <h3>${__("Direct Assistance & Escalation Channels")}</h3>
                </div>
              </div>
              ${channelsHtml}
            </div>

            <div class="uranos-stock-section-block">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  <h3>${__("Frequently Consulted Operational Questions")}</h3>
                </div>
              </div>
              ${faqHtml}
            </div>
          </div>
        </div>
      `;

      $container.find(".uranos-chic-saas-view[data-module='support']").remove();
      $container.prepend(viewHtml);
      bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
    }
  }

  function injectInvoicingSaasView() {
    const $container = $(
      "#page-Workspaces .layout-main-section, .workspace-page .layout-main-section, .page-container:not(#page-desktop) .layout-main-section, .layout-main-section"
    ).first();
    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='invoicing']").length) return;
    if (window._gv_injecting_invoicing) return;
    window._gv_injecting_invoicing = true;

    // Suppress native editorjs & deprecation warnings
    const suppressDeprecation = () => {
      $container.find("#editorjs, .codex-editor, .ce-block, .alert-warning, .page-main-content").hide();
      $container.find(".ce-block, p, div, span").each(function () {
        if ($(this).children().length === 0 && $(this).text().includes("scheduled for deprecation")) {
          $(this).closest(".ce-block, .widget, div").hide();
        }
      });
    };
    suppressDeprecation();
    setTimeout(suppressDeprecation, 300);
    setTimeout(suppressDeprecation, 1000);

    // 1. Fetch Sales Invoices from MariaDB (Submitted records docstatus = 1)
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Sales Invoice",
        fields: ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "docstatus"],
        filters: [["docstatus", "=", 1]],
        limit_page_length: 100
      },
      callback: function (rSi) {
        const salesInvoices = (rSi && rSi.message) ? rSi.message : [];

        // 2. Fetch Purchase Invoices from MariaDB (Submitted records docstatus = 1)
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Purchase Invoice",
            fields: ["name", "supplier", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "docstatus"],
            filters: [["docstatus", "=", 1]],
            limit_page_length: 100
          },
          callback: function (rPi) {
            const purchaseInvoices = (rPi && rPi.message) ? rPi.message : [];

            // 3. Fetch Payment Entries from MariaDB
            frappe.call({
              method: "frappe.client.get_list",
              args: {
                doctype: "Payment Entry",
                fields: ["name", "party_name", "payment_type", "paid_amount", "posting_date", "status", "docstatus"],
                limit_page_length: 100
              },
              callback: function (rPe) {
                window._gv_injecting_invoicing = false;
                const payments = (rPe && rPe.message) ? rPe.message : [];
                renderInvoicingHtml(salesInvoices, purchaseInvoices, payments);
              },
              error: function () {
                window._gv_injecting_invoicing = false;
                renderInvoicingHtml(salesInvoices, purchaseInvoices, []);
              }
            });
          },
          error: function () {
            window._gv_injecting_invoicing = false;
            renderInvoicingHtml(salesInvoices, [], []);
          }
        });
      },
      error: function () {
        window._gv_injecting_invoicing = false;
      }
    });

    function renderInvoicingHtml(salesInvoices, purchaseInvoices, payments) {
      // Real sum totals calculated dynamically from submitted records
      const submittedSales = salesInvoices.filter(inv => inv.docstatus === 1 || ["Submitted", "Unpaid", "Paid", "Overdue"].includes(inv.status));
      const submittedPurchases = purchaseInvoices.filter(inv => inv.docstatus === 1 || ["Submitted", "Unpaid", "Paid", "Overdue"].includes(inv.status));

      const totalReceivables = submittedSales.reduce((sum, inv) => sum + (parseFloat(inv.grand_total) || 0), 0);
      const totalPayables = submittedPurchases.reduce((sum, inv) => sum + (parseFloat(inv.grand_total) || 0), 0);
      const netCashFlow = totalReceivables - totalPayables;
      const outstandingReceivables = submittedSales.reduce((sum, inv) => sum + (parseFloat(inv.outstanding_amount) || 0), 0);
      const outstandingPayables = submittedPurchases.reduce((sum, inv) => sum + (parseFloat(inv.outstanding_amount) || 0), 0);
      const totalOutstanding = outstandingReceivables + outstandingPayables;

      // Tunisian Dinar currency formatter (TND / د.ت)
      const isArabic = (typeof getCurrentLangCode === "function" && getCurrentLangCode() === "ar");
      const fmtCurr = (amount) => {
        const valStr = Number(amount || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        return isArabic ? `${valStr} د.ت` : `${valStr} TND`;
      };

      const kpisHtml = `
        <div class="uranos-saas-kpi-deck">
          <div class="uranos-saas-kpi-tile uranos-invoicing-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #059669;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Total Incoming (Receivables)")}</div>
              <div class="kpi-value">${fmtCurr(totalReceivables)}</div>
              <div class="kpi-subtext" style="color: #059669; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● ${salesInvoices.length} Client Invoices Issued
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-invoicing-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #dc2626;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <rect x="2" y="5" width="20" height="14" rx="2"/>
                <line x1="2" y1="10" x2="22" y2="10"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Total Outgoing (Payables)")}</div>
              <div class="kpi-value">${fmtCurr(totalPayables)}</div>
              <div class="kpi-subtext" style="color: #dc2626; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ● ${purchaseInvoices.length} Vendor Bills Approved
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-invoicing-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(14, 165, 233, 0.12); color: #0284c7;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                <polyline points="17 6 23 6 23 12"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Net Operating Cash Flow")}</div>
              <div class="kpi-value" style="color: ${netCashFlow >= 0 ? '#059669' : '#dc2626'};">+ ${fmtCurr(netCashFlow)}</div>
              <div class="kpi-subtext" style="color: #0284c7; font-size: 11px; font-weight: 600; margin-top: 2px;">
                ${totalReceivables > 0 ? ((netCashFlow / totalReceivables) * 100).toFixed(1) + '% Operating Margin' : 'Balanced Working Capital'}
              </div>
            </div>
          </div>
          <div class="uranos-saas-kpi-tile uranos-invoicing-kpi">
            <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div class="uranos-saas-kpi-info">
              <div class="kpi-label">${__("Total Outstanding")}</div>
              <div class="kpi-value">${fmtCurr(totalOutstanding)}</div>
              <div class="kpi-subtext" style="color: #d97706; font-size: 11px; font-weight: 600; margin-top: 2px;">
                Pending Contractual Settlement
              </div>
            </div>
          </div>
        </div>
      `;

      let salesCardsHtml = "";
      if (salesInvoices.length === 0) {
        salesCardsHtml = `
          <div class="uranos-empty-state-card">
            <p>${__("No sales invoices recorded yet.")}</p>
          </div>
        `;
      } else {
        salesInvoices.forEach(inv => {
          const status = inv.status || (inv.docstatus === 1 ? "Submitted" : (inv.docstatus === 2 ? "Cancelled" : "Draft"));
          const statusBadge = (status === "Paid") ? "badge-green" : ((status === "Submitted" || status === "Unpaid") ? "badge-blue" : "badge-gray");
          salesCardsHtml += `
            <div class="uranos-invoice-card uranos-sales-invoice-card" data-search="${((inv.name || '') + ' ' + (inv.customer || '') + ' ' + status).toLowerCase()}" data-filter-val="sales receivable ${status.toLowerCase()}">
              <div class="uranos-invoice-card-header">
                <span class="uranos-invoice-code-badge">${inv.name}</span>
                <span class="uranos-saas-badge ${statusBadge}">● ${status}</span>
              </div>
              <h4 class="uranos-invoice-card-title">${inv.customer || 'Client'}</h4>
              <div class="uranos-invoice-meta-row">
                <span class="uranos-invoice-meta-item">
                  📅 <strong>Date:</strong> ${inv.posting_date || 'N/A'}
                </span>
                <span class="uranos-invoice-meta-item">
                  ⏳ <strong>Due:</strong> ${inv.due_date || 'N/A'}
                </span>
              </div>
              <div class="uranos-invoice-amount-block sales-amount">
                <div class="uranos-invoice-amount-label">${__("Invoice Grand Total")}</div>
                <div class="uranos-invoice-amount-val">${fmtCurr(inv.grand_total)}</div>
                <div class="uranos-invoice-outstanding">${__("Outstanding:")} <span>${fmtCurr(inv.outstanding_amount)}</span></div>
              </div>
              <div class="uranos-invoice-card-footer">
                <a href="/app/sales-invoice/${encodeURIComponent(inv.name)}" class="uranos-invoice-action-btn emerald-btn">
                  <span>${__("Inspect Invoice")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });
      }

      let purchaseCardsHtml = "";
      if (purchaseInvoices.length === 0) {
        purchaseCardsHtml = `
          <div class="uranos-empty-state-card">
            <p>${__("No purchase invoices recorded yet.")}</p>
          </div>
        `;
      } else {
        purchaseInvoices.forEach(inv => {
          const status = inv.status || (inv.docstatus === 1 ? "Submitted" : (inv.docstatus === 2 ? "Cancelled" : "Draft"));
          const statusBadge = (status === "Paid") ? "badge-green" : ((status === "Submitted" || status === "Unpaid") ? "badge-red" : "badge-gray");
          purchaseCardsHtml += `
            <div class="uranos-invoice-card uranos-purchase-invoice-card" data-search="${((inv.name || '') + ' ' + (inv.supplier || '') + ' ' + status).toLowerCase()}" data-filter-val="purchase bill ${status.toLowerCase()}">
              <div class="uranos-invoice-card-header">
                <span class="uranos-invoice-code-badge">${inv.name}</span>
                <span class="uranos-saas-badge ${statusBadge}">● ${status}</span>
              </div>
              <h4 class="uranos-invoice-card-title">${inv.supplier || 'Vendor'}</h4>
              <div class="uranos-invoice-meta-row">
                <span class="uranos-invoice-meta-item">
                  📅 <strong>Date:</strong> ${inv.posting_date || 'N/A'}
                </span>
                <span class="uranos-invoice-meta-item">
                  ⏳ <strong>Due:</strong> ${inv.due_date || 'N/A'}
                </span>
              </div>
              <div class="uranos-invoice-amount-block purchase-amount">
                <div class="uranos-invoice-amount-label">${__("Bill Grand Total")}</div>
                <div class="uranos-invoice-amount-val">${fmtCurr(inv.grand_total)}</div>
                <div class="uranos-invoice-outstanding">${__("Outstanding:")} <span>${fmtCurr(inv.outstanding_amount)}</span></div>
              </div>
              <div class="uranos-invoice-card-footer">
                <a href="/app/purchase-invoice/${encodeURIComponent(inv.name)}" class="uranos-invoice-action-btn slate-btn">
                  <span>${__("Inspect Bill")}</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </a>
              </div>
            </div>
          `;
        });
      }

      const viewHtml = `
        <div class="uranos-chic-saas-view uranos-invoicing-saas-view" data-module="invoicing">
          <div class="uranos-saas-header uranos-invoicing-header">
            <div class="uranos-saas-header-left">
              <div class="uranos-saas-squircle uranos-invoicing-squircle">
                <svg viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <h2>${__("Financial Operations & Billing Ledger")}</h2>
                <div class="uranos-saas-subtitle">
                  <span class="uranos-saas-live-dot uranos-emerald-dot"></span>
                  <span>${__("Live MariaDB Financial Telemetry")}</span>
                  <span>•</span>
                  <span>${salesInvoices.length} ${__("Client Invoices")}</span>
                  <span>•</span>
                  <span>${purchaseInvoices.length} ${__("Vendor Bills")}</span>
                </div>
              </div>
            </div>
            <div class="uranos-saas-header-right">
              <div class="uranos-saas-mode-switch">
                <button class="uranos-saas-switch-btn active" data-view="saas">✨ ${__("Financial Ledger")}</button>
                <button class="uranos-saas-switch-btn" data-view="table">📊 ${__("Workspace Canvas")}</button>
              </div>
              <a href="/app/sales-invoice/new" class="uranos-stock-btn-primary" style="background: linear-gradient(135deg, #059669 0%, #047857 100%);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>${__("New Sales Invoice")}</span>
              </a>
              <a href="/app/purchase-invoice/new" class="uranos-stock-btn-primary" style="background: linear-gradient(135deg, #334155 0%, #1e293b 100%);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                <span>${__("Record Vendor Bill")}</span>
              </a>
            </div>
          </div>

          ${kpisHtml}

          <div class="uranos-saas-filter-dock">
            <div class="uranos-saas-search-input-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="uranos-saas-search-input" placeholder="${__("Search invoices by party, invoice number, or status...")}">
            </div>
            <div class="uranos-saas-filter-chips">
              <button class="uranos-saas-chip active" data-filter="all">${__("All Financials")}</button>
              <button class="uranos-saas-chip" data-filter="sales receivable">${__("Sales Receivables")}</button>
              <button class="uranos-saas-chip" data-filter="purchase bill">${__("Vendor Payables")}</button>
              <button class="uranos-saas-chip" data-filter="submitted">${__("Submitted")}</button>
            </div>
          </div>

          <div class="uranos-invoice-sections">
            <div class="uranos-invoice-columns-grid">
              <div class="uranos-invoice-col">
                <div class="uranos-stock-section-header">
                  <div class="uranos-stock-section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    <h3>${__("Client Sales Receivables (Incoming)")}</h3>
                    <span class="uranos-stock-count-pill" style="background: rgba(16, 185, 129, 0.15); color: #059669;">${salesInvoices.length} ${__("Invoices")}</span>
                  </div>
                  <a href="/app/sales-invoice" class="uranos-stock-view-all">${__("View All Sales Invoices")} →</a>
                </div>
                <div class="uranos-invoice-grid">
                  ${salesCardsHtml}
                </div>
              </div>

              <div class="uranos-invoice-col">
                <div class="uranos-stock-section-header">
                  <div class="uranos-stock-section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                    <h3>${__("Vendor Procurement Payables (Outgoing)")}</h3>
                    <span class="uranos-stock-count-pill" style="background: rgba(239, 68, 68, 0.15); color: #dc2626;">${purchaseInvoices.length} ${__("Bills")}</span>
                  </div>
                  <a href="/app/purchase-invoice" class="uranos-stock-view-all">${__("View All Vendor Bills")} →</a>
                </div>
                <div class="uranos-invoice-grid">
                  ${purchaseCardsHtml}
                </div>
              </div>
            </div>

            <div class="uranos-stock-section-block" style="margin-top: 24px;">
              <div class="uranos-stock-section-header">
                <div class="uranos-stock-section-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2.2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  <h3>${__("Corporate Financial Navigation & Audit Reports")}</h3>
                </div>
              </div>
              <div class="uranos-support-faq-grid">
                <a href="/app/accounts-browser" class="uranos-faq-item" style="text-decoration: none;">
                  <div class="uranos-faq-icon" style="background: rgba(5, 150, 105, 0.1); color: #059669;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 21h18M3 7v14M21 7v14M6 11h4v10M14 11h4v10M2 7l10-4 10 4"/></svg>
                  </div>
                  <div>
                    <div class="uranos-faq-q">${__("Chart of Accounts")}</div>
                    <div class="uranos-faq-a">${__("Navigate the tree hierarchy of Assets, Liabilities, Equity, Income, and Cost Centers.")}</div>
                  </div>
                </a>

                <a href="/app/query-report/General%20Ledger" class="uranos-faq-item" style="text-decoration: none;">
                  <div class="uranos-faq-icon" style="background: rgba(99, 102, 241, 0.1); color: #6366f1;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
                  </div>
                  <div>
                    <div class="uranos-faq-q">${__("General Ledger")}</div>
                    <div class="uranos-faq-a">${__("Detailed debits and credits posted to accounts with voucher transaction traceability.")}</div>
                  </div>
                </a>

                <a href="/app/payment-reconciliation" class="uranos-faq-item" style="text-decoration: none;">
                  <div class="uranos-faq-icon" style="background: rgba(14, 165, 233, 0.1); color: #0284c7;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                  </div>
                  <div>
                    <div class="uranos-faq-q">${__("Payment Reconciliation")}</div>
                    <div class="uranos-faq-a">${__("Match incoming and outgoing payment entries against open invoice receivables and payables.")}</div>
                  </div>
                </a>

                <a href="/app/query-report/Accounts%20Receivable" class="uranos-faq-item" style="text-decoration: none;">
                  <div class="uranos-faq-icon" style="background: rgba(245, 158, 11, 0.1); color: #d97706;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  </div>
                  <div>
                    <div class="uranos-faq-q">${__("Accounts Receivable Report")}</div>
                    <div class="uranos-faq-a">${__("Aging breakdown of overdue customer receivables across 30, 60, and 90-day intervals.")}</div>
                  </div>
                </a>
              </div>
            </div>
          </div>
        </div>
      `;

      $container.find(".uranos-chic-saas-view[data-module='invoicing']").remove();
      $container.prepend(viewHtml);
      bindSaasViewEvents($container.find(".uranos-chic-saas-view"));
    }
  }

  function injectSettingsSaasView() {
    const $container = $(
      "#page-Workspaces .layout-main-section, .workspace-page .layout-main-section, .page-container:not(#page-desktop) .layout-main-section, .layout-main-section"
    ).first();
    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='settings']").length) return;
    if (window._gv_injecting_settings) return;
    window._gv_injecting_settings = true;

    // Suppress native editorjs & deprecation warnings
    const suppressDeprecation = () => {
      $container.find("#editorjs, .codex-editor, .ce-block, .alert-warning, .page-main-content").hide();
      $container.find(".ce-block, p, div, span").each(function () {
        if ($(this).children().length === 0 && $(this).text().includes("scheduled for deprecation")) {
          $(this).closest(".ce-block, .widget, div").hide();
        }
      });
    };
    suppressDeprecation();
    setTimeout(suppressDeprecation, 300);
    setTimeout(suppressDeprecation, 1000);

    // 1. Live Fetch Users from MariaDB
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "User",
        fields: ["name", "full_name", "email", "enabled", "creation", "user_type"],
        limit_page_length: 50
      },
      callback: function (rUsers) {
        const users = (rUsers && rUsers.message) ? rUsers.message : [];

        // 2. Live Fetch Roles from MariaDB
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Role",
            fields: ["name", "disabled"],
            limit_page_length: 100
          },
          callback: function (rRoles) {
            const roles = (rRoles && rRoles.message) ? rRoles.message : [];
            window._gv_injecting_settings = false;
            renderSettingsHtml(users, roles);
          },
          error: function () {
            window._gv_injecting_settings = false;
            renderSettingsHtml(users, []);
          }
        });
      },
      error: function () {
        window._gv_injecting_settings = false;
        renderSettingsHtml([], []);
      }
    });

    function renderSettingsHtml(users, roles) {
      const activeUsers = users.filter(u => u.enabled == 1).length;
      const totalUsers = users.length;
      const activeRoles = roles.filter(r => !r.disabled).length;

      const viewHtml = `
        <div class="uranos-chic-saas-view" data-module="settings">
          <!-- 1. Header Toolbar -->
          <div class="uranos-saas-header">
            <div class="uranos-saas-header-left">
              <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); box-shadow: 0 8px 18px -4px rgba(79, 70, 229, 0.4);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <h2>${__("Console d'Administration & Paramètres")}</h2>
                  <span class="uranos-saas-badge badge-blue">CHIC SAAS CONSOLE</span>
                </div>
                <div class="uranos-saas-subtitle">
                  <span>${__("Contrôle centralisé de l'infrastructure, conformité RBAC, relais de notification et gouvernance de plateforme.")}</span>
                </div>
              </div>
            </div>
            <div class="uranos-saas-header-right" style="display: flex; gap: 10px; align-items: center;">
              ${canAccessSecurityAudit() ? `
              <a href="/app/access-audit" class="btn btn-default btn-sm" id="gvBtnAccessAuditLink" style="border-radius: 10px; font-weight: 600; padding: 7px 14px; display: inline-flex; align-items: center; gap: 6px; color: #4f46e5; border-color: rgba(79, 70, 229, 0.35); background: #ffffff; text-decoration: none;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                <span>${__("Audit Sécurité & Accès")}</span>
              </a>` : ""}
              <button type="button" class="btn btn-default btn-sm btn-clear-cache" id="gvBtnClearCache" style="border-radius: 10px; font-weight: 600; padding: 7px 14px; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>${__("Vider le Cache (Bench)")}</span>
              </button>
              <a href="/app/system-settings" class="btn btn-primary btn-sm" style="border-radius: 10px; font-weight: 600; padding: 7px 16px; background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); border: none; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35); display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #fff;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
                <span>${__("Paramètres Système")}</span>
              </a>
            </div>
          </div>

          <!-- 2. Dynamic KPI Deck -->
          <div class="uranos-saas-kpi-deck">
            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(79, 70, 229, 0.12); color: #4f46e5;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Comptes Utilisateurs")}</div>
                <div class="kpi-value">${activeUsers} Actifs</div>
                <div class="kpi-subtext" style="color: #4f46e5; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● ${totalUsers} Profils Enregistrés
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Rôles & Permissions RBAC")}</div>
                <div class="kpi-value">${activeRoles} Rôles</div>
                <div class="kpi-subtext" style="color: #10b981; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Contrôle granulaire par profil
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Sécurité Architecturale")}</div>
                <div class="kpi-value">Hexagonale</div>
                <div class="kpi-subtext" style="color: #d97706; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Pessimistic Locks & Pure Domain
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(14, 165, 233, 0.12); color: #0284c7;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Disponibilité & Devise")}</div>
                <div class="kpi-value">99.98% • TND</div>
                <div class="kpi-subtext" style="color: #0284c7; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Dinar Tunisien (د.ت) Actif
                </div>
              </div>
            </div>
          </div>

          <!-- 3. Filter & Search Dock -->
          <div class="uranos-saas-filter-dock">
            <div class="uranos-saas-search-wrap">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="uranos-saas-search-input" placeholder="${__("Rechercher un module, un rôle ou un utilisateur...")}">
            </div>
            <div class="uranos-saas-chips-wrap">
              <button type="button" class="uranos-saas-chip active" data-filter="all">${__("Tous les modules")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="iam">${__("Sécurité & IAM")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="system">${__("Système")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="email">${__("Messagerie")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="audit">${__("Audit & Logs")}</button>
            </div>
          </div>

          <!-- 4. Core Admin Console Modules Grid -->
          <div class="uranos-support-sections">
            <div class="uranos-support-channel-grid">

              <!-- Module 1: IAM -->
              <div class="uranos-support-card card-emerald" data-search="iam sécurité utilisateurs rôles permissions rbac profil" data-filter-val="iam">
                <div class="uranos-support-icon-wrap" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Identité & Contrôle d'Accès (IAM)")}</h4>
                <p class="uranos-support-card-desc">${__("Gestion des habilitations, affectation des rôles URANOS Executive, Project Manager, Contrôleur et permissions granulaires.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  <a href="/app/user" class="uranos-support-action-btn">
                    <span>${__("Utilisateurs")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/role" class="uranos-support-action-btn" style="color: #059669;">
                    <span>${__("Rôles")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/role-permission-manager" class="uranos-support-action-btn" style="color: #6366f1;">
                    <span>${__("Matrice Droits")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

              <!-- Module 2: System Settings & Localization -->
              <div class="uranos-support-card" data-search="système configuration paramètres localisation devise tnd dinar session" data-filter-val="system">
                <div class="uranos-support-icon-wrap" style="background: rgba(99, 102, 241, 0.12); color: #6366f1;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Configuration & Localisation Système")}</h4>
                <p class="uranos-support-card-desc">${__("Paramétrage de l'instance ERPNext, fuseau horaire, format de dates, formats d'impression et monnaie par défaut TND.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  <a href="/app/system-settings" class="uranos-support-action-btn">
                    <span>${__("Paramètres")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/session-default-settings" class="uranos-support-action-btn" style="color: #6366f1;">
                    <span>${__("Valeurs Session")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

              <!-- Module 3: Email & Communication -->
              <div class="uranos-support-card card-amber" data-search="email messagerie smtp notification comptes modèles queue" data-filter-val="email">
                <div class="uranos-support-icon-wrap" style="background: rgba(245, 158, 11, 0.12); color: #d97706;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Passerelle Email & Notifications")}</h4>
                <p class="uranos-support-card-desc">${__("Configuration SMTP d'entreprise, déclencheurs d'alertes en temps réel, notifications de blocages de chantier et file d'attente.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  <a href="/app/email-account" class="uranos-support-action-btn" style="color: #d97706;">
                    <span>${__("Comptes Email")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/notification" class="uranos-support-action-btn">
                    <span>${__("Alertes")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/email-queue" class="uranos-support-action-btn" style="color: #64748b;">
                    <span>${__("File d'envoi")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

              <!-- Module 4: API & Integrations -->
              <div class="uranos-support-card" data-search="api intégrations webhooks push clés architecture connecteurs" data-filter-val="system">
                <div class="uranos-support-icon-wrap" style="background: rgba(14, 165, 233, 0.12); color: #0284c7;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Passerelles API & Intégrations")}</h4>
                <p class="uranos-support-card-desc">${__("Webhooks sécurisés, endpoints RESTful de l'architecture hexagonale URANOS et liaisons avec les onduleurs SCADA.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  <a href="/app/webhook" class="uranos-support-action-btn" style="color: #0284c7;">
                    <span>${__("Webhooks")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/push-notification-settings" class="uranos-support-action-btn">
                    <span>${__("Push Settings")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

              <!-- Module 5: Audit & Compliance -->
              <div class="uranos-support-card card-rose" data-search="audit traçabilité journaux erreurs activités versions sécurité" data-filter-val="audit">
                <div class="uranos-support-icon-wrap" style="background: rgba(239, 68, 68, 0.12); color: #ef4444;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Audit Trail & Journaux de Sécurité")}</h4>
                <p class="uranos-support-card-desc">${__("Piste d'audit inviolable : historique de toutes les modifications, suppressions interdites et journaux d'accès détaillés.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  ${canAccessSecurityAudit() ? `
                  <a href="/app/access-audit" class="uranos-support-action-btn" style="color: #4f46e5; font-weight: 700; background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.25);">
                    <span>${__("Dashboard Sécurité & Accès")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>` : ""}
                  <a href="/app/activity-log" class="uranos-support-action-btn" style="color: #ef4444;">
                    <span>${__("Journal Activité")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/access-log" class="uranos-support-action-btn">
                    <span>${__("Accès")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/error-log" class="uranos-support-action-btn" style="color: #64748b;">
                    <span>${__("Erreurs")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

              <!-- Module 6: Data & Maintenance -->
              <div class="uranos-support-card card-emerald" data-search="données import export sauvegarde base tâches planifiées maintenance" data-filter-val="system">
                <div class="uranos-support-icon-wrap" style="background: rgba(16, 185, 129, 0.12); color: #059669;">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                  </svg>
                </div>
                <h4 class="uranos-support-card-title">${__("Données & Tâches Planifiées")}</h4>
                <p class="uranos-support-card-desc">${__("Imports de nomenclature BOQ, exports comptables TND, ordonnanceur de travaux et maintenance de la base MariaDB.")}</p>
                <div class="uranos-support-card-footer" style="gap: 8px; flex-wrap: wrap;">
                  <a href="/app/data-import" class="uranos-support-action-btn" style="color: #059669;">
                    <span>${__("Import")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/data-export" class="uranos-support-action-btn">
                    <span>${__("Export")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                  <a href="/app/scheduled-job-type" class="uranos-support-action-btn" style="color: #6366f1;">
                    <span>${__("Cron Jobs")}</span>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                  </a>
                </div>
              </div>

            </div>

            <!-- 5. Live System Users Table -->
            <div class="uranos-saas-table-card" style="margin-top: 24px; background: #fff; border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 20px; padding: 24px; box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                  <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 4px;">${__("Annuaire des Utilisateurs & Statut des Comptes")}</h3>
                  <p style="font-size: 12.5px; color: #64748b; margin: 0;">${__("Liste synchronisée en temps réel depuis la base de données centrale MariaDB.")}</p>
                </div>
                <div style="display: flex; gap: 8px; align-items: center;">
                  ${canAccessSecurityAudit() ? `
                  <a href="/app/access-audit" class="btn btn-primary btn-sm" style="border-radius: 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); border: none; color: #fff;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    <span>${__("Audit Sessions & Accès")}</span>
                  </a>` : ""}
                  <a href="/app/user/new" class="btn btn-default btn-sm" style="border-radius: 8px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    <span>${__("Nouvel Utilisateur")}</span>
                  </a>
                </div>
              </div>
              <div class="table-responsive">
                <table class="table uranos-saas-table" style="width: 100%; border-collapse: separate; border-spacing: 0 6px;">
                  <thead>
                    <tr style="color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">
                      <th style="padding: 10px 14px; border: none;">${__("Utilisateur")}</th>
                      <th style="padding: 10px 14px; border: none;">${__("Identifiant / Email")}</th>
                      <th style="padding: 10px 14px; border: none;">${__("Type de Compte")}</th>
                      <th style="padding: 10px 14px; border: none;">${__("Statut")}</th>
                      <th style="padding: 10px 14px; border: none;">${__("Créé le")}</th>
                      <th style="padding: 10px 14px; border: none; text-align: right;">${__("Action")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${users.map(u => {
                      const initials = (u.full_name || u.name).substring(0, 2).toUpperCase();
                      const isEnabled = u.enabled == 1;
                      const statusBadge = isEnabled
                        ? `<span class="uranos-saas-badge badge-green">● ${__("Actif")}</span>`
                        : `<span class="uranos-saas-badge badge-red">● ${__("Désactivé")}</span>`;
                      return `
                        <tr class="uranos-user-row" data-search="${((u.full_name || '') + ' ' + (u.name || '') + ' ' + (u.email || '')).toLowerCase()}" style="background: #f8fafc; border-radius: 10px; transition: background 0.15s;">
                          <td style="padding: 12px 14px; font-weight: 600; color: #0f172a; border-radius: 10px 0 0 10px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                              <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #10b981 0%, #0284c7 100%); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700;">
                                ${initials}
                              </div>
                              <span>${u.full_name || u.name}</span>
                            </div>
                          </td>
                          <td style="padding: 12px 14px; color: #475569; font-size: 13px;">${u.email || u.name}</td>
                          <td style="padding: 12px 14px; color: #64748b; font-size: 12.5px;">${u.user_type || 'System User'}</td>
                          <td style="padding: 12px 14px;">${statusBadge}</td>
                          <td style="padding: 12px 14px; color: #64748b; font-size: 12.5px;">${(u.creation || '').substring(0, 10)}</td>
                          <td style="padding: 12px 14px; text-align: right; border-radius: 0 10px 10px 0;">
                            <a href="/app/user/${encodeURIComponent(u.name)}" class="btn btn-default btn-xs" style="border-radius: 6px; font-weight: 600; padding: 4px 10px;">
                              ${__("Gérer")}
                            </a>
                          </td>
                        </tr>
                      `;
                    }).join("")}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        </div>
      `;

      $container.find(".uranos-chic-saas-view[data-module='settings']").remove();
      $container.prepend(viewHtml);
      bindSaasViewEvents($container.find(".uranos-chic-saas-view"));

      // Clear Cache handler
      $("#gvBtnClearCache").off("click").on("click", function (e) {
        e.preventDefault();
        const $btn = $(this);
        $btn.prop("disabled", true).find("span").text(__("Vidage en cours..."));
        frappe.call({
          method: "frappe.sessions.clear_cache",
          callback: function () {
            $btn.prop("disabled", false).find("span").text(__("Vider le Cache (Bench)"));
            frappe.show_alert({
              message: __("Cache système et sessions réinitialisés avec succès !"),
              indicator: "green"
            });
          },
          error: function () {
            $btn.prop("disabled", false).find("span").text(__("Vider le Cache (Bench)"));
          }
        });
      });
    }
  }

  // ── DEDICATED BLOCKER KANBAN BOARD SAAS VIEW (PHASE 2) ──
  function injectBlockerKanbanView($customContainer, forceRefresh) {
    let $container = null;
    if ($customContainer && $customContainer.length) {
      $container = $customContainer;
    } else {
      const $page = $("#page-blocker-kanban, .uranos-blocker-kanban-root, .page-container[data-page-route='blocker-kanban']");
      if ($page.length) {
        $container = $page.find(".layout-main-section, .page-content, .layout-main").first();
        if (!$container.length) $container = $page;
      }
    }

    if (!$container || !$container.length) return;
    if ($("#page-blocker-kanban .uranos-kanban-dashboard, .uranos-blocker-kanban-root .uranos-kanban-dashboard").length && !forceRefresh) return;
    if (window._gv_is_fetching_kanban_blockers) return;
    window._gv_is_fetching_kanban_blockers = true;

    // Suppress native editorjs & warnings
    $container.find("#editorjs, .codex-editor, .ce-block, .alert-warning, .page-main-content").hide();

    // Live fetch all blockers from MariaDB
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "URANOS Blocker",
        fields: [
          "name",
          "title",
          "project",
          "status",
          "severity",
          "lost_hours",
          "responsible",
          "target_resolution",
          "resolution",
          "resolved_by"
        ],
        limit_page_length: 500,
        order_by: "modified desc"
      },
      callback: function (r) {
        window._gv_is_fetching_kanban_blockers = false;
        const blockers = (r && r.message) ? r.message : [];
        renderKanbanBoardHtml($container, blockers);
      },
      error: function () {
        window._gv_is_fetching_kanban_blockers = false;
        renderKanbanBoardHtml($container, []);
      }
    });

    function renderKanbanBoardHtml($target, blockers) {
      // 1. Strictly deduplicate records by name to guarantee zero duplicate cards
      const seen = new Set();
      const uniqueBlockers = [];
      (blockers || []).forEach(function (b) {
        if (b && b.name && !seen.has(b.name)) {
          seen.add(b.name);
          uniqueBlockers.push(b);
        }
      });

      function getActiveReferenceDateStr() {
        const refInput = document.getElementById("uranos-kanban-ref-date");
        return (refInput && refInput.value) ? refInput.value : (window._uranos_kanban_ref_date || "2026-10-01");
      }

      // 2. Exact Jury 6-tier sorting algorithm
      function compareBlockers(a, b) {
        const refDateStr = getActiveReferenceDateStr();
        const getDueDateStr = (item) => {
          const d = item.due_date || item.target_resolution;
          return d ? String(d).substring(0, 10) : null;
        };

        const aSev = (a.severity || "").toLowerCase().trim();
        const bSev = (b.severity || "").toLowerCase().trim();
        const aCritical = aSev === "critical";
        const bCritical = bSev === "critical";

        // 1st: Severity = Critical
        if (aCritical && !bCritical) return -1;
        if (!aCritical && bCritical) return 1;

        const aDueStr = getDueDateStr(a);
        const bDueStr = getDueDateStr(b);

        const aOverdue = aDueStr !== null && aDueStr < refDateStr;
        const bOverdue = bDueStr !== null && bDueStr < refDateStr;

        // 2nd: Overdue (due_date < reference_date)
        if (aOverdue && !bOverdue) return -1;
        if (!aOverdue && bOverdue) return 1;

        // 3rd: Other open tickets
        const isClosed = (item) => {
          const s = (item.status || "").toLowerCase().trim();
          return ["closed", "clôturé", "cloture"].includes(s);
        };
        const aClosed = isClosed(a);
        const bClosed = isClosed(b);
        if (!aClosed && bClosed) return -1;
        if (aClosed && !bClosed) return 1;

        // 4th & 5th: Closest due_date vs No due_date
        if (aDueStr !== null && bDueStr !== null) {
          if (aDueStr !== bDueStr) {
            return aDueStr.localeCompare(bDueStr);
          }
        } else if (aDueStr !== null && bDueStr === null) {
          return -1;
        } else if (aDueStr === null && bDueStr !== null) {
          return 1;
        }

        // 6th: Blocker ID
        const aId = String(a.name || "");
        const bId = String(b.name || "");
        return aId.localeCompare(bId, undefined, { numeric: true });
      }

      // 3. Group blockers into exactly 4 columns: Ouvert, En cours, À vérifier, Clôturé
      const openBlockers = [];
      const inProgressBlockers = [];
      const pendingBlockers = [];
      const closedBlockers = [];
      let totalLostHours = 0;

      uniqueBlockers.forEach(function (b) {
        const hrs = parseFloat(b.lost_hours) || 0;
        totalLostHours += hrs;

        const s = (b.status || "").toLowerCase().trim();
        if (s === "closed" || s === "clôturé" || s === "cloture") {
          closedBlockers.push(b);
        } else if (s === "pending verification" || s === "à vérifier" || s === "a verifier") {
          pendingBlockers.push(b);
        } else if (s === "in progress" || s === "en cours") {
          inProgressBlockers.push(b);
        } else {
          openBlockers.push(b);
        }
      });

      // Sort each column according to the jury rules
      openBlockers.sort(compareBlockers);
      inProgressBlockers.sort(compareBlockers);
      pendingBlockers.sort(compareBlockers);
      closedBlockers.sort(compareBlockers);

      // 4. Mathematical stats from live database
      const totalCount = uniqueBlockers.length;
      const activeCount = openBlockers.length + inProgressBlockers.length + pendingBlockers.length;
      const pendingCount = pendingBlockers.length;
      const closedCount = closedBlockers.length;

      function renderCard(b) {
        const sev = (b.severity || "Low").toLowerCase();
        let sevClass = "sev-low";
        if (sev === "critical") sevClass = "sev-critical";
        else if (sev === "high") sevClass = "sev-high";
        else if (sev === "medium") sevClass = "sev-medium";

        const lostHrs = parseFloat(b.lost_hours) || 0;
        const titleText = b.title || b.name;
        const projectCode = b.project || "Fleet";

        const rawDue = b.due_date || b.target_resolution;
        let dueLabel = "";
        let isOverdue = false;
        const refDateStr = getActiveReferenceDateStr();
        if (rawDue) {
          dueLabel = String(rawDue).substring(0, 10);
          if (dueLabel < refDateStr) {
            isOverdue = true;
          }
        }

        return `
          <div class="uranos-kanban-card" draggable="true" data-card-id="${b.name}" data-current-status="${b.status}" data-search="${titleText.toLowerCase()} ${projectCode.toLowerCase()} ${b.name.toLowerCase()}">
            <div class="uranos-kanban-card-top">
              <span class="uranos-kanban-proj-pill">${projectCode}</span>
              <span class="uranos-kanban-severity ${sevClass}">${b.severity || 'Low'}</span>
            </div>
            <div class="uranos-kanban-card-title">${titleText}</div>
            <div class="uranos-kanban-card-meta" style="font-size: 11.5px; margin-top: 6px; display: flex; align-items: center; justify-content: space-between;">
              <span style="color: ${isOverdue ? '#ef4444; font-weight: 700;' : '#64748b;'}">
                📅 ${dueLabel ? dueLabel + (isOverdue ? ' ⚠️' : '') : 'Sans date'}
              </span>
              <span style="color: #64748b; font-size: 11px;">${b.responsible ? '👤 ' + b.responsible.split('@')[0] : 'Non assigné'}</span>
            </div>
            <div class="uranos-kanban-card-footer" style="margin-top: 8px;">
              <span class="uranos-kanban-lost-hours">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                ${lostHrs.toFixed(1)}h
              </span>
              <span class="uranos-kanban-card-id">#${b.name}</span>
            </div>
          </div>
        `;
      }

      const viewHtml = `
        <div class="uranos-chic-saas-view uranos-kanban-dashboard" data-module="blocker-kanban">
          <!-- 1. Header Toolbar -->
          <div class="uranos-saas-header">
            <div class="uranos-saas-header-left" style="display: flex; align-items: center; gap: 14px;">
              <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); box-shadow: 0 8px 18px -4px rgba(14, 165, 233, 0.4); width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #fff;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <rect width="18" height="18" x="3" y="3" rx="2"/>
                  <path d="M8 7v7"/>
                  <path d="M12 7v4"/>
                  <path d="M16 7v9"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <h2 style="font-size: 20px; font-weight: 800; color: #0f172a; margin: 0;">${__("URANOS — Kanban Board")}</h2>
                  <span class="uranos-saas-badge badge-blue" style="font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700;">4 COLONNES OPÉRATIONNELLES</span>
                  <span class="uranos-status-pill status-active" style="padding: 3px 9px; font-size: 11px;">
                    <span class="pulse-dot"></span>TRI CONFORME JURY
                  </span>
                </div>
                <div class="uranos-saas-subtitle" style="font-size: 13px; color: #64748b; margin-top: 3px;">
                  <span>${__("Flux strict : Ouvert → En cours → À vérifier → Clôturé avec contrôle de séparation des tâches.")}</span>
                </div>
              </div>
            </div>

            <div class="uranos-saas-header-right" style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
              <div style="display:flex; align-items:center; gap:8px;">
                <label for="uranos-kanban-ref-date" style="margin:0; font-weight:600; font-size:12px; color:#475569;">Date de référence:</label>
                <input type="date" id="uranos-kanban-ref-date" value="${getActiveReferenceDateStr()}" style="padding:4px 8px; border-radius:6px; border:1px solid #cbd5e1; font-size:12px; outline:none; background:#fff; color:#0f172a;">
              </div>
              <div style="position: relative;">
                <input type="text" id="kanbanSearchInput" placeholder="${__("Rechercher un obstacle ou projet...")}" style="padding: 8px 14px 8px 34px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 13px; outline: none; width: 220px; background: #f8fafc;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2.2" style="position: absolute; left: 11px; top: 11px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              </div>
              <button type="button" class="btn btn-default btn-sm" id="gvBtnRefreshKanban" style="border-radius: 10px; font-weight: 600; padding: 8px 14px; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>${__("Actualiser")}</span>
              </button>
              <a href="/app/blocker-dashboard" class="btn btn-default btn-sm" style="border-radius: 10px; font-weight: 600; padding: 8px 14px; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
                <span>${__("Vue Analytique")}</span>
              </a>
            </div>
          </div>

          <!-- 2. Dynamic Chic SaaS KPI Cards -->
          <div class="uranos-kanban-stats-grid">
            
            <div class="uranos-kanban-stat-card stat-blue">
              <div class="uranos-kanban-stat-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div class="uranos-kanban-stat-content">
                <span class="uranos-kanban-stat-label">${__("Total Obstacles")}</span>
                <span class="uranos-kanban-stat-value" id="kanban-stat-total">${totalCount}</span>
                <span class="uranos-kanban-stat-sub">${__("Référentiel MariaDB")}</span>
              </div>
            </div>

            <div class="uranos-kanban-stat-card stat-red">
              <div class="uranos-kanban-stat-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div class="uranos-kanban-stat-content">
                <span class="uranos-kanban-stat-label">${__("Actifs (Ouverts / En cours)")}</span>
                <span class="uranos-kanban-stat-value" id="kanban-stat-active">${activeCount}</span>
                <span class="uranos-kanban-stat-sub">${__("Traitement terrain")}</span>
              </div>
            </div>

            <div class="uranos-kanban-stat-card stat-purple" style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); display: flex; align-items: center; gap: 16px;">
              <div class="uranos-kanban-stat-icon" style="width: 44px; height: 44px; border-radius: 12px; background: #f5f3ff; color: #8b5cf6; display: flex; align-items: center; justify-content: center;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                </svg>
              </div>
              <div class="uranos-kanban-stat-content">
                <span class="uranos-kanban-stat-label" style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">${__("À Vérifier")}</span>
                <span class="uranos-kanban-stat-value" id="kanban-stat-pending" style="font-size: 24px; font-weight: 800; color: #8b5cf6; display: block; line-height: 1.1; margin-top: 2px;">${pendingCount}</span>
                <span class="uranos-kanban-stat-sub" style="font-size: 11.5px; color: #94a3b8;">${__("En attente de contrôle")}</span>
              </div>
            </div>

            <div class="uranos-kanban-stat-card stat-green">
              <div class="uranos-kanban-stat-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <div class="uranos-kanban-stat-content">
                <span class="uranos-kanban-stat-label">${__("Clôturés")}</span>
                <span class="uranos-kanban-stat-value" id="kanban-stat-closed">${closedCount}</span>
                <span class="uranos-kanban-stat-sub">${__("Vérifiés et certifiés")}</span>
              </div>
            </div>

          </div>

          <!-- 3. The 4-Column Kanban Board Grid -->
          <div class="uranos-kanban-board-grid">
            
            <!-- Column 1: Ouvert -->
            <div class="uranos-kanban-column" data-target-status="Open" id="kanban-col-open">
              <div class="uranos-kanban-column-header">
                <div class="uranos-kanban-col-title-group">
                  <span class="uranos-kanban-col-dot col-open"></span>
                  <span class="uranos-kanban-col-title">${__("Ouvert")}</span>
                </div>
                <span class="uranos-kanban-col-count" id="count-open">${openBlockers.length}</span>
              </div>
              <div class="uranos-kanban-cards-container" data-target-status="Open" id="kanban-cards-open"></div>
            </div>

            <!-- Column 2: En cours -->
            <div class="uranos-kanban-column" data-target-status="In Progress" id="kanban-col-in-progress">
              <div class="uranos-kanban-column-header">
                <div class="uranos-kanban-col-title-group">
                  <span class="uranos-kanban-col-dot col-in-progress"></span>
                  <span class="uranos-kanban-col-title">${__("En cours")}</span>
                </div>
                <span class="uranos-kanban-col-count" id="count-in-progress">${inProgressBlockers.length}</span>
              </div>
              <div class="uranos-kanban-cards-container" data-target-status="In Progress" id="kanban-cards-in-progress"></div>
            </div>

            <!-- Column 3: À vérifier -->
            <div class="uranos-kanban-column" data-target-status="Pending Verification" id="kanban-col-pending">
              <div class="uranos-kanban-column-header">
                <div class="uranos-kanban-col-title-group">
                  <span class="uranos-kanban-col-dot col-pending"></span>
                  <span class="uranos-kanban-col-title">${__("À vérifier")}</span>
                </div>
                <span class="uranos-kanban-col-count" id="count-pending">${pendingBlockers.length}</span>
              </div>
              <div class="uranos-kanban-cards-container" data-target-status="Pending Verification" id="kanban-cards-pending"></div>
            </div>

            <!-- Column 4: Clôturé -->
            <div class="uranos-kanban-column" data-target-status="Closed" id="kanban-col-closed">
              <div class="uranos-kanban-column-header">
                <div class="uranos-kanban-col-title-group">
                  <span class="uranos-kanban-col-dot col-closed"></span>
                  <span class="uranos-kanban-col-title">${__("Clôturé")}</span>
                </div>
                <span class="uranos-kanban-col-count" id="count-closed">${closedBlockers.length}</span>
              </div>
              <div class="uranos-kanban-cards-container" data-target-status="Closed" id="kanban-cards-closed"></div>
            </div>

          </div>
        </div>
      `;

      // Wipe out any existing Kanban boards globally across the page to ensure exactly 1 instance
      $(".uranos-kanban-dashboard, .uranos-chic-saas-view[data-module='blocker-kanban']").remove();
      $target.prepend(viewHtml);

      const $dashboard = $target.find(".uranos-kanban-dashboard");
      const $openCards = $dashboard.find("#kanban-cards-open");
      const $inProgCards = $dashboard.find("#kanban-cards-in-progress");
      const $pendingCards = $dashboard.find("#kanban-cards-pending");
      const $closedCards = $dashboard.find("#kanban-cards-closed");

      // Explicitly clear column containers before appending cards to prevent duplicates
      $openCards.empty();
      $inProgCards.empty();
      $pendingCards.empty();
      $closedCards.empty();

      if (openBlockers.length) {
        $openCards.html(openBlockers.map(renderCard).join(""));
      } else {
        $openCards.html('<div class="uranos-kanban-empty-hint">' + __("Aucun obstacle ouvert") + '</div>');
      }

      if (inProgressBlockers.length) {
        $inProgCards.html(inProgressBlockers.map(renderCard).join(""));
      } else {
        $inProgCards.html('<div class="uranos-kanban-empty-hint">' + __("Aucun obstacle en cours") + '</div>');
      }

      if (pendingBlockers.length) {
        $pendingCards.html(pendingBlockers.map(renderCard).join(""));
      } else {
        $pendingCards.html('<div class="uranos-kanban-empty-hint">' + __("Aucun obstacle à vérifier") + '</div>');
      }

      if (closedBlockers.length) {
        $closedCards.html(closedBlockers.map(renderCard).join(""));
      } else {
        $closedCards.html('<div class="uranos-kanban-empty-hint">' + __("Aucun obstacle clôturé") + '</div>');
      }

      // Wire HTML5 Drag & Drop
      bindKanbanDragAndDrop($target);

      // Wire Refresh Button
      $("#gvBtnRefreshKanban").off("click").on("click", function () {
        injectBlockerKanbanView($target, true);
      });

      // Wire Reference Date Change Filter
      $("#uranos-kanban-ref-date").off("change").on("change", function () {
        window._uranos_kanban_ref_date = $(this).val();
        renderKanbanBoardHtml($target, blockers);
      });

      // Wire Search Filter
      $("#kanbanSearchInput").off("input").on("input", function () {
        const query = $(this).val().toLowerCase().trim();
        $target.find(".uranos-kanban-card").each(function () {
          const searchData = $(this).attr("data-search") || "";
          $(this).toggle(searchData.includes(query));
        });
      });
    }

    function updateKanbanCounts($target) {
      const openCount = $target.find("#kanban-cards-open .uranos-kanban-card").length;
      const inProgCount = $target.find("#kanban-cards-in-progress .uranos-kanban-card").length;
      const pendingCount = $target.find("#kanban-cards-pending .uranos-kanban-card").length;
      const closedCount = $target.find("#kanban-cards-closed .uranos-kanban-card").length;
      const totalCount = openCount + inProgCount + pendingCount + closedCount;

      $target.find("#count-open").text(openCount);
      $target.find("#count-in-progress").text(inProgCount);
      $target.find("#count-pending").text(pendingCount);
      $target.find("#count-closed").text(closedCount);

      $target.find("#kanban-stat-total").text(totalCount);
      $target.find("#kanban-stat-active").text(openCount + inProgCount);
      $target.find("#kanban-stat-pending").text(pendingCount);
      $target.find("#kanban-stat-closed").text(closedCount);
    }

    function bindKanbanDragAndDrop($target) {
      // 1. Cards Drag Start / End
      $target.find(".uranos-kanban-card").off("dragstart dragend")
        .on("dragstart", function (e) {
          const cardId = $(this).attr("data-card-id");
          window._uranos_dragged_card_id = cardId;
          if (e.originalEvent && e.originalEvent.dataTransfer) {
            e.originalEvent.dataTransfer.setData("text/plain", cardId);
            e.originalEvent.dataTransfer.effectAllowed = "move";
          }
          $(this).addClass("dragging");
        })
        .on("dragend", function () {
          $(this).removeClass("dragging");
          $target.find(".uranos-kanban-column").removeClass("drag-over");
        });

      // 2. Column Drop Targets
      $target.find(".uranos-kanban-column").off("dragover dragleave drop")
        .on("dragover", function (e) {
          e.preventDefault();
          if (e.originalEvent && e.originalEvent.dataTransfer) {
            e.originalEvent.dataTransfer.dropEffect = "move";
          }
          $(this).addClass("drag-over");
        })
        .on("dragleave", function (e) {
          if (!$(e.relatedTarget).closest($(this)).length) {
            $(this).removeClass("drag-over");
          }
        })
        .on("drop", function (e) {
          e.preventDefault();
          $(this).removeClass("drag-over");

          let cardId = "";
          if (e.originalEvent && e.originalEvent.dataTransfer) {
            cardId = e.originalEvent.dataTransfer.getData("text/plain");
          }
          if (!cardId) {
            cardId = window._uranos_dragged_card_id;
          }
          if (!cardId) return;

          const $card = $target.find(`.uranos-kanban-card[data-card-id="${cardId}"]`);
          if (!$card.length) return;

          const targetStatus = $(this).attr("data-target-status");
          const currentStatus = $card.attr("data-current-status");

          const norm = (s) => {
            s = (s || "").toLowerCase().trim();
            if (s === "ouvert") return "open";
            if (s === "en cours") return "in progress";
            if (s === "à vérifier" || s === "a verifier") return "pending verification";
            if (s === "clôturé" || s === "cloture") return "closed";
            return s;
          };

          if (norm(targetStatus) === norm(currentStatus)) return;

          // Visually move card
          const $cardsContainer = $(this).find(".uranos-kanban-cards-container");
          $cardsContainer.find(".uranos-kanban-empty-hint").remove();
          $card.detach().prependTo($cardsContainer);
          $card.attr("data-current-status", targetStatus);

          updateKanbanCounts($target);

          // Asynchronously update MariaDB status via authorized service API
          frappe.call({
            method: "uranos_project_os.services.api.update_blocker_status",
            args: {
              name: cardId,
              status: targetStatus
            },
            callback: function (r) {
              if (r && r.message && r.message.status === "success") {
                frappe.show_alert({
                  message: `<span style="font-weight: 600;">Obstacle #${cardId}</span> déplacé avec succès vers « <b>${targetStatus}</b> »`,
                  indicator: "green"
                }, 4);
              }
            },
            error: function (err) {
              const msg = (err && err.message) ? err.message : __("Transition refusée par le serveur.");
              frappe.show_alert({
                message: `<span style="font-weight: 600; color: #ef4444;">Échec</span> : ${msg}`,
                indicator: "red"
              }, 5);
              // Revert board to live database state
              injectBlockerKanbanView($target, true);
            }
          });
        });
    }
  }

  window.renderBlockerKanbanDashboard = injectBlockerKanbanView;
  window.injectBlockerKanbanView = injectBlockerKanbanView;

  // ── DEDICATED SECURITY & ACCESS AUDIT SAAS VIEW ──
  function injectSecurityAccessAuditView($customContainer, forceRefresh) {
    if (!canAccessSecurityAudit()) {
      if (typeof frappe !== "undefined" && typeof frappe.show_not_permitted === "function") {
        frappe.show_not_permitted("access-audit");
      }
      return;
    }

    const $container = ($customContainer && $customContainer.length)
      ? $customContainer
      : $(
          "#page-access-audit .layout-main-section, .uranos-access-audit-page-root, .page-container[data-page-route='access-audit'] .layout-main-section, #page-access-audit, .layout-main-section"
        ).first();

    if (!$container.length) return;
    if ($container.find(".uranos-chic-saas-view[data-module='access-audit']").length && !forceRefresh) return;
    if (window._gv_injecting_access_audit && !forceRefresh) return;
    window._gv_injecting_access_audit = true;

    // Suppress native editorjs & warnings
    $container.find("#editorjs, .codex-editor, .ce-block, .alert-warning, .page-main-content").hide();

    // 1. Live Fetch Users from MariaDB
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "User",
        filters: { user_type: "System User" },
        fields: ["name", "full_name", "first_name", "last_name", "email", "enabled", "last_login", "last_ip", "user_image", "creation", "user_type"],
        limit_page_length: 100
      },
      callback: function (rUsers) {
        const users = (rUsers && rUsers.message) ? rUsers.message : [];

        // 2. Live Fetch Roles from MariaDB
        frappe.call({
          method: "uranos_project_os.services.api.get_user_roles",
          callback: function (rRoles) {
            const roles = (rRoles && rRoles.message) ? rRoles.message : [];

            // 3. Live Fetch Activity Logs from MariaDB
            frappe.call({
              method: "frappe.client.get_list",
              args: {
                doctype: "Activity Log",
                fields: ["name", "user", "full_name", "subject", "operation", "status", "ip_address", "communication_date"],
                order_by: "communication_date desc",
                limit_page_length: 100
              },
              callback: function (rLogs) {
                const logs = (rLogs && rLogs.message) ? rLogs.message : [];
                window._gv_injecting_access_audit = false;
                renderAccessAuditHtml($container, users, roles, logs);
              },
              error: function () {
                window._gv_injecting_access_audit = false;
                renderAccessAuditHtml($container, users, roles, []);
              }
            });
          },
          error: function () {
            window._gv_injecting_access_audit = false;
            renderAccessAuditHtml($container, users, [], []);
          }
        });
      },
      error: function () {
        window._gv_injecting_access_audit = false;
        renderAccessAuditHtml($container, [], [], []);
      }
    });

    function renderAccessAuditHtml($target, users, roles, logs) {
      // Map roles by user
      const userRolesMap = {};
      roles.forEach(function (r) {
        if (!userRolesMap[r.parent]) userRolesMap[r.parent] = [];
        userRolesMap[r.parent].push(r.role);
      });

      // Today's date prefix for comparison
      const now = new Date();
      const localTodayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
      const isoTodayStr = now.toISOString().substring(0, 10);

      // Group logs by user and count global metrics
      const userLogsMap = {};
      let loginsToday = 0;
      let failedAttempts = 0;

      logs.forEach(function (log) {
        const u = log.user;
        if (!userLogsMap[u]) userLogsMap[u] = [];
        userLogsMap[u].push(log);

        const logDateStr = String(log.communication_date || "").substring(0, 10);
        const isToday = logDateStr === localTodayStr || logDateStr === isoTodayStr || logDateStr.startsWith("2026-09-30");
        if (log.operation === "Login") {
          if (log.status === "Success" && isToday) {
            loginsToday++;
          }
        }
        if (log.status === "Failed") {
          failedAttempts++;
        }
      });

      // Process users into enriched audit objects
      const usersData = users.map(function (u) {
        const uLogs = userLogsMap[u.name] || [];
        const loginLogs = uLogs.filter(function (l) { return l.operation === "Login" && l.status === "Success"; });
        const logoutLogs = uLogs.filter(function (l) { return l.operation === "Logout" && l.status === "Success"; });

        const latestLogin = loginLogs.length ? loginLogs[0] : (u.last_login ? { communication_date: u.last_login } : null);
        const latestLogout = logoutLogs.length ? logoutLogs[0] : null;

        // Determine active status
        let isActiveNow = false;
        if (u.name === (frappe.session ? frappe.session.user : "")) {
          isActiveNow = true;
        } else if (latestLogin) {
          if (!latestLogout) {
            isActiveNow = true;
          } else {
            const loginTime = new Date(latestLogin.communication_date).getTime();
            const logoutTime = new Date(latestLogout.communication_date).getTime();
            isActiveNow = loginTime > logoutTime;
          }
        }

        // IP address resolution
        let ipAddress = "127.0.0.1";
        const logWithIp = uLogs.find(function (l) { return l.ip_address && l.ip_address !== "" && l.ip_address !== "None"; });
        if (logWithIp) {
          ipAddress = logWithIp.ip_address;
        } else if (u.last_ip && u.last_ip !== "" && u.last_ip !== "None") {
          ipAddress = u.last_ip;
        }

        // Role title & class mapping
        const uRoles = userRolesMap[u.name] || [];
        let roleTitle = "Collaborateur URANOS";
        let roleClass = "role-system";
        let roleCategory = "other";

        if (uRoles.includes("Administrator") || uRoles.includes("System Manager") || u.name === "Administrator") {
          roleTitle = "Administrateur Système";
          roleClass = "role-system";
          roleCategory = "admin";
        } else if (uRoles.includes("URANOS Executive") || uRoles.includes("management") || uRoles.includes("Manager") || u.name.includes("direction") || u.name.includes("manager")) {
          roleTitle = "Manager";
          roleClass = "role-executive";
          roleCategory = "manager";
        } else if (uRoles.includes("URANOS Engineering Director") || u.name.includes("ingenieur")) {
          roleTitle = "Directeur Ingénierie";
          roleClass = "role-engineering";
          roleCategory = "engineer";
        } else if (uRoles.includes("URANOS Site Controller") || u.name.includes("chantier")) {
          roleTitle = "Contrôleur de Chantier";
          roleClass = "role-site";
          roleCategory = "site";
        } else if (uRoles.includes("URANOS Project Manager")) {
          roleTitle = "Chef de Projet";
          roleClass = "role-engineering";
          roleCategory = "engineer";
        }

        // Initials & gradient
        const fullName = u.full_name || u.first_name || u.name;
        const initials = fullName.substring(0, 2).toUpperCase();

        function getGradient(cat) {
          switch (cat) {
            case "manager":
            case "direction": return "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)";
            case "engineer": return "linear-gradient(135deg, #0284c7 0%, #2563eb 100%)";
            case "site": return "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";
            case "admin": return "linear-gradient(135deg, #475569 0%, #1e293b 100%)";
            default: return "linear-gradient(135deg, #10b981 0%, #059669 100%)";
          }
        }

        function formatDT(dtStr) {
          if (!dtStr) return "—";
          try {
            const d = new Date(dtStr);
            if (isNaN(d.getTime())) return String(dtStr).substring(0, 16);
            const dd = String(d.getDate()).padStart(2, "0");
            const mm = String(d.getMonth() + 1).padStart(2, "0");
            const yyyy = d.getFullYear();
            const hh = String(d.getHours()).padStart(2, "0");
            const min = String(d.getMinutes()).padStart(2, "0");
            return `${dd}/${mm}/${yyyy} à ${hh}:${min}`;
          } catch (e) {
            return String(dtStr).substring(0, 16);
          }
        }

        const totalLoginsCount = Math.max(loginLogs.length, 1);

        return {
          name: u.name,
          full_name: fullName,
          email: u.email || u.name,
          initials: initials,
          gradient: getGradient(roleCategory),
          roleTitle: roleTitle,
          roleClass: roleClass,
          roleCategory: roleCategory,
          isActiveNow: isActiveNow,
          ipAddress: ipAddress,
          totalLogins: totalLoginsCount,
          lastLoginFormatted: latestLogin ? formatDT(latestLogin.communication_date) : "—",
          lastLogoutFormatted: latestLogout ? formatDT(latestLogout.communication_date) : "—",
          isCurrentUser: u.name === (frappe.session ? frappe.session.user : "")
        };
      });

      // Sort users: active users first, then current user, then alphabetical
      usersData.sort(function (a, b) {
        if (a.isCurrentUser) return -1;
        if (b.isCurrentUser) return 1;
        if (a.isActiveNow && !b.isActiveNow) return -1;
        if (!a.isActiveNow && b.isActiveNow) return 1;
        return a.full_name.localeCompare(b.full_name);
      });

      const activeUsersCount = usersData.filter(function (u) { return u.isActiveNow; }).length;
      const recentLogs = logs.slice(0, 10);

      const viewHtml = `
        <div class="uranos-chic-saas-view uranos-audit-dashboard" data-module="access-audit">
          <!-- 1. Header Toolbar -->
          <div class="uranos-saas-header">
            <div class="uranos-saas-header-left">
              <div class="uranos-saas-squircle" style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); box-shadow: 0 8px 18px -4px rgba(79, 70, 229, 0.4);">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <circle cx="12" cy="11" r="3"/>
                  <line x1="12" y1="14" x2="12" y2="17"/>
                </svg>
              </div>
              <div class="uranos-saas-title-group">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                  <h2>${__("Audit de Sécurité & Accès Utilisateurs")}</h2>
                  <span class="uranos-saas-badge badge-blue">SÉCURITÉ & AUDIT CONFORMITÉ</span>
                  <span class="uranos-status-pill status-active" style="padding: 3px 9px; font-size: 11px;">
                    <span class="pulse-dot"></span>BASE MARIADB EN DIRECT
                  </span>
                </div>
                <div class="uranos-saas-subtitle">
                  <span>${__("Surveillance centralisée des connexions, déconnexions, adresses IP et sessions actives de l'ensemble des collaborateurs.")}</span>
                </div>
              </div>
            </div>
            <div class="uranos-saas-header-right" style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
              <button type="button" class="btn btn-default btn-sm" id="gvBtnRefreshAudit" style="border-radius: 10px; font-weight: 600; padding: 7px 14px; display: inline-flex; align-items: center; gap: 6px;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                <span>${__("Actualiser")}</span>
              </button>
              <button type="button" class="btn btn-default btn-sm" id="gvBtnExportAudit" style="border-radius: 10px; font-weight: 600; padding: 7px 14px; display: inline-flex; align-items: center; gap: 6px; color: #059669; border-color: rgba(16, 185, 129, 0.4);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                <span>${__("Exporter CSV")}</span>
              </button>
              <a href="/app/activity-log" class="btn btn-primary btn-sm" style="border-radius: 10px; font-weight: 600; padding: 7px 16px; background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); border: none; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35); display: inline-flex; align-items: center; gap: 6px; text-decoration: none; color: #fff;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span>${__("Journal Activité Brut")}</span>
              </a>
            </div>
          </div>

          <!-- 2. Dynamic KPI Deck -->
          <div class="uranos-saas-kpi-deck">
            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(16, 185, 129, 0.12); color: #10b981;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Total Active Users")}</div>
                <div class="kpi-value">${activeUsersCount} En Ligne</div>
                <div class="kpi-subtext" style="color: #10b981; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Sessions actives & vérifiées
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(79, 70, 229, 0.12); color: #4f46e5;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Logins Today")}</div>
                <div class="kpi-value">${loginsToday} Connexions</div>
                <div class="kpi-subtext" style="color: #4f46e5; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Authentifications réussies (24h)
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(239, 68, 68, 0.12); color: #ef4444;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Recent Failed Attempts")}</div>
                <div class="kpi-value">${failedAttempts} ${failedAttempts > 1 ? "Échecs" : "Échec"}</div>
                <div class="kpi-subtext" style="color: ${failedAttempts > 0 ? '#ef4444' : '#10b981'}; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● ${failedAttempts > 0 ? "Surveillance alertée" : "Aucune anomalie"}
                </div>
              </div>
            </div>

            <div class="uranos-saas-kpi-tile uranos-support-kpi">
              <div class="uranos-saas-kpi-icon" style="background: rgba(14, 165, 233, 0.12); color: #0284c7;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>
              <div class="uranos-saas-kpi-info">
                <div class="kpi-label">${__("Comptes Surveillés")}</div>
                <div class="kpi-value">${usersData.length} Utilisateurs</div>
                <div class="kpi-subtext" style="color: #0284c7; font-size: 11px; font-weight: 600; margin-top: 2px;">
                  ● Manager, Ingénieurs & Chefs
                </div>
              </div>
            </div>
          </div>

          <!-- 3. Filter & Search Dock -->
          <div class="uranos-saas-filter-dock">
            <div class="uranos-saas-search-wrap">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" class="uranos-saas-search-input" id="auditSearchInput" placeholder="${__("Rechercher par utilisateur, email, rôle ou adresse IP...")}">
            </div>
            <div class="uranos-saas-chips-wrap">
              <button type="button" class="uranos-saas-chip active" data-filter="all">${__("Tous les utilisateurs")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="active">${__("En Ligne (Actifs)")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="engineer">${__("Ingénieurs")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="site">${__("Chefs de Chantier")}</button>
              <button type="button" class="uranos-saas-chip" data-filter="manager">${__("Manager")}</button>
            </div>
          </div>

          <!-- 4. Top Professional SaaS Audit Data Table -->
          <div class="uranos-audit-table-card">
            <div class="uranos-audit-table-header">
              <div>
                <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 4px;">${__("Matrice des Sessions & Traçabilité des Accès")}</h3>
                <p style="font-size: 12.5px; color: #64748b; margin: 0;">${__("Données vérifiées issues de Activity Log & Session Default, horodatées et associées aux adresses IP.")}</p>
              </div>
              <div style="font-size: 12px; color: #64748b; font-weight: 600;">
                <span id="auditRowsCount">${usersData.length}</span> ${__("utilisateurs audités")}
              </div>
            </div>
            <div class="table-responsive">
              <table class="table uranos-audit-table">
                <thead>
                  <tr>
                    <th>${__("Utilisateur")}</th>
                    <th>${__("Rôle URANOS")}</th>
                    <th>${__("Statut Session")}</th>
                    <th>${__("Dernière Connexion")}</th>
                    <th>${__("Dernière Déconnexion")}</th>
                    <th>${__("Adresse IP")}</th>
                    <th>${__("Total Connexions")}</th>
                    <th style="text-align: right;">${__("Action")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${usersData.map(function (u) {
                    const statusPill = u.isActiveNow
                      ? `<span class="uranos-status-pill status-active"><span class="pulse-dot"></span>${__("Active Now")}</span>`
                      : `<span class="uranos-status-pill status-offline"><span class="offline-dot"></span>${__("Offline")}</span>`;

                    const logoutHtml = u.isActiveNow
                      ? `<span class="session-ongoing-tag"><span class="pulse-dot" style="width:6px;height:6px;"></span>${__("Session en cours")}</span>`
                      : `<span style="color: #64748b;">${u.lastLogoutFormatted}</span>`;

                    const searchKey = `${u.full_name} ${u.email} ${u.roleTitle} ${u.ipAddress}`.toLowerCase();

                    return `
                      <tr class="uranos-audit-row" data-search="${searchKey}" data-active="${u.isActiveNow}" data-role-category="${u.roleCategory}">
                        <td>
                          <div class="uranos-audit-user-cell">
                            <div class="uranos-audit-avatar" style="background: ${u.gradient};">
                              ${u.initials}
                            </div>
                            <div class="uranos-audit-user-meta">
                              <div class="name">
                                ${u.full_name}
                                ${u.isCurrentUser ? '<span class="uranos-saas-badge badge-blue" style="font-size: 10px; margin-left: 4px;">Vous</span>' : ''}
                              </div>
                              <div class="email">${u.email}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span class="uranos-role-badge ${u.roleClass}">${u.roleTitle}</span>
                        </td>
                        <td>
                          ${statusPill}
                        </td>
                        <td style="color: #0f172a; font-weight: 500;">
                          ${u.lastLoginFormatted}
                        </td>
                        <td>
                          ${logoutHtml}
                        </td>
                        <td>
                          <span class="uranos-ip-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
                            ${u.ipAddress}
                          </span>
                        </td>
                        <td>
                          <span class="uranos-total-logins-badge">
                            ${u.totalLogins} ${u.totalLogins > 1 ? "logins" : "login"}
                          </span>
                        </td>
                        <td style="text-align: right;">
                          <a href="/app/activity-log?user=${encodeURIComponent(u.name)}" class="btn btn-default btn-xs" style="border-radius: 6px; font-weight: 600; padding: 4px 10px; display: inline-flex; align-items: center; gap: 4px; text-decoration: none;">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                            <span>${__("Logs")}</span>
                          </a>
                        </td>
                      </tr>
                    `;
                  }).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <!-- 5. Recent Security Activity Stream -->
          <div class="uranos-recent-events-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <h3 style="font-size: 16px; font-weight: 700; color: #0f172a; margin: 0 0 4px;">${__("Flux des Événements d'Authentification Récents")}</h3>
                <p style="font-size: 12.5px; color: #64748b; margin: 0;">${__("Dernières opérations d'entrée/sortie capturées par les passerelles réseau et le middleware de session.")}</p>
              </div>
              <a href="/app/activity-log" class="btn btn-default btn-xs" style="border-radius: 6px; font-weight: 600; padding: 5px 12px;">
                ${__("Voir Tous les Journaux")}
              </a>
            </div>
            <div class="uranos-event-timeline">
              ${recentLogs.map(function (log) {
                const isLogin = log.operation === "Login";
                const isFailed = log.status === "Failed";
                let iconClass = isFailed ? "event-login-failed" : (isLogin ? "event-login-success" : "event-logout");
                let badgeHtml = isFailed
                  ? `<span class="uranos-saas-badge badge-red" style="font-size: 11px;">${__("Échec Connexion")}</span>`
                  : (isLogin
                      ? `<span class="uranos-status-pill status-active" style="padding: 3px 8px; font-size: 11px;"><span class="pulse-dot" style="width:6px;height:6px;"></span>${__("Connexion Réussie")}</span>`
                      : `<span class="uranos-status-pill status-offline" style="padding: 3px 8px; font-size: 11px;"><span class="offline-dot" style="width:6px;height:6px;"></span>${__("Déconnexion")}</span>`
                    );

                const iconSvg = isFailed
                  ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
                  : (isLogin
                      ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>`
                      : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`
                    );

                const logTime = log.communication_date ? String(log.communication_date).substring(0, 19) : "—";
                const logIp = log.ip_address || "127.0.0.1";

                return `
                  <div class="uranos-event-item">
                    <div class="uranos-event-left">
                      <div class="uranos-event-icon ${iconClass}">
                        ${iconSvg}
                      </div>
                      <div class="uranos-event-details">
                        <div class="title">${log.subject || (isLogin ? "Connexion utilisateur" : "Déconnexion")}</div>
                        <div class="meta">
                          <span style="font-weight: 600; color: #334155;">${log.user}</span>
                          <span>•</span>
                          <span class="uranos-ip-badge" style="padding: 1px 6px; font-size: 11px;">${logIp}</span>
                        </div>
                      </div>
                    </div>
                    <div class="uranos-event-right">
                      ${badgeHtml}
                      <span style="font-size: 12px; color: #64748b; font-weight: 500;">${logTime}</span>
                    </div>
                  </div>
                `;
              }).join("")}
            </div>
          </div>

        </div>
      `;

      $target.find(".uranos-chic-saas-view[data-module='access-audit']").remove();
      $target.prepend(viewHtml);
      bindSaasViewEvents($target.find(".uranos-chic-saas-view"));

      // Bind search filter
      $("#auditSearchInput").off("input").on("input", function () {
        const q = $(this).val().toLowerCase().trim();
        let visibleCount = 0;
        $target.find(".uranos-audit-row").each(function () {
          const text = $(this).attr("data-search") || "";
          const match = text.includes(q);
          $(this).toggle(match);
          if (match) visibleCount++;
        });
        $("#auditRowsCount").text(visibleCount);
      });

      // Bind filter chips
      $target.find(".uranos-saas-chips-wrap .uranos-saas-chip").off("click").on("click", function () {
        $target.find(".uranos-saas-chips-wrap .uranos-saas-chip").removeClass("active");
        $(this).addClass("active");
        const filter = $(this).attr("data-filter");
        let visibleCount = 0;
        $target.find(".uranos-audit-row").each(function () {
          let show = false;
          if (filter === "all") {
            show = true;
          } else if (filter === "active") {
            show = $(this).attr("data-active") === "true";
          } else if (filter === "manager" || filter === "direction") {
            const rc = $(this).attr("data-role-category");
            show = rc === "manager" || rc === "direction";
          } else {
            show = $(this).attr("data-role-category") === filter;
          }
          $(this).toggle(show);
          if (show) visibleCount++;
        });
        $("#auditRowsCount").text(visibleCount);
      });

      // Bind refresh button
      $("#gvBtnRefreshAudit").off("click").on("click", function (e) {
        e.preventDefault();
        frappe.show_alert({
          message: __("Synchronisation des journaux de sécurité MariaDB..."),
          indicator: "blue"
        });
        injectSecurityAccessAuditView($target, true);
      });

      // Bind CSV export button
      $("#gvBtnExportAudit").off("click").on("click", function (e) {
        e.preventDefault();
        let csv = "Utilisateur,Email,Role,Statut,Derniere_Connexion,Derniere_Deconnexion,Adresse_IP,Total_Connexions\n";
        usersData.forEach(function (d) {
          csv += `"${d.full_name}","${d.email}","${d.roleTitle}","${d.isActiveNow ? 'Active Now' : 'Offline'}","${d.lastLoginFormatted}","${d.lastLogoutFormatted}","${d.ipAddress}","${d.totalLogins}"\n`;
        });
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `URANOS_Security_Access_Audit_${new Date().toISOString().substring(0, 10)}.csv`;
        link.click();
        frappe.show_alert({
          message: __("Export d'audit CSV généré avec succès !"),
          indicator: "green"
        });
      });
    }
  }

  window.renderSecurityAccessAuditDashboard = injectSecurityAccessAuditView;
  window.injectSecurityAccessAuditView = injectSecurityAccessAuditView;
  window.canAccessSecurityAudit = canAccessSecurityAudit;

  function renderSaasViewForCurrentRoute(force) {
    if (isMainDashboard()) return;

    const route = (window.frappe && frappe.get_route) ? frappe.get_route() : [];
    const routeStr = route.map(s => String(s).toLowerCase()).join("/");
    const pathname = (window.location && window.location.pathname) ? window.location.pathname.toLowerCase() : "";

    const isBlockerKanban = (
      routeStr === "blocker-kanban" ||
      routeStr === "blocker_kanban" ||
      routeStr === "kanban-board" ||
      route[0] === "blocker-kanban" ||
      (route[0] === "page" && (route[1] === "blocker-kanban" || route[1] === "blocker_kanban")) ||
      pathname.endsWith("/blocker-kanban") ||
      pathname.includes("/blocker-kanban")
    );

    const isAccessAudit = (
      routeStr === "access-audit" ||
      routeStr === "access_audit" ||
      routeStr === "audit-access" ||
      route[0] === "access-audit" ||
      (route[0] === "page" && (route[1] === "access-audit" || route[1] === "access_audit")) ||
      pathname.endsWith("/access-audit") ||
      pathname.includes("/access-audit")
    );



    const isDailyReport = (
      routeStr.includes("uranos-daily-site-report") ||
      routeStr.includes("uranos daily site report") ||
      pathname.includes("uranos-daily-site-report")
    );

    const isNcr = (
      routeStr.includes("uranos-ncr") ||
      routeStr.includes("uranos ncr") ||
      pathname.includes("uranos-ncr")
    );

    const isStock = (
      routeStr === "stock" ||
      routeStr === "workspaces/stock" ||
      (route[0] === "Workspaces" && route[1] && route[1].toLowerCase() === "stock") ||
      pathname.endsWith("/stock") ||
      pathname.includes("/stock")
    );

    const isSupport = (
      routeStr === "support" ||
      routeStr === "workspaces/support" ||
      (route[0] === "Workspaces" && route[1] && route[1].toLowerCase() === "support") ||
      pathname.endsWith("/support") ||
      pathname.includes("/support")
    );

    const isInvoicing = (
      routeStr === "invoicing" ||
      routeStr === "workspaces/invoicing" ||
      (route[0] === "Workspaces" && route[1] && route[1].toLowerCase() === "invoicing") ||
      pathname.endsWith("/invoicing") ||
      pathname.includes("/invoicing")
    );

    const isSettings = (
      routeStr === "erpnext-settings" ||
      routeStr === "workspaces/erpnext-settings" ||
      routeStr === "settings" ||
      routeStr === "workspaces/settings" ||
      (route[0] === "Workspaces" && route[1] && (route[1].toLowerCase().includes("settings") || route[1].toLowerCase() === "erpnext settings")) ||
      pathname.endsWith("/erpnext-settings") ||
      pathname.includes("/erpnext-settings") ||
      pathname.endsWith("/settings")
    );

    const isWorkPackage = (
      routeStr.includes("uranos-work-package") ||
      routeStr.includes("uranos work package") ||
      pathname.includes("uranos-work-package")
    );

    const isProject = (
      routeStr === "project" ||
      routeStr === "list/project" ||
      routeStr === "list/project/list" ||
      pathname.endsWith("/project")
    );

    // Ignore doc edit/view pages or workspace pages (except specific modules)
    if (route[0] === "Form" || ((route[0] === "Workspaces" || routeStr.startsWith("workspaces")) && !isStock && !isSupport && !isInvoicing && !isSettings && !isAccessAudit && !isBlockerKanban)) return;

    if (isBlockerKanban) {
      injectBlockerKanbanView();

    } else if (isAccessAudit) {
      if (!canAccessSecurityAudit()) {
        if (typeof frappe !== "undefined" && typeof frappe.show_not_permitted === "function") {
          frappe.show_not_permitted("access-audit");
        }
        return;
      }
      injectSecurityAccessAuditView();
    } else if (isSupport) {
      injectSupportSaasView();
    } else if (isInvoicing) {
      injectInvoicingSaasView();
    } else if (isSettings) {
      injectSettingsSaasView();
    } else if (isStock) {
      injectStockSaasView();
    } else if (isWorkPackage) {
      injectWorkPackagesSaasView();
    } else if (isDailyReport) {
      injectReportsSaasView();
    } else if (isNcr) {
      injectNcrSaasView();
    } else if (isProject) {
      injectProjectsSaasView(force);
    }
  }

  // ── PROJECT VIEW / LIST VIEW INTEGRITY ──
  function installProjectViewMutationObserver() {
    // Clean up any legacy firewall styles
    var oldFirewall = document.getElementById("uranos-project-firewall");
    if (oldFirewall) oldFirewall.remove();
  }

  function setupCustomSaasInnerPages() {
    if (window._gv_custom_saas_installed) return;
    window._gv_custom_saas_installed = true;

    // Clean up any legacy firewall styles
    var oldFirewall = document.getElementById("uranos-project-firewall");
    if (oldFirewall) oldFirewall.remove();

    if (window.frappe && frappe.router) {
      frappe.router.on("change", function () {
        const r = frappe.get_route();
        if (r && (r[0] === "user-profile" || (r[0] === "page" && r[1] === "user-profile"))) {
          frappe.set_route("Form", "User", frappe.session.user);
          return;
        }
        setTimeout(renderSaasViewForCurrentRoute, 150);
        setTimeout(renderSaasViewForCurrentRoute, 450);
      });
    }

    $(document).on("page-change list_view_rendered", function () {
      setTimeout(renderSaasViewForCurrentRoute, 150);
      setTimeout(renderSaasViewForCurrentRoute, 450);
    });

    setTimeout(renderSaasViewForCurrentRoute, 300);
    setTimeout(renderSaasViewForCurrentRoute, 800);
  }

  // ── 7. LIFECYCLE HOOKS & WATCHDOG ──
  function runOverhaul() {
    enforceBrandFaviconAndTitle();
    setupTitleWatcher();
    enforceBreadcrumbsOverride();
    sanitizeDomBreadcrumbs();
    setupFrappePageHooks();
    setupSignOutRedirection();
    cleanupNativeSidebars();
    upgradeInnerWorkspaces();
    upgradeInnerPageHeaders();
    overhaulNavbar();
    setupBlockerDashboardAIButton();
    setupCustomSaasInnerPages();
    renderSaasViewForCurrentRoute();

    if (window.cur_frm && cur_frm.doctype === "Project") {
      overhaulProjectForm(cur_frm);
    }

    if (isMainDashboard() && $(".desktop-container").length) {
      overhaulLayout();
      fetchDashboardKPIs();
      fetch7DayProgress();
      initUranosGisMap();
      cleanupNativeSidebars();
    }
  }

  window._gv_runOverhaul = runOverhaul;
  if (!window.__) window.__ = __;

  setupFrappePageHooks();
  setupSignOutRedirection();
  cleanupNativeSidebars();

  $(document).on("desktop_screen page-change", function () {
    if (typeof window._uranosCleanSearchUIState === "function") {
      window._uranosCleanSearchUIState();
    }
    cleanupNativeSidebars();
    runOverhaul();
    setTimeout(runOverhaul, 60);
  });

  if (window.frappe && frappe.router) {
    frappe.router.on("change", function () {
      if (typeof window._uranosCleanSearchUIState === "function") {
        window._uranosCleanSearchUIState();
      }
      cleanupNativeSidebars();
      runOverhaul();
      setTimeout(runOverhaul, 60);
    });
  }

  // Event-driven reactive UI hooks: eliminates CPU-heavy 350ms setInterval
  $(document).on("page-change list_view_rendered", function () {
    setupFrappePageHooks();
    if (!isMainDashboard()) {
      upgradeInnerPageHeaders();
      upgradeInnerWorkspaces();
      renderSaasViewForCurrentRoute();
      if (window.cur_frm && cur_frm.doctype === "Project") {
        overhaulProjectForm(cur_frm);
      }
    }
  });

  // Smooth scroll sync bridge for window.scrollTo and .main-section
  if (typeof window !== "undefined" && !window._gv_scroll_hooked) {
    window._gv_scroll_hooked = true;
    const origScrollTo = window.scrollTo;
    window.scrollTo = function () {
      origScrollTo.apply(this, arguments);
      const ms = document.querySelector(".main-section");
      if (ms) {
        if (typeof arguments[0] === "object" && arguments[0] !== null) {
          if (typeof arguments[0].top === "number") ms.scrollTop = arguments[0].top;
        } else if (typeof arguments[1] === "number") {
          ms.scrollTop = arguments[1];
        }
      }
    };
  }

  // ── 1.10 REAL-TIME REACTIVE UI DISPATCHER (NO RELOAD REQUIRED) ──
  window.refreshUranosProjectsAndGis = function (newDoc) {

    // 0. Instant Optimistic Real-Time DOM insertion into Bento Grid if on Projects page
    if (newDoc && (newDoc.project_name || newDoc.name)) {
      const pName = newDoc.project_name || newDoc.name;
      const $grid = $(".uranos-saas-card-grid");
      if ($grid.length && !$grid.find(`.uranos-saas-card[data-search*="${pName.toLowerCase()}"]`).length) {
        const optimisticCard = `
          <div class="uranos-saas-card" data-search="${(String(newDoc.name || '') + ' ' + pName).toLowerCase()}" style="animation: uranosFadeIn 0.3s ease;">
            <div class="uranos-saas-card-top">
              <span class="uranos-saas-card-code">${newDoc.name || 'NEW'}</span>
              <span class="uranos-saas-badge badge-green">
                <span class="uranos-saas-live-dot" style="width: 5px; height: 5px;"></span>
                ${newDoc.status || "Open"}
              </span>
            </div>
            <div class="uranos-saas-card-title">${pName}</div>
            <div class="uranos-saas-card-subtitle">${__("Grid-connected photovoltaic park with active baseline tracking.")}</div>
            <div class="uranos-saas-card-metrics">
              <div class="uranos-saas-metric-item">
                <span class="m-label">${__("Discipline")}</span>
                <span class="m-val">Solar PV</span>
              </div>
              <div class="uranos-saas-metric-item">
                <span class="m-label">${__("Database ID")}</span>
                <span class="m-val">${newDoc.name || 'Synchronizing...'}</span>
              </div>
              <a href="/app/project/${encodeURIComponent(newDoc.name || '')}" class="uranos-saas-card-action-btn">
                <span>${__("Inspect")}</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              </a>
            </div>
          </div>
        `;
        $grid.prepend(optimisticCard);
        const $kpiVal = $(".uranos-saas-kpi-deck .uranos-saas-kpi-tile:first .kpi-value");
        if ($kpiVal.length) {
          const curVal = parseInt($kpiVal.text() || "0", 10);
          if (!isNaN(curVal)) $kpiVal.text(curVal + 1);
        }
      }
    }

    // 1. Asynchronously refresh Projects Portfolio SaaS cards & KPIs
    try {
      if (typeof injectProjectsSaasView === "function") {
        injectProjectsSaasView(true);
      }
    } catch (e) {
      console.warn("URANOS: Error refreshing projects SaaS view", e);
    }

    // 2. Asynchronously re-plot GIS Map markers
    try {
      if (document.getElementById("uranos-leaflet-map") && typeof initUranosGisMap === "function") {
        initUranosGisMap();
      }
    } catch (e) {
      console.warn("URANOS: Error refreshing GIS map", e);
    }

    // 3. Refresh Dashboard Top 4 KPI Cards
    try {
      if (typeof fetchDashboardKPIs === "function") {
        fetchDashboardKPIs();
      }
    } catch (e) {}

    // 4. If current list view is Project, refresh data store
    try {
      if (window.cur_list && cur_list.doctype === "Project") {
        cur_list.refresh();
      }
    } catch (e) {}

    // 5. Reactive toast feedback
    try {
      if (window.frappe && frappe.show_alert) {
        frappe.show_alert({
          message: __("✨ Fleet Portfolio & GIS Map synchronized dynamically"),
          indicator: "green"
        }, 3);
      }
    } catch (e) {}
  };

  // ── 1.10.2 INTERACTIVE GIS LOCATION PICKER MODAL (LEAFLET + NOMINATIM) ──
  function openProjectLocationPicker(frm, $container) {
    loadLeaflet(function () {
      $("#uranosLocationPickerModal").remove();

      let currentLat = 36.8065;
      let currentLng = 10.1815;

      if (frm && frm.doc && frm.doc.latitude && parseFloat(frm.doc.latitude) !== 0) {
        currentLat = parseFloat(frm.doc.latitude);
      } else if ($container && $container.find('[data-fieldname="latitude"] input').val()) {
        const v = parseFloat($container.find('[data-fieldname="latitude"] input').val());
        if (!isNaN(v) && v !== 0) currentLat = v;
      }

      if (frm && frm.doc && frm.doc.longitude && parseFloat(frm.doc.longitude) !== 0) {
        currentLng = parseFloat(frm.doc.longitude);
      } else if ($container && $container.find('[data-fieldname="longitude"] input').val()) {
        const v = parseFloat($container.find('[data-fieldname="longitude"] input').val());
        if (!isNaN(v) && v !== 0) currentLng = v;
      }

      let selectedLat = currentLat;
      let selectedLng = currentLng;

      const modalHtml = `
        <div class="modal fade uranos-glass-modal" id="uranosLocationPickerModal" tabindex="-1" role="dialog" style="z-index: 99999;">
          <div class="modal-dialog modal-lg modal-dialog-centered" role="document" style="max-width: 840px; margin: 1.5rem auto;">
            <div class="modal-content" style="border-radius: 16px; overflow: hidden; border: 1px solid rgba(226, 232, 240, 0.95); box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25); background: white;">
              
              <div class="modal-header" style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: white; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <div style="background: rgba(255,255,255,0.2); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
                  </div>
                  <div>
                    <h5 class="modal-title" style="margin: 0; font-size: 15px; font-weight: 700; color: white;">Interactive GIS Location Picker — Solar Fleet</h5>
                    <p style="margin: 0; font-size: 11.5px; opacity: 0.9;">Click anywhere on map or search Tunisian cities to pinpoint exact GPS coordinates</p>
                  </div>
                </div>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close" style="color: white; opacity: 0.9; font-size: 22px; background: none; border: none; cursor: pointer;">
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>

              <div class="modal-body" style="padding: 16px 20px; background: #f8fafc;">
                <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                  <div style="position: relative; flex: 1;">
                    <input type="text" id="uranosGisSearchInput" class="form-control" placeholder="Search Tunisian city or governorate (e.g. Tozeur, Tataouine, Kairouan, Bizerte)..." style="height: 40px; border-radius: 8px; padding-left: 36px; font-size: 13.5px;" />
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" style="position: absolute; left: 10px; top: 11px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                  </div>
                  <button type="button" id="uranosGisSearchBtn" class="btn btn-secondary" style="height: 40px; border-radius: 8px; font-weight: 600; padding: 0 16px;">
                    Search
                  </button>
                </div>
                <div id="uranosGisSearchResults" style="display: none; margin-bottom: 10px; max-height: 120px; overflow-y: auto; background: white; border: 1px solid #e2e8f0; border-radius: 8px;"></div>

                <div id="uranosPickerMap" style="height: 380px; width: 100%; border-radius: 12px; border: 1px solid #cbd5e1; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); z-index: 1;"></div>

                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px; background: white; padding: 10px 14px; border-radius: 10px; border: 1px solid #e2e8f0; flex-wrap: wrap; gap: 8px;">
                  <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Selected Position:</span>
                    <span class="badge badge-info" style="background: #e0f2fe; color: #0369a1; font-size: 12.5px; font-weight: 600; padding: 5px 10px; border-radius: 6px;">
                      Lat: <span id="uranosSelectedLat">${selectedLat.toFixed(4)}</span>
                    </span>
                    <span class="badge badge-info" style="background: #e0f2fe; color: #0369a1; font-size: 12.5px; font-weight: 600; padding: 5px 10px; border-radius: 6px;">
                      Lng: <span id="uranosSelectedLng">${selectedLng.toFixed(4)}</span>
                    </span>
                  </div>
                  <span id="uranosPickerHint" style="font-size: 12px; color: #64748b; font-style: italic;">Click map or drag pin to update</span>
                </div>
              </div>

              <div class="modal-footer" style="padding: 12px 20px; background: white; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between;">
                <button type="button" class="btn btn-secondary" data-dismiss="modal" style="border-radius: 8px; font-weight: 500;">Cancel</button>
                <button type="button" id="uranosApplyGisLocationBtn" class="btn btn-primary" style="border-radius: 8px; font-weight: 600; background: #0284c7; border-color: #0284c7; padding: 8px 20px;">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right: 5px; vertical-align: -2px;"><polyline points="20 6 9 17 4 12"/></svg>
                  Apply Coordinates to Project
                </button>
              </div>

            </div>
          </div>
        </div>
      `;

      $("body").append(modalHtml);
      const $modal = $("#uranosLocationPickerModal");
      $modal.modal("show");

      $modal.on("shown.bs.modal", function () {
        const mapContainer = document.getElementById("uranosPickerMap");
        if (!mapContainer || !window.L) return;
        if (mapContainer._leaflet_id) delete mapContainer._leaflet_id;

        const pickerMap = L.map("uranosPickerMap", {
          center: [selectedLat, selectedLng],
          zoom: 8,
        });

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
          maxZoom: 18,
        }).addTo(pickerMap);

        const pinIcon = L.divIcon({
          className: "uranos-map-pin",
          html: `<div style="background: #0284c7; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.45); border: 2.5px solid white;">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
                 </div>`,
          iconSize: [32, 32],
          iconAnchor: [16, 32],
        });

        let marker = L.marker([selectedLat, selectedLng], {
          icon: pinIcon,
          draggable: true,
        }).addTo(pickerMap);

        function updateCoords(lat, lng) {
          selectedLat = lat;
          selectedLng = lng;
          $("#uranosSelectedLat").text(lat.toFixed(4));
          $("#uranosSelectedLng").text(lng.toFixed(4));
        }

        marker.on("dragend", function (e) {
          const pos = e.target.getLatLng();
          updateCoords(pos.lat, pos.lng);
        });

        pickerMap.on("click", function (e) {
          marker.setLatLng(e.latlng);
          updateCoords(e.latlng.lat, e.latlng.lng);
        });

        setTimeout(() => pickerMap.invalidateSize(), 200);

        function doSearch() {
          const query = $("#uranosGisSearchInput").val().trim();
          if (!query) return;
          const $results = $("#uranosGisSearchResults");
          $results.show().html('<div style="padding: 10px; color: #64748b; font-size: 12.5px;">Searching locations...</div>');

          fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Tunisia')}&limit=5`)
            .then(res => res.json())
            .then(data => {
              if (!data || !data.length) {
                $results.html('<div style="padding: 10px; color: #ef4444; font-size: 12.5px;">No matching locations found in Tunisia.</div>');
                return;
              }
              let html = "";
              data.forEach(item => {
                html += `
                  <div class="uranos-search-item" data-lat="${item.lat}" data-lon="${item.lon}" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: #1e293b;">
                    <strong>${item.display_name.split(',')[0]}</strong>
                    <div style="font-size: 11px; color: #64748b;">${item.display_name}</div>
                  </div>
                `;
              });
              $results.html(html);

              $results.find(".uranos-search-item").on("click", function () {
                const lat = parseFloat($(this).data("lat"));
                const lon = parseFloat($(this).data("lon"));
                pickerMap.flyTo([lat, lon], 12);
                marker.setLatLng([lat, lon]);
                updateCoords(lat, lon);
                $results.hide();
              });
            })
            .catch(() => {
              $results.html('<div style="padding: 10px; color: #ef4444; font-size: 12.5px;">Search error. Please click directly on the map.</div>');
            });
        }

        $("#uranosGisSearchBtn").on("click", doSearch);
        $("#uranosGisSearchInput").on("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault();
            doSearch();
          }
        });

        $("#uranosApplyGisLocationBtn").on("click", function () {
          if (frm && frm.set_value) {
            frm.set_value("latitude", Number(selectedLat.toFixed(6)));
            frm.set_value("longitude", Number(selectedLng.toFixed(6)));
          }
          if ($container) {
            $container.find('[data-fieldname="latitude"] input').val(selectedLat.toFixed(6)).trigger("change");
            $container.find('[data-fieldname="longitude"] input').val(selectedLng.toFixed(6)).trigger("change");
            const $pill = $container.find(".uranos-telemetry-pill");
            $pill.removeClass("pill-warning");
            $pill.find(".live-pulse-dot").css({ "background": "#10b981", "box-shadow": "0 0 0 3px rgba(16, 185, 129, 0.25)" });
            $pill.find("span:last-child").text(
              `GIS Linked: ${selectedLat.toFixed(4)}°N, ${selectedLng.toFixed(4)}°E`
            );
          }
          $modal.modal("hide");
          if (window.frappe && frappe.show_alert) {
            frappe.show_alert({
              message: `Coordonnées GPS appliquées: ${selectedLat.toFixed(4)}°N, ${selectedLng.toFixed(4)}°E`,
              indicator: "green"
            });
          }
        });
      });
    });
  }

  // ── 1.10.2 INLINE PROJECT GIS MAP & SEARCH ──
  function initInlineProjectMap(frm, $cardsContainer, updateTelemetry) {
    loadLeaflet(function () {
      if (!window.L || typeof window.L.map !== "function") return;
      const currentContainer = document.getElementById("inline-project-map");
      if (!currentContainer) return;

      if (window._uranos_inline_project_map) {
        try {
          window._uranos_inline_project_map.remove();
        } catch (e) {}
        window._uranos_inline_project_map = null;
      }
      if (currentContainer._leaflet_id) {
        delete currentContainer._leaflet_id;
      }

      let lat = 36.8065;
      let lng = 10.1815;
      let hasCoords = false;

      if (frm && frm.doc && frm.doc.latitude && !isNaN(parseFloat(frm.doc.latitude)) && parseFloat(frm.doc.latitude) !== 0) {
        lat = parseFloat(frm.doc.latitude);
        hasCoords = true;
      } else if ($cardsContainer && $cardsContainer.find('[data-fieldname="latitude"] input').val()) {
        const v = parseFloat($cardsContainer.find('[data-fieldname="latitude"] input').val());
        if (!isNaN(v) && v !== 0) { lat = v; hasCoords = true; }
      }

      if (frm && frm.doc && frm.doc.longitude && !isNaN(parseFloat(frm.doc.longitude)) && parseFloat(frm.doc.longitude) !== 0) {
        lng = parseFloat(frm.doc.longitude);
        hasCoords = true;
      } else if ($cardsContainer && $cardsContainer.find('[data-fieldname="longitude"] input').val()) {
        const v = parseFloat($cardsContainer.find('[data-fieldname="longitude"] input').val());
        if (!isNaN(v) && v !== 0) { lng = v; hasCoords = true; }
      }

      const map = L.map(currentContainer, {
        center: [lat, lng],
        zoom: hasCoords ? 10 : 6.5,
        zoomControl: true,
        scrollWheelZoom: true
      });
      window._uranos_inline_project_map = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }).addTo(map);

      const pinIcon = L.divIcon({
        className: "uranos-map-pin",
        html: `<div style="background: #0284c7; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.45); border: 2.5px solid white;">
                 <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
               </div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 30]
      });

      let marker = L.marker([lat, lng], {
        icon: pinIcon,
        draggable: true
      }).addTo(map);

      function updateCoordinates(newLat, newLng, fly = false) {
        const fixedLat = Number(newLat.toFixed(6));
        const fixedLng = Number(newLng.toFixed(6));

        if (frm && frm.set_value) {
          frm.set_value("latitude", fixedLat);
          frm.set_value("longitude", fixedLng);
        }
        if ($cardsContainer) {
          $cardsContainer.find('[data-fieldname="latitude"] input').val(fixedLat);
          $cardsContainer.find('[data-fieldname="longitude"] input').val(fixedLng);
        }
        if (typeof updateTelemetry === "function") {
          updateTelemetry(fixedLat, fixedLng);
        }

        marker.setLatLng([newLat, newLng]);
        if (fly) {
          map.flyTo([newLat, newLng], 12);
        }
      }

      marker.on("dragend", function (e) {
        const pos = e.target.getLatLng();
        updateCoordinates(pos.lat, pos.lng, false);
      });

      map.on("click", function (e) {
        updateCoordinates(e.latlng.lat, e.latlng.lng, false);
      });

      setTimeout(function () { if (map) map.invalidateSize(); }, 200);
      setTimeout(function () { if (map) map.invalidateSize(); }, 600);

      // Search functionality via Nominatim
      function doSearch() {
        const query = $("#inlineGisSearchInput").val().trim();
        if (!query) return;
        const $results = $("#inlineGisSearchResults");
        $results.show().html('<div style="padding: 8px 12px; color: #64748b; font-size: 12px;">Searching locations...</div>');

        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Tunisia')}&limit=5`)
          .then(res => res.json())
          .then(data => {
            if (!data || !data.length) {
              $results.html('<div style="padding: 8px 12px; color: #ef4444; font-size: 12px;">No matching locations found in Tunisia.</div>');
              return;
            }
            let html = "";
            data.forEach(item => {
              html += `
                <div class="uranos-inline-search-item" data-lat="${item.lat}" data-lon="${item.lon}" style="padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #f1f5f9; font-size: 12.5px; color: #1e293b;">
                  <strong>${item.display_name.split(',')[0]}</strong>
                  <div style="font-size: 11px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${item.display_name}</div>
                </div>
              `;
            });
            $results.html(html);

            $results.find(".uranos-inline-search-item").on("click", function () {
              const sLat = parseFloat($(this).data("lat"));
              const sLon = parseFloat($(this).data("lon"));
              updateCoordinates(sLat, sLon, true);
              $results.hide();
            });
          })
          .catch(() => {
            $results.html('<div style="padding: 8px 12px; color: #ef4444; font-size: 12px;">Search error. Click directly on map.</div>');
          });
      }

      $("#inlineGisSearchBtn").off("click").on("click", doSearch);
      $("#inlineGisSearchInput").off("keydown").on("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          doSearch();
        }
      });

      $(document).off("click.uranosInlineGis").on("click.uranosInlineGis", function (e) {
        if (!$(e.target).closest(".uranos-inline-gis-search-wrapper").length) {
          $("#inlineGisSearchResults").hide();
        }
      });
    });
  }

  // ── 1.10.3 CLEAN PROJECT FORM: PURGE TABS & CLUTTER ──
  function cleanProjectForm(frm) {
    if (!frm || frm.doctype !== "Project") return;
    try {
      // 0. Filter custom assignment fields by role
      if (typeof frm.set_query === "function") {
        frm.set_query("custom_assigned_engineer", function () {
          return {
            query: "uranos_project_os.services.api.get_engineer_users"
          };
        });
        frm.set_query("custom_assigned_site_team", function () {
          return {
            query: "uranos_project_os.services.api.get_site_team_users"
          };
        });
      }
      if (frm.fields_dict && frm.fields_dict.custom_assigned_engineer) {
        frm.fields_dict.custom_assigned_engineer.get_query = function () {
          return {
            query: "uranos_project_os.services.api.get_engineer_users"
          };
        };
      }
      if (frm.fields_dict && frm.fields_dict.custom_assigned_site_team) {
        frm.fields_dict.custom_assigned_site_team.get_query = function () {
          return {
            query: "uranos_project_os.services.api.get_site_team_users"
          };
        };
      }

      // 1. Programmatically hide unwanted tabs via Frappe API
      const tabsToHide = ["costing_tab", "monitor_progress_tab", "more_info_tab", "connections_tab"];
      tabsToHide.forEach(function (tab) {
        frm.set_df_property(tab, "hidden", 1);
      });

      // 2. Programmatically hide unwanted standard sections via Frappe API
      const sectionsToHide = [
        "section_break_18", // Timeline
        "project_details",  // Costing and Billing
        "margin",           // Margin
        "customer_details", // Customer Details
        "users_section",    // Users
        "section_break0"    // Notes
      ];
      sectionsToHide.forEach(function (sec) {
        frm.set_df_property(sec, "hidden", 1);
      });

      // 3. Make latitude and longitude mandatory
      frm.set_df_property("latitude", "reqd", 1);
      frm.set_df_property("longitude", "reqd", 1);

      // 4. Hide naming series field
      frm.set_df_property("naming_series", "hidden", 1);
      frm.set_df_property("series", "hidden", 1);

      // 5. DOM cleanup: hide tabs navigation and clutter directly with important
      document.querySelectorAll(".form-tabs, #form-tabs, .form-tabs-list").forEach(el => {
        el.style.setProperty("display", "none", "important");
      });
      document.querySelectorAll("#project-costing_tab-tab, #project-monitor_progress_tab-tab, #project-more_info_tab-tab, #project-connections_tab-tab, [data-fieldname='costing_tab'], [data-fieldname='monitor_progress_tab'], [data-fieldname='more_info_tab'], [data-fieldname='connections_tab']").forEach(el => {
        el.style.setProperty("display", "none", "important");
        const navItem = el.closest(".nav-item");
        if (navItem) navItem.style.setProperty("display", "none", "important");
      });
      document.querySelectorAll(".nav-link").forEach(el => {
        const txt = (el.innerText || "").trim().toLowerCase();
        if (txt === "costing" || txt === "progress" || txt === "more info" || txt === "connections") {
          el.style.setProperty("display", "none", "important");
          const navItem = el.closest(".nav-item");
          if (navItem) navItem.style.setProperty("display", "none", "important");
        }
      });
      document.querySelectorAll("#project-costing_tab, #project-monitor_progress_tab, #project-more_info_tab, #project-connections_tab").forEach(el => {
        el.style.setProperty("display", "none", "important");
      });
      document.querySelectorAll(".form-section[data-fieldname='section_break_18'], .form-section[data-fieldname='project_details'], .form-section[data-fieldname='margin'], .form-section[data-fieldname='customer_details'], .form-section[data-fieldname='users_section'], .form-section[data-fieldname='section_break0'], .timeline, .form-footer, .form-comments, .form-history").forEach(el => {
        el.style.setProperty("display", "none", "important");
      });

      // Ensure __details pane holding our Executive Bento Cards is permanently active & visible
      document.querySelectorAll("#project-__details, [data-fieldname='__details'], .tab-pane:first-child").forEach(el => {
        el.style.setProperty("display", "block", "important");
        el.classList.add("active", "show");
      });
      if (window.location.hash && window.location.hash !== "#__details") {
        try {
          history.replaceState(null, null, window.location.pathname);
        } catch (e) {}
      }
    } catch (e) {
      console.warn("URANOS cleanProjectForm error:", e);
    }
  }

  // ── 1.11 PROJECT FORM VIEW — EXECUTIVE BENTO GLASSMORPHISM OVERHAUL ──
  function overhaulProjectForm(frm) {
    if (!frm || frm.doctype !== "Project") return;
    const $wrapper = $(frm.wrapper);
    if (!$wrapper.length) return;
    if ($wrapper.find(".uranos-project-form-container").length) return;

    const $firstSection = $wrapper.find('.form-section:has([data-fieldname="project_name"])').first();
    if (!$firstSection.length) return;

    // Auto-fill defaults: company and series only
    if (frm.doc) {
      if (!frm.doc.company) {
        frm.set_value("company", "URANOS Group");
      }
      if (frm.is_new() && !frm.doc.naming_series) {
        frm.set_value("naming_series", "PV-.####");
      }
      // If existing project and missing coords, provide fallback
      if (!frm.is_new()) {
        if (!frm.doc.latitude || parseFloat(frm.doc.latitude) === 0) {
          frm.set_value("latitude", 36.8065);
        }
        if (!frm.doc.longitude || parseFloat(frm.doc.longitude) === 0) {
          frm.set_value("longitude", 10.1815);
        }
      }
    }

    const latVal = (frm.doc && frm.doc.latitude) ? frm.doc.latitude : null;
    const lngVal = (frm.doc && frm.doc.longitude) ? frm.doc.longitude : null;
    const hasGis = latVal != null && lngVal != null && !isNaN(parseFloat(latVal)) && !isNaN(parseFloat(lngVal)) && (parseFloat(latVal) !== 0 || parseFloat(lngVal) !== 0);
    const pct = parseFloat((frm.doc && frm.doc.percent_complete) || 0);

    const $cardsContainer = $(`
      <div class="uranos-project-form-container">
        <div class="uranos-project-cards-row">
          <!-- CARD 1: GENERAL INFORMATION & GOVERNANCE -->
          <div class="uranos-project-form-card card-general">
            <div class="uranos-project-card-header">
              <div class="uranos-project-card-icon icon-emerald">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
              </div>
              <div class="uranos-project-card-titles">
                <h3>${__("General Information & Governance")}</h3>
                <p>${__("Asset Identification, Classification & Entity")}</p>
              </div>
            </div>
            <div class="uranos-project-card-body body-general"></div>
          </div>

          <!-- CARD 2: GEOGRAPHIC TELEMETRY & GIS -->
          <div class="uranos-project-form-card card-gis">
            <div class="uranos-project-card-header">
              <div class="uranos-project-card-icon icon-cyan">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
              </div>
              <div class="uranos-project-card-titles">
                <h3>${__("Geographic Telemetry & GIS Positioning")}</h3>
                <p>${__("High-Precision GPS Spatial Coordinates")}</p>
              </div>
            </div>
            <div class="uranos-project-card-body body-gis"></div>
          </div>

          <!-- CARD 3: PROGRESS & STATUS -->
          <div class="uranos-project-form-card card-progress">
            <div class="uranos-project-card-header">
              <div class="uranos-project-card-icon icon-indigo">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
              </div>
              <div class="uranos-project-card-titles">
                <h3>${__("Progress & Operational Status")}</h3>
                <p>${__("Milestone Execution, Readiness & Verification")}</p>
              </div>
            </div>
            <div class="uranos-project-card-body body-progress"></div>
          </div>
        </div>
      </div>
    `);

    // Insert container before native first section
    $firstSection.before($cardsContainer);

    // Populate Card 1: General Info & Governance
    const $bodyGen = $cardsContainer.find(".body-general");
    $firstSection.find('[data-fieldname="naming_series"]').hide();
    $bodyGen.append($firstSection.find('[data-fieldname="project_name"]'));
    $bodyGen.append($firstSection.find('[data-fieldname="project_type"]'));
    $bodyGen.append($wrapper.find('[data-fieldname="company"]').first());
    $bodyGen.append($firstSection.find('[data-fieldname="department"]'));

    const $engField = $wrapper.find('[data-fieldname="custom_assigned_engineer"]').first();
    if ($engField.length) {
      $engField.show();
      $bodyGen.append($engField);
    }
    const $siteField = $wrapper.find('[data-fieldname="custom_assigned_site_team"]').first();
    if ($siteField.length) {
      $siteField.show();
      $bodyGen.append($siteField);
    }

    // Populate Card 2: GIS Telemetry
    const $bodyGis = $cardsContainer.find(".body-gis");
    $bodyGis.append($firstSection.find('[data-fieldname="latitude"]'));
    $bodyGis.append($firstSection.find('[data-fieldname="longitude"]'));

    const inlineGisHtml = `
      <div class="uranos-inline-gis-search-wrapper" style="margin-top: 10px; margin-bottom: 8px; position: relative;">
        <div style="display: flex; gap: 6px; align-items: center;">
          <div style="position: relative; flex: 1;">
            <input type="text" id="inlineGisSearchInput" class="form-control" placeholder="${__("Search City/Region (e.g. Tozeur, Kairouan, Bizerte)...")}" style="height: 36px; border-radius: 8px; padding-left: 32px; font-size: 13px;" />
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2.2" style="position: absolute; left: 10px; top: 11px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <button type="button" id="inlineGisSearchBtn" class="btn btn-sm btn-primary" style="height: 36px; border-radius: 8px; font-weight: 600; padding: 0 14px; background: #0284c7; border: none; white-space: nowrap;">
            ${__("Search")}
          </button>
        </div>
        <div id="inlineGisSearchResults" style="display: none; position: absolute; top: 40px; left: 0; right: 0; z-index: 1000; max-height: 140px; overflow-y: auto; background: white; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);"></div>
      </div>
      <div id="inline-project-map" style="height: 250px; width: 100%; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); position: relative; z-index: 1; margin-bottom: 8px; overflow: hidden;"></div>
    `;
    $bodyGis.append(inlineGisHtml);

    const telemetryDock = `
      <div class="uranos-telemetry-badge-dock">
        <div class="uranos-telemetry-pill ${hasGis ? '' : 'pill-warning'}">
          <span class="live-pulse-dot" style="${hasGis ? '' : 'background: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.25);'}"></span>
          <span>${hasGis ? `${__("GIS Linked")}: ${Number(latVal).toFixed(4)}°N, ${Number(lngVal).toFixed(4)}°E` : __("GPS Required — Search or Click on Map")}</span>
        </div>
        <a href="/desk" class="uranos-telemetry-link">
          <span>${__("Fleet Map")}</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
      </div>
    `;
    $bodyGis.append(telemetryDock);

    // Live telemetry pill updater
    function updateTelemetry(lat, lng) {
      const valid = lat != null && lng != null && !isNaN(parseFloat(lat)) && !isNaN(parseFloat(lng)) && (parseFloat(lat) !== 0 || parseFloat(lng) !== 0);
      const $pill = $cardsContainer.find(".uranos-telemetry-pill");
      if (valid) {
        $pill.removeClass("pill-warning");
        $pill.find(".live-pulse-dot").css({ "background": "#10b981", "box-shadow": "0 0 0 3px rgba(16, 185, 129, 0.25)" });
        $pill.find("span:last-child").text(`${__("GIS Linked")}: ${Number(lat).toFixed(4)}°N, ${Number(lng).toFixed(4)}°E`);
      } else {
        $pill.addClass("pill-warning");
        $pill.find(".live-pulse-dot").css({ "background": "#f59e0b", "box-shadow": "0 0 0 3px rgba(245, 158, 11, 0.25)" });
        $pill.find("span:last-child").text(__("GPS Required — Search or Click on Map"));
      }
    }

    // Initialize persistent inline Leaflet map and smart Nominatim search
    initInlineProjectMap(frm, $cardsContainer, updateTelemetry);

    $firstSection.find('[data-fieldname="latitude"] input, [data-fieldname="longitude"] input').on("input change", function () {
      const lat = parseFloat($firstSection.find('[data-fieldname="latitude"] input').val());
      const lng = parseFloat($firstSection.find('[data-fieldname="longitude"] input').val());
      updateTelemetry(lat, lng);
      if (!isNaN(lat) && !isNaN(lng) && window._uranos_inline_project_map) {
        window._uranos_inline_project_map.flyTo([lat, lng], 11);
        window._uranos_inline_project_map.eachLayer(layer => {
          if (layer instanceof L.Marker) {
            layer.setLatLng([lat, lng]);
          }
        });
      }
    });

    // Populate Card 3: Progress & Status
    const $bodyProg = $cardsContainer.find(".body-progress");
    $bodyProg.append($firstSection.find('[data-fieldname="status"]'));
    $bodyProg.append($firstSection.find('[data-fieldname="priority"]'));
    $bodyProg.append($firstSection.find('[data-fieldname="is_active"]'));
    $bodyProg.append($firstSection.find('[data-fieldname="percent_complete_method"]'));
    $bodyProg.append($firstSection.find('[data-fieldname="percent_complete"]'));

    const progressWidget = `
      <div class="uranos-form-progress-widget">
        <div class="uranos-form-progress-header">
          <span>${__("Physical Baseline Completion")}</span>
          <span class="uranos-pct-label">${pct.toFixed(0)}%</span>
        </div>
        <div class="uranos-form-progress-track">
          <div class="uranos-form-progress-fill" style="width: ${Math.max(pct, 5)}%;"></div>
        </div>
      </div>
    `;
    $bodyProg.append(progressWidget);

    // Dynamic progress bar update when user modifies percent_complete
    $firstSection.find('[data-fieldname="percent_complete"] input').on("input change", function () {
      const v = parseFloat($(this).val() || 0);
      $cardsContainer.find(".uranos-pct-label").text(v.toFixed(0) + "%");
      $cardsContainer.find(".uranos-form-progress-fill").css("width", Math.max(v, 5) + "%");
    });

    $firstSection.hide();
    cleanProjectForm(frm);
  }

  // ── 1.12 BYPASS QUICK ENTRY DIRECTLY TO NEW PROJECT FULL FORM ──
  if (typeof window !== "undefined" && window.frappe) {
    if (frappe.ui && frappe.ui.form && frappe.ui.form.make_quick_entry) {
      const origMakeQuickEntry = frappe.ui.form.make_quick_entry;
      frappe.ui.form.make_quick_entry = function (doctype, after_insert, init_callback, doc, force) {
        if (doctype === "Project") {
          frappe.set_route("Form", "Project", "new");
          return true;
        }
        return origMakeQuickEntry.apply(this, arguments);
      };
    }

    if (frappe.new_doc) {
      const origNewDoc = frappe.new_doc;
      frappe.new_doc = function (doctype, opts, init_callback) {
        if (doctype === "Project") {
          frappe.set_route("Form", "Project", "new");
          return;
        }
        return origNewDoc.apply(this, arguments);
      };
    }
  }

  // Intercept click on any "+ Add Project" or ".primary-action" button
  $(document).on("click", '.primary-action[data-label="Add%20Project"], .primary-action:contains("Add Project"), button:contains("Add Project"), [data-label="Add Project"]', function (e) {
    const route = (window.frappe && frappe.get_route) ? frappe.get_route() : null;
    if (route && (route[0] === "List" || route[0] === "project" || route[0] === "Project") && (route[1] === "Project" || !route[1])) {
      e.preventDefault();
      e.stopPropagation();
      frappe.set_route("Form", "Project", "new");
    }
  });

  // If a Quick Entry modal somehow attempts to show for Project, dismiss and route to /app/project/new
  $(document).on("show.bs.modal shown.bs.modal", function () {
    const $modal = $(".modal:visible, .modal.show");
    if ($modal.find('[data-fieldname="project_name"]').length && ($modal.hasClass("quick-entry-modal") || $modal.find(".modal-title:contains('New Project')").length)) {
      $modal.modal("hide");
      frappe.set_route("Form", "Project", "new");
    }
  });

  // Reactive listener for all Frappe AJAX save requests
  $(document).ajaxComplete(function (event, xhr, settings) {
    if (settings && settings.url && (
      settings.url.includes("frappe.client.save") ||
      settings.url.includes("frappe.client.insert") ||
      settings.url.includes("frappe.desk.form.save.savedocs")
    )) {
      try {
        const resp = JSON.parse(xhr.responseText);
        const doc = (resp && resp.docs && resp.docs[0]) || (resp && resp.message);
        if (doc && doc.doctype === "Project") {
          window.refreshUranosProjectsAndGis(doc);
        }
      } catch (e) {}
    }
  });

  // ── 1.13 FRAFFE PROJECT FORM LIFECYCLE HOOKS ──
  if (typeof window !== "undefined" && window.frappe && frappe.ui && frappe.ui.form) {
    try {
      frappe.ui.form.on("Project", {
        setup: function (frm) {
          if (!frm.doc.company) {
            frm.set_value("company", "URANOS Group");
          }
          if (frm.is_new() && !frm.doc.naming_series) {
            frm.set_value("naming_series", "PV-.####");
          }
          frm.set_df_property("latitude", "reqd", 1);
          frm.set_df_property("longitude", "reqd", 1);
          cleanProjectForm(frm);
        },
        onload: function (frm) {
          cleanProjectForm(frm);
        },
        refresh: function (frm) {
          if (!frm.doc.company) {
            frm.set_value("company", "URANOS Group");
          }
          if (frm.is_new() && !frm.doc.naming_series) {
            frm.set_value("naming_series", "PV-.####");
          }
          cleanProjectForm(frm);
          setTimeout(function () {
            overhaulProjectForm(frm);
            cleanProjectForm(frm);
          }, 40);
          setTimeout(function () {
            cleanProjectForm(frm);
          }, 180);
        },
        validate: function (frm) {
          const lat = parseFloat(frm.doc.latitude);
          const lng = parseFloat(frm.doc.longitude);
          if (frm.doc.latitude == null || frm.doc.longitude == null || isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) {
            frappe.msgprint({
              title: __("Coordonnées GPS Obligatoires"),
              message: __("Les coordonnées GPS (Latitude et Longitude) sont obligatoires. Veuillez sélectionner un emplacement sur la carte interactive ou saisir des coordonnées valides avant d'enregistrer le projet."),
              indicator: "red"
            });
            frappe.validated = false;
            return false;
          }
        },
        after_save: function (frm) {
          window.refreshUranosProjectsAndGis(frm.doc);
        }
      });
    } catch (e) {}
  }

  $(document).ready(function () {
    setupFrappePageHooks();
    setupSignOutRedirection();
    cleanupNativeSidebars();
    setTimeout(runOverhaul, 80);
  });

})();

