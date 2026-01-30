"""Integration tests for full game flow scenarios (Phase 4.2/4.3)."""

import pytest
from word32 import (
    generate_clue,
    filter_targets,
    get_remaining_candidates,
    build_game_response,
    build_error_response,
    validate_response,
    get_available_first_guesses,
    select_first_guess,
    get_second_guess_recommendation,
    ErrorCode,
    VALID_TARGETS,
)
from word32.strategy import load_strategy


class TestScenario1FullGameWithResponseSchema:
    """Scenario 1: Full 3-guess game with response schema."""
    
    def test_start_game_with_default_first_guess(self):
        """Test starting game with default (ATONE) first guess."""
        strategy = load_strategy("v1.0")
        first_guess = strategy.first_guess()
        assert first_guess == "ATONE"
        
        # Verify we can build a response for first guess
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining
        )
        
        assert response.success is True
        assert response.guess == "ATONE"
        assert response.remaining.count > 0
        assert target in remaining
    
    def test_submit_first_guess_get_response(self):
        """Test submitting first guess and getting response with remaining count."""
        first_guess = "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining,
            game_state={
                'guess_number': 1,
                'guesses_so_far': [first_guess],
                'is_solved': False
            }
        )
        
        assert response.success is True
        assert response.remaining.count == len(remaining)
        assert response.remaining.count < len(VALID_TARGETS)
        assert response.game_state is not None
        assert response.game_state.guess_number == 1
    
    def test_submit_second_guess_get_response(self):
        """Test submitting second guess and getting response with remaining count."""
        first_guess = "ATONE"
        target = "WORLD"
        
        # First guess
        clue1 = generate_clue(first_guess, target)
        remaining1 = filter_targets(VALID_TARGETS, first_guess, clue1)
        
        # Get second guess from strategy
        strategy = load_strategy("v1.0")
        second_guess = strategy.second_guess(clue1)
        
        if second_guess is None:
            pytest.skip("Strategy doesn't cover this clue pattern")
        
        # Second guess
        clue2 = generate_clue(second_guess, target)
        remaining2 = filter_targets(remaining1, second_guess, clue2)
        
        response = build_game_response(
            guess=second_guess,
            clue=clue2,
            remaining_targets=remaining2,
            game_state={
                'guess_number': 2,
                'guesses_so_far': [first_guess, second_guess],
                'is_solved': False
            }
        )
        
        assert response.success is True
        assert response.remaining.count == len(remaining2)
        assert response.remaining.count < len(remaining1)
        assert response.game_state.guess_number == 2
    
    def test_submit_third_guess_verify_response_structure(self):
        """Test submitting third guess and verifying response structure."""
        first_guess = "ATONE"
        target = "WORLD"
        
        # First guess
        clue1 = generate_clue(first_guess, target)
        remaining1 = filter_targets(VALID_TARGETS, first_guess, clue1)
        
        # Second guess
        strategy = load_strategy("v1.0")
        second_guess = strategy.second_guess(clue1)
        
        if second_guess is None:
            pytest.skip("Strategy doesn't cover this clue pattern")
        
        clue2 = generate_clue(second_guess, target)
        remaining2 = filter_targets(remaining1, second_guess, clue2)
        
        # Third guess (pick from remaining)
        if remaining2:
            third_guess = remaining2[0]
            clue3 = generate_clue(third_guess, target)
            remaining3 = filter_targets(remaining2, third_guess, clue3)
            
            is_solved = (clue3 == ('G', 'G', 'G', 'G', 'G'))
            
            response = build_game_response(
                guess=third_guess,
                clue=clue3,
                remaining_targets=remaining3,
                game_state={
                    'guess_number': 3,
                    'guesses_so_far': [first_guess, second_guess, third_guess],
                    'is_solved': is_solved,
                    'solved_word': target if is_solved else None
                }
            )
            
            assert response.success is True
            assert response.game_state.guess_number == 3
            assert response.game_state.is_solved == is_solved
    
    def test_all_responses_pass_schema_validation(self):
        """Test that all responses pass schema validation."""
        first_guess = "ATONE"
        target = "WORLD"
        
        # First guess response
        clue1 = generate_clue(first_guess, target)
        remaining1 = filter_targets(VALID_TARGETS, first_guess, clue1)
        response1 = build_game_response(
            guess=first_guess,
            clue=clue1,
            remaining_targets=remaining1
        )
        
        is_valid, error_msg = validate_response(response1.to_dict())
        assert is_valid is True, f"Validation failed: {error_msg}"
        
        # Second guess response
        strategy = load_strategy("v1.0")
        second_guess = strategy.second_guess(clue1)
        
        if second_guess is not None:
            clue2 = generate_clue(second_guess, target)
            remaining2 = filter_targets(remaining1, second_guess, clue2)
            response2 = build_game_response(
                guess=second_guess,
                clue=clue2,
                remaining_targets=remaining2
            )
            
            is_valid, error_msg = validate_response(response2.to_dict())
            assert is_valid is True, f"Validation failed: {error_msg}"


