"""Tests for the strategy functions of the 32word library."""

from word32.strategy import load_strategy, get_second_guess, Strategy

def test_load_strategy():
    strategy = load_strategy("v1.0")
    assert isinstance(strategy, Strategy)
    assert strategy.version == "v1.0"
    assert strategy.first_guess() == "ATONE"

def test_get_second_guess():
    strategy = load_strategy()
    # Test with a valid clue pattern from ATONE: all black (XXXXX -> no letters match)
    clue = ('B', 'B', 'B', 'B', 'B')
    second_guess = get_second_guess(strategy, clue)
    assert isinstance(second_guess, str)
    assert len(second_guess) == 5
    assert second_guess.upper() == "PIRLS"

    # Test with another clue pattern: last letter green (XXXXG)
    clue = ('B', 'B', 'B', 'B', 'G')
    second_guess = strategy.second_guess(clue)
    assert isinstance(second_guess, str)
    assert second_guess.upper() == "GERLE"

def test_strategy_metadata():
    strategy = load_strategy()
    metadata = strategy.metadata()
    assert isinstance(metadata, dict)
    assert metadata['version'] == 'v1.0'
    assert 'description' in metadata
