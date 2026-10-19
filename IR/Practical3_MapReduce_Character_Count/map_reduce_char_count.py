"""
Practical 3 : Map-Reduce program to count each alphabetic character
Aim         : Count how many times each letter (A-Z, a-z) appears in a
              dataset. Counting is case-insensitive and non-alphabetic
              characters are ignored. The Map-Reduce steps are shown in
              Python so no Hadoop setup is needed.
"""

from collections import defaultdict
from pathlib import Path

DATASET = Path(__file__).parent / "dataset.txt"


# ---------------- MAP PHASE ----------------
def mapper(line):
    """Break a line into (letter, 1) pairs. Ignore non-letters, lowercase them."""
    for char in line:
        if char.isalpha():
            yield char.lower(), 1


# ---------------- SHUFFLE PHASE ----------------
def shuffle(mapped_pairs):
    """Group all values that have the same key."""
    grouped = defaultdict(list)
    for key, value in mapped_pairs:
        grouped[key].append(value)
    return grouped


# ---------------- REDUCE PHASE ----------------
def reducer(key, values):
    """Add the 1's for one letter."""
    return key, sum(values)


def main():
    lines = DATASET.read_text().splitlines()

    # Map : each line -> list of (letter, 1)
    mapped = []
    for line in lines:
        mapped.extend(mapper(line))

    # Shuffle : (letter, 1) pairs -> letter -> [1, 1, 1, ...]
    grouped = shuffle(mapped)

    # Reduce : total count for every letter
    counts = {}
    for key, values in sorted(grouped.items()):
        letter, count = reducer(key, values)
        counts[letter] = count

    print("Alphabetic character count (case-insensitive):")
    for letter, count in counts.items():
        print(f"  {letter} : {count}")

    print("\nTotal letters:", sum(counts.values()))


if __name__ == "__main__":
    main()
