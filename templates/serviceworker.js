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

    // Check if user is currently viewing a conversation
    // If so, suppress notifications for NEW_MESSAGE type
    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            let isViewingConversation = false;
            
            // Check all clients (not just focused ones) to see if user is viewing a conversation
            for (const client of clientList) {
                const url = new URL(client.url);
                // Check if user is viewing a conversation page
                if (url.pathname.includes('/messaging/conversation/')) {
                    isViewingConversation = true;
                    break;
                }
            }
            
            // Suppress NEW_MESSAGE notifications when viewing any conversation
            if (isViewingConversation && data.data && data.data.type === 'NEW_MESSAGE') {
                console.log('Suppressing push notification - user is viewing conversation');
                return Promise.resolve();
            }

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

            return self.registration.showNotification(title, options);
        }).catch((error) => {
            console.error('Error in push event handler:', error);
        })
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

