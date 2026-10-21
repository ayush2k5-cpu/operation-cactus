import base64
import os

from covertrace.entropy import shannon_entropy


def test_repeated_char_is_zero():
    assert shannon_entropy("aaaa") == 0.0


def test_two_symbols_is_one_bit():
    assert shannon_entropy("ab") == 1.0


def test_four_symbols_is_two_bits():
    assert shannon_entropy("abcd") == 2.0


def test_random_base32_is_high():
    label = base64.b32encode(os.urandom(24)).decode().lower()[:32]
    assert len(label) == 32
    assert shannon_entropy(label) > 3.5
