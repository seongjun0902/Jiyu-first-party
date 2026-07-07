const CACHE_NAME = 'jiyu-party-v2';
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
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  // 실시간 데이터 / 지도: 항상 네트워크 우선
  const networkFirst = ['firebaseio.com', 'maps.google.com'];
  if (networkFirst.some(domain => url.hostname.includes(domain))) {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    return;
  }

  // 폰트 파일 / Cloudinary 이미지: URL이 불변이므로 캐시 우선 (재방문 시 네트워크 요청 없음)
  const cacheFirst = ['fonts.gstatic.com', 'res.cloudinary.com'];
  if (cacheFirst.some(domain => url.hostname.includes(domain))) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          if (response && (response.status === 200 || response.type === 'opaque')) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // 폰트 CSS: 캐시 즉시 응답 + 백그라운드 갱신 (stale-while-revalidate)
  if (url.hostname.includes('fonts.googleapis.com')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        const fetched = fetch(event.request).then(response => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        }).catch(() => cached);
        return cached || fetched;
      })
    );
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
