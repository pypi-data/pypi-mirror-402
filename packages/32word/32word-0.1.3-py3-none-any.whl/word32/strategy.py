"""Strategy loading and execution for the 32word library."""

import json
from pathlib import Path
from typing import Optional, Dict, List


class Strategy:
    """A pre-computed Wordle strategy with second-guess lookups."""

    def __init__(self, version="v1.0", lookup_table: dict = None):
        self.version = version
        self.first_guess_word = "ATONE"
        self.lookup_table = lookup_table or {}

    def first_guess(self) -> str:
        """Return the recommended first guess."""
        return self.first_guess_word

    def second_guess(self, clue: tuple) -> Optional[str]:
        """Get the optimal second guess for a given first-guess clue.

        Args:
            clue: A tuple of 5 characters representing the Wordle clue
              'G' for green, 'Y' for yellow, 'B' for black/gray

        Returns:
            The optimal second guess word, or None if clue not in lookup table
        """
        if not self.lookup_table:
            return None

        # Convert clue tuple to string pattern
        # Replace 'B' (black) with 'X' (the convention used in strategy lookup)
        clue_list = list(clue)
        clue_list = ['X' if c == 'B' else c for c in clue_list]
        clue_pattern = ''.join(clue_list)

        # Get the lookup table for this first guess
        first_guess_table = self.lookup_table.get(self.first_guess_word)
        if not first_guess_table:
            return None

        # Get candidates for this clue pattern
        candidates = first_guess_table.get(clue_pattern)
        if not candidates or len(candidates) == 0:
            return None

        # Return the top-ranked (rank 1) second guess
        return candidates[0]['second_guess']

    def metadata(self) -> dict:
        return {
            'version': self.version,
            'first_guess': 'ATONE',
            'penalty_function': 'expected_remaining',
            'depth': 2,
            'symmetric': True,
            'created': '2026-01-15',
            'description': 'Optimal two-deep ATONE strategy minimizing expected remaining targets'
        }


def load_strategy(version: str = "v1.0") -> Strategy:
    """Load a pre-computed strategy table.

    Args:
        version: Strategy version (default "v1.0")

    Returns:
        A Strategy object with populated lookup table
    """
    # Load the strategy JSON file
    data_dir = Path(__file__).parent.joinpath('data')
    strategy_file = data_dir.joinpath(f'{version}.json')

    lookup_table = {}
    if strategy_file.exists():
        with open(strategy_file, 'r') as f:
            lookup_table = json.load(f)

    return Strategy(version=version, lookup_table=lookup_table)


def get_second_guess(strategy: Strategy, first_clue: tuple) -> Optional[str]:
    """Convenience function for getting the optimal second guess.

    Args:
        strategy: A Strategy object (from load_strategy)
        first_clue: The clue tuple from the first guess

    Returns:
        The optimal second guess word, or None if not found
    """
    return strategy.second_guess(first_clue)


# Phase 4.3: First guess selection and strategy lookup functions

# Cache for first guess options and strategy lookup (loaded once)
_first_guess_cache: Optional[List[Dict]] = None
_strategy_lookup_cache: Optional[Dict] = None


def _load_first_guess_options() -> List[Dict]:
    """Load Phase 2 naive-32 first guess options from data file."""
    global _first_guess_cache
    
    if _first_guess_cache is not None:
        return _first_guess_cache
    
    data_dir = Path(__file__).parent.joinpath('data')
    naive_32_file = data_dir.joinpath('phase2_naive_32.json')
    
    if not naive_32_file.exists():
        _first_guess_cache = []
        return _first_guess_cache
    
    with open(naive_32_file, 'r') as f:
        options = json.load(f)
    
    # Transform to match expected format
    _first_guess_cache = []
    for entry in options:
        transformed = {
            'first_guess': entry['guess'].upper(),
            'rank': entry['rank'],
            'expected_remaining': entry.get('expected_remaining', 0.0),
            'metrics': {
                'max_remaining': entry.get('max_remaining', 0),
                'clue_diversity': entry.get('clue_diversity', 0),
                'variance': entry.get('variance', 0.0),
                'std_dev': entry.get('std_dev', 0.0)
            },
            'available': True,
            'coverage': 0.8125  # Default coverage estimate
        }
        _first_guess_cache.append(transformed)
    
    return _first_guess_cache


