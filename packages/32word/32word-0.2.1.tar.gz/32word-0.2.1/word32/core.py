"""Core functions for the 32word library.

This module provides fundamental Wordle gameplay functions including clue generation,
target filtering, and word validation.
"""

from collections import Counter
from typing import Literal
from .data_loader import VALID_GUESSES, VALID_TARGETS
from .config import get_guess_validation_mode

# Type alias for clue codes
ClueCode = Literal['G', 'Y', 'B']
ClueTuple = tuple[ClueCode, ClueCode, ClueCode, ClueCode, ClueCode]


def generate_clue(guess: str, target: str) -> ClueTuple:
    """Generate Wordle clue for a guess against a target word.

    Args:
        guess: The 5-letter word being guessed
        target: The 5-letter target word

    Returns:
        A tuple of 5 clue codes:
        - 'G' for Green (correct letter, correct position)
        - 'Y' for Yellow (correct letter, wrong position)
        - 'B' for Black/Gray (letter not in target)

    Raises:
        ValueError: If guess or target is not exactly 5 letters

    Example:
        >>> generate_clue("RAISE", "CRANE")
        ('B', 'Y', 'G', 'B', 'G')
    """
    if len(guess) != 5 or len(target) != 5:
        raise ValueError("Both guess and target must be exactly 5 letters")

    guess = guess.upper()
    target = target.upper()

    clue = [''] * 5
    target_counts = Counter(target)

    # First pass: find greens
    for i in range(5):
        if guess[i] == target[i]:
            clue[i] = 'G'
            target_counts[guess[i]] -= 1

    # Second pass: find yellows and blacks
    for i in range(5):
        if not clue[i]:
            if target_counts[guess[i]] > 0:
                clue[i] = 'Y'
                target_counts[guess[i]] -= 1
            else:
                clue[i] = 'B'

    return tuple(clue)


def filter_targets(targets: list[str], guess: str, clue: ClueTuple) -> list[str]:
    """Filter targets based on a guess and its resulting clue.

    Returns only the target words that would produce the given clue
    when the given guess is made against them.

    Args:
        targets: List of potential target words to filter
        guess: The word that was guessed
        clue: The clue tuple returned by Wordle (5-element tuple of 'G', 'Y', 'B')

    Returns:
        List of target words that match the clue pattern

    Example:
        >>> filter_targets(["CRANE", "RAISE", "STALE"], "RAISE", ('B', 'Y', 'G', 'B', 'G'))
        ['CRANE']
    """
    guess = guess.upper()

    return [
        target for target in targets
        if generate_clue(guess, target) == clue
    ]


def is_valid_word(word: str, targets_only: bool = None) -> bool:
    """Check if a word is in Wordle's valid guess list.

    Args:
        word: The word to check
        targets_only: If True, only check against target words (3,158 words).
                     If False, check against all valid guesses (14,855 words).
                     If None, uses the global configuration setting.

    Returns:
        True if the word is valid, False otherwise
        
    Example:
        >>> is_valid_word("ABOUT")  # True (in both lists)
        True
        >>> is_valid_word("AAHED")  # True if mode='all', False if mode='targets_only'
        True
        >>> # Use targets_only parameter to override global config
        >>> is_valid_word("AAHED", targets_only=True)
        False
    """
    word_upper = word.upper()
    
    # Use parameter if provided, otherwise use global config
    if targets_only is None:
        mode = get_guess_validation_mode()
        targets_only = (mode == 'targets_only')
    
    if targets_only:
        return word_upper in VALID_TARGETS
    else:
        return word_upper in VALID_GUESSES


def get_remaining_candidates(targets: list[str], guess: str, clue: ClueTuple) -> int:
    """Count how many target words remain after a guess.

    This is a convenience function that counts the results of filter_targets().

    Args:
        targets: List of potential target words
        guess: The guess that was made
        clue: The clue tuple returned by Wordle (5-element tuple of 'G', 'Y', 'B')

    Returns:
        The number of remaining candidate words that match the clue

    Example:
        >>> get_remaining_candidates(["CRANE", "RAISE", "STALE"], "RAISE", ('B', 'Y', 'G', 'B', 'G'))
        1
    """
    return len(filter_targets(targets, guess, clue))
