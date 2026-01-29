"""Custom exceptions for the 32word library.

Provides specific exception types for different error conditions,
enabling better error handling and clearer error messages.
"""


class Word32Error(Exception):
    """Base exception for all 32word library errors."""
    pass


class DataValidationError(Word32Error):
    """Raised when data file validation fails.
    
    Attributes:
        filename: Name of the file that failed validation
        message: Detailed error message
    """
    def __init__(self, filename: str, message: str):
        self.filename = filename
        self.message = message
        super().__init__(f"Data validation error in {filename}: {message}")


class StrategyNotFoundError(Word32Error):
    """Raised when a requested strategy cannot be found.
    
    Attributes:
        strategy_name: Name or identifier of the missing strategy
        message: Detailed error message
    """
    def __init__(self, strategy_name: str, message: str = ""):
        self.strategy_name = strategy_name
        self.message = message
        if message:
            super().__init__(f"Strategy '{strategy_name}' not found: {message}")
        else:
            super().__init__(f"Strategy '{strategy_name}' not found")


class InvalidClueError(Word32Error):
    """Raised when an invalid clue tuple is provided.
    
    Attributes:
        clue: The invalid clue that was provided
        message: Detailed error message
    """
    def __init__(self, clue, message: str = ""):
        self.clue = clue
        self.message = message
        if message:
            super().__init__(f"Invalid clue {clue}: {message}")
        else:
            super().__init__(f"Invalid clue: {clue}")


class InvalidGuessError(Word32Error):
    """Raised when an invalid guess word is provided.
    
    Attributes:
        guess: The invalid guess that was provided
        message: Detailed error message
    """
    def __init__(self, guess: str, message: str = ""):
        self.guess = guess
        self.message = message
        if message:
            super().__init__(f"Invalid guess '{guess}': {message}")
        else:
            super().__init__(f"Invalid guess: '{guess}'")
