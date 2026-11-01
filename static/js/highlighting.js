// tabi 5.0.0 loads both Giallo palettes without scoping them to the UI theme.
// Keep its generated stylesheets, but enable only the active palette.
const highlightingPalettes = [...document.querySelectorAll('link[rel="stylesheet"]')]
    .filter((link) => /\/giallo-(light|dark)\.css(?:\?|$)/.test(link.href));

function syncHighlighting() {
    const theme = document.documentElement.dataset.theme
        || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    highlightingPalettes.forEach((link) => {
        link.media = link.href.includes(`giallo-${theme}.css`) ? 'all' : 'not all';
    });
}

syncHighlighting();
window.addEventListener('themeChanged', syncHighlighting);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncHighlighting);
