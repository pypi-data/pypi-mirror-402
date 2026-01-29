"""
32word - The game engine for 3-2-Word: Solve Wordle in three guesses.
"""

__version__ = "0.2.0"

# Data validation on import
from .data_manager import get_data_manager

# Perform startup validation
_data_manager = get_data_manager()
_validation_issues = _data_manager.validate_data_completeness()
if _validation_issues:
    import warnings
    warnings.warn(
        f"Data validation issues detected: {', '.join(_validation_issues)}. "
        "Some Phase 4.2/4.3 features may not work correctly. "
        "See docs/DATA_COMPLETENESS_CHECKLIST.md for recovery steps.",
        UserWarning
    )

# Core functions
from .core import generate_clue, filter_targets, is_valid_word, get_remaining_candidates

# Configuration
from .config import set_guess_validation_mode, get_guess_validation_mode, reset_guess_validation_mode
from .strategy import (
    load_strategy,
    load_strategy_by_components,
    list_strategies_by_depth,
    list_all_strategies,
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

# Custom exceptions
from .exceptions import (
    Word32Error,
    DataValidationError,
    StrategyNotFoundError,
    InvalidClueError,
    InvalidGuessError,
)

__all__ = [
    # Core functions
    "generate_clue",
    "filter_targets",
    "is_valid_word",
    "get_remaining_candidates",
    # Configuration
    "set_guess_validation_mode",
    "get_guess_validation_mode",
    "reset_guess_validation_mode",
    "load_strategy",
    "load_strategy_by_components",
    "list_strategies_by_depth",
    "list_all_strategies",
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
    # Custom exceptions
    "Word32Error",
    "DataValidationError",
    "StrategyNotFoundError",
    "InvalidClueError",
    "InvalidGuessError",
]
