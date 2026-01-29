"""
Pytest configuration and fixtures for file-compass tests.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing."""
    return '''
def hello(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtract b from a."""
        return a - b
'''


@pytest.fixture
def sample_markdown():
    """Sample Markdown content for testing."""
    return '''
# Project Title

A description of the project.

## Installation

Run `pip install project`.

## Usage

```python
import project
project.run()
```

## License

MIT
'''


@pytest.fixture
def temp_python_file(tmp_path, sample_python_code):
    """Create a temporary Python file."""
    file_path = tmp_path / "test_module.py"
    file_path.write_text(sample_python_code)
    return file_path


@pytest.fixture
def temp_markdown_file(tmp_path, sample_markdown):
    """Create a temporary Markdown file."""
    file_path = tmp_path / "README.md"
    file_path.write_text(sample_markdown)
    return file_path
