const CACHE_NAME = 'agrivision-v1';

const STATIC_ASSETS = [
  '/',
  '/static/index.html',
  '/static/style.css',
  '/static/app.js',
  '/static/manifest.json',
  '/static/icon.png',
  '/static/home_images/diagnose1.jpg',
  '/static/home_images/guide.jpg',
  '/static/home_images/market1.jpg',
  '/static/home_images/hero.png',
  '/static/guide_images/alternaria_alternata.jpg',
  '/static/guide_images/cercospora_nicotianae.jpg',
  '/static/guide_images/TMV.jpg',
  '/static/guide_images/Angular_leaf_spot.jpg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Only cache GET requests and ignore API calls
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/')) return;

  // Stale-While-Revalidate Strategy
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        // Cache the new response for future
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Fallback for failed network
        console.log('[Service Worker] Fetch failed, relying on cache only.');
      });

      return cachedResponse || fetchPromise;
    })
  );
});
