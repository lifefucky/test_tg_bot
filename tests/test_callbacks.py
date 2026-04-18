"""Pure callback parsing (no Bot / aiogram)."""

import pytest

from utils.callbacks import parse_pagination_callback


def test_parse_pagination_callback_ok():
    offset, cat = parse_pagination_callback("m|7|1811,1817")
    assert offset == 7
    assert cat == "1811,1817"


def test_parse_pagination_callback_bad_input():
    with pytest.raises((ValueError, IndexError)):
        parse_pagination_callback("not-m-format")
