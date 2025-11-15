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
    let targetUrl = notificationData.url || '/notifications/';
    
    // Make sure URL is absolute
    if (!targetUrl.startsWith('http')) {
        // Get the origin from any existing client or use a default
        event.waitUntil(
            self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
                let origin = '/';
                if (clientList.length > 0) {
                    const url = new URL(clientList[0].url);
                    origin = url.origin;
                }
                targetUrl = origin + (targetUrl.startsWith('/') ? targetUrl : '/' + targetUrl);
                
                // Try to focus existing window or open new one
                for (const client of clientList) {
                    if (client.url.includes(targetUrl) || client.url === targetUrl) {
                        return client.focus();
                    }
                }
                
                if (self.clients.openWindow) {
                    return self.clients.openWindow(targetUrl);
                }
            })
        );
    } else {
        event.waitUntil(
            self.clients.openWindow(targetUrl)
        );
    }
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

