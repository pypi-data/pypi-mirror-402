"""Cross-platform consistency tests for the 32word library.

Ensures that CLI, Web App, and Discord bot receive identical data and behavior
from the 32word library. All functions must be deterministic and produce
identical results across simulated platforms.
"""

import pytest
import json
from word32 import (
    generate_clue,
    filter_targets,
    get_remaining_candidates,
    get_available_first_guesses,
    select_first_guess,
    get_second_guess_recommendation,
    get_strategy_for_first_guess,
    build_game_response,
    build_error_response,
    validate_response,
    VALID_TARGETS,
    VALID_GUESSES,
)


class TestFunctionResultConsistency:
    """Test that functions return identical results across platforms."""
    
    def test_get_available_first_guesses_identical_results(self):
        """Test that get_available_first_guesses() returns identical results."""
        # Simulate multiple platform calls
        result1 = get_available_first_guesses()
        result2 = get_available_first_guesses()
        result3 = get_available_first_guesses()
        
        # All should be identical
        assert result1 == result2 == result3
        
        # Verify structure
        assert len(result1) == 32
        assert all('first_guess' in entry for entry in result1)
        assert all('rank' in entry for entry in result1)
    
    def test_select_first_guess_case_insensitive_consistency(self):
        """Test that select_first_guess() validates identically (case-insensitive)."""
        available = get_available_first_guesses()
        if not available:
            pytest.skip("No first guesses available")
        
        test_guess = available[0]['first_guess']
        
        # Test different case variations
        result1 = select_first_guess(test_guess.upper())
        result2 = select_first_guess(test_guess.lower())
        result3 = select_first_guess(test_guess.capitalize())
        
        # All should return same result
        assert result1 == result2 == result3
        assert result1 is not None
        assert result1['first_guess'] == test_guess.upper()
    
    def test_select_first_guess_error_handling_consistency(self):
        """Test that select_first_guess() error handling is identical."""
        # Invalid guess should return None consistently
        result1 = select_first_guess("INVALID")
        result2 = select_first_guess("INVALID")
        result3 = select_first_guess("INVALID")
        
        assert result1 == result2 == result3 == None
    
    def test_get_second_guess_recommendation_identical_results(self):
        """Test that get_second_guess_recommendation() returns same results."""
        available = get_available_first_guesses()
        if not available:
            pytest.skip("No first guesses available")
        
        first_guess = available[0]['first_guess']
        clue = ('G', 'Y', 'B', 'B', 'B')
        
        # Multiple calls should return identical results
        result1 = get_second_guess_recommendation(first_guess, clue)
        result2 = get_second_guess_recommendation(first_guess, clue)
        result3 = get_second_guess_recommendation(first_guess, clue)
        
        assert result1 == result2 == result3
    
    def test_get_strategy_for_first_guess_identical_dictionaries(self):
        """Test that get_strategy_for_first_guess() returns identical dictionaries."""
        available = get_available_first_guesses()
        if not available:
            pytest.skip("No first guesses available")
        
        first_guess = available[0]['first_guess']
        
        # Multiple calls should return identical dictionaries
        result1 = get_strategy_for_first_guess(first_guess)
        result2 = get_strategy_for_first_guess(first_guess)
        result3 = get_strategy_for_first_guess(first_guess)
        
        assert result1 == result2 == result3
        assert isinstance(result1, dict)


