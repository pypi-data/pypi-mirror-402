"""Core functions for the 32word library."""

from collections import Counter
from .data_loader import VALID_GUESSES


def generate_clue(guess: str, target: str) -> tuple[str, str, str, str, str]:
    """Generate Wordle clue for a guess against a target word.

    'G' for Green (correct letter, correct position)
    'Y' for Yellow (correct letter, wrong position)
    'B' for Black/Gray (letter not in target)
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


def filter_targets(targets: list[str], guess: str, clue: tuple) -> list[str]:
    """Filter targets based on a guess and its resulting clue."""

    guess = guess.upper()

    return [
        target for target in targets
        if generate_clue(guess, target) == clue
    ]


def is_valid_word(word: str) -> bool:
    """Check if a word is in Wordle's valid guess list.

    Args:
        word: The word to check

    Returns:
        True if the word is valid, False otherwise
    """
    return word.upper() in VALID_GUESSES


def get_remaining_candidates(targets: list[str], guess: str, clue: tuple) -> int:
    """Count how many target words remain after a guess.

    Args:
        targets: List of potential target words
        guess: The guess that was made
        clue: The clue returned by Wordle

    Returns:
        The number of remaining candidate words
    """
    return len(filter_targets(targets, guess, clue))
