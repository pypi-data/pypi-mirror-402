"""API response schema for Wordle gameplay interactions.

Provides standardized JSON response structures for all gameplay interactions
across CLI, Web App, and Discord bot platforms.
"""

import json
import random
from typing import Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum


class ResponseVersion(str, Enum):
    """Response schema version."""
    V1_0 = "1.0"


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    INVALID_GUESS = "INVALID_GUESS"
    INVALID_CLUE = "INVALID_CLUE"
    INCOMPLETE_GAME = "INCOMPLETE_GAME"
    MISSING_DATA = "MISSING_DATA"
    INVALID_TARGET = "INVALID_TARGET"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class RemainingWords:
    """Remaining words information."""
    count: int
    sample: list[str]
    all_words: bool  # True if sample contains all remaining words
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class StrategyRecommendation:
    """Strategy recommendation information."""
    recommended_guess: str
    confidence: float  # 0.0 to 1.0
    coverage: float  # Coverage percentage (0.0 to 1.0)
    pattern_info: Optional[str] = None  # Human-readable pattern description
    expected_remaining: Optional[float] = None
    max_remaining: Optional[int] = None
    rank: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class GameState:
    """Game state metadata."""
    guess_number: int
    guesses_so_far: list[str]
    is_solved: bool
    solved_word: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ResponseMetadata:
    """Response metadata."""
    strategy_version: Optional[str] = None  # e.g., "ATONE"
    response_version: str = ResponseVersion.V1_0.value
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class GameResponse:
    """Complete game response structure."""
    success: bool
    guess: str
    clue: list[str]  # ['G', 'Y', 'X', 'X', 'Y']
    remaining: RemainingWords
    strategy: Optional[StrategyRecommendation] = None
    game_state: Optional[GameState] = None
    metadata: Optional[ResponseMetadata] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'success': self.success,
            'guess': self.guess,
            'clue': self.clue,
            'remaining': self.remaining.to_dict(),
        }
        
        if self.strategy:
            result['strategy'] = self.strategy.to_dict()
        
        if self.game_state:
            result['game_state'] = self.game_state.to_dict()
        
        if self.metadata:
            result['metadata'] = self.metadata.to_dict()
        
        return result
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ErrorResponse:
    """Error response structure."""
    success: bool = False
    error: str = ""
    error_code: str = ""
    message: str = ""
    metadata: Optional[ResponseMetadata] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'success': self.success,
            'error': self.error,
            'error_code': self.error_code,
            'message': self.message,
        }
        
        if self.metadata:
            result['metadata'] = self.metadata.to_dict()
        
        return result
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def format_clue_tuple(clue: tuple) -> list[str]:
    """Convert clue tuple to list of strings.
    
    Args:
        clue: Tuple of ('G', 'Y', 'X') codes
        
    Returns:
        List of strings ['G', 'Y', 'X', ...]
    """
    return list(clue)


def get_remaining_sample(
    targets: list[str],
    size: int = 5,
    random_sample: bool = False
) -> tuple[list[str], bool]:
    """Get sample of remaining words.
    
    Args:
        targets: List of remaining target words
        size: Maximum sample size
        random_sample: If True, use random sampling; if False, use first N
        
    Returns:
        Tuple of (sample list, all_words bool)
    """
    if not targets:
        return [], True
    
    all_words = len(targets) <= size
    
    if all_words:
        sample = sorted(targets)
    elif random_sample:
        sample = sorted(random.sample(targets, min(size, len(targets))))
    else:
        sample = sorted(targets)[:size]
    
    return sample, all_words


