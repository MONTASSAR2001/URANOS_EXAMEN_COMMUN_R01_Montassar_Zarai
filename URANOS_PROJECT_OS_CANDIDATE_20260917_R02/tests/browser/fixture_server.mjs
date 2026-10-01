/** Synthetic HTTP transport fixture ONLY. This is not ERPNext, does not prove
 * permissions/migrations/stock behavior and must never be used as a product. */
import http from "node:http";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../apps/uranos_project_os/uranos_project_os");
const assets = ["offline.html","app.js","app.css","queue.js","i18n.js","sw.js","manifest.webmanifest","app-icon.svg"];
const mime = {".js":"text/javascript; charset=utf-8",".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".webmanifest":"application/manifest+json",".svg":"image/svg+xml"};
export async function createFixtureServer() {
  const state = {user:"controller-a@example.invalid",roles:["Executive","Site Controller","Team Lead","Storekeeper","Procurement Logistics","QA QC"],allowedProjects:["DEMO-PV-A","DEMO-PV-B","DEMO-PV-C"],mode:"ok",receipts:new Map(),requests:[],submits:[],verified:[],keyUnavailable:false};
  const projects = [{name:"DEMO-PV-A",project_name:"Médenine · Démo 1 MW"},{name:"DEMO-PV-B",project_name:"Djerba · Démo 1 MW"},{name:"DEMO-PV-C",project_name:"Zarzis · Démo 1 MW"}];
  const server = http.createServer(async (request,response) => {
    const url = new URL(request.url,"http://fixture.invalid");
    const json = (message,status = 200) => {response.writeHead(status,{"Content-Type":"application/json","Cache-Control":"no-store, private"});response.end(JSON.stringify(status === 200 ? {message} : message));};
    try {
      if (url.pathname.startsWith("/api/method/")) {
        let body = ""; for await (const chunk of request) body += chunk;
        const params = request.method === "POST" ? JSON.parse(body || "{}") : Object.fromEntries(url.searchParams);
        const method = url.pathname.split("services.")[1];
        state.requests.push({method,verb:request.method,actor:request.headers["x-uranos-user"]});
        if (!state.user) return json({exc_type:"AuthenticationError"},401);
        if (request.method === "POST" && (request.headers["x-uranos-user"] !== state.user || request.headers["x-frappe-csrf-token"] !== "synthetic-csrf")) return json({exc_type:"PermissionError"},403);
        if (method === "api.bootstrap") return json({user:state.user,language:"fr",roles:state.roles.map(role => `URANOS ${role}`),projects:projects.filter(project => state.allowedProjects.includes(project.name)),finance_allowed:false,csrf_token:"synthetic-csrf",server_time:"2026-09-17 12:00:00",environment:"synthetic-browser-fixture"});
        if (method === "offline.encryption_key") {
          if (state.keyUnavailable) return json({exc_type:"Unavailable"},503);
          return json({key_base64:Buffer.alloc(32,state.user === "controller-a@example.invalid" ? 1 : 2).toString("base64")});
        }
        if (method === "api.project_context") return json({project:params.project,work_packages:[{name:`${params.project}-WP030`,code:"WP-030",title:"Battage et forage",uom:"pieux",baseline_version:"BASELINE-DEMO-V1",status:"In Progress",modified:"2026-09-16 10:00:00",qty_planned:1000},{name:`${params.project}-WP050`,code:"WP-050",title:"Pose des modules",uom:"modules",baseline_version:"BASELINE-DEMO-V1",status:"In Progress",modified:"2026-09-16 10:00:00",qty_planned:2000}],kit_templates:[{name:`${params.project}-KIT`,kit_code:"KIT-DEMO",kit_version:"1",activity:"STRUCTURE",status:"Approved"}],warehouses:[{name:`${params.project}-Available`,warehouse_name:"Disponible"},{name:`${params.project}-WIP`,warehouse_name:"Travaux en cours"}],kit_issues:[{name:`${params.project}-ISSUE-1`,work_package:`${params.project}-WP030`,activity:"BATTAGE",zone:"Z01",crew:"TEAM-DEMO",status:"Issued"},{name:`${params.project}-ISSUE-2`,work_package:`${params.project}-WP050`,activity:"MODULES",zone:"Z02",crew:"TEAM-DEMO",status:"Issued"}],cable_reels:[{name:`${params.project}-REEL-1`,reel_id:"REEL-DEMO-001",item_code:"CABLE-DEMO",status:"Available"}]});
        if (method === "api.dashboard") return json({project:params.project,physical_progress:params.project === "DEMO-PV-C" ? null : 35,planned_progress:params.project === "DEMO-PV-C" ? null : 49,material_readiness:params.project === "DEMO-PV-C" ? null : 80,status:params.project === "DEMO-PV-C" ? "Unknown" : "Red",as_of:"2026-09-17 12:00:00",work_packages:[{work_package:`${params.project}-WP030`,qty_planned:1000,qty_reported:600,qty_verified:400,completion_percent:40},{work_package:`${params.project}-WP050`,qty_planned:2000,qty_reported:900,qty_verified:600,completion_percent:30}],blockers:[{name:"BLOCK-DEMO-1",title:"Câble AC attendu · fenêtre de pose à revoir",severity:"Critical",status:"Open"}],ncrs:[{name:"NCR-DEMO-1",defect:"Contrôle de serrage à reprendre",severity:"High",status:"Open"}],alerts:[],shipments:[{name:"SHIP-DEMO-1",status:"In Transit",eta_initial:"2026-09-20",eta_revised:"2026-09-27",need_by:"2026-09-23",criticality:"Critical"}]});
        if (method === "api.pending_verifications") return json([{name:"PROGRESS-DEMO-1",work_package:`${params.project}-WP030`,activity:"BATTAGE",zone:"Z01",crew:"Équipe DEMO",qty_reported:12,reported_by:"team-a@example.invalid",posting_date:"2026-09-17",status:"Pending Verification"},{name:"PROGRESS-SELF",work_package:`${params.project}-WP030`,activity:"BATTAGE",zone:"Z02",crew:"Équipe DEMO",qty_reported:2,reported_by:state.user,posting_date:"2026-09-17",status:"Pending Verification"}]);
        if (method === "offline.synchronize") {
          const envelope = JSON.parse(params.envelope);
          if (!state.allowedProjects.includes(envelope.project)) return json({exc_type:"PermissionError"},403);
          if (state.mode === "conflict") return json({exc_type:"OfflineConflict"},409);
          if (state.mode === "reject") return json({exc_type:"OfflineValidationError"},422);
          const id = `${state.user}:${envelope.uuid}`;
          const prior = state.receipts.get(id);
          if (prior && JSON.stringify(prior.envelope) !== JSON.stringify(envelope)) return json({exc_type:"OfflineConflict"},409);
          const doctype = {progress:"URANOS Field Progress Entry",daily_report:"URANOS Daily Site Report",kit_request:"URANOS Kit Issue",kit_return:"URANOS Kit Return",inspection:"URANOS Field Inspection"}[envelope.operation];
          const result = {uuid:envelope.uuid,status:"synced",docstatus:0,doctype,name:`DRAFT-${state.receipts.size + (prior ? 0 : 1)}`,duplicate:!!prior};
          if (prior) result.name = prior.result.name;
          else state.receipts.set(id,{envelope,result});
          if (state.mode === "lost-response") {state.mode = "ok"; return json({exc_type:"GatewayError"},502);}
          return json(result);
        }
        if (method === "operations.submit_progress") {state.submits.push(params.name);return json({status:"Pending Verification",name:params.name});}
        if (method === "operations.verify_progress") {state.verified.push(params);return json({status:"Verified",name:params.name});}
        return json({exc_type:"UnknownFixtureMethod"},404);
      }
      let filename;
      if (url.pathname === "/uranos") filename = path.join(root,"www/uranos.html");
      else if (url.pathname.startsWith("/assets/uranos_project_os/field/") && assets.includes(url.pathname.split("/").at(-1))) filename = path.join(root,"public/field",url.pathname.split("/").at(-1));
      else {response.writeHead(404);return response.end("Synthetic fixture: route not implemented");}
      let content = await readFile(filename);
      if (url.pathname === "/uranos") content = content.toString().replace("{{ csrf_token | e }}","synthetic-csrf");
      response.writeHead(200,{"Content-Type":mime[path.extname(filename)] || "application/octet-stream",...(url.pathname === "/uranos" ? {"Cache-Control":"no-store, private"} : {})});response.end(content);
    } catch (error) {json({exc_type:"FixtureError",message:error.message},500);}
  });
  await new Promise(resolve => server.listen(0,"127.0.0.1",resolve));
  return {url:`http://127.0.0.1:${server.address().port}`,state,close:() => new Promise(resolve => server.close(resolve))};
}
