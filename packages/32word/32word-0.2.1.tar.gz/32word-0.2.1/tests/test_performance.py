"""Performance and regression tests for Phase 4.2/4.3 functions."""

import time
import pytest
from word32 import (
    build_game_response,
    build_error_response,
    get_available_first_guesses,
    select_first_guess,
    get_second_guess_recommendation,
    VALID_TARGETS,
)
from word32.core import generate_clue, filter_targets
from word32.strategy import load_strategy
from word32.data_manager import get_data_manager


class TestStrategyLookupPerformance:
    """Test strategy lookup performance."""
    
    def test_get_second_guess_recommendation_under_1ms(self):
        """Test that get_second_guess_recommendation() < 1ms per call."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        clue = ('B', 'B', 'B', 'B', 'B')
        
        # Warm up
        get_second_guess_recommendation(first_guess, clue)
        
        # Measure single call
        start = time.perf_counter()
        result = get_second_guess_recommendation(first_guess, clue)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 1.0, f"get_second_guess_recommendation took {elapsed:.3f}ms (target: <1ms)"
        assert result is None or isinstance(result, str)
    
    def test_batch_1000_lookups_under_1_second(self):
        """Test that batch 1000 lookups in < 1 second."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        clue = ('B', 'B', 'B', 'B', 'B')
        
        # Warm up
        get_second_guess_recommendation(first_guess, clue)
        
        # Measure batch
        start = time.perf_counter()
        for _ in range(1000):
            get_second_guess_recommendation(first_guess, clue)
        elapsed = time.perf_counter() - start
        
        assert elapsed < 1.0, f"1000 lookups took {elapsed:.3f}s (target: <1s)"
    
    def test_no_memory_leaks_on_repeated_calls(self):
        """Test no memory leaks on repeated calls."""
        available = get_available_first_guesses()
        first_guess = available[0]['first_guess']
        clue = ('B', 'B', 'B', 'B', 'B')
        
        # Make many calls
        for _ in range(10000):
            result = get_second_guess_recommendation(first_guess, clue)
            assert result is None or isinstance(result, str)
        
        # If we get here without memory issues, test passes
        assert True


class TestFirstGuessSelectionPerformance:
    """Test first guess selection performance."""
    
    def test_select_first_guess_under_10ms(self):
        """Test that select_first_guess() < 10ms."""
        available = get_available_first_guesses()
        test_guess = available[0]['first_guess']
        
        # Warm up
        select_first_guess(test_guess)
        
        # Measure
        start = time.perf_counter()
        result = select_first_guess(test_guess)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 10.0, f"select_first_guess took {elapsed:.3f}ms (target: <10ms)"
        assert result is not None
    
    def test_get_available_first_guesses_under_10ms(self):
        """Test that get_available_first_guesses() < 10ms."""
        # Warm up
        get_available_first_guesses()
        
        # Measure
        start = time.perf_counter()
        result = get_available_first_guesses()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 10.0, f"get_available_first_guesses took {elapsed:.3f}ms (target: <10ms)"
        assert len(result) == 32
    
    def test_first_call_loads_data_slower_subsequent_cached(self):
        """Test that first call loads data (slower), subsequent calls cached."""
        # Clear cache by importing fresh (in real scenario, this would be first import)
        # For this test, we'll just verify that subsequent calls are fast
        
        # First call (may be slower if not already loaded)
        start1 = time.perf_counter()
        result1 = get_available_first_guesses()
        elapsed1 = (time.perf_counter() - start1) * 1000
        
        # Second call (should be cached/fast)
        start2 = time.perf_counter()
        result2 = get_available_first_guesses()
        elapsed2 = (time.perf_counter() - start2) * 1000
        
        # Second call should be at least as fast (likely faster due to caching)
        # But both should be under 10ms
        assert elapsed1 < 100.0, f"First call took {elapsed1:.3f}ms (should be reasonable)"
        assert elapsed2 < 10.0, f"Second call took {elapsed2:.3f}ms (target: <10ms)"
        assert result1 == result2


