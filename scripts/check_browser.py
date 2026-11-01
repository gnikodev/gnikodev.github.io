"""Browser regressions; install scripts/requirements-browser.txt and Chromium first."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import expect, sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check_browser(base):
    with sync_playwright() as playwright:
        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
        browser = playwright.chromium.launch(executable_path=executable)
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="light")
            # Test our page scripts and CSP without contacting analytics services.
            context.route("https://www.googletagmanager.com/**",
                          lambda route: route.fulfill(status=200, body=""))
            # Exercise the real tabi integration and CSP without creating GitHub
            # discussions, depending on network availability, or loading a login UI.
            context.route("https://giscus.app/client.js", lambda route: route.fulfill(
                status=200, content_type="application/javascript", body="""
                const stylesheet = document.createElement('link');
                stylesheet.rel = 'stylesheet';
                stylesheet.href = 'https://giscus.app/default.css';
                document.head.appendChild(stylesheet);
                const frame = document.createElement('iframe');
                frame.className = 'giscus-frame';
                frame.src = 'https://giscus.app/test-frame';
                const container = document.currentScript.parentElement;
                setTimeout(() => container.appendChild(frame), 200);
                """))
            context.route("https://giscus.app/default.css", lambda route: route.fulfill(
                status=200, content_type="text/css", body=".giscus-frame { width: 100%; border: 0; }"))
            context.route("https://giscus.app/test-frame", lambda route: route.fulfill(
                status=200, content_type="text/html", body="""
                <!doctype html><body>Comments test frame<script>
                addEventListener('message', event => {
                    if (event.data.giscus?.setConfig?.theme) {
                        parent.postMessage({testGiscusTheme: event.data.giscus.setConfig.theme}, '*');
                    }
                });
                parent.postMessage({giscus: {resizeHeight: 200}}, '*');
                </script></body>
                """))
            context.add_init_script("""
                window.testGiscusTheme = null;
                addEventListener('message', event => {
                    if (event.origin === 'https://giscus.app' && event.data.testGiscusTheme) {
                        window.testGiscusTheme = event.data.testGiscusTheme;
                    }
                });
            """)
            errors = []
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text)
                    if message.type == "error" else None)

            for prefix in ["", "/en"]:
                page.goto(base + prefix + "/", wait_until="networkidle")
                assert page.locator("#comments").count() == 0
                avatar = page.locator(".home-title").evaluate(
                    "element => getComputedStyle(element, '::before').backgroundImage"
                )
                assert "m192.png" in avatar, avatar
                icons = page.locator('link[rel~="icon"]').evaluate_all(
                    "elements => elements.map(element => element.href)"
                )
                assert icons and all(url.startswith(base) and "?h=" in url for url in icons), icons
                expect(page.locator("#home-banner-header")).to_have_text(
                    "Hi! I'm Nikolay Gushcharin" if prefix else "Привет! Я Николай Гущарин"
                )
                expect(page.locator("#banner-home-img")).to_be_visible()
                assert page.locator("main h1").count() == 1
                expect(page.locator(f'#banner-home-subtitle a[href="{base}{prefix}/about/"]')).to_be_visible()
                title = page.locator(".home-title")
                before_hover = title.bounding_box()
                nav_before = page.locator(".nav-navs").first.bounding_box()
                title.hover()
                assert title.bounding_box() == before_hover, "Branding moved on hover"
                assert page.locator(".nav-navs").first.bounding_box() == nav_before, "Navigation moved on hover"
                assert title.evaluate("element => getComputedStyle(element, '::before').position") == "static"
                page.locator("#search-button").click()
                terms = ["Obsidian", "Rust"]
                if not prefix:
                    terms.append("синхронизация")
                for term in terms:
                    page.locator("#searchInput").fill(term)
                    # Wait for this query's asynchronous results, not the previous query.
                    expect(page.locator("#results a").first).to_be_visible()
                    links = page.locator("#results a").evaluate_all(
                        "elements => elements.map(element => element.href)"
                    )
                    assert all(("/en/" in url) == bool(prefix) for url in links), links
                    expected_slug = "rust-work-with-configs" if term == "Rust" else "obsidian-android-git-sync"
                    expect(page.locator(f'#results a[href*="/{expected_slug}/"]').first).to_be_visible()

            page.goto(base + "/blog/obsidian-android-git-sync/", wait_until="networkidle")
            comments_script = page.locator('#comments script[src="https://giscus.app/client.js"]')
            expect(comments_script).to_have_attribute("data-term", "obsidian-android-git-sync")
            expect(comments_script).to_have_attribute("data-mapping", "specific")
            expect(comments_script).to_have_attribute("data-category-id", "DIC_kwDOMkqe1M4C0Y8a")
            expect(comments_script).to_have_attribute("data-lang", "ru")
            expect(page.frame_locator(".giscus-frame").locator("body")).to_be_visible()
            token = page.locator('.giallo span[class^="z-"]').first
            expect(token).to_be_visible()
            before = token.evaluate("element => getComputedStyle(element).color")
            page.locator(".theme-switcher").click()
            page.wait_for_function(
                "old => getComputedStyle(document.querySelector('.giallo span[class^=z-]')).color !== old",
                arg=before,
            )
            page.wait_for_function("() => window.testGiscusTheme === 'noborder_dark'")
            page.locator(".language-switcher summary").click()
            page.locator('.language-switcher a[lang="en"]').click()
            expect(page).to_have_url(base + "/en/blog/obsidian-android-git-sync/")
            expect(page.locator('#comments script[src="https://giscus.app/client.js"]')).to_have_attribute("data-lang", "en")
            expect(page.locator("#comments")).to_have_attribute("data-term", "obsidian-android-git-sync")

            # A saved dark theme must also reach an iframe loaded after the page.
            page.reload(wait_until="networkidle")
            expect(page.locator("html")).to_have_attribute("data-theme", "dark")
            expect(page.locator('#comments script[src="https://giscus.app/client.js"]')).to_have_attribute("data-theme", "noborder_dark")
            page.wait_for_function("() => window.testGiscusTheme === 'noborder_dark'")
            # Switch before the mock iframe is appended, then check its ready state.
            page.reload(wait_until="domcontentloaded")
            page.locator(".theme-switcher").click()
            page.wait_for_function("() => window.testGiscusTheme === 'noborder_light'")

            page.goto(base + "/about/", wait_until="networkidle")
            expect(page.locator("#main-content h1")).to_have_text("Обо мне")
            assert page.locator("#comments").count() == 0

            page.set_viewport_size({"width": 390, "height": 844})
            for path in ["/", "/en/", "/blog/obsidian-android-git-sync/"]:
                page.goto(base + path, wait_until="networkidle")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), path

            assert not errors, "\n".join(errors)
            print("Browser checks OK: branding, favicons, Giscus, search, palettes, translations, mobile, JS and CSP")
        finally:
            browser.close()


def main():
    with TemporaryDirectory(prefix="tabi-browser-") as directory:
        output = Path(directory) / "site"
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(output))
        )
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            subprocess.run(["zola", "build", "--base-url", base, "--output-dir", str(output)], check=True)
            Thread(target=server.serve_forever, daemon=True).start()
            try:
                check_browser(base)
            finally:
                server.shutdown()
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
