// Service Worker for FileShare Pro PWA
// Only caches static files

const CACHE_NAME = 'fileshare-pro-v2';
const STATIC_CACHE_URLS = [
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg'
  // CDN resources will be cached on-demand during fetch
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        // Only cache if available, don't fail installation
        return cache.addAll(STATIC_CACHE_URLS).catch((error) => {
          console.warn('[Service Worker] Some assets failed to cache:', error);
        });
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

  // Only cache truly static files (not dynamic pages)
  const isStaticFile = 
    url.pathname.startsWith('/static/') &&
    (url.pathname.endsWith('.png') || 
     url.pathname.endsWith('.jpg') || 
     url.pathname.endsWith('.svg') || 
     url.pathname.endsWith('.json') ||
     url.pathname.endsWith('.css') ||
     url.pathname.endsWith('.js'));

  // Also cache CDN resources
  const isCDNResource = 
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('cdnjs.cloudflare.com');

  if (isStaticFile || isCDNResource) {
    // Cache-first strategy for static files only
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
          }).catch(() => cachedResponse || new Response('Offline', { status: 503 }));
        })
    );
  } else {
    // Network-only strategy for all dynamic content
    event.respondWith(
      fetch(request).catch(() => {
        // Only show offline page for document requests
        if (request.destination === 'document') {
          return new Response(
            '<html><body style="font-family: sans-serif; text-align: center; padding: 50px;"><h1>Offline</h1><p>Please check your internet connection.</p></body></html>',
            { headers: { 'Content-Type': 'text/html' } }
          );
        }
        return new Response('Offline', { status: 503 });
      })
    );
  }
});

// Handle messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