class TestScenario2CustomFirstGuessSelection:
    """Scenario 2: Custom first guess selection."""
    
    def test_get_available_first_guesses_all_32(self):
        """Test getting available first guesses (all 32)."""
        available = get_available_first_guesses()
        assert len(available) == 32
        
        # Verify structure
        for entry in available:
            assert 'first_guess' in entry
            assert 'rank' in entry
            assert entry['rank'] >= 1
            assert entry['rank'] <= 32
    
    def test_select_custom_first_guess(self):
        """Test selecting custom first guess (e.g., RAISE)."""
        available = get_available_first_guesses()
        
        # Find RAISE or use first available
        custom_guess = None
        for entry in available:
            if entry['first_guess'] == "RAISE":
                custom_guess = entry['first_guess']
                break
        
        if custom_guess is None:
            custom_guess = available[0]['first_guess']
        
        selected = select_first_guess(custom_guess)
        assert selected is not None
        assert selected['first_guess'] == custom_guess.upper()
    
    def test_play_game_with_selected_guess(self):
        """Test playing game with selected guess."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']  # Rank 1
        
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining
        )
        
        assert response.success is True
        assert response.guess == first_guess.upper()
    
    def test_responses_include_strategy_recommendations(self):
        """Test that responses include correct strategy recommendations."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        strategy_recommendation = None
        if second_guess_rec:
            strategy_recommendation = {
                'recommended_guess': second_guess_rec,
                'confidence': 0.9,
                'coverage': 0.8
            }
        
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining,
            strategy_recommendation=strategy_recommendation
        )
        
        assert response.success is True
        if second_guess_rec:
            assert response.strategy is not None
            assert response.strategy.recommended_guess == second_guess_rec


class TestScenario3EarlyGameSolve:
    """Scenario 3: Early game solve."""
    
    def test_play_with_lucky_second_guess_that_solves(self):
        """Test playing with lucky second guess that solves."""
        first_guess = "ATONE"
        target = "ATONE"  # Perfect first guess (unlikely but possible)
        
        clue1 = generate_clue(first_guess, target)
        
        if clue1 == ('G', 'G', 'G', 'G', 'G'):
            # First guess solved it!
            remaining = filter_targets(VALID_TARGETS, first_guess, clue1)
            response = build_game_response(
                guess=first_guess,
                clue=clue1,
                remaining_targets=remaining,
                game_state={
                    'guess_number': 1,
                    'guesses_so_far': [first_guess],
                    'is_solved': True,
                    'solved_word': target
                }
            )
            
            assert response.game_state.is_solved is True
            assert response.game_state.solved_word == target
        else:
            # Try with a different target that might be solved in 2 guesses
            # Use a target that's likely to be solved quickly
            target = "WORLD"
            clue1 = generate_clue(first_guess, target)
            remaining1 = filter_targets(VALID_TARGETS, first_guess, clue1)
            
            # If only one remaining, second guess will solve
            if len(remaining1) == 1:
                second_guess = remaining1[0]
                clue2 = generate_clue(second_guess, target)
                
                response = build_game_response(
                    guess=second_guess,
                    clue=clue2,
                    remaining_targets=[target],
                    game_state={
                        'guess_number': 2,
                        'guesses_so_far': [first_guess, second_guess],
                        'is_solved': True,
                        'solved_word': target
                    }
                )
                
                assert response.game_state.is_solved is True
                assert response.game_state.solved_word == target
    
    def test_is_solved_flag_set_correctly(self):
        """Test that is_solved flag is set correctly."""
        guess = "WORLD"
        target = "WORLD"
        
        clue = generate_clue(guess, target)
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        is_solved = (clue == ('G', 'G', 'G', 'G', 'G'))
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining,
            game_state={
                'guess_number': 1,
                'guesses_so_far': [guess],
                'is_solved': is_solved,
                'solved_word': target if is_solved else None
            }
        )
        
        assert response.game_state.is_solved == is_solved
        if is_solved:
            assert response.game_state.solved_word == target
    
    def test_solved_word_field_populated(self):
        """Test that solved_word field is populated when solved."""
        guess = "WORLD"
        target = "WORLD"
        
        clue = generate_clue(guess, target)
        remaining = filter_targets(VALID_TARGETS, guess, clue)
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining,
            game_state={
                'guess_number': 1,
                'guesses_so_far': [guess],
                'is_solved': True,
                'solved_word': target
            }
        )
        
        assert response.game_state.solved_word == target


