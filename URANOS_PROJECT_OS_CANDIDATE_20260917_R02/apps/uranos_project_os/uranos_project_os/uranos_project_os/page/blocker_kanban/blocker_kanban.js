/**
 * blocker_kanban.js — URANOS Blocker Kanban Board Page Controller
 */

/* global frappe, $ */

frappe.pages["blocker-kanban"].on_page_load = function (wrapper) {
  "use strict";

  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __("URANOS — Kanban Board"),
    single_column: true
  });

  var $container = $(page.main);
  $container.addClass("uranos-blocker-kanban-root");

  function mountKanban() {
    if (window.renderBlockerKanbanDashboard) {
      window.renderBlockerKanbanDashboard($container, true);
    }
  }

  mountKanban();

  // If desk_theme.js hasn't loaded yet, retry smoothly once
  if (!window.renderBlockerKanbanDashboard) {
    var checkCount = 0;
    var timer = setInterval(function () {
      checkCount++;
      if (window.renderBlockerKanbanDashboard) {
        clearInterval(timer);
        mountKanban();
      } else if (checkCount > 20) {
        clearInterval(timer);
      }
    }, 150);
  }
};

frappe.pages["blocker-kanban"].on_page_show = function (wrapper) {
  "use strict";
  if (window.renderBlockerKanbanDashboard) {
    var $container = $(wrapper).find(".uranos-blocker-kanban-root, .layout-main-section").first();
    if (!$container.length) $container = $(wrapper);
    window.renderBlockerKanbanDashboard($container, false);
  }
};
