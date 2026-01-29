"""Data loading for the 32word library.

This module provides functions to load word lists (targets and valid guesses).
It uses DataManager internally for validation and caching, while maintaining
backwards compatibility with the original API.
"""

import logging
from pathlib import Path
from typing import List

# Set up logging
logger = logging.getLogger(__name__)

# Cache for loaded word lists
_targets_cache: List[str] = []
_guesses_cache: List[str] = []


def _load_word_list(filename: str) -> List[str]:
    """Load a word list from the package's data directory.
    
    Args:
        filename: Name of the word list file (e.g., "targets.txt")
        
    Returns:
        List of uppercase words from the file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If the file cannot be read
    """
    # Correctly locate the data file within the package
    data_dir = Path(__file__).parent.joinpath('data')
    filepath = data_dir.joinpath(filename)
    
    if not filepath.exists():
        logger.error(f"Word list file not found: {filepath}")
        raise FileNotFoundError(f"Word list file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            words = [line.strip().upper() for line in f if line.strip() and len(line.strip()) == 5]
        logger.debug(f"Loaded {len(words)} words from {filename}")
        return words
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        raise


def load_targets() -> List[str]:
    """Load the list of valid Wordle target words.
    
    Uses DataManager for validation if available, but maintains backwards
    compatibility with direct file loading.
    
    Returns:
        List of 5-letter uppercase target words (typically ~2,309 words)
        
    Example:
        >>> targets = load_targets()
        >>> len(targets)
        2309
    """
    global _targets_cache
    
    if _targets_cache:
        return _targets_cache
    
    # Try to use DataManager for validation
    try:
        from .data_manager import get_data_manager
        data_manager = get_data_manager()
        # Validate that targets.txt exists and is valid
        issues = data_manager.validate_data_completeness()
        target_issues = [i for i in issues if 'targets.txt' in i]
        if target_issues:
            logger.warning(f"Data validation issues for targets.txt: {target_issues}")
    except Exception as e:
        logger.debug(f"DataManager not available for validation: {e}")
    
    _targets_cache = _load_word_list("targets.txt")
    return _targets_cache


def load_valid_guesses() -> List[str]:
    """Load the list of all valid Wordle guess words.
    
    This includes both target words and additional valid guess words.
    Uses DataManager for validation if available.
    
    Returns:
        List of 5-letter uppercase valid guess words (typically ~12,950 words)
        
    Example:
        >>> guesses = load_valid_guesses()
        >>> len(guesses)
        12950
    """
    global _guesses_cache
    
    if _guesses_cache:
        return _guesses_cache
    
    # Try to use DataManager for validation
    try:
        from .data_manager import get_data_manager
        data_manager = get_data_manager()
        # Validate that valid_guesses.txt exists and is valid
        issues = data_manager.validate_data_completeness()
        guess_issues = [i for i in issues if 'valid_guesses.txt' in i]
        if guess_issues:
            logger.warning(f"Data validation issues for valid_guesses.txt: {guess_issues}")
    except Exception as e:
        logger.debug(f"DataManager not available for validation: {e}")
    
    _guesses_cache = _load_word_list("valid_guesses.txt")
    return _guesses_cache


# Module-level constants for backwards compatibility
# These are loaded on first access to maintain backwards compatibility
# while allowing lazy loading
def _get_valid_targets() -> List[str]:
    """Get valid targets, loading if necessary."""
    if not _targets_cache:
        return load_targets()
    return _targets_cache


def _get_valid_guesses() -> List[str]:
    """Get valid guesses, loading if necessary."""
    if not _guesses_cache:
        return load_valid_guesses()
    return _guesses_cache


# For backwards compatibility, provide module-level constants
# These will be populated on first import
VALID_TARGETS = _get_valid_targets()
VALID_GUESSES = _get_valid_guesses()
