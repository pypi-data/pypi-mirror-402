"""Tests for the core logic of the 32word library."""

import pytest
from word32.core import generate_clue, filter_targets, is_valid_word, get_remaining_candidates

@pytest.mark.parametrize("guess, target, expected_clue", [
    ("AAAAA", "BBBBB", ("B", "B", "B", "B", "B")),
    ("AAAAA", "ABCDE", ("G", "B", "B", "B", "B")),
    ("ABCDE", "AAAAA", ("G", "B", "B", "B", "B")),
    ("STARE", "TRASH", ("Y", "Y", "G", "Y", "B")), # Corrected expected clue
    ("ADIEU", "ADIEU", ("G", "G", "G", "G", "G")),
    ("SALET", "POPPY", ("B", "B", "B", "B", "B")),
    ("GEESE", "EERIE", ("B", "G", "Y", "B", "G")), # Corrected expected clue
    ("LEVEL", "VALID", ("Y", "B", "Y", "B", "B")), # Corrected expected clue
    ("TESTS", "START", ("Y", "B", "Y", "Y", "B")), # Corrected expected clue
])
def test_generate_clue(guess, target, expected_clue):
    assert generate_clue(guess, target) == expected_clue

def test_filter_targets():
    targets = ["APPLE", "APPLY", "APTLY", "HAPPY"]
    guess = "APPLY"
    clue = ("G", "G", "B", "B", "G") # Clue for APPLY against APPLE
    
    # The only word that should match is APPLE
    # Let me re-check this.
    # A P P L E
    # A P P L Y
    # G G G G B is the clue for APPLY against APPLE.
    # My test case was wrong.

    clue = ("G", "G", "G", "G", "B") # Clue for APPLE vs APPLY
    filtered = filter_targets(targets, "APPLE", clue)
    # The only word that when guessed with "APPLE" gives clue "GGGBB" should be "APPLY"
    # No, that's not right. The function is filter_targets(targets, guess, clue)
    # The guess is "APPLY", the clue is what wordle returns.
    # So I need to simulate wordle. Let's say the target is "APTLY".
    # guess = "APPLY", target = "APTLY" -> clue = ('G', 'G', 'B', 'Y', 'G')
    
    targets = ["APPLE", "APPLY", "APTLY", "HAPPY"]
    guess = "APPLY"
    # Let's assume the true target is "APTLY"
    # Then the clue would be:
    # A -> G
    # P -> G
    # P -> B
    # L -> Y
    # Y -> G
    # clue = ('G', 'G', 'B', 'Y', 'G')
    
    # This is not how filter_targets works.
    # filter_targets takes a list of *potential* targets, a guess that was made, and the clue that was returned.
    # It then returns which of the potential targets are still possible.
    
    # Let's try again.
    # Potential targets are ["APPLE", "APPLY", "APTLY", "HAPPY"]
    # We guess "HAPPY". Wordle returns a clue.
    # Let's say the actual target is "APPLE"
    # `generate_clue("HAPPY", "APPLE")` -> ('B', 'Y', 'G', 'B', 'B')
    
    # Now we filter with that clue.
    # `filter_targets(targets, "HAPPY", ('B', 'Y', 'G', 'B', 'B'))`
    # This should return ["APPLE"]
    
    guess = "HAPPY"
    clue_from_apple = generate_clue(guess, "APPLE") # ('B', 'Y', 'G', 'B', 'B')
    
    filtered = filter_targets(targets, guess, clue_from_apple)
    assert filtered == ["APPLE"]

    # Another one.
    # targets = ["BOOST", "ROAST", "COAST"]
    # guess = "ROAST", target = "COAST" -> clue = ('B', 'G', 'G', 'G', 'G')
    targets = ["BOOST", "ROAST", "COAST"]
    guess = "ROAST"
    clue_from_coast = generate_clue(guess, "COAST") # ('B', 'G', 'G', 'G', 'G')
    filtered = filter_targets(targets, guess, clue_from_coast)
    assert filtered == ["COAST"]
    
    # And if the guess was the actual target
    targets = ["BOOST", "ROAST", "COAST"]
    guess = "ROAST"
    clue_from_roast = generate_clue(guess, "ROAST") # ('G', 'G', 'G', 'G', 'G')
    filtered = filter_targets(targets, guess, clue_from_roast)
    assert filtered == ["ROAST"]


def test_is_valid_word():
    """Test word validation against valid guesses."""
    # Valid words should return True
    assert is_valid_word("STARE") is True
    assert is_valid_word("stare") is True  # case insensitive
    assert is_valid_word("ADIEU") is True

    # Invalid words should return False
    assert is_valid_word("XXXXX") is False
    assert is_valid_word("ABCDE") is False  # likely not a valid Wordle word
    assert is_valid_word("TEST") is False  # too short


def test_get_remaining_candidates():
    """Test counting remaining candidates after a guess."""
    targets = ["APPLE", "APPLY", "APTLY", "HAPPY", "HARPY"]

    # Test filtering with HAPPY -> APPLE clue
    guess = "HAPPY"
    clue = generate_clue(guess, "APPLE")
    remaining = get_remaining_candidates(targets, guess, clue)
    assert remaining == 1  # Only APPLE matches

    # Test filtering with HAPPY -> HARPY clue
    clue = generate_clue(guess, "HARPY")
    remaining = get_remaining_candidates(targets, guess, clue)
    assert remaining == 1  # Only HARPY matches

    # Test all blacks clue
    clue = ("B", "B", "B", "B", "B")
    remaining = get_remaining_candidates(targets, "ZZZZZ", clue)
    assert remaining == len(targets)  # All should remain if no letters match