def build_game_response(
    guess: str,
    clue: tuple,
    remaining_targets: list[str],
    strategy_recommendation: Optional[dict] = None,
    game_state: Optional[dict] = None,
    strategy_version: Optional[str] = None,
    mode: Literal['full', 'minimal', 'extended'] = 'full',
    sample_size: int = 5,
    random_sample: bool = False
) -> GameResponse:
    """Build standardized game response.
    
    Args:
        guess: The guessed word
        clue: Clue tuple ('G', 'Y', 'X')
        remaining_targets: List of remaining compatible targets
        strategy_recommendation: Optional dict with strategy info:
            - recommended_guess: str
            - confidence: float (0.0-1.0)
            - coverage: float (0.0-1.0)
            - pattern_info: Optional[str]
            - expected_remaining: Optional[float]
            - max_remaining: Optional[int]
            - rank: Optional[int]
        game_state: Optional dict with game state:
            - guess_number: int
            - guesses_so_far: list[str]
            - is_solved: bool
            - solved_word: Optional[str]
        strategy_version: Strategy version identifier (e.g., "ATONE")
        mode: Response mode ('full', 'minimal', 'extended')
        sample_size: Number of words to include in sample
        random_sample: If True, use random sampling for remaining words
        
    Returns:
        GameResponse object
    """
    # Format clue
    clue_list = format_clue_tuple(clue)
    
    # Get remaining words sample
    sample, all_words = get_remaining_sample(
        remaining_targets,
        size=sample_size,
        random_sample=random_sample
    )
    
    remaining = RemainingWords(
        count=len(remaining_targets),
        sample=sample,
        all_words=all_words
    )
    
    # Build strategy recommendation if provided
    strategy = None
    if strategy_recommendation and mode != 'minimal':
        strategy = StrategyRecommendation(
            recommended_guess=strategy_recommendation.get('recommended_guess', ''),
            confidence=strategy_recommendation.get('confidence', 0.0),
            coverage=strategy_recommendation.get('coverage', 0.0),
            pattern_info=strategy_recommendation.get('pattern_info'),
            expected_remaining=strategy_recommendation.get('expected_remaining'),
            max_remaining=strategy_recommendation.get('max_remaining'),
            rank=strategy_recommendation.get('rank')
        )
    
    # Build game state if provided
    game_state_obj = None
    if game_state and mode != 'minimal':
        game_state_obj = GameState(
            guess_number=game_state.get('guess_number', 0),
            guesses_so_far=game_state.get('guesses_so_far', []),
            is_solved=game_state.get('is_solved', False),
            solved_word=game_state.get('solved_word')
        )
    
    # Build metadata
    metadata = ResponseMetadata(
        strategy_version=strategy_version,
        response_version=ResponseVersion.V1_0.value
    )
    
    return GameResponse(
        success=True,
        guess=guess.upper(),
        clue=clue_list,
        remaining=remaining,
        strategy=strategy,
        game_state=game_state_obj,
        metadata=metadata
    )


def build_error_response(
    error_type: str,
    message: str,
    error_code: Optional[ErrorCode] = None
) -> ErrorResponse:
    """Build standardized error response.
    
    Args:
        error_type: Human-readable error type
        message: Detailed error message
        error_code: Standard error code (defaults to UNKNOWN_ERROR)
        
    Returns:
        ErrorResponse object
    """
    if error_code is None:
        error_code = ErrorCode.UNKNOWN_ERROR
    
    metadata = ResponseMetadata(response_version=ResponseVersion.V1_0.value)
    
    return ErrorResponse(
        success=False,
        error=error_type,
        error_code=error_code.value,
        message=message,
        metadata=metadata
    )


def validate_response(response: dict, schema_version: str = "1.0") -> tuple[bool, Optional[str]]:
    """Validate response structure.
    
    Args:
        response: Response dictionary to validate
        schema_version: Expected schema version
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields for success response
    if response.get('success', False):
        required_fields = ['guess', 'clue', 'remaining']
        for field in required_fields:
            if field not in response:
                return False, f"Missing required field: {field}"
        
        # Validate clue format
        clue = response.get('clue', [])
        if not isinstance(clue, list) or len(clue) != 5:
            return False, "Clue must be a list of 5 elements"
        
        for code in clue:
            if code not in ['G', 'Y', 'X']:
                return False, f"Invalid clue code: {code}"
        
        # Validate remaining structure
        remaining = response.get('remaining', {})
        if not isinstance(remaining, dict):
            return False, "Remaining must be a dictionary"
        
        required_remaining = ['count', 'sample', 'all_words']
        for field in required_remaining:
            if field not in remaining:
                return False, f"Missing required remaining field: {field}"
        
        # Validate metadata if present
        metadata = response.get('metadata', {})
        if metadata:
            if metadata.get('response_version') != schema_version:
                return False, f"Schema version mismatch: expected {schema_version}"
    
    # Check required fields for error response
    else:
        required_fields = ['error', 'error_code', 'message']
        for field in required_fields:
            if field not in response:
                return False, f"Missing required error field: {field}"
    
    return True, None
