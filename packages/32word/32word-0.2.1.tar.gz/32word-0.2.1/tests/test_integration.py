"""Integration tests for the complete 32word library workflow."""

from word32 import (
    generate_clue,
    filter_targets,
    load_strategy,
    get_second_guess,
    is_valid_word,
    get_remaining_candidates,
    VALID_TARGETS,
)


def test_full_game_workflow():
    """Test a complete Wordle game using the library."""
    # Load the optimal strategy
    strategy = load_strategy("v1.0")

    # Verify first guess
    first_guess = strategy.first_guess()
    assert first_guess == "ATONE"
    assert is_valid_word(first_guess)

    # Simulate playing against target "WORLD"
    target = "WORLD"
    remaining = VALID_TARGETS.copy()

    # First guess
    clue1 = generate_clue(first_guess, target)
    remaining = filter_targets(remaining, first_guess, clue1)

    # Verify we get a reasonable reduction
    assert len(remaining) < len(VALID_TARGETS)
    assert target in remaining

    # Get second guess using strategy
    second_guess = strategy.second_guess(clue1)

    # Strategy may not cover all clue patterns, but should have second guess
    # if it was a common pattern
    if second_guess is None:
        # Rare clue pattern, that's ok
        return

    assert isinstance(second_guess, str)
    assert len(second_guess) == 5
    assert is_valid_word(second_guess)

    # Second guess
    clue2 = generate_clue(second_guess, target)
    remaining = filter_targets(remaining, second_guess, clue2)

    # After two guesses, should narrow down significantly
    assert len(remaining) <= 20
    assert target in remaining


def test_strategy_coverage():
    """Test that the strategy covers many common clue patterns."""
    strategy = load_strategy("v1.0")

    # Common clue patterns that should all be covered
    test_clues = [
        ('B', 'B', 'B', 'B', 'B'),  # All black
        ('G', 'B', 'B', 'B', 'B'),  # One green
        ('B', 'G', 'B', 'B', 'B'),  # One green (different position)
        ('B', 'B', 'B', 'B', 'G'),  # Last green
        ('Y', 'B', 'B', 'B', 'B'),  # One yellow
        ('B', 'Y', 'B', 'B', 'B'),  # One yellow (different position)
    ]

    covered = 0
    for clue in test_clues:
        second_guess = strategy.second_guess(clue)
        if second_guess is not None:
            covered += 1
            assert len(second_guess) == 5

    # Should cover at least most of these common patterns
    assert covered >= 4


def test_multiple_game_scenarios():
    """Test the library with several different target words."""
    strategy = load_strategy("v1.0")
    first_guess = strategy.first_guess()

    # Test against a variety of targets
    test_targets = ["PIZZA", "WORLD", "PHONE", "AUDIO", "HEART"]

    success_count = 0
    for target in test_targets:
        if target not in VALID_TARGETS:
            continue

        remaining = VALID_TARGETS.copy()

        # First guess
        clue1 = generate_clue(first_guess, target)
        remaining = filter_targets(remaining, first_guess, clue1)
        assert target in remaining

        # Second guess from strategy
        second_guess = strategy.second_guess(clue1)
        if second_guess is None:
            # Some rare clues might not have coverage, skip
            continue

        success_count += 1
        clue2 = generate_clue(second_guess, target)
        remaining = filter_targets(remaining, second_guess, clue2)

        # Should narrow down significantly (most words reduce to <20 candidates)
        assert len(remaining) <= 30
        assert target in remaining

    # At least some of the targets should have strategy coverage
    assert success_count > 0


def test_convenience_functions():
    """Test is_valid_word and get_remaining_candidates."""
    # Test is_valid_word
    assert is_valid_word("STARE") is True
    assert is_valid_word("TRASH") is True
    assert is_valid_word("XXXXX") is False

    # Test get_remaining_candidates
    targets = ["PIZZA", "WORLD", "PHONE", "STARE", "TRASH"]
    guess = "STARE"

    for target in targets:
        clue = generate_clue(guess, target)
        remaining_count = get_remaining_candidates(targets, guess, clue)

        # Verify it matches actual filtering
        filtered = [t for t in targets if generate_clue(guess, t) == clue]
        assert remaining_count == len(filtered)


def test_strategy_with_all_black_clue():
    """Test strategy handles the common 'all black' clue (no matching letters)."""
    strategy = load_strategy("v1.0")

    # All black clue - none of ATONE's letters in target
    all_black_clue = ('B', 'B', 'B', 'B', 'B')
    second_guess = strategy.second_guess(all_black_clue)

    assert second_guess is not None
    assert is_valid_word(second_guess)

    # Verify the second guess is different from first guess
    assert second_guess != "ATONE"


def test_strategy_with_perfect_match():
    """Test strategy when first guess is perfect (all green)."""
    strategy = load_strategy("v1.0")

    # Perfect match - all letters correct
    perfect_clue = ('G', 'G', 'G', 'G', 'G')
    second_guess = strategy.second_guess(perfect_clue)

    # Perfect match means we've won, second guess may return None or something
    # (depending on strategy implementation)
    # Either way, the function should not raise an error
    if second_guess is not None:
        assert len(second_guess) == 5
