/* Focused Desk actions. Client role hints do not replace server authorization. */
(() => {
  if (window.uranosSupportWorkflowsRegistered) return;
  window.uranosSupportWorkflowsRegistered = true;
  const ar = String(frappe.boot.lang || "fr").startsWith("ar");
  const labels = {
    workflow: ["Actions URANOS", "إجراءات أورانوس"], save: ["Enregistrez le brouillon avant cette action.", "احفظ المسودة قبل هذا الإجراء."],
    confirm: ["Confirmer", "تأكيد"], note: ["Note / justification", "ملاحظة / تبرير"], proof: ["Preuves jointes", "الأدلة المرفقة"],
    file: ["Fichier privé", "ملف خاص"], proofHint: ["Joignez les preuves au document, puis sélectionnez-les ici.", "أرفق الأدلة بالمستند ثم اخترها هنا."],
    analysis: ["Lancer l'analyse d'impact", "بدء تحليل التأثير"], technical: ["Approuver techniquement", "الموافقة الفنية"],
    assess: ["Évaluer le coût", "تقييم التكلفة"], cost: ["Impact coût signé (zéro à confirmer)", "أثر التكلفة بالإشارة (تأكيد الصفر)"],
    policy: ["Politique financière approuvée", "السياسة المالية المعتمدة"], finance: ["Signer la validation financière", "توقيع الموافقة المالية"],
    release: ["Autoriser la mise en œuvre", "السماح بالتنفيذ"], implement: ["Enregistrer la mise en œuvre", "تسجيل التنفيذ"],
    verify: ["Vérifier la mise en œuvre", "التحقق من التنفيذ"], close: ["Clôturer après vérification", "الإغلاق بعد التحقق"],
    reject: ["Rejeter avec motif", "الرفض مع السبب"], submit: ["Figer et soumettre le rapport", "تثبيت التقرير وإرساله"],
    approveReport: ["Approuver le rapport", "اعتماد التقرير"], assign: ["Affecter un responsable", "تعيين مسؤول"],
    user: ["Responsable", "المسؤول"], answer: ["Répondre avec preuves", "الإجابة مع الأدلة"], response: ["Réponse", "الإجابة"],
    resolve: ["Soumettre la résolution", "إرسال الحل"], resolution: ["Résolution constatée", "الحل المنفذ"],
    hours: ["Heures réellement perdues", "ساعات التعطل الفعلية"], review: ["Revoir la sévérité", "مراجعة الخطورة"],
    severity: ["Sévérité", "الخطورة"], waiting: ["Une validation indépendante reste nécessaire.", "لا تزال هناك حاجة إلى موافقة مستقلة."],
    frozen: ["Rapport figé à la soumission", "تقرير ثابت عند الإرسال"], installed: ["Installations vérifiées", "التركيبات المتحقق منها"],
    pending: ["Déclarations en attente", "تصريحات بانتظار التحقق"], moves: ["Mouvements ERP validés", "حركات المخزون المعتمدة"],
    source: ["Référence", "المرجع"], activity: ["Activité / zone", "النشاط / المنطقة"], qty: ["Quantité vérifiée", "الكمية المتحقق منها"],
    approvePolicy: ["Approuver la politique Change Cost", "اعتماد سياسة تكلفة التغيير"],
    // Phase 3 — Blocker service layer labels
    blkAssign:        ["Affecter un responsable",          "تعيين مسؤول"],
    blkJustification: ["Justification (obligatoire)",      "المبرر (إلزامي)"],
    blkSubmit:        ["Soumettre la résolution",          "إرسال الحل"],
    blkAction:        ["Action corrective constatée",      "الإجراء التصحيحي المنفذ"],
    blkClose:         ["Clôturer après vérification",      "الإغلاق بعد التحقق"],
    blkReviewReason:  ["Note de vérification (optionnel)", "ملاحظة التحقق (اختياري)"],
    blkReopen:        ["Rouvrir pour reprise",             "إعادة فتح للمعالجة"],
    blkReason:        ["Motif de réouverture",             "سبب إعادة الفتح"],
    blkGoldenRule:    [
      "Règle d'or : vous avez soumis cette résolution. Un vérificateur indépendant est requis pour la clôture.",
      "القاعدة الذهبية: قمت بتقديم هذا الحل. يلزم وجود مدقق مستقل للإغلاق.",
    ],
    blkResolved:      ["Résolution soumise en attente de vérification indépendante.", "تم إرسال الحل في انتظار التحقق المستقل."],
    blkClosed:        ["Blocage clôturé avec succès.",     "تم إغلاق العائق بنجاح."],
    blkReopened:      ["Blocage rouvert pour reprise.",    "تمت إعادة فتح العائق."],
  };
  const t = key => labels[key][ar ? 1 : 0];
  const roles = (...names) => names.some(name => frappe.user_roles.includes(`URANOS ${name}`));
  const finance = () => roles("Executive", "Finance Controller");
  const engineering = () => roles("Engineering Director");
  const coordinator = () => roles("Engineering Director", "Project Manager", "Site Controller");
  const esc = value => frappe.utils.escape_html(String(value ?? ""));

  function run(frm, service, method, args = {}) {
    if (frm.is_dirty()) return frappe.msgprint(t("save"));
    return frappe.call({method: `uranos_project_os.services.${service}.${method}`, type: "POST",
      args: {name: frm.doc.name, ...args}, freeze: true,
      callback: async ({message}) => {
        if (message?.pending_independent_signature || message?.pending_independent_review) frappe.msgprint(t("waiting"));
        await frm.reload_doc();
      }});
  }

  function prompt(frm, title, fields, callback, evidence = false) {
    if (frm.is_dirty()) return frappe.msgprint(t("save"));
    if (evidence) fields.push({fieldname: "files", label: t("proof"), fieldtype: "Table", reqd: 1,
      description: t("proofHint"), fields: [{fieldname: "file", label: t("file"), fieldtype: "Link", options: "File", reqd: 1, in_list_view: 1}]});
    const dialog = new frappe.ui.Dialog({title, fields, primary_action_label: t("confirm"), primary_action(values) {
      if (evidence) values.evidence_files = (values.files || []).map(row => row.file);
      delete values.files;
      dialog.hide();
      callback(values);
    }});
    dialog.show();
  }

  const note = () => [{fieldname: "note", fieldtype: "Small Text", label: t("note"), reqd: 1}];
  const add = (frm, label, action) => frm.add_custom_button(t(label), action, t("workflow"));
  const change = (frm, status, label, needsNote = false, proof = false) => add(frm, label, () => {
    const perform = args => run(frm, "changes", "transition_change", {status, ...args});
    return needsNote || proof ? prompt(frm, t(label), note(), perform, proof) : perform({});
  });

  frappe.ui.form.on("URANOS Change Request", {refresh(frm) {
    if (frm.is_new()) return;
    const state = frm.doc.status;
    if (state === "Proposed" && roles("Project Manager", "Engineering Director", "Civil Director", "Electrical Execution Manager")) change(frm, "Impact Analysis", "analysis");
    if (["Proposed", "Impact Analysis"].includes(state) && finance()) add(frm, "assess", () => prompt(frm, t("assess"), [
      {fieldname: "cost_impact", fieldtype: "Currency", label: t("cost"), reqd: 1},
      {fieldname: "policy", fieldtype: "Link", options: "URANOS Approval Policy", label: t("policy"), reqd: 1,
        get_query: () => ({filters: {project: frm.doc.project, action: "Change Cost", status: "Approved", enabled: 1}})},
    ], args => run(frm, "changes", "assess_change_cost", args)));
    if (state === "Impact Analysis" && engineering()) change(frm, "Technical Approval", "technical");
    if (state === "Technical Approval" && finance()) change(frm, "Financial Approval", "finance", true);
    if (["Technical Approval", "Financial Approval"].includes(state) && (engineering() || finance())) change(frm, "Approved", "release");
    if (state === "Approved" && roles("Project Manager", "Civil Director", "Electrical Execution Manager", "Engineering Director")) change(frm, "Implemented", "implement", true);
    if (state === "Implemented" && engineering()) change(frm, "Verified", "verify", true, true);
    if (state === "Verified" && engineering()) change(frm, "Closed", "close");
    if (["Proposed", "Impact Analysis", "Technical Approval", "Financial Approval"].includes(state) && roles("Engineering Director", "Project Manager")) change(frm, "Rejected", "reject", true);
  }});

  frappe.ui.form.on("URANOS Approval Policy", {refresh(frm) {
    if (!frm.is_new() && frm.doc.action === "Change Cost" && frm.doc.status === "Draft" && finance())
      add(frm, "approvePolicy", () => run(frm, "changes", "approve_change_policy"));
  }});

  frappe.ui.form.on("URANOS Daily Site Report", {refresh(frm) {
    if (frm.is_new()) return;
    if (frm.doc.status === "Draft" && frm.doc.recorded_by === frappe.session.user && roles("Team Lead", "Site Controller", "Project Manager"))
      add(frm, "submit", () => run(frm, "reports", "submit_daily_report"));
    if (frm.doc.status === "Submitted" && frm.doc.submitted_by !== frappe.session.user && roles("Site Controller", "Project Manager"))
      add(frm, "approveReport", () => run(frm, "reports", "approve_daily_report"));
    for (const field of ["progress_summary", "stock_summary", "blockers_summary", "qa_hse_summary"]) frm.toggle_display(field, false);
    if (!frm.doc.snapshot_at || !frm.fields_dict.snapshot_preview) return;
    try {
      const progress = JSON.parse(frm.doc.progress_summary), stock = JSON.parse(frm.doc.stock_summary);
      const rows = progress.verified_installed || [];
      frm.fields_dict.snapshot_preview.$wrapper.html(`<section dir="${ar ? "rtl" : "ltr"}">
        <h4>${t("frozen")} · ${esc(frm.doc.snapshot_at)}</h4>
        <p>${t("installed")}: ${rows.length} · ${t("pending")}: ${(progress.pending_declarations || []).length} · ${t("moves")}: ${(stock.submitted_erp_movements || []).length}</p>
        <table class="table table-bordered"><thead><tr><th>${t("source")}</th><th>${t("activity")}</th><th>${t("qty")}</th></tr></thead>
        <tbody>${rows.map(row => `<tr><td>${esc(row.name)}</td><td>${esc(row.activity)} / ${esc(row.zone)}</td><td>${esc(row.qty_verified)} ${esc(row.uom)}</td></tr>`).join("")}</tbody></table></section>`);
    } catch { frm.fields_dict.snapshot_preview.$wrapper.text("A COMPLETER"); }
  }});

  frappe.ui.form.on("URANOS RFI", {refresh(frm) {
    if (frm.is_new()) return;
    if (frm.doc.status === "Open" && roles("Engineering Director", "Project Manager")) add(frm, "assign", () => prompt(frm, t("assign"), [
      {fieldname: "assignee", fieldtype: "Link", options: "User", label: t("user"), reqd: 1},
    ], args => run(frm, "reports", "assign_rfi", args)));
    if (frm.doc.status === "Assigned" && frm.doc.assignee === frappe.session.user) add(frm, "answer", () => prompt(frm, t("answer"), [
      {fieldname: "response", fieldtype: "Small Text", label: t("response"), reqd: 1},
    ], args => run(frm, "reports", "answer_rfi", args), true));
    if (frm.doc.status === "Answered" && frm.doc.answered_by !== frappe.session.user && (frm.doc.requester === frappe.session.user || roles("Engineering Director", "Project Manager")))
      add(frm, "close", () => run(frm, "reports", "close_rfi"));
  }});

  // ─── Phase 3: URANOS Blocker — Service Layer Dialogs ───────────────────────
  // All mutations are routed to uranos_project_os.services.blockers.* (Phase 2).
  // Client-side role checks are a UX courtesy only; server enforces all rules.
  // ───────────────────────────────────────────────────────────────────────────
  frappe.ui.form.on("URANOS Blocker", {refresh(frm) {
    if (frm.is_new()) return;
    const status = frm.doc.status;
    const user   = frappe.session.user;

    // ── 1. Open → In Progress ─────────────────────────────────────────────
    // Coordinators assign a responsible person. Justification is mandatory
    // because 'responsible' is a CRITICAL_FIELDS entry in domain/blockers.py.
    if (status === "Open" && coordinator()) {
      add(frm, "blkAssign", () => {
        if (frm.is_dirty()) return frappe.msgprint(t("save"));
        const d = new frappe.ui.Dialog({
          title: t("blkAssign"),
          fields: [
            {
              fieldname: "responsible",
              fieldtype: "Link",
              options:   "User",
              label:     t("user"),
              reqd:      1,
              get_query: () => ({filters: {enabled: 1}}),
            },
            {
              fieldname:   "justification",
              fieldtype:   "Small Text",
              label:       t("blkJustification"),
              description: ar
                ? "سبب تعيين هذا الشخص لحل العائق"
                : "Expliquez pourquoi cette personne est désignée pour résoudre le blocage.",
              reqd: 1,
            },
          ],
          primary_action_label: t("confirm"),
          primary_action(values) {
            d.hide();
            frappe.call({
              method: "uranos_project_os.services.blockers.assign_blocker",
              type:   "POST",
              args:   {name: frm.doc.name, responsible: values.responsible, justification: values.justification},
              freeze: true,
              callback: async () => {
                frappe.show_alert({message: __("Blocker assigned — now In Progress"), indicator: "blue"});
                await frm.reload_doc();
              },
            });
          },
        });
        d.show();
      });
    }

    // ── 2. In Progress → Pending Verification ────────────────────────────
    // Only the named responsible person can submit a resolution. The server
    // enforces this; the client-side check is a courtesy shortcut.
    if (status === "In Progress" && frm.doc.responsible === user) {
      add(frm, "blkSubmit", () => {
        if (frm.is_dirty()) return frappe.msgprint(t("save"));
        const d = new frappe.ui.Dialog({
          title: t("blkSubmit"),
          fields: [
            {
              fieldname:   "corrective_action",
              fieldtype:   "Small Text",
              label:       t("blkAction"),
              description: ar
                ? "صِف الإجراء التصحيحي المنفَّذ ميدانياً بالتفصيل."
                : "Décrivez précisément l'action corrective réalisée sur le terrain.",
              reqd: 1,
            },
          ],
          primary_action_label: t("confirm"),
          primary_action(values) {
            d.hide();
            frappe.call({
              method: "uranos_project_os.services.blockers.submit_resolution",
              type:   "POST",
              args:   {name: frm.doc.name, corrective_action: values.corrective_action},
              freeze: true,
              callback: async () => {
                frappe.show_alert({message: t("blkResolved"), indicator: "orange"});
                await frm.reload_doc();
              },
            });
          },
        });
        d.show();
      });
    }

    // ── 3. Pending Verification → Closed ─────────────────────────────────
    // Golden Rule: the resolver cannot be the closer. If the current user IS
    // the resolver we show an explanatory warning inside the dialog so that
    // the context is crystal-clear before the server rejects the action.
    if (status === "Pending Verification" && coordinator()) {
      add(frm, "blkClose", () => {
        if (frm.is_dirty()) return frappe.msgprint(t("save"));

        const selfVerify = frm.doc.resolved_by && frm.doc.resolved_by === user;
        const goldenRuleField = selfVerify
          ? [{
              fieldname: "_golden_rule_warning",
              fieldtype: "HTML",
              options:   `<div class="alert alert-warning" role="alert" style="border-left:4px solid #e67e22;padding:10px 14px;border-radius:4px;margin-bottom:12px;">
                            <strong>${ar ? "⚠️ تحذير" : "⚠️ Attention"}</strong><br>
                            ${esc(t("blkGoldenRule"))}
                          </div>`,
            }]
          : [];

        const d = new frappe.ui.Dialog({
          title: t("blkClose"),
          fields: [
            ...goldenRuleField,
            {
              fieldname:   "review_reason",
              fieldtype:   "Small Text",
              label:       t("blkReviewReason"),
              description: ar
                ? "ملاحظة التحقق الميداني (اختياري)"
                : "Note de vérification sur le terrain (optionnel).",
              reqd: 0,
            },
          ],
          primary_action_label: t("confirm"),
          primary_action(values) {
            d.hide();
            frappe.call({
              method: "uranos_project_os.services.blockers.close_blocker",
              type:   "POST",
              args:   {name: frm.doc.name, review_reason: values.review_reason || ""},
              freeze: true,
              callback: async () => {
                frappe.show_alert({message: t("blkClosed"), indicator: "green"});
                await frm.reload_doc();
              },
            });
          },
        });
        d.show();
      });
    }

    // ── 4. Reopen for Rework (Pending Verification or Closed → In Progress) ─
    // A coordinator can reject a resolution and send it back. A mandatory
    // reason is required by the domain to maintain the audit trail.
    if (["Pending Verification", "Closed"].includes(status) && coordinator()) {
      add(frm, "blkReopen", () => {
        if (frm.is_dirty()) return frappe.msgprint(t("save"));
        const d = new frappe.ui.Dialog({
          title: t("blkReopen"),
          fields: [
            {
              fieldname:   "reason",
              fieldtype:   "Small Text",
              label:       t("blkReason"),
              description: ar
                ? "وضّح سبب رفض الحل وما الذي يجب تصحيحه."
                : "Expliquez pourquoi la résolution est rejetée et ce qui doit être corrigé.",
              reqd: 1,
            },
          ],
          primary_action_label: t("confirm"),
          primary_action(values) {
            d.hide();
            frappe.call({
              method: "uranos_project_os.services.blockers.reopen_blocker",
              type:   "POST",
              args:   {name: frm.doc.name, reason: values.reason},
              freeze: true,
              callback: async () => {
                frappe.show_alert({message: t("blkReopened"), indicator: "blue"});
                await frm.reload_doc();
              },
            });
          },
        });
        d.show();
      });
    }

    // ── 5. Severity Review (Open or In Progress) ──────────────────────────
    // Retained: still routes to services.reports for the controlled severity
    // change (separate audit path from lifecycle transitions).
    if (["Open", "In Progress"].includes(status) && coordinator()) {
      add(frm, "review", () => prompt(frm, t("review"), [
        {fieldname: "severity", fieldtype: "Select", options: ["Low", "Medium", "High", "Critical"], label: t("severity"), reqd: 1},
        {fieldname: "reason",   fieldtype: "Small Text", label: t("note"), reqd: 1},
      ], args => run(frm, "reports", "review_blocker_severity", args)));
    }
  }});
})();
