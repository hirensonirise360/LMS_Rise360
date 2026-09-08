const CACHE_NAME = 'RISE360-LMS-v1';
const STATIC_CACHE_URLS = [
    '/static/css/style.min.css',
    '/static/css/uea.css',
    '/static/vendor/bootstrap-5.3.2/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    '/static/img/rise360-logo.png',
    '/favicon.ico',
    '/offline/' // Pre-cache the offline fallback page
];

// 1. Install Event: Cache Static Assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('Opened cache, adding static assets');
            return cache.addAll(STATIC_CACHE_URLS);
        })
    );
    self.skipWaiting();
});

// 2. Activate Event: Clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// 3. Fetch Event: Cache-First for static, Network-First for HTML
self.addEventListener('fetch', event => {
    const request = event.request;

    // Cache-first strategy for static files and images
    if (request.url.includes('/static/') || request.destination === 'image' || request.destination === 'font') {
        event.respondWith(
            caches.match(request).then(response => {
                return response || fetch(request).then(fetchRes => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, fetchRes.clone());
                        return fetchRes;
                    });
                });
            })
        );
        return;
    }

    // Network-first strategy for HTML pages (with fallback to offline.html)
    if (request.mode === 'navigate' || request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match('/offline/');
            })
        );
    }
});
