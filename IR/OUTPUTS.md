# IR Practicals — Outputs

This page records the output produced by each Information Retrieval practical,
with a short explanation of what every result means.

All commands are run from inside the practical's own folder.

| No. | Practical | Command |
|-----|-----------|---------|
| 1 | Document Similarity | `python3 document_similarity.py` |
| 2 | PageRank | `python3 pagerank.py` |
| 3 | Map-Reduce Character Count | `python3 map_reduce_char_count.py` |
| 4 | Web Crawler | `python3 web_crawler.py` |
| 5 | XML Web Graph + Topic PageRank | `python3 xml_topic_pagerank.py` |
| Mini Project | Document Summarization | `python3 summarizer.py` |

---

## Practical 1 — Similarity between Two Text Documents

**Aim:** Read two documents and measure how similar they are using cosine
similarity of word frequencies.

**Documents compared**

| Document | File | Words |
|----------|------|-------|
| Document 1 | `doc1.txt` | 58 |
| Document 2 | `doc2.txt` | 52 |

Both documents are about cricket and share most of their vocabulary.

**Common words (34):**

```
a, and, ball, between, by, countries, cricket, eleven, hitting, in, is,
many, match, matches, more, of, on, played, players, running, runs, score,
sport, stadiums, team, teams, television, the, to, two, watching, wickets,
wins, with
```

**Result**

| Measure | Value |
|---------|-------|
| Cosine similarity | `0.8820` |
| Percentage | `88.20 %` |
| Verdict | The two documents are **very similar** |

**What the output shows:** 34 words occur in both documents, so their word
frequency vectors point in almost the same direction. A cosine score close to
1 means high similarity; 0.8820 is above the 0.80 threshold, so the program
reports "very similar".

---

## Practical 2 — PageRank Algorithm

**Aim:** Compute the importance of web pages from their link structure using
the PageRank formula (damping factor `d = 0.85`, 50 iterations).

**Input web graph**

```
A -> B, C
B -> C
C -> A
D -> C
```

**PageRank scores**

| Rank | Page | Score | Meaning |
|------|------|-------|---------|
| 1 | C | `0.3941` | Most important — receives links from A, B and D |
| 2 | A | `0.3725` | Receives a link from C |
| 3 | B | `0.1958` | Receives a link from A |
| 4 | D | `0.0375` | Has no incoming links |

**Result:** The most important page is **C**.

**What the output shows:** PageRank distributes importance along links. Page C
is linked to by three pages, so it collects the highest score. Page D links to
C but is not linked back by anyone, so it ends with the lowest score. Comparing
the table with the initial equal score (`1/4 = 0.25` per page) shows how the
link structure changes the ranking.

---

## Practical 3 — Map-Reduce Program to Count Alphabetic Characters

**Aim:** Count how many times each letter A–Z appears in a dataset using the
Map, Shuffle and Reduce phases (case-insensitive, non-letters ignored).

**Input dataset**

```
In 2026, Data Science & Information Retrieval are popular subjects!
Students love Python3, Hadoop, MapReduce, and Big-Data tools.
The quick brown fox jumps over the lazy dog -- 123 times.
```

**Map-Reduce phases**

| Phase | Action | Example |
|-------|--------|---------|
| Map | Emit `(letter, 1)` for every alphabetic character | `I -> (i, 1)`, `n -> (n, 1)` |
| Shuffle | Group all values by letter | `i -> [1, 1, 1, ...]` |
| Reduce | Sum the 1s for each letter | `i -> 8` |

**Character counts**

| Letter | Count | Letter | Count |
|:------:|:-----:|:------:|:-----:|
| a | 12 | n | 8 |
| b | 3 | o | 13 |
| c | 5 | p | 6 |
| d | 7 | q | 1 |
| e | 14 | r | 8 |
| f | 2 | s | 8 |
| g | 2 | t | 12 |
| h | 4 | u | 6 |
| i | 8 | v | 3 |
| j | 2 | w | 1 |
| k | 1 | x | 1 |
| l | 5 | y | 2 |
| m | 4 | z | 1 |

**Result:** Total letters counted = **139**.

**What the output shows:** `e` is the most frequent letter (14 times), followed
by `o` (13) and `a` / `t` (12 each). Digits, spaces and punctuation such as
`2026`, `&`, `!`, `-` and `3` are excluded because only letters are counted.
Upper- and lower-case letters are merged (`A` and `a` both count as `a`).

---

## Practical 4 — Simple Web Crawler

**Aim:** Visit a website, follow the links found on its pages and print every
page visited (breadth-first with a depth limit of 2 and a maximum of 5 pages).

**Command**

```bash
python3 web_crawler.py
```

