/**
 * CactusCat Client Library
 * Ported from Pytron Client (v2.0)
 */

(function () {
    if (window.__cactus_initialized) return;

    // 1. INTERNAL STORE
    const _state = {};
    const _eventWrappers = new Map();

    // 2. BACKEND READINESS
    const isReady = () => {
        return typeof window.ipc !== 'undefined' && typeof window.ipc.postMessage === 'function';
    };

    const waitForBackend = (timeout = 3000) => {
        return new Promise((resolve) => {
            if (isReady()) return resolve();
            const start = Date.now();
            const interval = setInterval(() => {
                if (isReady()) {
                    clearInterval(interval);
                    resolve();
                } else if (Date.now() - start > timeout) {
                    clearInterval(interval);
                    console.warn("[CactusCat] Backend wait timed out.");
                    resolve();
                }
            }, 50);
        });
    };

    // 3. CORE API
    const cactusApi = {
        is_ready: true,
        version: "1.0.6",
        
        // --- State Management ---
        state: new Proxy(_state, {
            get: (target, prop) => target[prop],
            set: (target, prop, value) => {
                console.warn("[CactusCat] Native state should be modified via Python or cactus.call('set_state', ...)");
                target[prop] = value;
                return true;
            }
        }),

        // --- Event Bus ---
        on: (event, callback) => {
            const wrapper = (e) => callback(e.detail !== undefined ? e.detail : e);
            if (!_eventWrappers.has(callback)) _eventWrappers.set(callback, wrapper);
            window.addEventListener(event, wrapper);
        },

        off: (event, callback) => {
            const wrapper = _eventWrappers.get(callback);
            if (wrapper) {
                window.removeEventListener(event, wrapper);
                _eventWrappers.delete(callback);
            }
        },

        emit: (event, data) => {
            window.dispatchEvent(new CustomEvent(event, { detail: data }));
        },

        // --- RPC Bridge ---
        call: async (method, ...args) => {
            if (!isReady()) {
                await waitForBackend();
            }

            return new Promise((resolve, reject) => {
                const callId = Math.random().toString(36).substring(2, 15);
                const timeout = setTimeout(() => {
                    window.removeEventListener(`rpc_result_${callId}`, handler);
                    reject(new Error(`RPC Timeout: ${method}`));
                }, 10000);

                const handler = (event) => {
                    clearTimeout(timeout);
                    window.removeEventListener(`rpc_result_${callId}`, handler);
                    const { result, error } = event.detail;
                    if (error !== undefined) reject(new Error(error));
                    else resolve(result);
                };

                window.addEventListener(`rpc_result_${callId}`, handler);

                window.ipc.postMessage(JSON.stringify({
                    type: 'rpc',
                    method,
                    args,
                    id: callId
                }));
            });
        },

        log: (msg) => {
            console.log(`[CactusCat] ${msg}`);
            cactusApi.call('log', msg).catch(() => {});
        },

        // --- Window Actions ---
        close: () => cactusApi.call('close'),
        minimize: () => cactusApi.call('minimize'),
        maximize: () => cactusApi.call('maximize'),
        set_title: (title) => cactusApi.call('set_title', title),
        
        publish: (event, data) => {
            return cactusApi.call('publish_event', { event, data });
        },

        asset: async (key) => {
            // Map pytron:// to ccat:// if needed
            if (key.startsWith('pytron://')) key = key.replace('pytron://', 'ccat://');
            if (key.startsWith('data/')) key = `ccat://${key}`;
            
            const url = (key.includes('://')) ? key : `ccat://${key}`;
            const resp = await fetch(url);
            return await resp.blob();
        }
    };

    // 4. THE PROXY SHIM (For pytron-like calls: cactus.greet())
    const cactus = new Proxy(cactusApi, {
        get: (target, prop) => {
            if (prop in target) return target[prop];
            if (typeof prop === 'symbol' || prop === 'then' || prop === 'toJSON') return undefined;

            // Dynamic Python call
            return (...args) => target.call(prop, ...args);
        }
    });

    // 5. GLOBAL LISTENERS
    window.addEventListener('ccat:state-update', (e) => {
        const { key, value } = e.detail;
        _state[key] = value;
        
        // Dispatch specific state event
        window.dispatchEvent(new CustomEvent(`state:${key}`, { detail: value }));
        // Dispatch generic state event
        window.dispatchEvent(new CustomEvent('cactus:state', { detail: { ..._state } }));
        // Legacy support
        window.dispatchEvent(new CustomEvent('pytron:state', { detail: { ..._state } }));

        // Handle Plugin Auto-Injection
        if (key === '_plugins' && Array.isArray(value)) {
            value.forEach(plugin => {
                const scriptId = `cactus-plugin-${plugin.name}`;
                if (plugin.ui_entry && !document.getElementById(scriptId)) {
                    console.log(`[CactusCat] Loading Plugin UI: ${plugin.name} from ${plugin.ui_entry}`);
                    const script = document.createElement('script');
                    script.id = scriptId;
                    script.src = plugin.ui_entry;
                    script.type = 'module';
                    document.head.appendChild(script);

                    // Optional: Handle slots/web components
                    if (plugin.slot) {
                        script.onload = () => {
                            document.querySelectorAll(`[data-cactus-slot="${plugin.slot}"], [data-pytron-slot="${plugin.slot}"]`)
                                .forEach(container => {
                                    const el = document.createElement(`${plugin.name}-widget`);
                                    if (!container.querySelector(el.tagName)) {
                                        container.appendChild(el);
                                    }
                                });
                        };
                    }
                }
            });
        }
    });

    // Global Fetch Interceptor for pytron:// legacy links
    const _originalFetch = window.fetch;
    window.fetch = async (...args) => {
        if (typeof args[0] === 'string' && args[0].startsWith('pytron://')) {
            args[0] = args[0].replace('pytron://', 'ccat://');
        }
        return _originalFetch(...args);
    };

    // Asset Protocol Helper (Replaces ccat:// src automatically)
    const handleAssets = (node) => {
        const tags = ['IMG', 'SCRIPT', 'LINK', 'VIDEO', 'AUDIO'];
        const process = (el) => {
            if (el.tagName && tags.includes(el.tagName)) {
                const attr = el.tagName === 'LINK' ? 'href' : 'src';
                const val = el.getAttribute(attr);
                if (val && val.startsWith('pytron://')) {
                    el.setAttribute(attr, val.replace('pytron://', 'ccat://'));
                }
            }
        };
        if (node.querySelectorAll) {
            process(node);
            node.querySelectorAll(tags.join(',')).forEach(process);
        }
    };

    const observer = new MutationObserver((mutations) => {
        mutations.forEach(m => m.addedNodes.forEach(handleAssets));
    });

    // Capture Global Errors and send to Python
    window.addEventListener('error', (event) => {
        cactus.call('report_error', {
            message: event.message,
            source: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error ? event.error.stack : ''
        }).catch(() => {});
    });

    // 6. INITIALIZATION
    window.cactus = cactus;
    window.pytron = cactus; // Backward compatibility
    window.__cactus_initialized = true;

    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
        handleAssets(document.body);
    } else {
        window.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.body, { childList: true, subtree: true });
            handleAssets(document.body);
        });
    }

    console.log("%c CactusCat Client Initialized ", "background: #ff5500; color: #fff; font-weight: bold;");

    // Auto-sync initial state
    waitForBackend().then(() => {
        cactus.call('get_state').then(initialState => {
            for (const key in initialState) {
                _state[key] = initialState[key];
                window.dispatchEvent(new CustomEvent(`state:${key}`, { detail: initialState[key] }));
            }
            window.dispatchEvent(new CustomEvent('cactus:state', { detail: { ..._state } }));
        }).catch(err => console.error("Failed to sync initial state", err));
    });

})();
