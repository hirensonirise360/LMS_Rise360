// Initialize IndexedDB for Sync Queue
const DB_NAME = 'RISE360_OfflineDB';
const STORE_NAME = 'sync_queue';

function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = event => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

// Queue a request to IndexedDB
async function queueRequest(url, method, body) {
    const db = await initDB();
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    store.add({
        url: url,
        method: method,
        body: body,
        timestamp: Date.now()
    });
}

// Custom Fetch Wrapper
window.apiFetch = async function(url, options = {}) {
    if (!navigator.onLine && (options.method === 'POST' || options.method === 'PUT')) {
        console.warn('Offline: Queueing request for later sync.');
        await queueRequest(url, options.method, options.body);
        return { queued: true, message: 'Action saved offline' };
    }
    
    try {
        const response = await fetch(url, options);
        localStorage.setItem('rise360_last_sync', Date.now());
        return response;
    } catch (err) {
        if (options.method === 'POST' || options.method === 'PUT') {
            await queueRequest(url, options.method, options.body);
            return { queued: true, message: 'Network failed. Action saved offline.' };
        }
        throw err;
    }
}

// Replay queued requests when online
async function syncOfflineQueue() {
    if (!navigator.onLine) return;
    
    const db = await initDB();
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();

    request.onsuccess = async () => {
        const queuedItems = request.result;
        if (queuedItems.length === 0) return;

        console.log(`Syncing ${queuedItems.length} offline actions...`);
        
        for (const item of queuedItems) {
            try {
                // Get CSRF Token safely
                const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
                
                await fetch(item.url, {
                    method: item.method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                        'X-Offline-Replay': 'true' // Flag for idempotency on Django side
                    },
                    body: item.body
                });

                // Remove from queue upon success
                const deleteTx = db.transaction(STORE_NAME, 'readwrite');
                deleteTx.objectStore(STORE_NAME).delete(item.id);
            } catch (err) {
                console.error("Failed to sync item", item.id, err);
            }
        }
        localStorage.setItem('rise360_last_sync', Date.now());
    };
}

// Listen for network status changes
window.addEventListener('online', syncOfflineQueue);
