"""
Mini Project : Document Summarization System
=============================================
A command line tool that creates an extractive summary of a text document.
It picks the most important sentences of the document itself.

Algorithm (slightly optimized, still simple):
  1. Split the document into sentences.
  2. Remove common (stop) words and give every remaining word a TF-IDF
     weight - words that repeat a lot inside the document matter more,
     but words that appear in almost every sentence matter less.
  3. Score every sentence = average TF-IDF weight of its words, with a
     small bonus for sentences near the start of the document.
  4. Greedily pick the best sentences, skipping sentences that are too
     similar to ones already picked (removes repetition).
  5. Show the picked sentences in their original order.

Run 'python3 summarizer.py --help' to see all the options.
"""

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

VERSION = "2.0"
DEFAULT_DOCUMENT = Path(__file__).parent / "sample_document.txt"
DEFAULT_SENTENCES = 3
REDUNDANCY_LIMIT = 0.6          # two sentences are "too similar" above this
POSITION_BONUS = 0.15           # bonus for the first sentences of the document

# common words that carry no meaning for summarization
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to", "of",
    "for", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "it", "its", "this", "that", "these", "those", "as", "has", "have", "had",
    "not", "no", "so", "we", "you", "they", "he", "she", "his", "her", "will",
    "can", "also", "more", "most", "than", "then", "when", "where", "which",
    "who", "what", "how", "all", "any", "each", "few", "other", "some", "such",
    "only", "own", "same", "too", "very", "just", "do", "does", "did", "into",
    "over", "after", "before", "between", "out", "up", "down", "off", "again",
    "once", "here", "there", "about", "new",
}


# ----------------------------------------------------------------------
#  Text processing
# ----------------------------------------------------------------------

def split_sentences(text):
    """Split text into sentences. A new sentence starts after . ! ?
    followed by a space and a capital letter (or a quote)."""
    text = " ".join(text.split())                       # remove extra spaces
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", text)
    return [part.strip() for part in parts if part.strip()]


def clean_words(sentence):
    """Return the useful words of a sentence (lowercase, no stopwords)."""
    letters = "".join(char.lower() if char.isalpha() else " " for char in sentence)
    return [word for word in letters.split() if word not in STOPWORDS and len(word) > 1]


# ----------------------------------------------------------------------
#  Scoring (the optimized part)
# ----------------------------------------------------------------------

def word_weights(sentence_words):
    """TF-IDF weight of every word, normalized between 0 and 1.

    TF  = how often the word appears in the document.
    IDF = how rare the word is (appears in few sentences -> more important).
    A word that is in every sentence (like 'satellite' in a satellite news
    article) is common, and a word used often but not everywhere is a better
    keyword.
    """
    counts = Counter()                    # word -> how many times in total
    sentences_with_word = Counter()       # word -> in how many sentences

    for words in sentence_words:
        counts.update(words)
        sentences_with_word.update(set(words))     # set() -> count once per sentence

    if not counts:
        return {}

    most_common = max(counts.values())
    total_sentences = len(sentence_words)

    weights = {}
    for word, count in counts.items():
        term_frequency = count / most_common
        inverse_document_frequency = math.log((1 + total_sentences) /
                                              (1 + sentences_with_word[word])) + 1
        weights[word] = term_frequency * inverse_document_frequency

    highest = max(weights.values())
    return {word: value / highest for word, value in weights.items()}


def sentence_scores(sentence_words, weights):
    """Score every sentence = average word weight, plus a small bonus for
    sentences near the beginning (they often carry the main idea)."""
    scores = []
    total = len(sentence_words)

    for index, words in enumerate(sentence_words):
        if words:
            score = sum(weights.get(word, 0) for word in words) / len(words)
        else:
            score = 0
        position_bonus = 1 + POSITION_BONUS * (1 - index / max(total - 1, 1))
        scores.append(score * position_bonus)

    return scores


def similarity(first_words, second_words):
    """Jaccard similarity of two sentences (0 = different, 1 = same words)."""
    first, second = set(first_words), set(second_words)
    union = first | second
    return len(first & second) / len(union) if union else 0.0


def select_sentences(scores, sentence_words, number):
    """Pick the best scored sentences one by one. A sentence that is too
    similar to an already picked sentence is skipped, so the summary does
    not repeat the same information."""
    best_first = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    picked, skipped = [], []

    for index in best_first:
        if len(picked) == number:
            break
        too_similar = any(similarity(sentence_words[index], sentence_words[other]) > REDUNDANCY_LIMIT
                          for other in picked)
        (skipped if too_similar else picked).append(index)

    # if too many were skipped, fill the remaining places with the best skipped ones
    for index in skipped:
        if len(picked) == number:
            break
        picked.append(index)

    picked.sort()               # summary keeps the original order of sentences
    return picked


