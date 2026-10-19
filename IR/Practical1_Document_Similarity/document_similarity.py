"""
Practical 1 : Compute similarity between two text documents
Aim         : Read two documents and find how similar they are using
              cosine similarity of word frequencies.
"""

import math
from collections import Counter
from pathlib import Path

DOC1 = Path(__file__).parent / "doc1.txt"
DOC2 = Path(__file__).parent / "doc2.txt"


def words_in(document):
    """Return the list of words in a document (lowercase, punctuation removed)."""
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in document)
    return cleaned.split()


def cosine_similarity(count1, count2):
    """Cosine similarity between two word-count dictionaries."""
    common_words = set(count1) & set(count2)      # words present in both documents

    dot_product = sum(count1[word] * count2[word] for word in common_words)
    length1 = math.sqrt(sum(count * count for count in count1.values()))
    length2 = math.sqrt(sum(count * count for count in count2.values()))

    if length1 == 0 or length2 == 0:
        return 0.0
    return dot_product / (length1 * length2)


def main():
    words1 = words_in(DOC1.read_text())
    words2 = words_in(DOC2.read_text())

    count1 = Counter(words1)      # word -> how many times it appears
    count2 = Counter(words2)

    similarity = cosine_similarity(count1, count2)

    print("Document 1 :", DOC1.name, "-", len(words1), "words")
    print("Document 2 :", DOC2.name, "-", len(words2), "words")
    print(f"\nCosine similarity = {similarity:.4f}  ({similarity * 100:.2f} %)")

    if similarity > 0.8:
        print("Result: the two documents are very similar")
    elif similarity > 0.4:
        print("Result: the two documents are somewhat similar")
    else:
        print("Result: the two documents are different")


if __name__ == "__main__":
    main()
