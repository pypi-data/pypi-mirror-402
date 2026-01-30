"""Configuration settings for the 32word library.

Provides global configuration options that control library behavior,
such as whether to restrict guesses to target words only.
"""

from typing import Literal

# Global configuration state
_guess_validation_mode: Literal['all', 'targets_only'] = 'all'


def set_guess_validation_mode(mode: Literal['all', 'targets_only']) -> None:
    """Set the guess validation mode.
    
    Args:
        mode: Validation mode:
            - 'all': Allow all valid guesses (14,855 words) - default
            - 'targets_only': Only allow target words (3,158 words)
    
    Example:
        >>> from word32.config import set_guess_validation_mode
        >>> set_guess_validation_mode('targets_only')
        >>> from word32 import is_valid_word
        >>> is_valid_word('AAHED')  # False (not a target word)
        False
        >>> is_valid_word('ABOUT')  # True (is a target word)
        True
    """
    global _guess_validation_mode
    if mode not in ('all', 'targets_only'):
        raise ValueError(f"Invalid mode: {mode}. Must be 'all' or 'targets_only'")
    _guess_validation_mode = mode


def get_guess_validation_mode() -> Literal['all', 'targets_only']:
    """Get the current guess validation mode.
    
    Returns:
        Current validation mode: 'all' or 'targets_only'
    """
    return _guess_validation_mode


def reset_guess_validation_mode() -> None:
    """Reset guess validation mode to default ('all')."""
    global _guess_validation_mode
    _guess_validation_mode = 'all'
