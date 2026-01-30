import argparse

from .core import count_symbols, get_sentence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Count unique symbols.")
    parser.add_argument("--string", type=str)
    parser.add_argument("--file", type=str)
    return parser


def main() -> None:
    parser = build_parser()
    print(count_symbols(get_sentence(parser.parse_args())))
