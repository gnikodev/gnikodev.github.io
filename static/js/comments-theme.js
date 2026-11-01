// tabi's async Giscus loader can miss a theme change while its iframe loads.
// Read the current site theme again when the frame appears and becomes ready.
(() => {
    const comments = document.getElementById('comments');
    if (!comments) return;

    const watched = new WeakSet();
    const ready = new WeakSet();
    const applied = new WeakMap();

    function syncTheme(force = false) {
        const dark = document.documentElement.dataset.theme === 'dark';
        const theme = dark ? comments.dataset.darkTheme : comments.dataset.lightTheme;
        const script = comments.querySelector('script[src="https://giscus.app/client.js"]');
        if (script) script.dataset.theme = theme;

        const frame = comments.querySelector('iframe.giscus-frame');
        if (!frame) return;
        if (!watched.has(frame)) {
            watched.add(frame);
            frame.addEventListener('load', () => syncTheme(true));
        }
        if (force || applied.get(frame) !== theme) {
            frame.contentWindow.postMessage({ giscus: { setConfig: { theme } } }, 'https://giscus.app');
            applied.set(frame, theme);
        }
    }

    new MutationObserver(() => syncTheme()).observe(comments, { childList: true, subtree: true });
    new MutationObserver(() => syncTheme()).observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-theme'],
    });
    window.addEventListener('themeChanged', () => syncTheme());
    window.addEventListener('message', (event) => {
        const frame = comments.querySelector('iframe.giscus-frame');
        if (event.origin === 'https://giscus.app' && frame
            && event.source === frame.contentWindow && event.data?.giscus && !ready.has(frame)) {
            ready.add(frame);
            syncTheme(true);
        }
    });
    syncTheme();
})();
