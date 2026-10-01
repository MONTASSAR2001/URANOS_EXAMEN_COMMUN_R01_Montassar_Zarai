# URANOS Project OS

Frappe/ERPNext **version 16** custom application. Install only into an isolated,
supported Linux bench with ERPNext already installed. The repository root is the
engineering repository; this subdirectory is the installable Frappe app.

```sh
bench get-app /absolute/path/to/repository/apps/uranos_project_os
bench --site staging.example.local install-app uranos_project_os
bench --site staging.example.local migrate
bench --site staging.example.local run-tests --app uranos_project_os
```

No production people, passwords, thresholds, BOM quantities or business authority
are created at installation. Assign explicit Project User Permissions and the
minimum URANOS roles before use. For this sanitized evaluation snapshot, see
`README_CANDIDAT.md` at the snapshot root. Installation and native Frappe tests
are not yet validated on a real bench; the portable exercise needs no ERP site.
