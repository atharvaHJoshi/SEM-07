# IR Practicals (Information Retrieval)

All Group 1 practicals (1 to 5) plus the Group 2 mini-project "Document Summarization System", as per the LP-IV schedule.

| No. | Practical | File |
|-----|-----------|------|
| 1 | Similarity between two text documents (cosine similarity) | `Practical1_Document_Similarity/document_similarity.py` |
| 2 | PageRank algorithm | `Practical2_PageRank/pagerank.py` |
| 3 | Map-Reduce program to count alphabetic characters | `Practical3_MapReduce_Character_Count/map_reduce_char_count.py` |
| 4 | Simple web crawler | `Practical4_Web_Crawler/web_crawler.py` |
| 5 | Parse XML, build web graph and topic specific PageRank | `Practical5_XML_WebGraph_Topic_PageRank/xml_topic_pagerank.py` |
| Mini Project | Document summarization system | `MiniProject_Document_Summarization/summarizer.py` |

## How to run

```
python3 document_similarity.py
python3 pagerank.py
python3 map_reduce_char_count.py
python3 web_crawler.py            # optional: python3 web_crawler.py <url>
python3 xml_topic_pagerank.py
```

Or run all five at once from here: `../run_all.sh ir`
The mini-project runs with: `../run_all.sh project`

All programs use only Python's standard library (no extra installation).
Practical 4 needs internet and by default crawls `https://example.com`;
you can pass any URL as an argument.
