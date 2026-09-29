#!/usr/bin/env python3
"""
test_extract.py - Unit tests for extract.py data processing functions.
Run using: pytest scripts/test_extract.py
"""

from scripts.extract import clean_currency_val


def test_clean_currency_val_standard():
    assert clean_currency_val("12,50,000") == 1250000.0
    assert clean_currency_val("₹ 5,00,000") == 500000.0


def test_clean_currency_val_numeric():
    assert clean_currency_val(1000) == 1000.0
    assert clean_currency_val(4500.50) == 4500.50


def test_clean_currency_val_empty_or_invalid():
    assert clean_currency_val(None) == 0.0
    assert clean_currency_val("N/A") == 0.0