"""Tests for utility functions."""

from ralphy.utils import slugify, calculate_cost


def test_slugify_basic():
    """Test basic slugification."""
    assert slugify("Hello World") == "hello-world"


def test_slugify_special_chars():
    """Test slugification with special characters."""
    assert slugify("Add dark mode toggle!") == "add-dark-mode-toggle"


def test_slugify_max_length():
    """Test slugification respects max length."""
    long_text = "This is a very long task description that should be truncated"
    result = slugify(long_text, max_length=20)
    assert len(result) <= 20


def test_slugify_strips_hyphens():
    """Test that leading/trailing hyphens are stripped."""
    assert slugify("  test  ") == "test"
    assert slugify("--test--") == "test"


def test_calculate_cost():
    """Test cost calculation."""
    cost = calculate_cost(1000, 500)
    # 1000 * 0.000003 + 500 * 0.000015 = 0.003 + 0.0075 = 0.0105
    assert cost == "0.0105"


def test_calculate_cost_zero():
    """Test cost calculation with zero tokens."""
    cost = calculate_cost(0, 0)
    assert cost == "0.0000"
