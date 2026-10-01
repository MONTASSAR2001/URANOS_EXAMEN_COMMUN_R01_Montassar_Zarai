/* Deliberately asset-scoped. Never cache API responses, /uranos, private files,
 * authenticated HTML, errors or any request outside this exact allowlist. */
const CACHE = "uranos-field-static-v3";
const ROOT = "/assets/uranos_project_os/field/";
const FILES = ["offline.html", "app.css", "app.js", "i18n.js", "queue.js", "manifest.webmanifest", "app-icon.svg"].map(name => ROOT + name);
self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => Promise.all(FILES.map(async path => {
  const response = await fetch(path, {credentials: "omit", cache: "no-store", redirect: "error"});
  if (!response.ok || response.redirected || new URL(response.url).pathname !== path) throw new Error("Static shell unavailable");
  await cache.put(path, response);
})))));
self.addEventListener("activate", event => event.waitUntil(Promise.all([caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith("uranos-field-static-") && key !== CACHE).map(key => caches.delete(key)))), self.clients.claim()])));
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || url.search || !FILES.includes(url.pathname)) return;
  event.respondWith(caches.open(CACHE).then(async cache => {
    const stored = await cache.match(event.request);
    if (stored) return stored;
    const response = await fetch(event.request);
    if (response.ok && !response.redirected && response.type === "basic") await cache.put(event.request, response.clone());
    return response;
  }));
});
