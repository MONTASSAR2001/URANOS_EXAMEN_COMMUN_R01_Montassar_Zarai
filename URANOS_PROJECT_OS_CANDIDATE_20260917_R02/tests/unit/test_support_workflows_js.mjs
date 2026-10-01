// Node boundary smoke test only; not browser/Frappe integration evidence.
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";
const handlers = {}, calls = [];
const frappe = {boot: {lang: "ar"}, user_roles: ["URANOS Site Controller"], session: {user: "reviewer"},
  utils: {escape_html: value => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;")},
  ui: {form: {on: (doctype, handler) => { handlers[doctype] = handler; }}, Dialog: class {}},
  call: options => calls.push(options), msgprint() {},
};
const script = fs.readFileSync("apps/uranos_project_os/uranos_project_os/public/js/workflows.js", "utf8");
vm.runInNewContext(script, {frappe, window: {}});
assert.equal(Object.keys(handlers).length, 5);
const buttons = [];
const frm = {doc: {name: "REPORT", status: "Submitted", submitted_by: "author"},
  is_new: () => false, is_dirty: () => false, add_custom_button: (label, callback) => buttons.push({label, callback}),
  toggle_display() {}, reload_doc() {}, fields_dict: {},
};
handlers["URANOS Daily Site Report"].refresh(frm);
assert.equal(buttons.length, 1);
assert.match(buttons[0].label, /التقرير/);
buttons[0].callback();
assert.equal(calls[0].type, "POST");
assert.equal(calls[0].method, "uranos_project_os.services.reports.approve_daily_report");
assert.deepEqual(JSON.parse(JSON.stringify(calls[0].args)), {name: "REPORT"});
console.log("5 Desk registrations; Arabic reviewer action; narrow POST payload: PASS (Node stub, not browser)");
