from unittest import mock

import pytest

import argparse

from src.symbol_counter import count_symbols, get_sentence


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", 0),
        ("aaaa", 0),
        ("aabbc", 1),
        ("test", 2),
        ("abcd", 4),
    ],
)
def test_count_symbols(value, expected):
    assert count_symbols(value) == expected

def test_cache():
    count_symbols.cache_clear()

    count_symbols("a")
    info = count_symbols.cache_info()
    assert info.hits == 0
    assert info.misses == 1
    assert info.currsize == 1

    count_symbols("a")
    info = count_symbols.cache_info()
    assert info.hits == 1
    assert info.misses == 1
    assert info.currsize == 1

    count_symbols("b")
    info = count_symbols.cache_info()
    assert info.hits == 1
    assert info.misses == 2
    assert info.currsize == 2


def test_get_sentence_from_string():
    args = argparse.Namespace(string="asd", file=None)
    assert get_sentence(args) == "asd"


def test_get_sentence_from_file_overrides_string():
    with mock.patch("builtins.open", mock.mock_open(read_data="from-file")):
        args = argparse.Namespace(string="ignored", file="mocked.txt")
        assert get_sentence(args) == "from-file"
