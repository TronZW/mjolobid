self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    if (!(self.Notification && self.Notification.permission === 'granted')) {
        return;
    }

    const data = (() => {
        try {
            return event.data ? event.data.json() : {};
        } catch (err) {
            return {
                title: 'MjoloBid',
                body: event.data ? event.data.text() : '',
            };
        }
    })();

    const title = data.title || 'MjoloBid';
    const options = {
        body: data.body || '',
        icon: data.icon,
        badge: data.badge,
        tag: data.tag || `mjolobid-${Date.now()}`,
        data: {
            url: data.url || '/notifications/',
            ...data.data,
        },
        vibrate: data.vibrate || [100, 50, 100],
        actions: data.actions || [],
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const notificationData = event.notification.data || {};
    const targetUrl = notificationData.url || '/notifications/';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            for (const client of clientList) {
                const url = new URL(client.url);
                if (url.pathname === new URL(targetUrl, url.origin).pathname) {
                    client.focus();
                    return;
                }
            }
            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
        })
    );
});

self.addEventListener('pushsubscriptionchange', (event) => {
    event.waitUntil(
        self.registration.pushManager.subscribe(event.oldSubscription.options).then((subscription) => {
            return fetch('/notifications/api/push-subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(subscription.toJSON()),
            });
        })
    );
});

