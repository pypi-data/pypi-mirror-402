"""Tests for the response schema module (Phase 4.2)."""

import json
import pytest
from word32.response_schema import (
    build_game_response,
    build_error_response,
    validate_response,
    GameResponse,
    ErrorResponse,
    RemainingWords,
    StrategyRecommendation,
    GameState,
    ResponseMetadata,
    ErrorCode,
    ResponseVersion,
    get_remaining_sample,
    format_clue_tuple,
)
from word32.core import generate_clue, filter_targets
from word32.data_loader import VALID_TARGETS


class TestBuildGameResponse:
    """Test build_game_response function."""
    
    def test_success_case_all_fields(self):
        """Test success case with all fields present."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = ["STALE", "STAMP", "STACK", "STICK", "STOCK"]
        strategy_recommendation = {
            'recommended_guess': 'CLOUD',
            'confidence': 0.95,
            'coverage': 0.85,
            'pattern_info': 'One green, one yellow',
            'expected_remaining': 12.5,
            'max_remaining': 25,
            'rank': 1
        }
        game_state = {
            'guess_number': 1,
            'guesses_so_far': ['STARE'],
            'is_solved': False,
            'solved_word': None
        }
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            strategy_recommendation=strategy_recommendation,
            game_state=game_state,
            strategy_version="ATONE",
            mode='full'
        )
        
        assert response.success is True
        assert response.guess == "STARE"
        assert response.clue == ['G', 'Y', 'B', 'B', 'B']
        assert response.remaining.count == 5
        assert len(response.remaining.sample) == 5
        assert response.remaining.all_words is True
        assert response.strategy is not None
        assert response.strategy.recommended_guess == 'CLOUD'
        assert response.strategy.confidence == 0.95
        assert response.game_state is not None
        assert response.game_state.guess_number == 1
        assert response.metadata is not None
        assert response.metadata.strategy_version == "ATONE"
    
    def test_minimal_mode(self):
        """Test minimal mode with only essential fields."""
        guess = "RAISE"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = ["WORLD", "PHONE", "AUDIO"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            mode='minimal'
        )
        
        assert response.success is True
        assert response.guess == "RAISE"
        assert response.remaining.count == 3
        assert response.strategy is None  # Not included in minimal mode
        assert response.game_state is None  # Not included in minimal mode
        assert response.metadata is not None  # Metadata always included
    
    def test_extended_mode(self):
        """Test extended mode with all optional fields."""
        guess = "ATONE"
        clue = ('G', 'G', 'B', 'B', 'B')
        remaining_targets = ["APPLE", "APPLY", "APTLY"]
        strategy_recommendation = {
            'recommended_guess': 'PIRLS',
            'confidence': 0.9,
            'coverage': 0.8
        }
        game_state = {
            'guess_number': 1,
            'guesses_so_far': ['ATONE'],
            'is_solved': False
        }
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            strategy_recommendation=strategy_recommendation,
            game_state=game_state,
            mode='extended'
        )
        
        assert response.strategy is not None
        assert response.game_state is not None
    
    def test_edge_case_zero_remaining(self):
        """Test edge case with 0 remaining words."""
        guess = "WORLD"
        clue = ('G', 'G', 'G', 'G', 'G')
        remaining_targets = []
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        assert response.remaining.count == 0
        assert response.remaining.sample == []
        assert response.remaining.all_words is True
    
    def test_edge_case_one_remaining(self):
        """Test edge case with 1 remaining word."""
        guess = "STARE"
        clue = ('G', 'G', 'G', 'G', 'Y')
        remaining_targets = ["STARS"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        assert response.remaining.count == 1
        assert response.remaining.sample == ["STARS"]
        assert response.remaining.all_words is True
    
    def test_edge_case_many_remaining(self):
        """Test edge case with many remaining words (2309)."""
        # Use actual targets for realistic test
        guess = "ZZZZZ"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS.copy()
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            sample_size=10
        )
        
        assert response.remaining.count == len(VALID_TARGETS)
        assert len(response.remaining.sample) == 10
        assert response.remaining.all_words is False
    
    def test_random_sampling(self):
        """Test that random sampling produces different samples."""
        guess = "STARE"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS[:100]  # First 100 targets
        
        response1 = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            sample_size=5,
            random_sample=True
        )
        
        response2 = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets,
            sample_size=5,
            random_sample=True
        )
        
        # Samples should be different (very unlikely to be identical)
        # But both should have 5 items
        assert len(response1.remaining.sample) == 5
        assert len(response2.remaining.sample) == 5
        # Note: There's a tiny chance they're the same, but very unlikely
    
    def test_sample_size_variations(self):
        """Test different sample sizes."""
        guess = "RAISE"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = VALID_TARGETS[:50]
        
        for size in [5, 10, 20, 50]:
            response = build_game_response(
                guess=guess,
                clue=clue,
                remaining_targets=remaining_targets,
                sample_size=size
            )
            
            if size >= len(remaining_targets):
                assert response.remaining.all_words is True
                assert len(response.remaining.sample) == len(remaining_targets)
            else:
                assert len(response.remaining.sample) == size
    
    def test_response_serialization_to_dict(self):
        """Test response serialization to dictionary."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = ["STALE", "STAMP"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        result_dict = response.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['success'] is True
        assert result_dict['guess'] == "STARE"
        assert result_dict['clue'] == ['G', 'Y', 'B', 'B', 'B']
        assert 'remaining' in result_dict
        assert result_dict['remaining']['count'] == 2
    
    def test_response_serialization_to_json(self):
        """Test response serialization to JSON."""
        guess = "ATONE"
        clue = ('B', 'B', 'B', 'B', 'B')
        remaining_targets = ["WORLD"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        json_str = response.to_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed['success'] is True
        assert parsed['guess'] == "ATONE"


class TestBuildErrorResponse:
    """Test build_error_response function."""
    
    def test_all_error_codes(self):
        """Test all error codes."""
        error_codes = [
            ErrorCode.INVALID_GUESS,
            ErrorCode.INVALID_CLUE,
            ErrorCode.INCOMPLETE_GAME,
            ErrorCode.MISSING_DATA,
            ErrorCode.INVALID_TARGET,
            ErrorCode.UNKNOWN_ERROR,
        ]
        
        for error_code in error_codes:
            response = build_error_response(
                error_type="Test Error",
                message="Test message",
                error_code=error_code
            )
            
            assert response.success is False
            assert response.error == "Test Error"
            assert response.error_code == error_code.value
            assert response.message == "Test message"
    
    def test_custom_messages(self):
        """Test custom error messages."""
        response = build_error_response(
            error_type="Custom Error",
            message="This is a custom error message with details",
            error_code=ErrorCode.INVALID_GUESS
        )
        
        assert response.error == "Custom Error"
        assert response.message == "This is a custom error message with details"
        assert response.error_code == ErrorCode.INVALID_GUESS.value
    
    def test_default_error_code(self):
        """Test default error code when not specified."""
        response = build_error_response(
            error_type="Some Error",
            message="Some message"
        )
        
        assert response.error_code == ErrorCode.UNKNOWN_ERROR.value
    
    def test_error_response_json_serialization(self):
        """Test error response JSON serialization."""
        response = build_error_response(
            error_type="Test",
            message="Test message",
            error_code=ErrorCode.INVALID_GUESS
        )
        
        json_str = response.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['success'] is False
        assert parsed['error'] == "Test"
        assert parsed['error_code'] == ErrorCode.INVALID_GUESS.value


class TestValidateResponse:
    """Test validate_response function."""
    
    def test_valid_success_response(self):
        """Test valid success response passes validation."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = ["STALE", "STAMP"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        is_valid, error_msg = validate_response(response.to_dict())
        assert is_valid is True
        assert error_msg is None
    
    def test_valid_error_response(self):
        """Test valid error response passes validation."""
        response = build_error_response(
            error_type="Test",
            message="Test message",
            error_code=ErrorCode.INVALID_GUESS
        )
        
        is_valid, error_msg = validate_response(response.to_dict())
        assert is_valid is True
        assert error_msg is None
    
    def test_missing_required_fields(self):
        """Test missing required fields fail validation."""
        # Missing 'guess' field
        invalid_response = {
            'success': True,
            'clue': ['G', 'Y', 'B', 'B', 'B'],
            'remaining': {'count': 5, 'sample': [], 'all_words': False}
        }
        
        is_valid, error_msg = validate_response(invalid_response)
        assert is_valid is False
        assert 'guess' in error_msg.lower()
    
    def test_invalid_clue_codes(self):
        """Test invalid clue codes fail validation."""
        invalid_response = {
            'success': True,
            'guess': 'STARE',
            'clue': ['G', 'Y', 'Z', 'B', 'B'],  # 'Z' is invalid
            'remaining': {'count': 5, 'sample': [], 'all_words': False}
        }
        
        is_valid, error_msg = validate_response(invalid_response)
        assert is_valid is False
        assert 'clue' in error_msg.lower() or 'invalid' in error_msg.lower()
    
    def test_invalid_clue_length(self):
        """Test invalid clue length fails validation."""
        invalid_response = {
            'success': True,
            'guess': 'STARE',
            'clue': ['G', 'Y', 'B'],  # Wrong length
            'remaining': {'count': 5, 'sample': [], 'all_words': False}
        }
        
        is_valid, error_msg = validate_response(invalid_response)
        assert is_valid is False
    
    def test_version_mismatch_detection(self):
        """Test version mismatch detection."""
        response = build_game_response(
            guess="STARE",
            clue=('G', 'Y', 'B', 'B', 'B'),
            remaining_targets=["STALE"]
        )
        
        response_dict = response.to_dict()
        # Change version to mismatch
        response_dict['metadata']['response_version'] = "2.0"
        
        is_valid, error_msg = validate_response(response_dict, schema_version="1.0")
        assert is_valid is False
        assert 'version' in error_msg.lower() or 'mismatch' in error_msg.lower()


class TestDataClasses:
    """Test dataclass to_dict methods and serialization."""
    
    def test_remaining_words_to_dict(self):
        """Test RemainingWords to_dict method."""
        remaining = RemainingWords(
            count=5,
            sample=["WORD1", "WORD2", "WORD3"],
            all_words=False
        )
        
        result = remaining.to_dict()
        assert result['count'] == 5
        assert result['sample'] == ["WORD1", "WORD2", "WORD3"]
        assert result['all_words'] is False
    
    def test_strategy_recommendation_to_dict(self):
        """Test StrategyRecommendation to_dict method."""
        strategy = StrategyRecommendation(
            recommended_guess="CLOUD",
            confidence=0.95,
            coverage=0.85,
            pattern_info="Test pattern",
            expected_remaining=12.5,
            max_remaining=25,
            rank=1
        )
        
        result = strategy.to_dict()
        assert result['recommended_guess'] == "CLOUD"
        assert result['confidence'] == 0.95
        assert 'pattern_info' in result
    
    def test_strategy_recommendation_none_values(self):
        """Test StrategyRecommendation removes None values."""
        strategy = StrategyRecommendation(
            recommended_guess="CLOUD",
            confidence=0.95,
            coverage=0.85,
            pattern_info=None,
            expected_remaining=None
        )
        
        result = strategy.to_dict()
        assert 'pattern_info' not in result
        assert 'expected_remaining' not in result
    
    def test_game_state_to_dict(self):
        """Test GameState to_dict method."""
        game_state = GameState(
            guess_number=2,
            guesses_so_far=["STARE", "CLOUD"],
            is_solved=False,
            solved_word=None
        )
        
        result = game_state.to_dict()
        assert result['guess_number'] == 2
        assert result['guesses_so_far'] == ["STARE", "CLOUD"]
        assert result['is_solved'] is False
        assert result['solved_word'] is None
    
    def test_response_metadata_to_dict(self):
        """Test ResponseMetadata to_dict method."""
        metadata = ResponseMetadata(
            strategy_version="ATONE",
            response_version=ResponseVersion.V1_0.value
        )
        
        result = metadata.to_dict()
        assert result['strategy_version'] == "ATONE"
        assert result['response_version'] == ResponseVersion.V1_0.value
    
    def test_roundtrip_serialization(self):
        """Test roundtrip serialization (to_dict → JSON → parse → to_dict)."""
        guess = "STARE"
        clue = ('G', 'Y', 'B', 'B', 'B')
        remaining_targets = ["STALE", "STAMP"]
        
        response = build_game_response(
            guess=guess,
            clue=clue,
            remaining_targets=remaining_targets
        )
        
        # Convert to dict
        response_dict = response.to_dict()
        
        # Convert to JSON
        json_str = json.dumps(response_dict)
        
        # Parse back
        parsed_dict = json.loads(json_str)
        
        # Validate parsed dict
        is_valid, error_msg = validate_response(parsed_dict)
        assert is_valid is True
        assert parsed_dict['guess'] == "STARE"
        assert parsed_dict['remaining']['count'] == 2


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_format_clue_tuple(self):
        """Test format_clue_tuple function."""
        clue = ('G', 'Y', 'B', 'X', 'G')
        result = format_clue_tuple(clue)
        assert result == ['G', 'Y', 'B', 'X', 'G']
        assert isinstance(result, list)
    
    def test_get_remaining_sample_empty(self):
        """Test get_remaining_sample with empty list."""
        sample, all_words = get_remaining_sample([], size=5)
        assert sample == []
        assert all_words is True
    
    def test_get_remaining_sample_all_words(self):
        """Test get_remaining_sample when all words fit."""
        targets = ["WORD1", "WORD2", "WORD3"]
        sample, all_words = get_remaining_sample(targets, size=5)
        assert len(sample) == 3
        assert all_words is True
        assert sample == sorted(targets)
    
    def test_get_remaining_sample_partial(self):
        """Test get_remaining_sample with partial sample."""
        targets = ["WORD1", "WORD2", "WORD3", "WORD4", "WORD5", "WORD6"]
        sample, all_words = get_remaining_sample(targets, size=3)
        assert len(sample) == 3
        assert all_words is False
        assert sample == sorted(targets)[:3]
    
    def test_get_remaining_sample_random(self):
        """Test get_remaining_sample with random sampling."""
        targets = ["WORD1", "WORD2", "WORD3", "WORD4", "WORD5", "WORD6"]
        sample, all_words = get_remaining_sample(targets, size=3, random_sample=True)
        assert len(sample) == 3
        assert all_words is False
        # All items should be from original list
        assert all(word in targets for word in sample)