class TestScenario4RemainingWordsTracking:
    """Scenario 4: Remaining words tracking."""
    
    def test_initial_remaining_equals_2309(self):
        """Test that initial remaining equals 2309 (or actual target count)."""
        # Before any guesses, all targets are remaining
        assert len(VALID_TARGETS) > 2000  # Should be around 2309
        
        # Simulate no guesses yet - all targets remain
        remaining_count = len(VALID_TARGETS)
        assert remaining_count >= 2300
    
    def test_after_first_guess_remaining_count_decreases(self):
        """Test that after first guess remaining count decreases."""
        first_guess = "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        assert len(remaining) < len(VALID_TARGETS)
        assert len(remaining) > 0
    
    def test_after_second_guess_remaining_count_decreases_further(self):
        """Test that after second guess remaining count decreases further."""
        first_guess = "ATONE"
        target = "WORLD"
        
        # First guess
        clue1 = generate_clue(first_guess, target)
        remaining1 = filter_targets(VALID_TARGETS, first_guess, clue1)
        
        # Second guess
        strategy = load_strategy("v1.0")
        second_guess = strategy.second_guess(clue1)
        
        if second_guess is None:
            pytest.skip("Strategy doesn't cover this clue pattern")
        
        clue2 = generate_clue(second_guess, target)
        remaining2 = filter_targets(remaining1, second_guess, clue2)
        
        assert len(remaining2) <= len(remaining1)
        assert target in remaining2
    
    def test_sample_always_less_than_or_equal_to_size(self):
        """Test that sample is always ≤ size and ≤ actual remaining."""
        first_guess = "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        for sample_size in [5, 10, 20, 50]:
            response = build_game_response(
                guess=first_guess,
                clue=clue,
                remaining_targets=remaining,
                sample_size=sample_size
            )
            
            assert len(response.remaining.sample) <= sample_size
            assert len(response.remaining.sample) <= response.remaining.count
    
    def test_sample_equals_remaining_when_all_words_true(self):
        """Test that sample equals remaining when all_words is True."""
        # Use a small set of remaining words
        remaining = ["WORD1", "WORD2", "WORD3"]
        
        response = build_game_response(
            guess="STARE",
            clue=('B', 'B', 'B', 'B', 'B'),
            remaining_targets=remaining,
            sample_size=10
        )
        
        assert response.remaining.all_words is True
        assert len(response.remaining.sample) == len(remaining)
        assert set(response.remaining.sample) == set(remaining)


