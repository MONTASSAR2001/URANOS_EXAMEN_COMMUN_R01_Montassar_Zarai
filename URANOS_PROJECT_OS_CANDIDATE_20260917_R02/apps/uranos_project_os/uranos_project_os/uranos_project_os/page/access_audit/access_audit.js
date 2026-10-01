/**
 * access_audit.js — URANOS Security & Access Audit Page Controller
 */

/* global frappe, $ */

frappe.pages["access-audit"].on_page_load = function (wrapper) {
  "use strict";

  if (window.canAccessSecurityAudit && !window.canAccessSecurityAudit()) {
    if (typeof frappe.show_not_permitted === "function") {
      frappe.show_not_permitted("access-audit");
    }
    return;
  }

  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("Security & Access Audit"),
    single_column: true
  });

  var $container = $(page.main);
  $container.addClass("uranos-access-audit-page-root");

  if (window.renderSecurityAccessAuditDashboard) {
    window.renderSecurityAccessAuditDashboard($container);
  } else {
    // Wait for desk_theme.js to be fully available
    var attempts = 0;
    var interval = setInterval(function () {
      attempts++;
      if (window.renderSecurityAccessAuditDashboard) {
        clearInterval(interval);
        window.renderSecurityAccessAuditDashboard($container);
      } else if (attempts > 20) {
        clearInterval(interval);
      }
    }, 100);
  }
};
