"""
32word - The game engine for 3-2-Word: Solve Wordle in three guesses.
"""

__version__ = "0.1.3"

# Core functions
from .core import generate_clue, filter_targets, is_valid_word, get_remaining_candidates
from .strategy import (
    load_strategy, 
    get_second_guess, 
    Strategy,
    # Phase 4.3 functions
    select_first_guess,
    get_available_first_guesses,
    get_strategy_for_first_guess,
    get_second_guess_recommendation,
)
from .data_loader import VALID_TARGETS, VALID_GUESSES

# Phase 4.2 response schema
from .response_schema import (
    GameResponse,
    ErrorResponse,
    RemainingWords,
    StrategyRecommendation,
    GameState,
    ResponseMetadata,
    ErrorCode,
    ResponseVersion,
    build_game_response,
    build_error_response,
    validate_response,
    get_remaining_sample,
)

__all__ = [
    # Core functions
    "generate_clue",
    "filter_targets",
    "is_valid_word",
    "get_remaining_candidates",
    "load_strategy",
    "get_second_guess",
    "Strategy",
    "VALID_TARGETS",
    "VALID_GUESSES",
    # Phase 4.3 functions
    "select_first_guess",
    "get_available_first_guesses",
    "get_strategy_for_first_guess",
    "get_second_guess_recommendation",
    # Phase 4.2 response schema
    "GameResponse",
    "ErrorResponse",
    "RemainingWords",
    "StrategyRecommendation",
    "GameState",
    "ResponseMetadata",
    "ErrorCode",
    "ResponseVersion",
    "build_game_response",
    "build_error_response",
    "validate_response",
    "get_remaining_sample",
]