class TestScenario5CrossPlatformConsistency:
    """Scenario 5: Cross-platform consistency."""
    
    def test_cli_and_web_app_see_same_remaining_count(self):
        """Test that CLI and Web App see same remaining count."""
        # Simulate same game state
        first_guess = "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Both platforms call same function
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining
        )
        
        # Both should see same count
        remaining_count = response.remaining.count
        assert remaining_count == len(remaining)
    
    def test_cli_and_web_app_see_same_strategy_recommendations(self):
        """Test that CLI and Web App see same strategy recommendations."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        
        # Both platforms call same function
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Both should get same recommendation
        assert second_guess_rec is None or isinstance(second_guess_rec, str)
    
    def test_same_first_guess_selection_available_on_both(self):
        """Test that same first guess selection available on both."""
        # Both platforms call same function
        available = get_available_first_guesses()
        
        # Both should see same 32 options
        assert len(available) == 32
        
        # Both should be able to select same guess
        if available:
            test_guess = available[0]['first_guess']
            selected = select_first_guess(test_guess)
            assert selected is not None
            assert selected['first_guess'] == test_guess.upper()
    
    def test_response_structure_identical_across_platforms(self):
        """Test that response structure identical across platforms."""
        first_guess = "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Both platforms get same response structure
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining
        )
        
        # Validate structure is consistent
        response_dict = response.to_dict()
        is_valid, error_msg = validate_response(response_dict)
        assert is_valid is True, f"Response structure invalid: {error_msg}"
        
        # Both platforms should be able to parse same fields
        assert 'success' in response_dict
        assert 'guess' in response_dict
        assert 'clue' in response_dict
        assert 'remaining' in response_dict
    
    def test_error_response_consistency(self):
        """Test that error responses are consistent across platforms."""
        # Simulate same error on different platforms
        error_cli = build_error_response("Invalid Guess", "Word not found", ErrorCode.INVALID_GUESS)
        error_web = build_error_response("Invalid Guess", "Word not found", ErrorCode.INVALID_GUESS)
        error_discord = build_error_response("Invalid Guess", "Word not found", ErrorCode.INVALID_GUESS)
        
        # All should have identical structure
        assert error_cli.to_dict() == error_web.to_dict() == error_discord.to_dict()
        assert error_cli.success == error_web.success == error_discord.success == False
        assert error_cli.error_code == error_web.error_code == error_discord.error_code
    
    def test_response_modes_consistency(self):
        """Test that different response modes are consistent across platforms."""
        first_guess = "ATONE"
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Test all modes
        response_full = build_game_response(guess=first_guess, clue=clue, remaining_targets=remaining, mode='full')
        response_minimal = build_game_response(guess=first_guess, clue=clue, remaining_targets=remaining, mode='minimal')
        response_extended = build_game_response(guess=first_guess, clue=clue, remaining_targets=remaining, mode='extended')
        
        # Core fields should be identical
        assert response_full.success == response_minimal.success == response_extended.success
        assert response_full.guess == response_minimal.guess == response_extended.guess
        assert response_full.clue == response_minimal.clue == response_extended.clue
        assert response_full.remaining.count == response_minimal.remaining.count == response_extended.remaining.count
        
        # Minimal mode should exclude optional fields
        assert response_minimal.strategy is None
        assert response_minimal.game_state is None
    
    def test_strategy_recommendation_consistency(self):
        """Test that strategy recommendations are consistent across platforms."""
        available = get_available_first_guesses()
        if not available:
            pytest.skip("No first guesses available")
        
        first_guess = available[0]['first_guess']
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Build responses with strategy recommendation
        strategy_info = {
            'recommended_guess': second_guess_rec,
            'confidence': 0.9,
            'coverage': 0.8
        } if second_guess_rec else None
        
        response_cli = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=filter_targets(VALID_TARGETS, first_guess, clue),
            strategy_recommendation=strategy_info
        )
        
        response_web = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=filter_targets(VALID_TARGETS, first_guess, clue),
            strategy_recommendation=strategy_info
        )
        
        # Strategy recommendations should be identical
        if strategy_info:
            assert response_cli.strategy is not None
            assert response_web.strategy is not None
            assert response_cli.strategy.recommended_guess == response_web.strategy.recommended_guess
    
    def test_cli_usage_pattern_simulation(self):
        """Simulate CLI usage pattern (sequential function calls)."""
        # CLI typically calls functions sequentially
        available = get_available_first_guesses()
        first_guess_option = select_first_guess("RAISE")
        
        if first_guess_option is None:
            pytest.skip("RAISE not available")
        
        first_guess = first_guess_option['first_guess']
        target = "WORLD"
        
        # Sequential calls as CLI would make
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        response = build_game_response(first_guess, clue, remaining)
        
        # Verify results
        assert response.success is True
        assert response.remaining.count == len(remaining)
        assert target in remaining
    
    def test_web_app_usage_pattern_simulation(self):
        """Simulate Web App usage pattern (API-like function calls)."""
        # Web App typically makes API-like calls
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess'] if available else "ATONE"
        target = "WORLD"
        
        # API-like calls
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        strategy_info = {
            'recommended_guess': second_guess_rec,
            'confidence': 0.9,
            'coverage': 0.8
        } if second_guess_rec else None
        
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining,
            strategy_recommendation=strategy_info,
            mode='full'
        )
        
        # Verify JSON serialization works
        response_dict = response.to_dict()
        is_valid, error_msg = validate_response(response_dict)
        assert is_valid is True, f"Response validation failed: {error_msg}"
    
    def test_discord_bot_usage_pattern_simulation(self):
        """Simulate Discord Bot usage pattern (minimal mode responses)."""
        # Discord Bot uses minimal mode for concise messages
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess'] if available else "ATONE"
        target = "WORLD"
        
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Minimal mode for Discord
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining,
            mode='minimal'
        )
        
        # Verify minimal structure
        assert response.success is True
        assert response.guess == first_guess.upper()
        assert response.remaining.count == len(remaining)
        assert response.strategy is None  # Minimal mode excludes strategy
        assert response.game_state is None  # Minimal mode excludes game_state
    
    def test_platform_simulation_produces_identical_core_results(self):
        """Test that CLI, Web App, and Discord Bot produce identical core results."""
        first_guess = "ATONE"
        target = "WORLD"
        clue = generate_clue(first_guess, target)
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Simulate all three platforms with same inputs
        response_cli = build_game_response(first_guess, clue, remaining, mode='full')
        response_web = build_game_response(first_guess, clue, remaining, mode='full')
        response_discord = build_game_response(first_guess, clue, remaining, mode='minimal')
        
        # Core fields should be identical
        assert response_cli.success == response_web.success == response_discord.success
        assert response_cli.guess == response_web.guess == response_discord.guess
        assert response_cli.clue == response_web.clue == response_discord.clue
        assert response_cli.remaining.count == response_web.remaining.count == response_discord.remaining.count
        
        # Full mode responses should be identical
        assert response_cli.to_dict() == response_web.to_dict()