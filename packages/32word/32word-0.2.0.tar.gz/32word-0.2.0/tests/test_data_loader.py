"""Tests for the data loading functions of the 32word library."""

from word32.data_loader import load_targets, load_valid_guesses, VALID_TARGETS, VALID_GUESSES

def test_load_targets():
    targets = load_targets()
    assert isinstance(targets, list)
    assert len(targets) > 2000  # Should be 2309
    assert all(isinstance(word, str) for word in targets)
    assert all(len(word) == 5 for word in targets)
    assert all(word.isupper() for word in targets)

def test_load_valid_guesses():
    guesses = load_valid_guesses()
    assert isinstance(guesses, list)
    assert len(guesses) > 12000  # Should be around 12950
    assert all(isinstance(word, str) for word in guesses)
    assert all(len(word) == 5 for word in guesses)
    assert all(word.isupper() for word in guesses)

def test_preloaded_lists():
    assert isinstance(VALID_TARGETS, list)
    assert len(VALID_TARGETS) > 2000
    assert isinstance(VALID_GUESSES, list)
    assert len(VALID_GUESSES) > 12000

def test_targets_are_subset_of_guesses():
    target_set = set(VALID_TARGETS)
    guess_set = set(VALID_GUESSES)
    assert target_set.issubset(guess_set)
