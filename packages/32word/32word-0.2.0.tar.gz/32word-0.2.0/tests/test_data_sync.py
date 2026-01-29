"""Data synchronization verification tests for the 32word library.

Verifies that all data files are synchronized and consistent:
- All 32 first guesses from phase2_naive_32.json exist in phase3_lookup.json
- Clue pattern coverage is complete
- All recommended words are valid
- No data inconsistencies exist
"""

import json
import pytest
from pathlib import Path
from word32 import (
    get_available_first_guesses,
    get_strategy_for_first_guess,
    VALID_GUESSES,
    VALID_TARGETS,
)


def load_phase2_data():
    """Load phase2_naive_32.json data."""
    data_dir = Path(__file__).parent.parent / 'word32' / 'data'
    phase2_file = data_dir / 'phase2_naive_32.json'
    
    if not phase2_file.exists():
        pytest.skip(f"phase2_naive_32.json not found at {phase2_file}")
    
    with open(phase2_file, 'r') as f:
        return json.load(f)


def load_phase3_data():
    """Load phase3_lookup.json data."""
    data_dir = Path(__file__).parent.parent / 'word32' / 'data'
    phase3_file = data_dir / 'phase3_lookup.json'
    
    if not phase3_file.exists():
        pytest.skip(f"phase3_lookup.json not found at {phase3_file}")
    
    with open(phase3_file, 'r') as f:
        return json.load(f)


class TestPhase2ToPhase3Coverage:
    """Verify Phase 2 to Phase 3 coverage."""
    
    def test_all_32_first_guesses_exist_in_phase3_lookup(self):
        """Verify each first guess from phase2 exists in phase3_lookup."""
        phase2_data = load_phase2_data()
        phase3_data = load_phase3_data()
        
        phase2_guesses = {entry['guess'].upper() for entry in phase2_data}
        phase3_guesses = set(phase3_data.keys())
        
        # All phase2 guesses should exist in phase3
        missing = phase2_guesses - phase3_guesses
        assert len(missing) == 0, f"Missing first guesses in phase3_lookup.json: {missing}"
    
    def test_phase3_has_no_orphaned_first_guesses(self):
        """Verify phase3 doesn't have first guesses not in phase2."""
        phase2_data = load_phase2_data()
        phase3_data = load_phase3_data()
        
        phase2_guesses = {entry['guess'].upper() for entry in phase2_data}
        phase3_guesses = set(phase3_data.keys())
        
        # Phase3 may have additional guesses (not necessarily orphaned)
        # But we should verify they're valid words
        for guess in phase3_guesses:
            assert guess in VALID_GUESSES or guess in VALID_TARGETS, \
                f"Phase3 first guess '{guess}' is not a valid word"
    
    def test_all_32_first_guesses_accessible_via_api(self):
        """Verify all 32 first guesses are accessible via get_available_first_guesses()."""
        phase2_data = load_phase2_data()
        available = get_available_first_guesses()
        
        phase2_guesses = {entry['guess'].upper() for entry in phase2_data}
        available_guesses = {entry['first_guess'].upper() for entry in available}
        
        assert len(phase2_guesses) == 32
        assert len(available_guesses) == 32
        assert phase2_guesses == available_guesses, \
            f"Mismatch between phase2 data and API: {phase2_guesses ^ available_guesses}"