def summarize(text, number=None, ratio=None):
    """Run the whole summarization and return a result dictionary."""
    sentences = split_sentences(text)
    if not sentences:
        return {"sentences": [], "summary": [], "weights": {}, "scores": [], "number": 0}

    if number is None:
        number = DEFAULT_SENTENCES if ratio is None else max(1, round(len(sentences) * ratio))
    number = max(1, min(number, len(sentences)))

    sentence_words = [clean_words(sentence) for sentence in sentences]
    weights = word_weights(sentence_words)
    scores = sentence_scores(sentence_words, weights)
    picked = select_sentences(scores, sentence_words, number)

    return {
        "sentences": sentences,
        "summary": [sentences[index] for index in picked],
        "weights": weights,
        "scores": scores,
        "number": len(picked),
    }


# ----------------------------------------------------------------------
#  Output
# ----------------------------------------------------------------------

def print_report(document, result, show_stats):
    """Print a nicely formatted report of the summary."""
    sentences = result["sentences"]
    summary = result["summary"]
    words = len(" ".join(sentences).split())
    summary_words = len(" ".join(summary).split())
    compression = (1 - summary_words / words) * 100 if words else 0

    print("=" * 62)
    print("                DOCUMENT SUMMARIZATION REPORT")
    print("=" * 62)
    print(f" Document       : {document.name}")
    print(f" Original size  : {len(sentences)} sentences, {words} words")
    print(f" Summary length : {len(summary)} sentences "
          f"({len(summary) / len(sentences) * 100:.0f}% of the document)")

    print("\n----------------------- SUMMARY -----------------------")
    for i, sentence in enumerate(summary, 1):
        print(f" {i}. {sentence}")

    print(f"\n Summary size   : {summary_words} words")
    print(f" Compression    : {compression:.1f}% smaller than the original")

    if show_stats:
        print("\n------------------------ STATS ------------------------")
        top_keywords = sorted(result["weights"].items(), key=lambda item: item[1], reverse=True)
        top_keywords = [f"{word} ({weight:.2f})" for word, weight in top_keywords[:10]]
        print(" Top keywords   :", ", ".join(top_keywords))
        print(" Sentence scores (higher = more important):")
        ranked = sorted(enumerate(result["scores"], 1), key=lambda item: item[1], reverse=True)
        for number, score in ranked[:5]:
            print(f"   sentence {number:>2} : {score:.3f}")


# ----------------------------------------------------------------------
#  Command line interface
# ----------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="summarizer",
        description="Document Summarization System - makes an extractive summary "
                    "of a text file (TF-IDF based).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 summarizer.py                        summarize the sample document\n"
            "  python3 summarizer.py article.txt            summarize your own file\n"
            "  python3 summarizer.py article.txt -n 5       summary of 5 sentences\n"
            "  python3 summarizer.py article.txt -r 0.3     summary = 30% of the sentences\n"
            "  python3 summarizer.py article.txt -o out.txt save the summary to a file\n"
            "  python3 summarizer.py article.txt -q         print only the summary text\n"
            "  python3 summarizer.py article.txt --stats    show keywords and scores\n"
        ),
    )
    parser.add_argument("file", nargs="?", default=str(DEFAULT_DOCUMENT), metavar="FILE",
                        help="text file to summarize (default: sample_document.txt)")
    size = parser.add_mutually_exclusive_group()
    size.add_argument("-n", "--sentences", type=int, metavar="N",
                      help=f"number of sentences in the summary (default: {DEFAULT_SENTENCES})")
    size.add_argument("-r", "--ratio", type=float, metavar="R",
                      help="summary size as a fraction of the document, e.g. 0.3")
    parser.add_argument("-o", "--output", metavar="FILE",
                        help="also save the summary to this file")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="print only the summary sentences (no report)")
    parser.add_argument("-s", "--stats", action="store_true",
                        help="show top keywords and sentence scores")
    parser.add_argument("--version", action="version", version=f"Document Summarizer {VERSION}")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.sentences is not None and args.sentences < 1:
        parser.error("--sentences must be 1 or more")
    if args.ratio is not None and not 0 < args.ratio <= 1:
        parser.error("--ratio must be between 0 and 1 (e.g. 0.3)")

    document = Path(args.file)
    if not document.is_file():
        sys.exit(f"error: file not found: {document}")

    try:
        text = document.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        sys.exit(f"error: could not read {document}: {error}")

    result = summarize(text, number=args.sentences, ratio=args.ratio)
    if not result["summary"]:
        sys.exit("error: the document has no text to summarize")

    if args.quiet:
        print("\n".join(result["summary"]))
    else:
        print_report(document, result, args.stats)

    if args.output:
        Path(args.output).write_text("\n".join(result["summary"]) + "\n", encoding="utf-8")
        print(f"Summary saved to: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
