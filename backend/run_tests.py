import sys
import pytest

if __name__ == "__main__":
    with open("test_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        pytest.main(["-v", "-l", "tests/test_integration_e2e.py"])
