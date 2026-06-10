const CACHE_NAME = 'jiyu-party-v1';
const STATIC_ASSETS = [
  '/Jiyu-first-party/',
  '/Jiyu-first-party/index.html',
  '/Jiyu-first-party/style.css',
  '/Jiyu-first-party/manifest.json',
  '/Jiyu-first-party/icons/icon-192.png',
  '/Jiyu-first-party/icons/icon-512.png'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const networkFirst = ['firebaseio.com','cloudinary.com','fonts.googleapis.com','fonts.gstatic.com','maps.google.com'];
  if (networkFirst.some(domain => url.hostname.includes(domain))) {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    return;
  }
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response && response.status === 200 && response.type !== 'opaque') {
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, response.clone()));
        }
        return response;
      });
    })
  );
});
