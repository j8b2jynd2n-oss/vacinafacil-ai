// Bump a versão sempre que o HTML mudar — força limpeza do cache antigo
const CACHE = 'vacinafacil-v4';

// Apenas assets verdadeiramente estáticos ficam em cache
const STATIC = ['/manifest.json', '/icon.svg'];

// Rotas que nunca devem ser cacheadas
const NO_CACHE = ['/chat', '/tts', '/feedback', '/admin', '/curadoria', '/privacidade'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(STATIC))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  // Apaga todos os caches antigos (v1, v2, …)
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* ── PUSH NOTIFICATIONS ────────────────────── */
self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : {};
  e.waitUntil(
    self.registration.showNotification(data.title || 'VacinaFácil AI 💉', {
      body: data.body || 'Nova informação sobre vacinação disponível.',
      icon: '/icon.svg',
      badge: '/icon.svg',
      tag: 'vacina-notif',
      renotify: true,
      data: { url: data.url || '/' }
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
      for (const c of cs) {
        if (c.url === (e.notification.data?.url || '/') && 'focus' in c) return c.focus();
      }
      return clients.openWindow(e.notification.data?.url || '/');
    })
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const path = new URL(e.request.url).pathname;

  // API e páginas dinâmicas: nunca cacheia, vai direto na rede
  if (NO_CACHE.some(p => path.startsWith(p))) return;

  // HTML principal (/): network-first — sempre busca versão mais recente
  // fallback para cache se offline
  if (path === '/') {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) {
            caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          }
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Assets estáticos: cache-first
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(res => {
        if (res.ok && STATIC.includes(path)) {
          caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        }
        return res;
      });
    })
  );
});
