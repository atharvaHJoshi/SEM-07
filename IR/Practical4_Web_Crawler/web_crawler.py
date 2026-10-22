"""
Practical 4 : Simple web crawler
Aim         : Visit a website, follow the links found on its pages and print
              every page visited (breadth-first, with a depth limit).
Usage       : python3 web_crawler.py [start_url]
"""

import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

START_URL = sys.argv[1] if len(sys.argv) > 1 else "https://quotes.toscrape.com/"
MAX_PAGES = 5        # stop after visiting this many pages
MAX_DEPTH = 2        # do not follow links deeper than this


class LinkFinder(HTMLParser):
    """Collect all href links from an HTML page."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value:
                    self.links.append(value)


def get_page(url):
    """Download a page and return its HTML text (None if it fails)."""
    request = Request(url, headers={"User-Agent": "SimpleCrawler/1.0"})
    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as error:
        print("  could not open", url, "->", error)
        return None


def main():
    print("Simple Web Crawler")
    print("Start URL :", START_URL)
    print("Max pages :", MAX_PAGES)
    print("Max depth :", MAX_DEPTH)
    print("-" * 60)

    visited = set()             # pages already seen
    queue = [(START_URL, 0)]    # (url, depth) pairs still to visit
    start_domain = urlparse(START_URL).netloc

    while queue and len(visited) < MAX_PAGES:
        url, depth = queue.pop(0)      # take the first url (BFS)

        if url in visited:
            continue
        visited.add(url)
        print(f"[{len(visited)}] visiting: {url}  (depth {depth})")

        html = get_page(url)
        if html is None:
            continue

        finder = LinkFinder()
        finder.feed(html)

        for link in finder.links:
            full_url = urljoin(url, link)          # relative -> full url
            full_url = full_url.split("#")[0]      # remove #section part

            # stay on the same website and do not go deeper than 2 levels
            if urlparse(full_url).netloc == start_domain and depth < MAX_DEPTH:
                if full_url not in visited:
                    queue.append((full_url, depth + 1))

    print("-" * 60)
    print("Pages visited:", len(visited))


if __name__ == "__main__":
    main()