def _load_strategy_lookup() -> Dict:
    """Load Phase 3 strategy lookup from data file."""
    global _strategy_lookup_cache
    
    if _strategy_lookup_cache is not None:
        return _strategy_lookup_cache
    
    data_dir = Path(__file__).parent.joinpath('data')
    lookup_file = data_dir.joinpath('phase3_lookup.json')
    
    if not lookup_file.exists():
        _strategy_lookup_cache = {}
        return _strategy_lookup_cache
    
    with open(lookup_file, 'r') as f:
        _strategy_lookup_cache = json.load(f)
    
    return _strategy_lookup_cache


def get_available_first_guesses() -> List[Dict]:
    """Get all available first guess options with metrics.
    
    Returns all 32 naive patterns from Phase 2 analysis, sorted by rank.
    Each entry includes rank, guess, expected_remaining, and other metrics.
    
    Returns:
        List of dictionaries, each containing:
        - first_guess: str (the word)
        - rank: int (1-32)
        - expected_remaining: float
        - max_remaining: int
        - clue_diversity: int
        - variance: float
        - std_dev: float
        - total_targets: int
        - available: bool (always True for these)
        - coverage: float (estimated coverage, default 0.8125)
    """
    return _load_first_guess_options().copy()


def select_first_guess(user_choice: str) -> Optional[Dict]:
    """Select and validate a first guess from available options.
    
    Args:
        user_choice: The first guess word selected by user (e.g., "RAISE", "STALE")
        
    Returns:
        Dictionary with first guess information, or None if not found:
        {
            "first_guess": "RAISE",
            "rank": 1,
            "expected_remaining": 90.15,
            "metrics": {
                "max_remaining": 240,
                "clue_diversity": 137,
                "variance": 1234.56,
                "std_dev": 35.12
            },
            "available": true,
            "coverage": 0.8125
        }
    """
    available = get_available_first_guesses()
    user_choice_upper = user_choice.upper()
    
    for option in available:
        if option['first_guess'] == user_choice_upper:
            return option
    
    return None


def get_strategy_for_first_guess(first_guess: str) -> Dict[str, str]:
    """Get all second-guess recommendations for a first guess.
    
    Returns a dictionary mapping clue patterns to recommended second guesses.
    This provides full strategy coverage for the selected first guess.
    
    Args:
        first_guess: The first guess word (e.g., "RAISE", "ATONE")
        
    Returns:
        Dictionary mapping clue pattern strings to second guess words:
        {
            "GXXXG": "AGILE",
            "GXXXX": "ALIAS",
            "XXGXG": "BROSE",
            ...
        }
        Returns empty dict if first guess not found in lookup.
    """
    lookup = _load_strategy_lookup()
    first_guess_upper = first_guess.upper()
    
    if first_guess_upper not in lookup:
        return {}
    
    # Extract second guesses from lookup structure
    # Lookup structure: {first_guess: {clue_pattern: [{second_guess: ..., rank: ...}, ...]}}
    first_guess_data = lookup[first_guess_upper]
    result = {}
    
    for clue_pattern, candidates in first_guess_data.items():
        if candidates and len(candidates) > 0:
            # Get the top-ranked (rank 1) second guess
            result[clue_pattern] = candidates[0]['second_guess']
    
    return result


def get_second_guess_recommendation(first_guess: str, clue: tuple) -> Optional[str]:
    """Get recommended second guess for a (first_guess, clue) pair.
    
    Args:
        first_guess: The first guess word
        clue: The clue tuple ('G', 'Y', 'B', ...)
        
    Returns:
        Recommended second guess word, or None if not found
    """
    lookup = _load_strategy_lookup()
    first_guess_upper = first_guess.upper()
    
    if first_guess_upper not in lookup:
        return None
    
    # Convert clue tuple to string pattern
    # Replace 'B' (black) with 'X' (the convention used in strategy lookup)
    clue_list = list(clue)
    clue_list = ['X' if c == 'B' else c for c in clue_list]
    clue_pattern = ''.join(clue_list)
    
    # Get candidates for this clue pattern
    first_guess_data = lookup[first_guess_upper]
    candidates = first_guess_data.get(clue_pattern)
    
    if not candidates or len(candidates) == 0:
        return None
    
    # Return the top-ranked (rank 1) second guess
    return candidates[0]['second_guess']
