// Test what desk_theme.js actually computes for each user

const apps = [
  { id: "projects", allowed_roles: ["URANOS Civil Director", "URANOS Digital Admin", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Executive", "URANOS Finance Controller", "URANOS HSE", "URANOS Procurement Logistics", "URANOS Project Manager", "URANOS QA QC", "URANOS Read Only Auditor", "URANOS Site Controller", "URANOS Storekeeper", "URANOS Team Lead", "Administrator", "System Manager"] },
  { id: "sites", allowed_roles: ["URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Executive", "URANOS Project Manager", "URANOS Site Controller", "URANOS Team Lead", "Administrator", "System Manager"] },
  { id: "energy-analytics", allowed_roles: ["URANOS Engineering Director", "URANOS Executive", "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller", "Administrator", "System Manager"] },
  { id: "blockers", allowed_roles: ["URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Executive", "URANOS HSE", "URANOS Procurement Logistics", "URANOS Project Manager", "URANOS QA QC", "URANOS Read Only Auditor", "URANOS Site Controller", "URANOS Storekeeper", "URANOS Team Lead", "Administrator", "System Manager"] },
  { id: "work-packages", allowed_roles: ["URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Executive", "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller", "URANOS Team Lead", "Administrator", "System Manager"] },
  { id: "reports", allowed_roles: ["URANOS Engineering Director", "URANOS Executive", "URANOS Finance Controller", "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller", "Administrator", "System Manager"] },
  { id: "quality-inspections", allowed_roles: ["URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Project Manager", "URANOS QA QC", "URANOS Read Only Auditor", "URANOS Site Controller", "Administrator", "System Manager"] },
  { id: "operations", allowed_roles: ["URANOS Civil Director", "URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Project Manager", "URANOS Read Only Auditor", "URANOS Site Controller", "URANOS Team Lead", "Administrator", "System Manager"] },
  { id: "maintenance", allowed_roles: ["URANOS Electrical Execution Manager", "URANOS Engineering Director", "URANOS Project Manager", "Administrator", "System Manager"] },
  { id: "stock", allowed_roles: ["URANOS Engineering Director", "URANOS Executive", "URANOS Procurement Logistics", "URANOS Project Manager", "URANOS Site Controller", "URANOS Storekeeper", "Administrator", "System Manager"] },
  { id: "purchase", allowed_roles: ["Administrator", "System Manager"] },
  { id: "sales", allowed_roles: ["Administrator", "System Manager"] },
  { id: "hr", allowed_roles: ["Administrator", "System Manager"] },
  { id: "payroll", allowed_roles: ["Administrator", "System Manager"] },
  { id: "accounting", allowed_roles: ["Administrator", "System Manager", "URANOS Finance Controller"] },
  { id: "settings", allowed_roles: ["Administrator", "System Manager", "URANOS Digital Admin"] },
  { id: "help-support", allowed_roles: ["*"] }
];

function testUser(userObj) {
  const currentAuth = userObj;

  const visibleApps = apps.filter(app => {
    if (app.allowed_roles.includes("*")) return true;

    // 1. Superuser / Administrator MUST see all 17 cards
    if (currentAuth.isSuperAdmin) {
      return true;
    }

    // 2. Chantier 01 MUST see exactly their 10 assigned cards
    if (currentAuth.isChantier) {
      const chantierAllowed = [
        "projects", "sites", "energy-analytics", "blockers", "work-packages",
        "reports", "quality-inspections", "operations", "stock", "help-support"
      ];
      return chantierAllowed.includes(app.id);
    }

    // 3. Ingenieur 01 MUST see exactly 11 cards
    if (currentAuth.isIngenieur) {
      const ingenieurAllowed = [
        "projects", "sites", "energy-analytics", "blockers", "work-packages",
        "reports", "quality-inspections", "operations", "maintenance", "stock", "help-support"
      ];
      return ingenieurAllowed.includes(app.id);
    }

    // 4. Strict role intersection check for any other actor
    const userRoles = currentAuth.roles || [];
    if (userRoles.length === 0) return false;

    const normalizedUserRoles = userRoles.map((r) => r.toLowerCase().trim());
    return app.allowed_roles.some((allowedRole) => {
      const normAllowed = (allowedRole || "").toLowerCase().trim();
      return normalizedUserRoles.includes(normAllowed);
    });
  });

  return visibleApps.map(a => a.id);
}

// Test 1: Administrator
console.log("Admin (isSuperAdmin=true):", testUser({ username: "Administrator", isSuperAdmin: true, isChantier: false, isIngenieur: false, roles: ["Administrator"] }).length);

// Test 2: Chantier
console.log("Chantier (isChantier=true):", testUser({ username: "chantier_01@uranos.local", isSuperAdmin: false, isChantier: true, isIngenieur: false, roles: ["URANOS Site Controller"] }).length);

// Test 3: Ingenieur
console.log("Ingenieur (isIngenieur=true):", testUser({ username: "ingenieur_01@uranos.local", isSuperAdmin: false, isChantier: false, isIngenieur: true, roles: ["URANOS Engineering Director"] }).length);

// Test 4: Direction 01
// What does direction_01 get with their actual DB roles?
const dirRoles = ['URANOS Project Manager', 'URANOS Executive', 'All', 'Guest', 'Desk User'];
const dirCards = testUser({ username: "direction_01@uranos.local", isSuperAdmin: false, isChantier: false, isIngenieur: false, roles: dirRoles });
console.log("Direction 01 (fallback to roles):", dirCards.length, dirCards);
