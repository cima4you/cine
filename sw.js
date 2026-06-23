const CACHE = 'rcine-v1';
const URLS = ['/', '/index.html', '/manifest.json', '/data-loader.js', '/logo.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(URLS)));
  self.skipWaiting();
});
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      const c = caches.open(CACHE);
      c.then(cache => cache.put(e.request, res.clone()));
      return res;
    }))
  );
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.matchAll({type:'window'}).then(cls => {
    if (cls[0]) { cls[0].focus(); return; }
    clients.openWindow('/');
  }));
});
