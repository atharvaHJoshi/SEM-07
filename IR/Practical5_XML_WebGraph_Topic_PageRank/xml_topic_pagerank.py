"""
Practical 5 : Parse XML text, generate Web graph and compute topic
              specific page rank
Aim         : Read an XML description of web pages and links, build the
              web graph and rank pages of one topic higher using topic
              specific (personalised) PageRank.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

XML_FILE = Path(__file__).parent / "webgraph.xml"
TOPIC = "sports"
DAMPING = 0.85
ITERATIONS = 50


def build_web_graph(root):
    """Return graph (page -> links) and the set of pages of the topic."""
    graph = {}
    topic_pages = set()

    for page in root.findall("page"):
        name = page.get("id")
        graph[name] = [link.get("to") for link in page.findall("link")]
        if page.get("topic") == TOPIC:
            topic_pages.add(name)

    return graph, topic_pages


def topic_pagerank(graph, topic_pages):
    """PageRank where the random surfer always restarts on a topic page."""
    pages = list(graph)

    # teleport always goes to a topic page, so topic pages get extra rank
    teleport = {page: (1 / len(topic_pages) if page in topic_pages else 0)
                for page in pages}

    rank = teleport.copy()       # start the surfer on the topic pages

    for _ in range(ITERATIONS):
        new_rank = {}
        for page in pages:
            votes = 0.0
            for other in pages:
                out_links = graph[other]
                if out_links and page in out_links:
                    votes += rank[other] / len(out_links)
            new_rank[page] = (1 - DAMPING) * teleport[page] + DAMPING * votes
        rank = new_rank

    return rank


def main():
    root = ET.parse(XML_FILE).getroot()
    graph, topic_pages = build_web_graph(root)

    print("Web graph from", XML_FILE.name + ":")
    for page, links in graph.items():
        mark = "  [topic page]" if page in topic_pages else ""
        print(f"  {page} -> {', '.join(links) if links else 'no links'}{mark}")

    print(f"\nTopic: {TOPIC}  (topic pages: {', '.join(sorted(topic_pages))})")

    rank = topic_pagerank(graph, topic_pages)

    print("\nTopic specific PageRank (topic pages get a higher score):")
    for page, score in sorted(rank.items(), key=lambda item: -item[1]):
        mark = " <-- topic page" if page in topic_pages else ""
        print(f"  {page} : {score:.4f}{mark}")


if __name__ == "__main__":
    main()
