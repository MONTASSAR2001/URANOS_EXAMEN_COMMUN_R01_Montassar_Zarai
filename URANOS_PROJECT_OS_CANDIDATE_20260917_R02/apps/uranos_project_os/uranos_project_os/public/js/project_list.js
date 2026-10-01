frappe.provide("frappe.listview_settings");

frappe.listview_settings["Project"] = {
  add_fields: [
    "status",
    "priority",
    "is_active",
    "percent_complete",
    "expected_end_date",
    "project_name",
    "custom_assigned_engineer",
    "custom_assigned_site_team"
  ],
  filters: [],
  get_indicator: function (doc) {
    if (doc.status === "Open" && doc.percent_complete) {
      return [__("{0}%", [cint(doc.percent_complete)]), "orange", "percent_complete,>,0|status,=,Open"];
    } else if (doc.status === "Completed") {
      return [__("Completed"), "green", "status,=,Completed"];
    } else if (doc.status === "On hold") {
      return [__("On hold"), "blue", "status,=,On hold"];
    } else {
      return [__(doc.status), frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
    }
  },
  onload: function (listview) {
    if (listview && listview.filter_area) {
      const filters = listview.filter_area.get();
      if (filters && filters.length > 0) {
        listview.filter_area.clear(false);
        listview.refresh();
      }
    }
  }
};
