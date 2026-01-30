"""Data validation and integrity checking for the 32word library.

This module provides centralized data validation, integrity checking, and
caching for all required data files in the 32word library.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Set up logging
logger = logging.getLogger(__name__)


class DataManager:
    """Manages data file loading, validation, and integrity checking.
    
    Provides centralized data validation and caching for all required data files
    in the 32word library. Validates file existence, JSON structure, and
    computes runtime checksums for integrity verification.
    """
    
    def __init__(self):
        """Initialize DataManager with data directory path."""
        self._data_dir = Path(__file__).parent.joinpath('data')
        self._validation_cache: Optional[List[str]] = None
        self._checksum_cache: Dict[str, str] = {}
        self._loaded_data_cache: Dict[str, any] = {}
    
    def _get_file_path(self, filename: str) -> Path:
        """Get full path to a data file."""
        return self._data_dir.joinpath(filename)
    
    def get_file_checksum(self, filepath: Path) -> str:
        """Compute MD5 checksum for a file at runtime.
        
        Args:
            filepath: Path to the file to checksum
            
        Returns:
            MD5 checksum as hexadecimal string
        """
        if str(filepath) in self._checksum_cache:
            return self._checksum_cache[str(filepath)]
        
        if not filepath.exists():
            return ""
        
        md5_hash = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        checksum = md5_hash.hexdigest()
        self._checksum_cache[str(filepath)] = checksum
        return checksum
    
    def verify_json_integrity(self, filepath: Path) -> Tuple[bool, Optional[str]]:
        """Validate JSON file structure and integrity.
        
        Args:
            filepath: Path to JSON file to validate
            
        Returns:
            Tuple of (is_valid, error_message). error_message is None if valid.
        """
        if not filepath.exists():
            return False, f"File does not exist: {filepath.name}"
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in {filepath.name}: {str(e)}"
        except Exception as e:
            return False, f"Error reading {filepath.name}: {str(e)}"
        
        # Validate structure based on filename
        filename = filepath.name
        
        if filename == 'phase2_naive_32.json':
            if not isinstance(data, list):
                return False, f"{filename}: Expected array, got {type(data).__name__}"
            if len(data) != 32:
                return False, f"{filename}: Expected 32 entries, got {len(data)}"
            required_fields = ['rank', 'guess', 'expected_remaining']
            for i, entry in enumerate(data):
                if not isinstance(entry, dict):
                    return False, f"{filename}: Entry {i} is not a dict"
                for field in required_fields:
                    if field not in entry:
                        return False, f"{filename}: Entry {i} missing required field '{field}'"
                if not isinstance(entry.get('guess', ''), str) or len(entry.get('guess', '')) != 5:
                    return False, f"{filename}: Entry {i} has invalid guess (must be 5-letter string)"
        
        elif filename == 'phase3_lookup.json':
            if not isinstance(data, dict):
                return False, f"{filename}: Expected dict, got {type(data).__name__}"
            # Validate structure: {first_guess: {clue_pattern: [{second_guess, rank, ...}, ...]}}
            for first_guess, patterns in data.items():
                if not isinstance(patterns, dict):
                    return False, f"{filename}: Invalid structure for first_guess '{first_guess}'"
                for clue_pattern, candidates in patterns.items():
                    if not isinstance(candidates, list):
                        return False, f"{filename}: Invalid candidates for pattern '{clue_pattern}'"
                    for candidate in candidates:
                        if not isinstance(candidate, dict):
                            return False, f"{filename}: Invalid candidate structure in '{clue_pattern}'"
                        if 'second_guess' not in candidate:
                            return False, f"{filename}: Candidate missing 'second_guess' in '{clue_pattern}'"
        
        elif filename == 'v1.0.json':
            if not isinstance(data, dict):
                return False, f"{filename}: Expected dict, got {type(data).__name__}"
            # Basic validation - structure should be compatible with Strategy class
            # This is a legacy file, so we're lenient on structure
        
        return True, None
    
    def _validate_word_list(self, filepath: Path, expected_min: int, expected_max: int) -> Tuple[bool, Optional[str]]:
        """Validate a word list file.
        
        Args:
            filepath: Path to word list file
            expected_min: Minimum expected word count
            expected_max: Maximum expected word count
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filepath.exists():
            return False, f"File does not exist: {filepath.name}"
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                words = []
                for line_num, line in enumerate(f, 1):
                    word = line.strip()
                    if word:
                        if len(word) != 5:
                            return False, f"{filepath.name}: Line {line_num} has invalid word length: '{word}'"
                        if not word.isalpha():
                            return False, f"{filepath.name}: Line {line_num} has non-alphabetic word: '{word}'"
                        words.append(word.upper())
            
            word_count = len(words)
            if word_count < expected_min:
                return False, f"{filepath.name}: Expected at least {expected_min} words, got {word_count}"
            if word_count > expected_max:
                return False, f"{filepath.name}: Expected at most {expected_max} words, got {word_count}"
            
            # Check for duplicates
            if len(words) != len(set(words)):
                return False, f"{filepath.name}: Contains duplicate words"
            
        except Exception as e:
            return False, f"Error reading {filepath.name}: {str(e)}"
        
        return True, None
    
    def validate_data_completeness(self) -> List[str]:
        """Validate that all required data files are present and valid.
        
        Returns:
            List of validation issue messages. Empty list if all data is valid.
        """
        # Use cached result if available
        if self._validation_cache is not None:
            logger.debug("Using cached validation results")
            return self._validation_cache
        
        logger.debug("Starting data completeness validation")
        issues = []
        
        # Required files with their validation functions
        # Note: Actual counts are higher than documented "standard" counts
        # due to extended word lists. Ranges allow for reasonable variation.
        required_files = {
            'targets.txt': lambda p: self._validate_word_list(p, 2300, 3200),
            'valid_guesses.txt': lambda p: self._validate_word_list(p, 12900, 15000),
            'phase2_naive_32.json': lambda p: self.verify_json_integrity(p),
            'phase3_lookup.json': lambda p: self.verify_json_integrity(p),
            'v1.0.json': lambda p: self.verify_json_integrity(p),
        }
        
        for filename, validate_func in required_files.items():
            filepath = self._get_file_path(filename)
            is_valid, error_msg = validate_func(filepath)
            if not is_valid:
                logger.warning(f"Validation failed for {filename}: {error_msg}")
                issues.append(f"{filename}: {error_msg}")
            else:
                logger.debug(f"Validation passed for {filename}")
        
        # Cache the result
        self._validation_cache = issues
        if issues:
            logger.warning(f"Data validation found {len(issues)} issue(s)")
        else:
            logger.info("All data files validated successfully")
        return issues
    
    def get_required_files(self) -> Dict[str, Dict]:
        """Get information about all required data files.
        
        Returns:
            Dictionary mapping filename to file info (size, checksum, exists)
        """
        required_files = [
            'targets.txt',
            'valid_guesses.txt',
            'phase2_naive_32.json',
            'phase3_lookup.json',
            'v1.0.json',
        ]
        
        result = {}
        for filename in required_files:
            filepath = self._get_file_path(filename)
            exists = filepath.exists()
            size = filepath.stat().st_size if exists else 0
            checksum = self.get_file_checksum(filepath) if exists else ""
            
            result[filename] = {
                'exists': exists,
                'size': size,
                'checksum': checksum,
                'path': str(filepath),
            }
        
        return result
    
    def load_all_data(self) -> Dict[str, any]:
        """Lazy-load and cache all data files.
        
        Returns:
            Dictionary mapping filename to loaded data
        """
        if self._loaded_data_cache:
            return self._loaded_data_cache
        
        result = {}
        
        # Load word lists
        from .data_loader import load_targets, load_valid_guesses
        result['targets'] = load_targets()
        result['valid_guesses'] = load_valid_guesses()
        
        # Load JSON files
        json_files = ['phase2_naive_32.json', 'phase3_lookup.json', 'v1.0.json']
        for filename in json_files:
            filepath = self._get_file_path(filename)
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    result[filename] = json.load(f)
            else:
                result[filename] = None
        
        self._loaded_data_cache = result
        return result


# Module-level singleton instance
_data_manager_instance: Optional[DataManager] = None


def get_data_manager() -> DataManager:
    """Get the singleton DataManager instance.
    
    Returns:
        DataManager instance
    """
    global _data_manager_instance
    if _data_manager_instance is None:
        _data_manager_instance = DataManager()
    return _data_manager_instance
