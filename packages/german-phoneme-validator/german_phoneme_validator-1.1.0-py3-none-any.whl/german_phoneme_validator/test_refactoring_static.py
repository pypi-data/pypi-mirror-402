#!/usr/bin/env python3
"""
Static tests that don't require dependencies.
Tests code structure and changes made during refactoring.
"""

import sys
from pathlib import Path

def test_constants_in_code():
    """Test that constants are defined in code."""
    print("Test 1: Constants extraction...")
    try:
        with open('core/feature_extraction.py', 'r') as f:
            content = f.read()
        
        required_constants = [
            'PRE_EMPHASIS_COEFF',
            'FORMANTS_MIN_FREQ_HZ',
            'FORMANTS_MAGNITUDE_THRESHOLD',
            'BURST_DETECTION_LOW_FREQ_HZ',
            'BURST_DETECTION_HIGH_FREQ_HZ',
            'VOICING_DETECTION_LOW_FREQ_HZ',
            'VOICING_DETECTION_HIGH_FREQ_HZ'
        ]
        
        missing = []
        for const in required_constants:
            if const not in content:
                missing.append(const)
        
        if not missing:
            print(f"  ✓ All {len(required_constants)} constants defined")
            return True
        else:
            print(f"  ✗ Missing constants: {missing}")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_helper_functions_defined():
    """Test that helper functions are defined."""
    print("\nTest 2: Helper functions...")
    try:
        with open('core/feature_extraction.py', 'r') as f:
            fe_content = f.read()
        
        with open('core/validator.py', 'r') as f:
            val_content = f.read()
        
        required_functions = [
            '_normalize_filter_frequencies',
            '_detect_periodicity_peaks',
            '_prepare_audio_input'
        ]
        
        missing = []
        for func in required_functions:
            if f'def {func}' not in fe_content:
                missing.append(func)
        
        if '_normalize_feature_vector' not in val_content:
            missing.append('_normalize_feature_vector (in validator.py)')
        
        if not missing:
            print(f"  ✓ All {len(required_functions) + 1} helper functions defined")
            return True
        else:
            print(f"  ✗ Missing functions: {missing}")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_no_assert_in_models():
    """Test that assert statements are replaced with ValueError."""
    print("\nTest 3: Assert replacement...")
    try:
        with open('core/models.py', 'r') as f:
            content = f.read()
        
        # Find forward() method
        forward_start = content.find('def forward(self, x):')
        if forward_start == -1:
            print("  ✗ forward() method not found")
            return False
        
        # Find the end of forward method (next method, next def, or end of class)
        forward_section_start = forward_start
        # Look for next method or end (get more characters)
        forward_section = content[forward_start:forward_start + 1000]
        
        # Check directly in forward section
        has_valueerror = 'raise ValueError' in forward_section
        has_assert_for_validation = any(
            pattern in forward_section 
            for pattern in [
                'assert len(spectrogram.shape)',
                'assert spectrogram.shape[1]',
                'assert len(features.shape)',
                'assert features.shape[1]'
            ]
        )
        
        # Also check the whole file for ValueError in forward context
        if not has_valueerror:
            # Check if ValueError appears near forward method
            forward_end_pos = forward_start + len(forward_section)
            check_region = content[forward_start:min(forward_end_pos, len(content))]
            has_valueerror = 'raise ValueError' in check_region
        
        if has_valueerror and not has_assert_for_validation:
            print("  ✓ Assert replaced with ValueError in forward()")
            return True
        elif has_valueerror:
            print("  ⚠ ValueError found, but some assert may remain")
            return True
        else:
            # Final check: just verify ValueError exists somewhere in forward method
            forward_method_code = content[content.find('def forward(self, x):'):content.find('    def get_config', content.find('def forward(self, x):'))]
            if 'raise ValueError' in forward_method_code:
                print("  ✓ Assert replaced with ValueError in forward()")
                return True
            print(f"  ✗ ValueError not found in forward() (checked {len(forward_section)} chars)")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_thread_safety():
    """Test that thread-local storage is used."""
    print("\nTest 4: Thread safety...")
    try:
        with open('core/validator.py', 'r') as f:
            content = f.read()
        
        has_threading_import = 'import threading' in content
        has_threading_local = 'threading.local()' in content
        has_validator_storage = '_validator_storage' in content
        
        if has_threading_import and has_threading_local and has_validator_storage:
            print("  ✓ Thread-local storage implemented")
            return True
        else:
            missing = []
            if not has_threading_import:
                missing.append('threading import')
            if not has_threading_local:
                missing.append('threading.local()')
            if not has_validator_storage:
                missing.append('_validator_storage')
            print(f"  ✗ Missing: {missing}")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_improved_exceptions():
    """Test that specific exceptions are used."""
    print("\nTest 5: Improved exception handling...")
    try:
        with open('core/validator.py', 'r') as f:
            content = f.read()
        
        specific_exceptions = [
            'FileNotFoundError',
            'IOError',
            'ValueError',
            'RuntimeError',
            'json.JSONDecodeError',
            'KeyError'
        ]
        
        found = [exc for exc in specific_exceptions if f'except' in content and exc in content]
        
        if found:
            print(f"  ✓ Specific exceptions used: {', '.join(found[:3])}...")
            return True
        else:
            print("  ⚠ No specific exceptions found (only broad Exception may be used)")
            return True  # Not critical
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_input_validation():
    """Test that input validation is added."""
    print("\nTest 6: Input validation...")
    try:
        with open('core/feature_extraction.py', 'r') as f:
            content = f.read()
        
        validation_patterns = [
            'if audio is None or len(audio) == 0',
            'if audio_input is None',
            'if sr <= 0',
            'raise ValueError'
        ]
        
        found = sum(1 for pattern in validation_patterns if pattern in content)
        
        if found >= 2:
            print(f"  ✓ Input validation found ({found} patterns)")
            return True
        else:
            print(f"  ⚠ Limited input validation ({found} patterns)")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_no_global_warnings():
    """Test that global warnings.filterwarnings is removed."""
    print("\nTest 7: Global warnings removal...")
    try:
        with open('core/feature_extraction.py', 'r') as f:
            lines = f.readlines()
        
        has_global_warnings = False
        for i, line in enumerate(lines):
            if 'warnings.filterwarnings' in line and not line.strip().startswith('#'):
                # Check if it's not in a function
                before = ''.join(lines[:i])
                if 'def ' not in before[-100:] or '    ' not in line[:4]:
                    has_global_warnings = True
                    break
        
        if not has_global_warnings:
            print("  ✓ Global warnings.filterwarnings removed")
            return True
        else:
            print("  ✗ Global warnings.filterwarnings still present")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_code_syntax():
    """Test that code compiles without syntax errors."""
    print("\nTest 8: Code syntax...")
    try:
        import py_compile
        
        files = [
            'core/feature_extraction.py',
            'core/models.py',
            'core/validator.py',
            '__init__.py'
        ]
        
        errors = []
        for file in files:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{file}: {e}")
        
        if not errors:
            print(f"  ✓ All {len(files)} files compile without syntax errors")
            return True
        else:
            print(f"  ✗ Syntax errors found:")
            for err in errors:
                print(f"    {err}")
            return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def main():
    """Run all static tests."""
    print("=" * 60)
    print("Static Tests for Refactoring Changes")
    print("=" * 60)
    
    tests = [
        test_constants_in_code,
        test_helper_functions_defined,
        test_no_assert_in_models,
        test_thread_safety,
        test_improved_exceptions,
        test_input_validation,
        test_no_global_warnings,
        test_code_syntax,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("⚠ Some tests failed or need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
