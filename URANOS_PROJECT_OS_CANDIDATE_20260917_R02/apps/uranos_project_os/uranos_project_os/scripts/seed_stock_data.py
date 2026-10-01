import frappe

def seed_stock():
    print("--- SEEDING STOCK DATA ---")

    company_name = "URANOS Group"

    # 1. Warehouses
    warehouses = [
        {"name": "Main Solar Depot", "state": "AVAILABLE", "project": "PV-01"},
        {"name": "Substation Spares Store", "state": "QUARANTINE", "project": "PV-01"},
        {"name": "Field Buffer Warehouse", "state": "RESERVED", "project": "PV-01"},
        {"name": "Central Logistics Hub", "state": "AVAILABLE", "project": "PV-01"}
    ]

    for wh in warehouses:
        wh_name = f"{wh['name']} - UG"
        if not frappe.db.exists("Warehouse", wh_name) and not frappe.db.exists("Warehouse", wh['name']):
            try:
                doc = frappe.get_doc({
                    "doctype": "Warehouse",
                    "warehouse_name": wh['name'],
                    "company": company_name,
                    "uranos_stock_state": wh['state'],
                    "uranos_project": wh['project']
                })
                doc.insert(ignore_permissions=True, ignore_mandatory=True)
                print(f"Created Warehouse: {doc.name}")
            except Exception as e:
                print(f"Error creating warehouse {wh['name']}: {e}")
                # Fallback to direct insertion if ERPNext hooks complain
                frappe.db.sql("""
                    INSERT INTO `tabWarehouse` (name, warehouse_name, company, uranos_stock_state, uranos_project, creation, modified, modified_by, owner)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                """, (wh_name, wh['name'], company_name, wh['state'], wh['project']))
                print(f"Fallback inserted Warehouse: {wh_name}")
        else:
            print(f"Warehouse {wh['name']} already exists.")

    # 2. Items
    items = [
        {
            "item_code": "SOLAR-PANEL-500W",
            "item_name": "Bifacial Monocrystalline Solar Panel 500W",
            "item_group": "Products",
            "stock_uom": "Unit",
            "valuation_rate": 185.0,
            "standard_rate": 220.0,
            "uranos_risk_class": "Class A - Critical PV",
            "description": "High-efficiency Tier 1 bifacial monocrystalline PV module with anti-reflective glass."
        },
        {
            "item_code": "CABLE-COPPER-50MM",
            "item_name": "Single Core Copper Solar Cable 50mm²",
            "item_group": "Raw Material",
            "stock_uom": "Meter",
            "valuation_rate": 14.5,
            "standard_rate": 18.0,
            "uranos_risk_class": "Class B - MV Infrastructure",
            "uranos_reel_tracking": 1,
            "description": "Double insulated halogen-free cross-linked polyethylene cable for solar DC array string connections."
        },
        {
            "item_code": "INVERTER-STRING-100KW",
            "item_name": "Three-Phase String Inverter 100kW (1500V DC)",
            "item_group": "Products",
            "stock_uom": "Unit",
            "valuation_rate": 4200.0,
            "standard_rate": 5100.0,
            "uranos_risk_class": "Class A - Critical Power",
            "description": "High performance 1500V DC multi-MPPT grid-tied utility scale string inverter."
        },
        {
            "item_code": "TRANSFORMER-OIL-DRUM",
            "item_name": "Dielectric Mineral Transformer Oil (200L Drum)",
            "item_group": "Consumable",
            "stock_uom": "Unit",
            "valuation_rate": 320.0,
            "standard_rate": 410.0,
            "uranos_risk_class": "Class C - Standard Consumable",
            "description": "Inhibited naphthenic mineral insulating oil for MV/HV oil-immersed substation transformers."
        }
    ]

    for itm in items:
        if not frappe.db.exists("Item", itm['item_code']):
            try:
                doc = frappe.get_doc({
                    "doctype": "Item",
                    "is_stock_item": 1,
                    **itm
                })
                doc.insert(ignore_permissions=True, ignore_mandatory=True)
                print(f"Created Item: {doc.item_code} - {doc.item_name}")
            except Exception as e:
                print(f"Error creating item {itm['item_code']}: {e}")
                frappe.db.sql("""
                    INSERT INTO `tabItem` (name, item_code, item_name, item_group, stock_uom, valuation_rate, standard_rate, is_stock_item, uranos_risk_class, description, creation, modified, modified_by, owner)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                """, (itm['item_code'], itm['item_code'], itm['item_name'], itm['item_group'], itm['stock_uom'], itm['valuation_rate'], itm['standard_rate'], itm['uranos_risk_class'], itm['description']))
                print(f"Fallback inserted Item: {itm['item_code']}")
        else:
            print(f"Item {itm['item_code']} already exists.")

    frappe.db.commit()
    print("--- STOCK SEEDING COMPLETED SUCCESSFULLY ---")
