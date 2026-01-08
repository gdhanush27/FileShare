// Service Worker for FileShare Pro PWA
// Only caches static files

const CACHE_NAME = 'fileshare-pro-v1';
const STATIC_CACHE_URLS = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg',
  // Add CSS and JS from CDN
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, { cache: 'no-cache' })));
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[Service Worker] Activation complete');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache for static files, network for everything else
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only cache static files
  const isStaticFile = 
    url.pathname.startsWith('/static/') ||
    url.pathname === '/' ||
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('bootstrap');

  if (isStaticFile) {
    // Cache-first strategy for static files
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // If not in cache, fetch from network and cache it
          return fetch(request).then((response) => {
            // Only cache successful responses
            if (!response || response.status !== 200 || response.type === 'error') {
              return response;
            }
            
            // Clone the response as it can only be consumed once
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
            
            return response;
          });
        })
        .catch(() => {
          // If both cache and network fail, return a basic offline page
          if (request.destination === 'document') {
            return new Response(
              '<html><body><h1>Offline</h1><p>Please check your internet connection.</p></body></html>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          }
        })
    );
  } else {
    // Network-only strategy for dynamic content (uploads, downloads, API calls)
    event.respondWith(fetch(request));
  }
});

// Handle messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
