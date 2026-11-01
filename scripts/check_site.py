"""Check rendered pages after `zola build`, without third-party dependencies."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
import tomllib
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.refs = []
        self.links = []
        self.canonical = []
        self.og_url = []
        self.lang = None
        self.redirect = False
        self.icons = []
        self.comments = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "div" and attrs.get("id") == "comments":
            self.comments.append(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
            self.refs.append(attrs["href"])
        if tag in {"img", "script", "source"} and attrs.get("src"):
            self.refs.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.refs.append(attrs["href"])
            if attrs.get("rel") == "canonical":
                self.canonical.append(attrs["href"])
            if "icon" in attrs.get("rel", "").split():
                self.icons.append(attrs["href"])
        if tag == "meta" and attrs.get("property") == "og:url":
            self.og_url.append(attrs.get("content"))
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            self.redirect = True


def front_matter(path):
    return tomllib.loads(path.read_text().split("+++", 2)[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("public"))
    parser.add_argument("--base-url")
    args = parser.parse_args()
    config = tomllib.loads(Path("config.toml").read_text())
    base = (args.base_url or config["base_url"]).rstrip("/")
    origin = urlsplit(base).netloc
    output = args.output_dir
    errors = []
    files = sorted(output.rglob("*.html"))
    assert files, f"No HTML found in {output}; run zola build first"
    pages = {}

    for path in files:
        relative = path.relative_to(output).as_posix()
        text = path.read_text()
        page = Page(text)
        pages[relative] = page
        page_url = base + "/" + relative.removesuffix("index.html")
        if relative != "404.html" and not page.redirect:
            if not page.icons or any(icon.startswith("data:") for icon in page.icons):
                errors.append(f"{relative}: missing image favicon or conflicting emoji favicon")
            if page.canonical != [page_url]:
                errors.append(f"{relative}: incorrect canonical {page.canonical}")
            if page.og_url != [page_url]:
                errors.append(f"{relative}: incorrect og:url {page.og_url}")
        for ref in page.refs:
            url = urlsplit(urljoin(page_url, ref))
            if url.scheme not in {"http", "https"} or url.netloc != origin:
                continue
            if "//" in url.path:
                errors.append(f"{relative}: double slash in {ref}")
            target = output / unquote(url.path.lstrip("/"))
            if not target.is_file() and not (target / "index.html").is_file():
                errors.append(f"{relative}: missing local target {ref}")
        if "goyo" in text.lower():
            errors.append(f"{relative}: leftover Goyo markup")

    for lang, suffix, prefix in [("ru", "", ""), ("en", ".en", "en/")]:
        home = pages[prefix + "index.html"]
        archive = pages[prefix + "archive/index.html"]
        posts = []
        for source in Path("content/blog").glob(f"*/index{suffix}.md"):
            metadata = front_matter(source)
            if metadata.get("draft", False):
                continue
            url = base + "/" + prefix + "blog/" + source.parent.name + "/"
            posts.append((metadata["date"], url))
            relative = prefix + "blog/" + source.parent.name + "/index.html"
            if pages[relative].lang != lang:
                errors.append(f"{relative}: wrong page language")
            comments = pages[relative].comments
            expected_comments = {
                "data-repo": config["extra"]["giscus"]["repo"],
                "data-repo-id": config["extra"]["giscus"]["repo_id"],
                "data-category-id": config["extra"]["giscus"]["category_id"],
                "data-mapping": "specific",
                "data-term": source.parent.name,
                "data-lang": lang,
            }
            if len(comments) != 1 or any(comments[0].get(key) != value
                                         for key, value in expected_comments.items()):
                errors.append(f"{relative}: missing comments or changed discussion mapping")
            if url not in archive.links:
                errors.append(f"{prefix}archive: missing {url}")
        expected = [url for _, url in sorted(posts, reverse=True)[:5]]
        actual = list(dict.fromkeys(url for url in home.links if url in {u for _, u in posts}))
        if actual != expected:
            errors.append(f"{prefix}homepage: wrong latest posts: {actual}")
        other_prefix = "en/" if lang == "ru" else ""
        other_urls = {base + "/" + other_prefix + "blog/" + p.parent.name + "/"
                      for p in Path("content/blog").glob("*/index.md")}
        if other_urls.intersection(home.links):
            errors.append(f"{prefix}homepage: posts from the wrong language")
        index = output / f"search_index.{lang}.json"
        if not index.is_file():
            errors.append(f"Missing search index: {index}")
        for stylesheet in ["giallo-light.css", "giallo-dark.css"]:
            if not (output / stylesheet).is_file():
                errors.append(f"Missing highlighting stylesheet: {stylesheet}")
    if errors:
        raise SystemExit("Site checks failed:\n" + "\n".join(sorted(set(errors))))
    print(f"Checked {len(files)} HTML files: targets, metadata, favicons, comments, posts, archives and indexes OK")


if __name__ == "__main__":
    main()