class TestResponseSchemaConsistency:
    """Test that response schema is consistent across platforms."""
    
    def test_build_game_response_identical_json_structure(self):
        """Test that build_game_response() produces identical JSON structure."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        # Build responses multiple times
        response1 = build_game_response(guess, clue, remaining)
        response2 = build_game_response(guess, clue, remaining)
        response3 = build_game_response(guess, clue, remaining)
        
        # Convert to dict and compare
        dict1 = response1.to_dict()
        dict2 = response2.to_dict()
        dict3 = response3.to_dict()
        
        # Core fields should be identical
        assert dict1['success'] == dict2['success'] == dict3['success']
        assert dict1['guess'] == dict2['guess'] == dict3['guess']
        assert dict1['clue'] == dict2['clue'] == dict3['clue']
        assert dict1['remaining']['count'] == dict2['remaining']['count'] == dict3['remaining']['count']
    
    def test_response_modes_consistency(self):
        """Test that all response modes ('full', 'minimal', 'extended') are consistent."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        # Test all modes
        response_full = build_game_response(guess, clue, remaining, mode='full')
        response_minimal = build_game_response(guess, clue, remaining, mode='minimal')
        response_extended = build_game_response(guess, clue, remaining, mode='extended')
        
        # All should have same core fields
        assert response_full.success == response_minimal.success == response_extended.success
        assert response_full.guess == response_minimal.guess == response_extended.guess
        assert response_full.clue == response_minimal.clue == response_extended.clue
        assert response_full.remaining.count == response_minimal.remaining.count == response_extended.remaining.count
        
        # Minimal mode should exclude strategy and game_state
        assert response_minimal.strategy is None
        assert response_minimal.game_state is None
    
    def test_validate_response_accepts_same_responses(self):
        """Test that validate_response() accepts same responses from all platforms."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        response = build_game_response(guess, clue, remaining)
        response_dict = response.to_dict()
        
        # Validate multiple times - should always pass
        is_valid1, error1 = validate_response(response_dict)
        is_valid2, error2 = validate_response(response_dict)
        is_valid3, error3 = validate_response(response_dict)
        
        assert is_valid1 == is_valid2 == is_valid3 == True
        assert error1 == error2 == error3 == None
    
    def test_response_serialization_identical_output(self):
        """Test that response serialization (to_dict(), to_json()) produces identical output."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        response = build_game_response(guess, clue, remaining)
        
        # Multiple serializations should be identical
        dict1 = response.to_dict()
        dict2 = response.to_dict()
        dict3 = response.to_dict()
        
        assert dict1 == dict2 == dict3
        
        # JSON serialization should also be identical
        json1 = response.to_json()
        json2 = response.to_json()
        json3 = response.to_json()
        
        assert json1 == json2 == json3
        
        # Parse back and verify structure
        parsed1 = json.loads(json1)
        parsed2 = json.loads(json2)
        assert parsed1 == parsed2


class TestRemainingWordsCalculation:
    """Test that remaining words calculation is consistent."""
    
    def test_filter_targets_identical_results(self):
        """Test that filter_targets() produces same results across platforms."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        
        # Multiple calls should return identical results
        result1 = filter_targets(VALID_TARGETS, guess, clue)
        result2 = filter_targets(VALID_TARGETS, guess, clue)
        result3 = filter_targets(VALID_TARGETS, guess, clue)
        
        assert result1 == result2 == result3
        assert len(result1) > 0
    
    def test_get_remaining_candidates_identical_counts(self):
        """Test that get_remaining_candidates() returns same counts."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        
        # Multiple calls should return identical counts
        count1 = get_remaining_candidates(VALID_TARGETS, guess, clue)
        count2 = get_remaining_candidates(VALID_TARGETS, guess, clue)
        count3 = get_remaining_candidates(VALID_TARGETS, guess, clue)
        
        assert count1 == count2 == count3
        assert count1 > 0
    
    def test_remaining_word_sampling_deterministic(self):
        """Test that remaining word sampling is deterministic (when random_sample=False)."""
        guess = "ATONE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        # Build responses with random_sample=False (deterministic)
        response1 = build_game_response(guess, clue, remaining, random_sample=False)
        response2 = build_game_response(guess, clue, remaining, random_sample=False)
        response3 = build_game_response(guess, clue, remaining, random_sample=False)
        
        # Samples should be identical when not using random sampling
        assert response1.remaining.sample == response2.remaining.sample == response3.remaining.sample


