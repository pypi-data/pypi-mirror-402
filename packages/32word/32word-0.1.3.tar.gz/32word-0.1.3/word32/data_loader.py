"""Data loading for the 32word library."""

import os
from pathlib import Path

def _load_word_list(filename: str) -> list[str]:
    """Load a word list from the package's data directory."""
    
    # Correctly locate the data file within the package
    data_dir = Path(__file__).parent.joinpath('data')
    filepath = data_dir.joinpath(filename)
    
    with open(filepath, 'r') as f:
        words = [line.strip().upper() for line in f if line.strip() and len(line.strip()) == 5]
    return words

def load_targets() -> list[str]:
    """Load the list of valid Wordle target words."""
    return _load_word_list("targets.txt")

def load_valid_guesses() -> list[str]:
    """Load the list of all valid Wordle guess words."""
    return _load_word_list("valid_guesses.txt")

VALID_TARGETS = load_targets()
VALID_GUESSES = load_valid_guesses()
