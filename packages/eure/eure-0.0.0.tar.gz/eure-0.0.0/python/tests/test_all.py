import pytest
import eure


def test_sum_as_string():
    assert eure.sum_as_string(1, 1) == "2"
