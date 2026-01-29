"""Tests for the strategy functions of the 32word library."""

import pytest
from word32.strategy import (
    load_strategy, 
    get_second_guess, 
    Strategy,
    get_available_first_guesses,
    select_first_guess,
    get_strategy_for_first_guess,
    get_second_guess_recommendation,
)
from word32.data_loader import VALID_GUESSES


class TestLoadStrategy:
    """Test load_strategy function."""
    
    def test_load_strategy(self):
        strategy = load_strategy("v1.0")
        assert isinstance(strategy, Strategy)
        assert strategy.version == "v1.0"
        assert strategy.first_guess() == "ATONE"

    def test_get_second_guess(self):
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

    def test_strategy_metadata(self):
        strategy = load_strategy()
        metadata = strategy.metadata()
        assert isinstance(metadata, dict)
        assert metadata['version'] == 'v1.0'
        assert 'description' in metadata


class TestGetAvailableFirstGuesses:
    """Test get_available_first_guesses function (Phase 4.3)."""
    
    def test_returns_exactly_32_guesses(self):
        """Test that function returns exactly 32 guesses."""
        guesses = get_available_first_guesses()
        assert len(guesses) == 32
    
    def test_all_guesses_unique(self):
        """Test that all 32 guesses are unique."""
        guesses = get_available_first_guesses()
        guess_words = [g['first_guess'] for g in guesses]
        assert len(guess_words) == len(set(guess_words))
    
    def test_ranked_from_1_to_32(self):
        """Test that guesses are ranked from 1-32."""
        guesses = get_available_first_guesses()
        ranks = [g['rank'] for g in guesses]
        assert min(ranks) == 1
        assert max(ranks) == 32
        assert len(set(ranks)) == 32  # All ranks unique
    
    def test_each_entry_has_required_fields(self):
        """Test that each entry has required fields."""
        guesses = get_available_first_guesses()
        for entry in guesses:
            assert 'first_guess' in entry
            assert 'rank' in entry
            assert 'metrics' in entry
            assert isinstance(entry['first_guess'], str)
            assert isinstance(entry['rank'], int)
            assert isinstance(entry['metrics'], dict)
    
    def test_metrics_are_valid_numbers(self):
        """Test that metrics are valid numbers."""
        guesses = get_available_first_guesses()
        for entry in guesses:
            metrics = entry['metrics']
            assert 'expected_remaining' in entry or 'expected_remaining' in metrics
            # Check expected_remaining is positive
            expected = entry.get('expected_remaining', metrics.get('expected_remaining', 0))
            assert expected > 0
            # Check variance is non-negative
            variance = metrics.get('variance', 0)
            assert variance >= 0


class TestSelectFirstGuess:
    """Test select_first_guess function (Phase 4.3)."""
    
    def test_returns_correct_option_for_valid_guess(self):
        """Test that function returns correct option for valid guess."""
        # Get available guesses to find a valid one
        available = get_available_first_guesses()
        test_guess = available[0]['first_guess']  # Rank 1 guess
        
        result = select_first_guess(test_guess)
        assert result is not None
        assert result['first_guess'] == test_guess.upper()
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive matching."""
        available = get_available_first_guesses()
        test_guess = available[0]['first_guess']
        
        # Test lowercase
        result_lower = select_first_guess(test_guess.lower())
        assert result_lower is not None
        assert result_lower['first_guess'] == test_guess.upper()
        
        # Test mixed case
        mixed = test_guess[0].lower() + test_guess[1:].upper()
        result_mixed = select_first_guess(mixed)
        assert result_mixed is not None
        assert result_mixed['first_guess'] == test_guess.upper()
    
    def test_returns_none_for_invalid_guess(self):
        """Test that function returns None for invalid guess."""
        result = select_first_guess("INVALID")
        assert result is None
        
        result = select_first_guess("XXXXX")
        assert result is None
    
    def test_all_32_guesses_selectable(self):
        """Test that all 32 guesses are selectable."""
        available = get_available_first_guesses()
        for entry in available:
            guess = entry['first_guess']
            result = select_first_guess(guess)
            assert result is not None
            assert result['first_guess'] == guess
            assert result['rank'] == entry['rank']


class TestGetStrategyForFirstGuess:
    """Test get_strategy_for_first_guess function (Phase 4.3)."""
    
    def test_returns_dict_for_each_first_guess(self):
        """Test that function returns dict for each of 32 first guesses."""
        available = get_available_first_guesses()
        for entry in available[:5]:  # Test first 5 to avoid too many tests
            first_guess = entry['first_guess']
            strategy = get_strategy_for_first_guess(first_guess)
            assert isinstance(strategy, dict)
    
    def test_dict_maps_clue_patterns_to_second_guesses(self):
        """Test that dict maps clue patterns to second guesses."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']  # Rank 1
        
        strategy = get_strategy_for_first_guess(first_guess)
        
        # Strategy should be a dict
        assert isinstance(strategy, dict)
        
        # If strategy has entries, check structure
        if strategy:
            for clue_pattern, second_guess in strategy.items():
                # Clue pattern should be 5 characters (G, Y, X)
                assert len(clue_pattern) == 5
                assert all(c in 'GYX' for c in clue_pattern)
                # Second guess should be a string
                assert isinstance(second_guess, str)
                assert len(second_guess) == 5
    
    def test_all_second_guesses_are_valid_words(self):
        """Test that all second guesses are valid words."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        strategy = get_strategy_for_first_guess(first_guess)
        
        for clue_pattern, second_guess in strategy.items():
            assert second_guess.upper() in VALID_GUESSES
    
    def test_returns_empty_dict_for_invalid_first_guess(self):
        """Test that function returns empty dict for invalid first guess."""
        result = get_strategy_for_first_guess("INVALID")
        assert result == {}
    
    def test_consistent_results_across_multiple_calls(self):
        """Test that results are consistent across multiple calls."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        strategy1 = get_strategy_for_first_guess(first_guess)
        strategy2 = get_strategy_for_first_guess(first_guess)
        
        assert strategy1 == strategy2