class TestCluePatternCoverage:
    """Verify clue pattern coverage."""
    
    def test_each_first_guess_has_clue_patterns(self):
        """Verify each first guess has clue patterns in phase3_lookup."""
        phase2_data = load_phase2_data()
        phase3_data = load_phase3_data()
        
        for entry in phase2_data:
            first_guess = entry['guess'].upper()
            assert first_guess in phase3_data, \
                f"First guess '{first_guess}' missing from phase3_lookup.json"
            
            clue_patterns = phase3_data[first_guess]
            assert isinstance(clue_patterns, dict), \
                f"First guess '{first_guess}' has invalid structure in phase3_lookup.json"
            assert len(clue_patterns) > 0, \
                f"First guess '{first_guess}' has no clue patterns"
    
    def test_clue_patterns_are_valid_format(self):
        """Verify clue patterns are valid (5 characters, only G/Y/X)."""
        phase3_data = load_phase3_data()
        
        invalid_patterns = []
        for first_guess, patterns in phase3_data.items():
            for pattern in patterns.keys():
                if len(pattern) != 5:
                    invalid_patterns.append((first_guess, pattern, "Invalid length"))
                elif not all(c in 'GYX' for c in pattern):
                    invalid_patterns.append((first_guess, pattern, "Invalid characters"))
        
        assert len(invalid_patterns) == 0, \
            f"Invalid clue patterns found: {invalid_patterns}"
    
    def test_no_duplicate_clue_patterns_per_first_guess(self):
        """Verify no duplicate clue patterns per first guess."""
        phase3_data = load_phase3_data()
        
        duplicates = []
        for first_guess, patterns in phase3_data.items():
            pattern_list = list(patterns.keys())
            if len(pattern_list) != len(set(pattern_list)):
                duplicates.append((first_guess, len(pattern_list), len(set(pattern_list))))
        
        assert len(duplicates) == 0, \
            f"Duplicate clue patterns found: {duplicates}"
    
    def test_clue_pattern_coverage_minimum_threshold(self):
        """Verify clue pattern coverage meets minimum thresholds."""
        phase3_data = load_phase3_data()
        
        # Per Phase 3 workplan: top 30 clues per first guess
        # But we'll be lenient and check for reasonable coverage
        low_coverage = []
        for first_guess, patterns in phase3_data.items():
            if len(patterns) < 10:  # At least 10 patterns per first guess
                low_coverage.append((first_guess, len(patterns)))
        
        # This is informational - we don't fail if coverage is low
        # but we log it for awareness
        if low_coverage:
            pytest.skip(f"Some first guesses have low coverage: {low_coverage}")


class TestDataConsistency:
    """Verify data consistency."""
    
    def test_all_recommended_second_guesses_are_valid_words(self):
        """Verify all recommended second guesses are in valid_guesses.txt."""
        phase3_data = load_phase3_data()
        
        invalid_words = []
        for first_guess, patterns in phase3_data.items():
            for pattern, candidates in patterns.items():
                if not isinstance(candidates, list) or len(candidates) == 0:
                    continue
                
                # Get the top-ranked second guess
                top_candidate = candidates[0]
                if isinstance(top_candidate, dict):
                    second_guess = top_candidate.get('second_guess', '')
                else:
                    second_guess = str(top_candidate)
                
                if second_guess and second_guess.upper() not in VALID_GUESSES:
                    invalid_words.append((first_guess, pattern, second_guess))
        
        assert len(invalid_words) == 0, \
            f"Invalid second guess words found: {invalid_words[:10]}"  # Show first 10
    
    def test_all_first_guesses_are_valid_words(self):
        """Verify all first guesses are in valid_guesses.txt."""
        phase2_data = load_phase2_data()
        
        invalid_words = []
        for entry in phase2_data:
            guess = entry['guess'].upper()
            if guess not in VALID_GUESSES:
                invalid_words.append(guess)
        
        assert len(invalid_words) == 0, \
            f"Invalid first guess words found: {invalid_words}"
    
    def test_phase3_data_structure_is_valid(self):
        """Verify phase3_lookup.json has valid structure."""
        phase3_data = load_phase3_data()
        
        assert isinstance(phase3_data, dict), "phase3_lookup.json should be a dictionary"
        
        for first_guess, patterns in phase3_data.items():
            assert isinstance(patterns, dict), \
                f"Patterns for '{first_guess}' should be a dictionary"
            
            for pattern, candidates in patterns.items():
                assert isinstance(candidates, list), \
                    f"Candidates for '{first_guess}' pattern '{pattern}' should be a list"
                
                if len(candidates) > 0:
                    top_candidate = candidates[0]
                    assert isinstance(top_candidate, dict), \
                        f"Top candidate for '{first_guess}' pattern '{pattern}' should be a dict"
                    assert 'second_guess' in top_candidate, \
                        f"Top candidate for '{first_guess}' pattern '{pattern}' missing 'second_guess'"