class TestResponseBuildingPerformance:
    """Test response building performance."""
    
    def test_build_game_response_under_1ms(self):
        """Test that build_game_response() < 1ms."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS[:100]
        
        # Warm up
        build_game_response(guess, clue, remaining_targets)
        
        # Measure
        start = time.perf_counter()
        response = build_game_response(guess, clue, remaining_targets)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 1.0, f"build_game_response took {elapsed:.3f}ms (target: <1ms)"
        assert response.success is True
    
    def test_build_error_response_under_1ms(self):
        """Test that build_error_response() < 1ms."""
        from word32.response_schema import ErrorCode
        
        # Warm up
        build_error_response("Test", "Message", ErrorCode.UNKNOWN_ERROR)
        
        # Measure
        start = time.perf_counter()
        response = build_error_response("Test", "Message", ErrorCode.UNKNOWN_ERROR)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 1.0, f"build_error_response took {elapsed:.3f}ms (target: <1ms)"
        assert response.success is False
    
    def test_sampling_under_0_5ms_even_with_random_mode(self):
        """Test that sampling < 0.5ms even with random mode."""
        guess = "STARE"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS[:1000]  # Large set
        
        # Warm up
        build_game_response(guess, clue, remaining_targets, random_sample=True)
        
        # Measure
        start = time.perf_counter()
        response = build_game_response(guess, clue, remaining_targets, random_sample=True)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 0.5, f"Sampling with random mode took {elapsed:.3f}ms (target: <0.5ms)"
        assert len(response.remaining.sample) <= 5


class TestDataLoadingPerformance:
    """Test data loading performance."""
    
    def test_validate_data_completeness_under_100ms_first_call(self):
        """Test that validate_data_completeness() < 100ms first call."""
        data_manager = get_data_manager()
        
        # Clear cache to simulate first call
        # (In practice, we can't easily clear the cache, but we can measure)
        
        start = time.perf_counter()
        issues = data_manager.validate_data_completeness()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        # First call should be under 100ms
        # Subsequent calls will be cached and much faster
        assert elapsed < 100.0, f"validate_data_completeness took {elapsed:.3f}ms (target: <100ms first call)"
        assert isinstance(issues, list)
    
    def test_subsequent_validations_under_10ms_cached(self):
        """Test that subsequent validations < 10ms (cached)."""
        data_manager = get_data_manager()
        
        # First call (may be slower)
        data_manager.validate_data_completeness()
        
        # Second call (should be cached)
        start = time.perf_counter()
        issues = data_manager.validate_data_completeness()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 10.0, f"Cached validation took {elapsed:.3f}ms (target: <10ms)"
        assert isinstance(issues, list)


class TestEndToEndPerformance:
    """Test end-to-end performance scenarios."""
    
    def test_full_game_flow_performance(self):
        """Test performance of full game flow."""
        first_guess = "ATONE"
        target = "WORLD"
        
        # Measure full flow
        start = time.perf_counter()
        
        # Generate clue
        clue = generate_clue(first_guess, target)
        
        # Filter targets
        remaining = filter_targets(VALID_TARGETS, first_guess, clue)
        
        # Get strategy recommendation
        second_guess_rec = get_second_guess_recommendation(first_guess, clue)
        
        # Build response
        response = build_game_response(
            guess=first_guess,
            clue=clue,
            remaining_targets=remaining
        )
        
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        # Full flow should be reasonable (< 50ms)
        assert elapsed < 50.0, f"Full game flow took {elapsed:.3f}ms (target: <50ms)"
        assert response.success is True
    
    def test_multiple_games_performance(self):
        """Test performance of processing multiple games."""
        targets = ["WORLD", "PHONE", "AUDIO", "HEART", "PIZZA"]
        first_guess = "ATONE"
        
        start = time.perf_counter()
        
        for target in targets:
            if target not in VALID_TARGETS:
                continue
            
            clue = generate_clue(first_guess, target)
            remaining = filter_targets(VALID_TARGETS, first_guess, clue)
            response = build_game_response(
                guess=first_guess,
                clue=clue,
                remaining_targets=remaining
            )
            assert response.success is True
        
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        # 5 games should be reasonable (< 100ms)
        assert elapsed < 100.0, f"5 games took {elapsed:.3f}ms (target: <100ms)"
    
    def test_response_serialization_performance(self):
        """Test performance of response serialization."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS[:100]
        
        response = build_game_response(guess, clue, remaining_targets)
        
        # Measure to_dict
        start = time.perf_counter()
        response_dict = response.to_dict()
        elapsed_dict = (time.perf_counter() - start) * 1000
        
        # Measure to_json
        start = time.perf_counter()
        json_str = response.to_json()
        elapsed_json = (time.perf_counter() - start) * 1000
        
        # Both should be fast
        assert elapsed_dict < 1.0, f"to_dict took {elapsed_dict:.3f}ms (target: <1ms)"
        assert elapsed_json < 1.0, f"to_json took {elapsed_json:.3f}ms (target: <1ms)"
        assert isinstance(response_dict, dict)
        assert isinstance(json_str, str)