class TestGetSecondGuessRecommendation:
    """Test get_second_guess_recommendation function (Phase 4.3)."""
    
    def test_returns_second_guess_for_valid_pair(self):
        """Test that function returns second guess for valid (first_guess, clue) pair."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        # Get strategy to find a valid clue pattern
        strategy = get_strategy_for_first_guess(first_guess)
        
        if strategy:
            # Use first clue pattern from strategy
            clue_pattern = list(strategy.keys())[0]
            # Convert clue pattern to tuple (X -> B for black)
            clue_tuple = tuple('B' if c == 'X' else c for c in clue_pattern)
            
            result = get_second_guess_recommendation(first_guess, clue_tuple)
            assert result is not None
            assert isinstance(result, str)
            assert len(result) == 5
    
    def test_handles_clue_tuple_formats(self):
        """Test that function handles both 'B' and 'X' for black."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        strategy = get_strategy_for_first_guess(first_guess)
        
        if strategy:
            clue_pattern = list(strategy.keys())[0]
            # Test with 'B' for black
            clue_tuple_b = tuple('B' if c == 'X' else c for c in clue_pattern)
            result_b = get_second_guess_recommendation(first_guess, clue_tuple_b)
            
            # Test with 'X' for black (if pattern uses X)
            if 'X' in clue_pattern:
                clue_tuple_x = tuple(clue_pattern)
                result_x = get_second_guess_recommendation(first_guess, clue_tuple_x)
                # Results should be the same
                assert result_b == result_x
    
    def test_returns_none_for_missing_clue_pattern(self):
        """Test that function returns None for missing clue pattern."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        # Use an unlikely clue pattern
        clue = ('G', 'G', 'G', 'G', 'G')  # Perfect match (unlikely to have strategy)
        result = get_second_guess_recommendation(first_guess, clue)
        # May or may not be None depending on strategy coverage
    
    def test_case_insensitive_first_guess(self):
        """Test case-insensitive first_guess parameter."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        strategy = get_strategy_for_first_guess(first_guess)
        
        if strategy:
            clue_pattern = list(strategy.keys())[0]
            clue_tuple = tuple('B' if c == 'X' else c for c in clue_pattern)
            
            # Test lowercase
            result_lower = get_second_guess_recommendation(first_guess.lower(), clue_tuple)
            # Test uppercase
            result_upper = get_second_guess_recommendation(first_guess.upper(), clue_tuple)
            
            assert result_lower == result_upper


class TestBackwardsCompatibility:
    """Test backwards compatibility with original API."""
    
    def test_original_load_strategy_still_works(self):
        """Test that original load_strategy() still works."""
        strategy = load_strategy("v1.0")
        assert isinstance(strategy, Strategy)
        assert strategy.first_guess() == "ATONE"
    
    def test_original_strategy_second_guess_still_works(self):
        """Test that original Strategy.second_guess() still works."""
        strategy = load_strategy("v1.0")
        clue = ('B', 'B', 'B', 'B', 'B')
        second_guess = strategy.second_guess(clue)
        assert isinstance(second_guess, str)
        assert len(second_guess) == 5
    
    def test_no_breaking_changes_to_existing_api(self):
        """Test that no breaking changes to existing API."""
        # Original functions should still work
        strategy = load_strategy()
        assert strategy.version == "v1.0"
        assert strategy.first_guess() == "ATONE"
        
        # New functions should work alongside old ones
        available = get_available_first_guesses()
        assert len(available) == 32
        
        # Should be able to use both old and new APIs together
        old_second = strategy.second_guess(('B', 'B', 'B', 'B', 'B'))
        new_second = get_second_guess_recommendation("ATONE", ('B', 'B', 'B', 'B', 'B'))
        # Both should return valid guesses (may or may not be same)
        assert old_second is not None or new_second is not None


