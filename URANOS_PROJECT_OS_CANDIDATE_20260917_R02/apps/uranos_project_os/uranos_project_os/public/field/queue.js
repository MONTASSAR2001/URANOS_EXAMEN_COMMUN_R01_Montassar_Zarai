/* Only draft envelopes live here. ERPNext remains authoritative. A queue can
 * only be opened after a fresh authenticated bootstrap for its owner. */
const STORE = "drafts";
const encoder = new TextEncoder();

export async function sha256(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))].map(x => x.toString(16).padStart(2, "0")).join("");
}

export async function openQueue(user, keyBase64, site = location.origin) {
  if (!user || user === "Guest") throw new Error("Authentication required");
  const scope = await sha256(encoder.encode(`${site}\0${user}`));
  const rawKey = Uint8Array.from(atob(keyBase64), value => value.charCodeAt(0));
  const key = await crypto.subtle.importKey("raw", rawKey, {name: "AES-GCM"}, false, ["encrypt", "decrypt"]);
  rawKey.fill(0);
  keyBase64 = null;
  const seal = async row => {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await crypto.subtle.encrypt({name: "AES-GCM", iv, additionalData: encoder.encode(scope + row.uuid)}, key, encoder.encode(JSON.stringify(row)));
    return {uuid: row.uuid, iv, ciphertext};
  };
  const unseal = async row => {
    if (!row) return undefined;
    const plaintext = await crypto.subtle.decrypt({name: "AES-GCM", iv: row.iv, additionalData: encoder.encode(scope + row.uuid)}, key, row.ciphertext);
    return JSON.parse(new TextDecoder().decode(plaintext));
  };
  const db = await new Promise((resolve, reject) => {
    const request = indexedDB.open(`uranos-field-v1-${scope}`, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, {keyPath: "uuid"});
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error("Local database is locked"));
  });
  const transaction = (mode, callback) => new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, mode);
    let result;
    const request = callback(tx.objectStore(STORE));
    request.onsuccess = () => { result = request.result; };
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error || new Error("Local write aborted"));
  });
  return {
    user, scope,
    all: async () => (await Promise.all((await transaction("readonly", store => store.getAll())).map(unseal))).sort((a, b) => b.created.localeCompare(a.created)),
    get: async uuid => unseal(await transaction("readonly", store => store.get(uuid))),
    // `add` fails on collision; no edit can silently replace an existing UUID.
    add: async row => { const encrypted = await seal(row); return transaction("readwrite", store => store.add(encrypted)); },
    update: async row => { const encrypted = await seal(row); return transaction("readwrite", store => store.put(encrypted)); },
    close: () => db.close(),
  };
}

export function newDraft(project, operation, payload, attachments = [], baseModified = null) {
  return {uuid: crypto.randomUUID(), operation, project, payload: structuredClone(payload), attachments,
    base_modified: baseModified};
}

export function errorState(error) {
  if (error.name === "AbortError" || error instanceof TypeError || error.status >= 500 && error.type !== "OfflineConflict" && error.type !== "OfflineValidationError") return "queued";
  if (error.type === "OfflineConflict" || error.status === 409) return "conflict";
  return "rejected";
}

export async function synchronizeDraft(queue, row, api, assertIdentity) {
  if (!row || row.state === "synced") return row;
  await assertIdentity(); // Must happen before changing or transmitting any row.
  row = {...row, state: "syncing", error: null, attempts: (row.attempts || 0) + 1};
  await queue.update(row);
  try {
    const response = await api("offline.synchronize", {envelope: JSON.stringify(row.envelope)}, "POST");
    if (response.status !== "synced" || response.uuid !== row.uuid || response.docstatus !== 0) {
      const error = new Error("Unexpected synchronization response");
      error.type = "OfflineValidationError";
      throw error;
    }
    row = {...row, state: "synced", result: response, syncedAt: new Date().toISOString(), error: null};
  } catch (error) {
    row = {...row, state: errorState(error), error: error.type || error.message || "Sync failed"};
  }
  await queue.update(row);
  return row;
}

export async function imageEvidence(files) {
  if (files.length > 5) throw new Error("evidenceLimit");
  const attachments = [];
  let total = 0;
  for (const file of files) {
    if (!["image/png", "image/jpeg"].includes(file.type) || file.size > 5 * 1024 * 1024) throw new Error("evidenceLimit");
    const bytes = new Uint8Array(await file.arrayBuffer());
    const isPNG = bytes.length >= 8 && [137,80,78,71,13,10,26,10].every((value, i) => bytes[i] === value);
    const isJPEG = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
    if (!(file.type === "image/png" ? isPNG : isJPEG)) throw new Error("evidenceInvalid");
    const digest = await sha256(bytes);
    if (attachments.some(item => item.sha256 === digest)) throw new Error("evidenceDuplicate");
    total += bytes.length;
    if (total > 15 * 1024 * 1024) throw new Error("evidenceLimit");
    let binary = "";
    for (let index = 0; index < bytes.length; index += 32768) binary += String.fromCharCode(...bytes.subarray(index, index + 32768));
    attachments.push({filename: file.name.replace(/[\\/:\x00]/g, "_").slice(0, 120), mime_type: file.type, sha256: digest, content_base64: btoa(binary)});
  }
  return attachments;
}