class TestMultipleFirstGuesses:
    """Test consistency across multiple first guesses."""
    
    def test_full_game_flow_with_raise_rank_1(self):
        """Test full game flow with RAISE (rank 1)."""
        available = get_available_first_guesses()
        
        # Find RAISE (rank 1)
        raise_option = None
        for option in available:
            if option['first_guess'] == 'RAISE':
                raise_option = option
                break
        
        if raise_option is None:
            pytest.skip("RAISE not found in available first guesses")
        
        assert raise_option['rank'] == 1
        
        # Simulate game
        first_guess = raise_option['first_guess']
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Build response
        response = build_game_response(first_guess, clue, remaining)
        
        # Verify consistency
        assert response.success is True
        assert response.guess == first_guess
        assert response.remaining.count == len(remaining)
        assert target in remaining
    
    def test_full_game_flow_with_stale_rank_2(self):
        """Test full game flow with STALE (rank 2)."""
        available = get_available_first_guesses()
        
        # Find STALE (rank 2)
        stale_option = None
        for option in available:
            if option['first_guess'] == 'STALE':
                stale_option = option
                break
        
        if stale_option is None:
            pytest.skip("STALE not found in available first guesses")
        
        assert stale_option['rank'] == 2
        
        # Simulate game
        first_guess = stale_option['first_guess']
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Build response
        response = build_game_response(first_guess, clue, remaining)
        
        # Verify consistency
        assert response.success is True
        assert response.guess == first_guess
        assert response.remaining.count == len(remaining)
    
    def test_full_game_flow_with_lowest_rank(self):
        """Test full game flow with lowest rank (rank 32)."""
        available = get_available_first_guesses()
        
        # Find rank 32
        lowest_option = None
        for option in available:
            if option['rank'] == 32:
                lowest_option = option
                break
        
        if lowest_option is None:
            pytest.skip("Rank 32 not found in available first guesses")
        
        # Simulate game
        first_guess = lowest_option['first_guess']
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Build response
        response = build_game_response(first_guess, clue, remaining)
        
        # Verify consistency
        assert response.success is True
        assert response.guess == first_guess
        assert response.remaining.count == len(remaining)
    
    def test_same_results_cli_and_simulated_web_app(self):
        """Test that CLI and simulated Web App produce same results."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        target = "WORLD"
        
        # Simulate CLI usage (sequential function calls)
        clue_cli = generate_clue(first_guess, target)
        remaining_cli = filter_targets(VALID_TARGETS, first_guess, clue_cli)
        response_cli = build_game_response(first_guess, clue_cli, remaining_cli)
        
        # Simulate Web App usage (same functions, different context)
        clue_web = generate_clue(first_guess, target)
        remaining_web = filter_targets(VALID_TARGETS, first_guess, clue_web)
        response_web = build_game_response(first_guess, clue_web, remaining_web)
        
        # Results should be identical
        assert response_cli.to_dict() == response_web.to_dict()
        assert response_cli.remaining.count == response_web.remaining.count


class TestEdgeCasesAcrossPlatforms:
    """Test edge cases are handled consistently across platforms."""
    
    def test_empty_remaining_words_solved_game(self):
        """Test empty remaining words (solved game)."""
        guess = "WORLD"
        target = "WORLD"
        clue = generate_clue(guess, target)
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        # Should have exactly one remaining (the target itself)
        assert len(remaining) == 1
        assert remaining[0] == target
        
        response = build_game_response(
            guess, clue, remaining,
            game_state={'guess_number': 1, 'guesses_so_far': [guess], 'is_solved': True, 'solved_word': target}
        )
        
        assert response.success is True
        assert response.remaining.count == 1
        assert response.game_state.is_solved is True
    
    def test_single_remaining_word(self):
        """Test single remaining word."""
        guess = "ATONE"
        target = "WORLD"
        clue = generate_clue(guess, target)
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        # If only one remaining, use it
        if len(remaining) == 1:
            response = build_game_response(guess, clue, remaining)
            assert response.remaining.count == 1
            assert response.remaining.all_words is True
            assert len(response.remaining.sample) == 1
    
    def test_missing_strategy_recommendations(self):
        """Test missing strategy recommendations."""
        available = get_available_first_guesses()
        if not available:
            pytest.skip("No first guesses available")
        
        first_guess = available[0]['first_guess']
        # Use an unlikely clue pattern that might not have coverage
        clue = ('X', 'X', 'X', 'X', 'X')  # All black (using X instead of B)
        
        recommendation = get_second_guess_recommendation(first_guess, clue)
        
        # Should handle None gracefully
        response = build_game_response(
            first_guess, clue, VALID_TARGETS[:10],
            strategy_recommendation={'recommended_guess': recommendation, 'confidence': 0.5} if recommendation else None
        )
        
        assert response.success is True
        # Strategy may or may not be present depending on recommendation
    
    def test_invalid_clue_patterns(self):
        """Test invalid clue patterns."""
        # Test with invalid clue length
        with pytest.raises(ValueError):
            build_game_response("ATONE", ('G', 'Y', 'B'), VALID_TARGETS[:10])
        
        # Test with invalid clue codes
        invalid_clue = ('G', 'Y', 'B', 'B', 'Z')  # Z is invalid
        # Should still build response, but clue validation happens elsewhere
        remaining = filter_targets(VALID_TARGETS, "ATONE", ('G', 'Y', 'B', 'B', 'B'))
        response = build_game_response("ATONE", invalid_clue, remaining)
        assert response.success is True  # Response builds, but clue may be invalid
    
    def test_generate_clue_identical_results(self):
        """Test that generate_clue() generates same clues."""
        guess = "ATONE"
        target = "WORLD"
        
        # Multiple calls should return identical clues
        clue1 = generate_clue(guess, target)
        clue2 = generate_clue(guess, target)
        clue3 = generate_clue(guess, target)
        
        assert clue1 == clue2 == clue3
    
    def test_error_response_consistency(self):
        """Test that error responses are consistent."""
        error1 = build_error_response("Test Error", "Test message")
        error2 = build_error_response("Test Error", "Test message")
        error3 = build_error_response("Test Error", "Test message")
        
        # All should be identical
        assert error1.to_dict() == error2.to_dict() == error3.to_dict()
        assert error1.success == error2.success == error3.success == False
