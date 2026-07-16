/* 球星风采 / 媒体资源：缓存优先，二次打开更顺 */
const CACHE_NAME = 'wc-media-v3';
const MEDIA_RE = /\/media\/(moments|journeys|reels)\//;

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k.startsWith('wc-media-') && k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;
  if (!MEDIA_RE.test(url.pathname)) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const hit = await cache.match(event.request);
      if (hit) return hit;
      try {
        const res = await fetch(event.request);
        if (res && res.ok) {
          cache.put(event.request, res.clone());
        }
        return res;
      } catch (err) {
        return hit || Response.error();
      }
    })
  );
});
