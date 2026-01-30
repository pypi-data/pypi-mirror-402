"""Strategy loading and execution for the 32word library.

This module provides strategy loading, first guess selection, and second guess
recommendations for the 32word library. Supports both legacy v1.0 format and
new Phase 3/4 lightweight formats with 32 first guess options.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, TypedDict, Literal

# Set up logging
logger = logging.getLogger(__name__)

# Type definitions for better type checking
class FirstGuessMetrics(TypedDict, total=False):
    """Metrics for a first guess option."""
    max_remaining: int
    clue_diversity: int
    variance: float
    std_dev: float

class FirstGuessOption(TypedDict, total=False):
    """First guess option with metrics."""
    first_guess: str
    rank: int
    expected_remaining: float
    metrics: FirstGuessMetrics
    available: bool
    coverage: float

ClueTuple = Tuple[str, str, str, str, str]


class Strategy:
    """A pre-computed Wordle strategy with second-guess lookups.

    Supports both legacy format (full clues dict) and new lightweight format
    (selected patterns with phase3_lookup reference). Can work with any of
    the 32 available first guesses, defaulting to ATONE for backwards compatibility.

    Attributes:
        version: Strategy version string
        first_guess_word: The first guess word this strategy uses
        lookup_table: Internal lookup table for clue patterns to second guesses
    """

    def __init__(
        self,
        version: str = "v1.0",
        data: Optional[Dict] = None,
        lookup_table: Optional[Dict] = None,
        phase3_lookup: Optional[Dict] = None,
        first_guess: Optional[str] = None
    ):
        """Initialize a strategy.

        Args:
            version: Strategy version string (e.g., "v1.0", "2d-8r-trice")
            data: Strategy data dict (for lightweight format)
            lookup_table: Full lookup table (for legacy format or populated from phase3_lookup)
            phase3_lookup: Phase 3 lookup table for pattern-based filtering
            first_guess: Optional first guess word to use (defaults to ATONE for backwards compatibility)
        """
        self.version = version
        self.data = data or {}
        self.lookup_table = lookup_table or {}
        self._phase3_lookup = phase3_lookup
        self._metadata = self.data.get("metadata", {})
        
        # Determine first guess: explicit parameter > data > default ATONE
        if first_guess:
            self.first_guess_word = first_guess.upper()
        else:
            self.first_guess_word = self.data.get("first_guess", "ATONE").upper()
        
        self.remainder_guess2 = self.data.get("remainder_guess2")
        self._selected_patterns = self.data.get("selected_patterns")

        # For v1.0 legacy format, the lookup_table is the full dict keyed by first guess
        # Extract the strategy for the selected first guess
        if self.version == "v1.0" and self.lookup_table:
            if self.first_guess_word in self.lookup_table:
                self.lookup_table = {self.first_guess_word: self.lookup_table[self.first_guess_word]}
            elif "ATONE" in self.lookup_table:
                # Fallback to ATONE for backwards compatibility
                logger.warning(f"First guess '{self.first_guess_word}' not found in v1.0 lookup, using ATONE")
                self.lookup_table = {"ATONE": self.lookup_table["ATONE"]}
                self.first_guess_word = "ATONE"

        # Build clues from phase3_lookup if needed
        if self._selected_patterns and not self.lookup_table:
            self._build_clues_from_lookup(phase3_lookup)
        
        # If no lookup_table was built and we have a first_guess, try to load from phase3_lookup
        if not self.lookup_table and not self._phase3_lookup:
            # Try to load phase3_lookup for this first guess using StrategyIndex
            try:
                phase3_data = _strategy_index.get_strategy_lookup()
                if phase3_data and self.first_guess_word.upper() in phase3_data:
                    self._phase3_lookup = phase3_data
                    logger.debug(f"Loaded phase3_lookup for first guess: {self.first_guess_word}")
            except Exception as e:
                logger.debug(f"Could not load phase3_lookup: {e}")

    def _build_clues_from_lookup(self, phase3_lookup: dict) -> None:
        """Build clues dict from phase3_lookup and selected patterns."""
        if not phase3_lookup:
            # Load phase3_lookup if not provided
            data_dir = Path(__file__).parent.joinpath('data')
            lookup_path = data_dir / 'phase3_lookup.json'
            if lookup_path.exists():
                with open(lookup_path, 'r') as f:
                    phase3_lookup = json.load(f)
            else:
                return

        self._phase3_lookup = phase3_lookup
        self.lookup_table = {}
        first_guess_upper = self.first_guess_word.upper()

        if first_guess_upper not in phase3_lookup:
            return

        first_guess_strategy = phase3_lookup[first_guess_upper]

        # Filter to only selected patterns
        for pattern in self._selected_patterns:
            if pattern in first_guess_strategy:
                # Create a clues dict similar to the old format
                candidates = first_guess_strategy[pattern]
                if candidates:
                    self.lookup_table[pattern] = {
                        'second_guess': candidates[0]['second_guess'],
                        'pattern_id': pattern
                    }

    def first_guess(self) -> str:
        """Return the recommended first guess."""
        return self.first_guess_word

    def second_guess(self, clue: ClueTuple) -> Optional[str]:
        """Get the optimal second guess for a given first-guess clue.

        Args:
            clue: A tuple of 5 characters representing the Wordle clue
              'G' for green, 'Y' for yellow, 'B' or 'X' for black/gray

        Returns:
            The optimal second guess word, or remainder_guess2, or None if not found

        Example:
            >>> strategy = load_strategy()
            >>> strategy.second_guess(('G', 'Y', 'B', 'B', 'B'))
            'CLOUD'
        """
        # Convert clue tuple to string pattern
        # Replace 'B' (black) with 'X' (the convention used in strategy lookup)
        clue_list = list(clue)
        clue_list = ['X' if c == 'B' else c for c in clue_list]
        clue_pattern = ''.join(clue_list)

        # For v1.0 legacy format, lookup_table is {FIRST_GUESS: {CLUE_PATTERN: [candidates]}}
        if self.version == "v1.0" and self.first_guess_word in self.lookup_table:
            first_guess_data = self.lookup_table[self.first_guess_word]
            if clue_pattern in first_guess_data:
                candidates = first_guess_data[clue_pattern]
                if candidates and len(candidates) > 0:
                    return candidates[0]['second_guess']

        # For new lightweight format, lookup_table is {CLUE_PATTERN: {second_guess: ...}}
        elif clue_pattern in self.lookup_table:
            return self.lookup_table[clue_pattern]['second_guess']

        # Fall back to remainder_guess2 if available
        if self.remainder_guess2:
            return self.remainder_guess2

        # Fall back to phase3_lookup if available
        if self._phase3_lookup:
            first_guess_upper = self.first_guess_word.upper()
            if first_guess_upper in self._phase3_lookup:
                first_guess_table = self._phase3_lookup[first_guess_upper]
                if clue_pattern in first_guess_table:
                    candidates = first_guess_table[clue_pattern]
                    if candidates:
                        return candidates[0]['second_guess']

        return None

    def metadata(self) -> dict:
        """Return strategy metadata."""
        if self._metadata:
            return self._metadata.copy()

        return {
            'version': self.version,
            'first_guess': self.first_guess_word,
            'penalty_function': 'expected_remaining',
            'depth': 2,
            'created': '2026-01-15',
            'description': f'Strategy for {self.first_guess_word}',
        }

    def clue_count(self) -> int:
        """Return the number of clue patterns in this strategy."""
        if self._selected_patterns:
            return len(self._selected_patterns)
        return len(self.lookup_table)


def load_strategy(version: str = "v1.0", first_guess: Optional[str] = None) -> Strategy:
    """Load a pre-computed strategy table.

    Supports both legacy v1.0 format and new lightweight depth-based formats.
    Can work with any of the 32 available first guesses.

    Examples:
        load_strategy("v1.0")  # Legacy format (defaults to ATONE)
        load_strategy("2d-8r-trice")  # New lightweight format
        load_strategy("v1.0", first_guess="RAISE")  # Use RAISE as first guess

    Args:
        version: Strategy version (default "v1.0")
        first_guess: Optional first guess word to use (defaults to strategy default, usually ATONE)

    Returns:
        A Strategy object with populated lookup table
    """
    data_dir = Path(__file__).parent.joinpath('data')

    # Check for lightweight format in strategies subdirectory
    strategy_file = data_dir / 'strategies' / f'{version.replace("-", "_")}.json'

    # Fall back to legacy location
    if not strategy_file.exists():
        strategy_file = data_dir / f'{version}.json'

    data = {}
    lookup_table = {}
    phase3_lookup = None

    if strategy_file.exists():
        with open(strategy_file, 'r') as f:
            data = json.load(f)

        # Check if this is a lightweight format
        if data.get("lookup_source") == "phase3_lookup":
            # Load phase3_lookup for this strategy
            lookup_path = data_dir / 'phase3_lookup.json'
            if lookup_path.exists():
                with open(lookup_path, 'r') as f:
                    phase3_lookup = json.load(f)
        else:
            # Legacy format - data is the lookup table itself
            lookup_table = data

    return Strategy(
        version=version,
        data=data,
        lookup_table=lookup_table,
        phase3_lookup=phase3_lookup,
        first_guess=first_guess
    )


def load_strategy_by_components(guess1: str, depth: int) -> Strategy:
    """Load a strategy by first guess and depth.

    Args:
        guess1: First guess word (e.g., "TRICE", "CRONE")
        depth: Number of clue patterns to memorize (e.g., 8, 16, 32)

    Returns:
        A Strategy object for the specified guess1 and depth

    Example:
        strategy = load_strategy_by_components("TRICE", 8)
    """
    version = f"2d-{depth}r-{guess1.lower()}"
    return load_strategy(version)


def list_strategies_by_depth(depth: int) -> List[dict]:
    """List all available strategies for a given depth.

    Args:
        depth: Clue count (8, 16, 32, 64, 243)

    Returns:
        List of strategy metadata dicts, sorted by win_rate descending

    Example:
        strategies = list_strategies_by_depth(8)
        for s in strategies:
            print(f"{s['guess1']}: {s['win_rate_2d']*100:.1f}%")
    """
    data_dir = Path(__file__).parent.joinpath('data')
    strategies_dir = data_dir / 'strategies'

    strategies = []
    if not strategies_dir.exists():
        return strategies

    pattern = f"2d_{depth}r_*.json"
    for filepath in strategies_dir.glob(pattern):
        with open(filepath, 'r') as f:
            data = json.load(f)
            if "metadata" in data:
                strategies.append(data["metadata"])

    # Sort by win rate descending
    strategies.sort(key=lambda s: -s.get("win_rate_2d", 0))

    return strategies


def list_all_strategies() -> List[dict]:
    """List all available strategies across all depths.

    Returns:
        List of all strategy metadata dicts, sorted by depth then win_rate

    Example:
        all_strategies = list_all_strategies()
    """
    data_dir = Path(__file__).parent.joinpath('data')
    strategies_dir = data_dir / 'strategies'

    strategies = []
    if not strategies_dir.exists():
        return strategies

    for filepath in strategies_dir.glob("2d_*.json"):
        with open(filepath, 'r') as f:
            data = json.load(f)
            if "metadata" in data:
                strategies.append(data["metadata"])

    # Sort by depth, then win rate
    strategies.sort(key=lambda s: (s.get("clue_count", 0), -s.get("win_rate_2d", 0)))

    return strategies


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

class StrategyIndex:
    """Index for efficient strategy lookups across all 32 first guesses.
    
    Provides O(1) lookup performance for second guess recommendations.
    Caches loaded data for efficient access.
    """
    
    def __init__(self):
        """Initialize StrategyIndex with empty caches."""
        self._first_guess_cache: Optional[List[FirstGuessOption]] = None
        self._strategy_lookup_cache: Optional[Dict[str, Dict[str, List[Dict]]]] = None
    
    def get_first_guess_options(self) -> List[FirstGuessOption]:
        """Get all available first guess options.
        
        Returns:
            List of first guess options, cached after first load.
        """
        if self._first_guess_cache is not None:
            return self._first_guess_cache
        
        data_dir = Path(__file__).parent.joinpath('data')
        naive_32_file = data_dir.joinpath('phase2_naive_32.json')
        
        if not naive_32_file.exists():
            logger.warning(f"phase2_naive_32.json not found at {naive_32_file}")
            self._first_guess_cache = []
            return self._first_guess_cache
        
        try:
            with open(naive_32_file, 'r') as f:
                options = json.load(f)
            logger.debug(f"Loaded {len(options)} first guess options from phase2_naive_32.json")
        except Exception as e:
            logger.error(f"Error loading phase2_naive_32.json: {e}")
            self._first_guess_cache = []
            return self._first_guess_cache
        
        # Transform to match expected format
        self._first_guess_cache = []
        for entry in options:
            transformed: FirstGuessOption = {
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
            self._first_guess_cache.append(transformed)
        
        return self._first_guess_cache
    
    def get_strategy_lookup(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Get the full strategy lookup table.
        
        Returns:
            Dictionary mapping first_guess -> clue_pattern -> list of candidates.
            Cached after first load for O(1) access.
        """
        if self._strategy_lookup_cache is not None:
            return self._strategy_lookup_cache
        
        data_dir = Path(__file__).parent.joinpath('data')
        lookup_file = data_dir.joinpath('phase3_lookup.json')
        
        if not lookup_file.exists():
            logger.warning(f"phase3_lookup.json not found at {lookup_file}")
            self._strategy_lookup_cache = {}
            return self._strategy_lookup_cache
        
        try:
            with open(lookup_file, 'r') as f:
                self._strategy_lookup_cache = json.load(f)
            logger.debug(f"Loaded strategy lookup with {len(self._strategy_lookup_cache)} first guesses")
        except Exception as e:
            logger.error(f"Error loading phase3_lookup.json: {e}")
            self._strategy_lookup_cache = {}
            return self._strategy_lookup_cache
        
        return self._strategy_lookup_cache
    
    def get_second_guess(self, first_guess: str, clue_pattern: str) -> Optional[str]:
        """Get second guess recommendation for a first guess and clue pattern.
        
        O(1) lookup performance using cached strategy lookup.
        
        Args:
            first_guess: The first guess word (case-insensitive)
            clue_pattern: The clue pattern string (e.g., "GXXYG")
            
        Returns:
            Recommended second guess word, or None if not found
        """
        lookup = self.get_strategy_lookup()
        first_guess_upper = first_guess.upper()
        
        if first_guess_upper not in lookup:
            return None
        
        first_guess_data = lookup[first_guess_upper]
        candidates = first_guess_data.get(clue_pattern)
        
        if not candidates or len(candidates) == 0:
            return None
        
        return candidates[0]['second_guess']