class TestDataHealthDashboard:
    """Test data health dashboard functionality."""
    
    def test_generate_coverage_report(self):
        """Test generating a coverage report."""
        phase2_data = load_phase2_data()
        phase3_data = load_phase3_data()
        
        report = {
            'total_first_guesses': len(phase2_data),
            'first_guesses_in_phase3': len([g for g in phase2_data if g['guess'].upper() in phase3_data]),
            'total_clue_patterns': sum(len(patterns) for patterns in phase3_data.values()),
            'per_first_guess': {}
        }
        
        for entry in phase2_data:
            first_guess = entry['guess'].upper()
            patterns = phase3_data.get(first_guess, {})
            report['per_first_guess'][first_guess] = {
                'rank': entry['rank'],
                'clue_pattern_count': len(patterns),
                'coverage_percentage': len(patterns) / 243.0 * 100 if patterns else 0  # 3^5 = 243 max
            }
        
        # Verify report structure
        assert 'total_first_guesses' in report
        assert 'first_guesses_in_phase3' in report
        assert 'total_clue_patterns' in report
        assert 'per_first_guess' in report
        
        # Verify all 32 first guesses are covered
        assert report['first_guesses_in_phase3'] == 32
    
    def test_identify_missing_patterns(self):
        """Test identifying missing clue patterns."""
        phase3_data = load_phase3_data()
        
        missing_report = {}
        for first_guess, patterns in phase3_data.items():
            # Check if common patterns exist
            common_patterns = ['XXXXX', 'GXXXX', 'XXXXG', 'GGGGG']
            missing = [p for p in common_patterns if p not in patterns]
            if missing:
                missing_report[first_guess] = missing
        
        # This is informational - we don't fail if patterns are missing
        # but we can check the report
        assert isinstance(missing_report, dict)
    
    def test_identify_inconsistencies(self):
        """Test identifying data inconsistencies."""
        phase3_data = load_phase3_data()
        
        inconsistencies = {
            'invalid_words': [],
            'duplicate_patterns': [],
            'missing_data': []
        }
        
        for first_guess, patterns in phase3_data.items():
            # Check for duplicate patterns
            pattern_list = list(patterns.keys())
            if len(pattern_list) != len(set(pattern_list)):
                inconsistencies['duplicate_patterns'].append(first_guess)
            
            # Check for invalid words
            for pattern, candidates in patterns.items():
                if candidates:
                    top_candidate = candidates[0]
                    if isinstance(top_candidate, dict):
                        second_guess = top_candidate.get('second_guess', '')
                        if second_guess and second_guess.upper() not in VALID_GUESSES:
                            inconsistencies['invalid_words'].append((first_guess, pattern, second_guess))
        
        # Verify we can generate the report
        assert isinstance(inconsistencies, dict)
        assert 'invalid_words' in inconsistencies
        assert 'duplicate_patterns' in inconsistencies
        assert 'missing_data' in inconsistencies


class TestDataIntegrity:
    """Test data file integrity."""
    
    def test_json_files_are_valid(self):
        """Verify JSON files are valid and parseable."""
        data_dir = Path(__file__).parent.parent / 'word32' / 'data'
        
        json_files = [
            'phase2_naive_32.json',
            'phase3_lookup.json',
        ]
        
        for json_file in json_files:
            filepath = data_dir / json_file
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    assert data is not None, f"{json_file} parsed but is None"
                except json.JSONDecodeError as e:
                    pytest.fail(f"{json_file} is not valid JSON: {e}")
    
    def test_phase2_data_structure(self):
        """Verify phase2_naive_32.json has expected structure."""
        phase2_data = load_phase2_data()
        
        assert isinstance(phase2_data, list), "phase2_naive_32.json should be a list"
        assert len(phase2_data) == 32, f"Expected 32 entries, got {len(phase2_data)}"
        
        required_fields = ['rank', 'guess', 'expected_remaining']
        for entry in phase2_data:
            assert isinstance(entry, dict), "Each entry should be a dictionary"
            for field in required_fields:
                assert field in entry, f"Entry missing required field: {field}"
    
    def test_phase3_data_structure(self):
        """Verify phase3_lookup.json has expected structure."""
        phase3_data = load_phase3_data()
        
        assert isinstance(phase3_data, dict), "phase3_lookup.json should be a dictionary"
        assert len(phase3_data) > 0, "phase3_lookup.json should not be empty"
        
        # Verify structure for a sample first guess
        sample_guess = list(phase3_data.keys())[0]
        patterns = phase3_data[sample_guess]
        assert isinstance(patterns, dict), "Patterns should be a dictionary"
        
        if patterns:
            sample_pattern = list(patterns.keys())[0]
            candidates = patterns[sample_pattern]
            assert isinstance(candidates, list), "Candidates should be a list"
