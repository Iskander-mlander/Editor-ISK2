"""
Test Runner
===========
Runs all unit tests for Editor ISK.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_tests():
    """Discover and run all tests."""
    # Configure test discovery
    loader = unittest.TestLoader()
    
    # Discover tests in unit directory
    suite = loader.discover(
        os.path.join(os.path.dirname(__file__), 'unit'),
        pattern='test_*.py'
    )
    
    return suite


def run_tests():
    """Run all tests and return results."""
    suite = discover_tests()
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)