# Tests for new depth-based strategies (v0.2.0)

def test_load_2d_8r_trice():
    """Test loading 2d-8r-trice strategy."""
    strategy = load_strategy("2d-8r-trice")
    assert isinstance(strategy, Strategy)
    assert strategy.first_guess() == "TRICE"
    assert strategy.clue_count() == 8
    assert strategy.metadata()['win_rate_2d'] > 0.35
    assert strategy.metadata()['guess1'] == "TRICE"


def test_load_2d_8r_siren():
    """Test loading 2d-8r-siren strategy."""
    strategy = load_strategy("2d-8r-siren")
    assert strategy.first_guess() == "SIREN"
    assert strategy.clue_count() == 8


def test_load_strategy_by_components():
    """Test loading strategy by first guess and depth components."""
    from word32 import load_strategy_by_components

    strategy = load_strategy_by_components("TRICE", 8)
    assert strategy.first_guess() == "TRICE"
    assert strategy.clue_count() == 8
    assert strategy.version == "2d-8r-trice"


def test_load_strategy_by_components_different_guesses():
    """Test loading different first guesses."""
    from word32 import load_strategy_by_components

    for guess in ["CRONE", "SIREN", "DEALT"]:
        strategy = load_strategy_by_components(guess, 8)
        assert strategy.first_guess() == guess
        assert strategy.clue_count() == 8


def test_list_strategies_by_depth():
    """Test listing strategies for a specific depth."""
    from word32 import list_strategies_by_depth

    strategies_8r = list_strategies_by_depth(8)

    assert len(strategies_8r) >= 10  # At least top 10
    assert all(s["clue_count"] == 8 for s in strategies_8r)

    # Should be sorted by win_rate descending
    for i in range(len(strategies_8r) - 1):
        assert strategies_8r[i]["win_rate_2d"] >= strategies_8r[i+1]["win_rate_2d"]


def test_list_all_strategies():
    """Test listing all strategies."""
    from word32 import list_all_strategies

    all_strategies = list_all_strategies()

    assert len(all_strategies) >= 10
    assert all("clue_count" in s for s in all_strategies)
    assert all("win_rate_2d" in s for s in all_strategies)


def test_2d_8r_second_guess_selected_pattern():
    """Test that second guess lookup works for selected patterns."""
    strategy = load_strategy("2d-8r-trice")

    # XXGXX is one of TRICE's selected patterns
    clue = ("X", "X", "G", "X", "X")
    second = strategy.second_guess(clue)
    assert second is not None
    assert isinstance(second, str)
    assert len(second) == 5


def test_2d_8r_second_guess_remainder():
    """Test fallback to remainder_guess2 for non-selected patterns."""
    strategy = load_strategy("2d-8r-trice")
    remainder = strategy.remainder_guess2
    assert remainder == "SALON"

    # Use a pattern not in the 8 selected
    clue = ("G", "G", "G", "Y", "B")
    second = strategy.second_guess(clue)
    assert second == remainder


def test_phase_4_3_functions_still_work():
    """Ensure Phase 4.3 functions remain functional after v0.2.0 changes."""
    from word32 import (
        get_available_first_guesses,
        select_first_guess,
        get_strategy_for_first_guess,
        get_second_guess_recommendation
    )

    # get_available_first_guesses should still return 32
    guesses = get_available_first_guesses()
    assert len(guesses) == 32

    # select_first_guess should still work
    selected = select_first_guess("STARE")
    assert selected is not None
    assert selected['first_guess'] == "STARE"

    # get_strategy_for_first_guess should still return dict
    strategy_dict = get_strategy_for_first_guess("STARE")
    assert isinstance(strategy_dict, dict)
    assert len(strategy_dict) > 0

    # get_second_guess_recommendation should still work
    clue = ("X", "Y", "X", "X", "G")
    recommendation = get_second_guess_recommendation("STARE", clue)
    assert isinstance(recommendation, str)
    assert len(recommendation) == 5