By default the crawler starts at `https://quotes.toscrape.com/` (a site made
for scraping practice); another URL can be passed as an argument.

**Output**

```
Simple Web Crawler
Start URL : https://quotes.toscrape.com/
Max pages : 5
Max depth : 2
------------------------------------------------------------
[1] visiting: https://quotes.toscrape.com/  (depth 0)
[2] visiting: https://quotes.toscrape.com/login  (depth 1)
[3] visiting: https://quotes.toscrape.com/author/Albert-Einstein  (depth 1)
[4] visiting: https://quotes.toscrape.com/tag/change/page/1/  (depth 1)
[5] visiting: https://quotes.toscrape.com/tag/deep-thoughts/page/1/  (depth 1)
------------------------------------------------------------
Pages visited: 5
```

**What the output shows:** The crawler starts at the home page (depth 0),
collects its links and then visits them in breadth-first order. All five
visited pages belong to the same website (`quotes.toscrape.com`), and the
depth number says how many links away each page is from the start page. The
crawl stops when the page limit of 5 is reached.

---

## Practical 5 — XML Web Graph and Topic-Specific PageRank

**Aim:** Parse an XML description of web pages, build the web graph and rank
pages using topic-specific (personalised) PageRank, where the random surfer
always restarts on a page of the chosen topic.

**Input:** `webgraph.xml`, topic = **sports** (topic pages: **B, C, D**).

**Web graph parsed from the XML**

| Page | Outgoing links | Topic page? |
|------|----------------|:-----------:|
| A | B, C | No |
| B | C, D | **Yes** |
| C | A | **Yes** |
| D | B, E | **Yes** |
| E | C | No |
| F | E, A | No |

**Topic-specific PageRank scores**

| Rank | Page | Score | Topic page? |
|------|------|-------|:-----------:|
| 1 | C | `0.3085` | **Yes** |
| 2 | A | `0.2622` | No |
| 3 | B | `0.2230` | **Yes** |
| 4 | D | `0.1448` | **Yes** |
| 5 | E | `0.0615` | No |
| 6 | F | `0.0000` | No |

**What the output shows:** The three sports pages (B, C, D) are highlighted as
topic pages. Because the teleport step always returns the surfer to a topic
page, those pages receive extra rank — C ranks first despite being one of three
topic pages. Page F has no incoming links and is not a topic page, so it ends
with a score of `0.0000`.

---

## Mini Project — Document Summarization System

**Aim:** Produce an extractive summary of a text document by selecting its most
important sentences using TF-IDF sentence scoring.

**Input:** `sample_document.txt` — 12 sentences, 187 words.

**Output**

```
==============================================================
                DOCUMENT SUMMARIZATION REPORT
==============================================================
 Document       : sample_document.txt
 Original size  : 12 sentences, 187 words
 Summary length : 3 sentences (25% of the document)

----------------------- SUMMARY -----------------------
 1. ISRO has successfully launched its latest communication satellite into orbit from the Sriharikota space centre.
 2. The satellite, named GSAT-25, was carried by the heaviest rocket built by ISRO.
 3. The ISRO chairman said the successful launch of the satellite is an important step for the country's space programme.

 Summary size   : 47 words
 Compression    : 74.9% smaller than the original
```

**Statistics (`--stats`)**

| Item | Value |
|------|-------|
| Top keywords | satellite (1.00), isro (0.75), launch (0.75), orbit (0.63), space (0.63), gsat (0.63), communication (0.47), centre (0.47), mission (0.47), internet (0.47) |
| Highest-scoring sentence | Sentence 1 (`0.582`) |
| Next best sentences | Sentence 2 (`0.534`), sentence 8 (`0.505`), sentence 4 (`0.488`), sentence 5 (`0.486`) |

**What the output shows:** The report states how large the original document is
and how much it was shortened. The three chosen sentences keep the main facts
(launch, satellite name, significance) in their original order. The summary is
47 words against 187 words, i.e. **74.9 % smaller**. The `--stats` view explains
the choice: "satellite" and "isro" carry the highest TF-IDF weights, and the
sentences containing them score best.

---

## Summary of Results

| Practical | Key result |
|-----------|------------|
| 1 — Document Similarity | Cosine similarity = **0.8820 (88.20 %)** → very similar |
| 2 — PageRank | Most important page = **C** (score `0.3941`) |
| 3 — Map-Reduce Character Count | **139** letters counted; `e` is most frequent (14) |
| 4 — Web Crawler | **5** pages visited from `https://quotes.toscrape.com/` |
| 5 — Topic PageRank | Top sports page = **C** (score `0.3085`) |
| Mini Project — Summarizer | 3-sentence summary, **74.9 %** compression |
