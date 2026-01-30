from collections import Counter
from functools import lru_cache
import argparse


@lru_cache(maxsize=16)
def count_symbols(sentence: str) -> int:
    c = Counter(sentence)
    return sum(1 for value in c.values() if value == 1)


def get_sentence(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            return handle.read()
    if args.string is not None:
        return args.string
    raise ValueError("Either --string or --file is required.")
