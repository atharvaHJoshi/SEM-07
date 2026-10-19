"""
Practical 2 : Implement PageRank algorithm
Aim         : Compute the importance of web pages from the link structure
              using the PageRank formula and show the ranking.
"""

DAMPING = 0.85      # chance that the user follows a link (d in the formula)
ITERATIONS = 50     # number of times the formula is applied

# The web graph : page -> list of pages it links to
web_graph = {
    "A": ["B", "C"],
    "B": ["C"],
    "C": ["A"],
    "D": ["C"],
}


def pagerank(graph):
    pages = list(graph)

    # Start with equal rank for every page : 1 / N
    rank = {page: 1 / len(pages) for page in pages}

    for _ in range(ITERATIONS):
        new_rank = {}
        for page in pages:
            # sum of ranks of pages that link to this page
            votes = 0.0
            for other in pages:
                if page in graph[other]:
                    votes += rank[other] / len(graph[other])
            new_rank[page] = (1 - DAMPING) / len(pages) + DAMPING * votes
        rank = new_rank

    return rank


def main():
    rank = pagerank(web_graph)

    print("Web graph (page -> links):")
    for page, links in web_graph.items():
        print(f"  {page} -> {', '.join(links)}")

    print("\nPageRank scores (higher = more important):")
    for page, score in sorted(rank.items(), key=lambda item: -item[1]):
        print(f"  {page} : {score:.4f}")

    best = max(rank, key=rank.get)
    print(f"\nMost important page: {best}")


if __name__ == "__main__":
    main()
