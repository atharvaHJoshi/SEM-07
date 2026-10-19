# Mini Project : Document Summarization System

**Subject:** Information Retrieval (410245 A) — Group 2 Mini Project

A command line (CLI) tool that reads a text document and automatically produces
a short summary of its most important sentences.

## Aim

Develop a document summarization system that creates an extractive summary —
it picks the most important sentences from the document itself. New sentences
are not written (writing new sentences is called abstractive summarization,
which is a separate mini-project).

## Features

- Command line interface with options (`-n`, `-r`, `-o`, `-q`, `--stats`)
- **TF-IDF based sentence scoring** — better than plain word counting
- Position bonus — the first sentences of a document often carry the main idea
- **Redundancy removal** — a sentence that repeats an already picked sentence
  is skipped (Jaccard similarity check)
- Save the summary to a file and print a clean report
- Clear error messages for missing files or wrong options

## How it works

1. The document is split into sentences.
2. Common words ("the", "is", ...) are removed and every remaining word gets a
   **TF-IDF weight**: words that repeat a lot inside the document matter more,
   but words that appear in almost every sentence matter less.
3. Every sentence is scored by the **average TF-IDF weight** of its words,
   with a small bonus for sentences near the start of the document.
4. The best sentences are picked one by one; a sentence that is too similar
   to an already picked sentence is skipped (so the summary has less repetition).
5. The picked sentences are printed in their original order.

## Files

| File | Purpose |
|------|---------|
| `summarizer.py` | the summarization system (CLI + algorithm) |
| `sample_document.txt` | a sample news article used for the demo |

## Usage

```bash
python3 summarizer.py                        # summarize the sample document
python3 summarizer.py article.txt            # summarize your own file
python3 summarizer.py article.txt -n 5       # summary of 5 sentences
python3 summarizer.py article.txt -r 0.3     # summary = 30% of the sentences
python3 summarizer.py article.txt -o out.txt # save the summary to a file
python3 summarizer.py article.txt -q         # print only the summary text
python3 summarizer.py article.txt --stats    # show keywords and scores
python3 summarizer.py --help                 # full help
```

| Option | Meaning |
|--------|---------|
| `FILE` | text file to summarize (default: `sample_document.txt`) |
| `-n, --sentences N` | number of sentences in the summary (default: 3) |
| `-r, --ratio R` | summary size as a fraction of the document, e.g. `0.3` |
| `-o, --output FILE` | also save the summary to this file |
| `-q, --quiet` | print only the summary sentences (good for piping) |
| `-s, --stats` | show top keywords and sentence scores |
| `--version` | show the version |

## Sample output

```
 Document       : sample_document.txt
 Original size  : 12 sentences, 187 words
 Summary length : 3 sentences (25% of the document)

----------------------- SUMMARY -----------------------
 1. ISRO has successfully launched its latest communication satellite into
    orbit from the Sriharikota space centre.
 2. The satellite, named GSAT-25, was carried by the heaviest rocket built
    by ISRO.
 3. The ISRO chairman said the successful launch of the satellite is an
    important step for the country's space programme.

 Summary size   : 47 words
 Compression    : 74.9% smaller than the original
```

With `--stats` it also shows the top keywords
(`satellite (1.00), isro (0.75), launch (0.75), orbit (0.63), ...`)
and the score of every sentence.

## Future scope

- Use word stemming so "satellite" and "satellites" count as one word.
- Add a bigger stopword list or support other languages.
- Support PDF or Word documents as input.
- Add a graphical interface (window instead of command line).
