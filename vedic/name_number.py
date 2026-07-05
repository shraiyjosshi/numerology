#!/usr/bin/env python3
"""Compute a name's numerology number using the Vedic letter chart."""

from __future__ import annotations

import argparse
import sys


LETTER_VALUES: dict[str, int] = {
    "A": 1, "B": 2, "C": 2, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 6, "Y": 1, "Z": 7,
}


def letter_breakdown(name: str) -> list[tuple[str, int]]:
    return [(c, LETTER_VALUES[c]) for c in name.upper() if c in LETTER_VALUES]


def reduce_to_root(n: int) -> int:
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def name_number(name: str) -> tuple[int, int, list[tuple[str, int]]]:
    pairs = letter_breakdown(name)
    total = sum(v for _, v in pairs)
    return total, reduce_to_root(total), pairs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("name", nargs="+", help="Name to score (one or more words)")
    p.add_argument("--quiet", "-q", action="store_true",
                   help="Print only the reduced single-digit number")
    args = p.parse_args()

    words = [w for arg in args.name for w in arg.split()]
    full = " ".join(words)
    total, root, _ = name_number(full)

    if args.quiet:
        print(root)
        return 0

    print(f"Name:  {full}")
    for word in words:
        w_total, w_root, w_pairs = name_number(word)
        letters = " ".join(f"{c}({v})" for c, v in w_pairs)
        print(f"  {word}: {letters}  sum={w_total}  root={w_root}")
    print(f"Total: {total}")
    print(f"Root:  {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