# Global StrategyIndex instance for module-level functions
_strategy_index = StrategyIndex()

# Legacy module-level cache variables (deprecated, use StrategyIndex instead)
_first_guess_cache: Optional[List[FirstGuessOption]] = None
_strategy_lookup_cache: Optional[Dict[str, Dict[str, List[Dict]]]] = None


def _load_first_guess_options() -> List[FirstGuessOption]:
    """Load Phase 2 naive-32 first guess options from data file.
    
    Legacy function - use StrategyIndex.get_first_guess_options() instead.
    
    Returns:
        List of first guess options with metrics, cached after first load.
    """
    return _strategy_index.get_first_guess_options()


def _load_strategy_lookup() -> Dict[str, Dict[str, List[Dict]]]:
    """Load Phase 3 strategy lookup from data file.
    
    Legacy function - use StrategyIndex.get_strategy_lookup() instead.
    
    Returns:
        Dictionary mapping first_guess -> clue_pattern -> list of candidates.
        Cached after first load.
    """
    return _strategy_index.get_strategy_lookup()


def get_available_first_guesses() -> List[FirstGuessOption]:
    """Get all available first guess options with metrics.
    
    Returns all 32 naive patterns from Phase 2 analysis, sorted by rank.
    Each entry includes rank, guess, expected_remaining, and other metrics.
    
    Returns:
        List of first guess option dictionaries, each containing:
        - first_guess: str (the word, e.g., "RAISE")
        - rank: int (1-32, where 1 is best)
        - expected_remaining: float (average remaining words after first guess)
        - metrics: dict with max_remaining, clue_diversity, variance, std_dev
        - available: bool (always True for these 32 options)
        - coverage: float (estimated coverage, default 0.8125)
    
    Example:
        >>> options = get_available_first_guesses()
        >>> print(options[0]['first_guess'])  # Top-ranked guess
        'RAISE'
    """
    return _load_first_guess_options().copy()


