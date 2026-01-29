import pytest
from src.utils import smart_optimize

def test_smart_optimize_strips_comments():
    content = """
def hello():
    # This is a comment
    print("hello") # Inline comment
    """
    optimized = smart_optimize(content)
    assert "# This is a comment" not in optimized
    assert "# Inline comment" not in optimized
    assert 'print("hello")' in optimized

def test_smart_optimize_preserves_code_blocks():
    content = """
Here is some code:
```python
# This should be minimized but preserved in place
def foo():
    pass
```
And more text.
    """
    optimized = smart_optimize(content)
    assert "def foo():" in optimized
    assert "Here is some code:" in optimized

def test_smart_optimize_empty_input():
    assert smart_optimize("") == ""
