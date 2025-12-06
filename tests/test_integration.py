"""Integration test for engine main() function."""

from engine import main


def test_main_as_script():
    """Test that main() can be called directly without errors."""
    # This hits the if __name__ == "__main__" path indirectly
    try:
        main()
        success = True
    except Exception:
        success = False
    
    assert success