def select_first_guess(user_choice: str) -> Optional[FirstGuessOption]:
    """Select and validate a first guess from available options.
    
    Args:
        user_choice: The first guess word selected by user (e.g., "RAISE", "STALE").
                     Case-insensitive.
        
    Returns:
        Dictionary with first guess information if found, None otherwise.
        Contains: first_guess, rank, expected_remaining, metrics, available, coverage.
    
    Example:
        >>> option = select_first_guess("RAISE")
        >>> print(option['rank'])
        1
    """
    available = get_available_first_guesses()
    user_choice_upper = user_choice.upper()
    
    for option in available:
        if option['first_guess'] == user_choice_upper:
            logger.debug(f"Selected first guess: {user_choice_upper} (rank {option['rank']})")
            return option
    
    logger.warning(f"First guess '{user_choice}' not found in available options")
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


def get_second_guess_recommendation(first_guess: str, clue: ClueTuple) -> Optional[str]:
    """Get recommended second guess for a (first_guess, clue) pair.
    
    This function provides O(1) lookup performance for second guess recommendations
    using the Phase 3 strategy lookup table.
    
    Args:
        first_guess: The first guess word (e.g., "RAISE", "ATONE"). Case-insensitive.
        clue: The clue tuple with 5 elements ('G', 'Y', 'B' or 'X', ...)
        
    Returns:
        Recommended second guess word if found, None otherwise.
    
    Example:
        >>> get_second_guess_recommendation("RAISE", ('G', 'Y', 'B', 'B', 'B'))
        'CLOUD'
    """
    lookup = _load_strategy_lookup()
    first_guess_upper = first_guess.upper()
    
    if first_guess_upper not in lookup:
        logger.debug(f"First guess '{first_guess_upper}' not found in strategy lookup")
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
        logger.debug(f"No strategy recommendation for pattern '{clue_pattern}' with first guess '{first_guess_upper}'")
        return None
    
    # Return the top-ranked (rank 1) second guess
    recommendation = candidates[0]['second_guess']
    logger.debug(f"Strategy recommendation for {first_guess_upper} + {clue_pattern}: {recommendation}")
    return recommendation
