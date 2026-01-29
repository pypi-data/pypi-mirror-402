"""Tests for core utility functions."""

import pytest

from simple_utils.core import (
    add_numbers,
    divide_numbers,
    format_currency,
    is_even,
    max_numbers,
    min_numbers,
    multiply_numbers,
    multiply_three_numbers,
    print_message,
    square_numbers,
)


class TestPrintMessage:
    """Tests for the print_message function."""

    def test_print_message_valid_string(self, capsys):
        """Test printing a valid string message."""
        message = "Hello, World!"
        print_message(message)

        captured = capsys.readouterr()
        assert captured.out.strip() == message

    def test_print_message_empty_string(self, capsys):
        """Test printing an empty string."""
        print_message("")

        captured = capsys.readouterr()
        assert captured.out.strip() == ""

    def test_print_message_multiline(self, capsys):
        """Test printing a multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        print_message(message)

        captured = capsys.readouterr()
        assert captured.out.strip() == message

    def test_print_message_with_special_characters(self, capsys):
        """Test printing message with special characters."""
        message = "Special chars: !@#$%^&*()_+-=[]{}|;':,.<>?"
        print_message(message)

        captured = capsys.readouterr()
        assert captured.out.strip() == message

    def test_print_message_type_error(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="Expected str, got int"):
            print_message(123)

        with pytest.raises(TypeError, match="Expected str, got list"):
            print_message(["not", "a", "string"])

        with pytest.raises(TypeError, match="Expected str, got NoneType"):
            print_message(None)


class TestAddNumbers:
    """Tests for the add_numbers function."""

    def test_add_integers(self):
        """Test adding two integers."""
        result = add_numbers(2, 3)
        assert result == 5
        assert isinstance(result, int)

    def test_add_floats(self):
        """Test adding two floats."""
        result = add_numbers(2.5, 1.5)
        assert result == 4.0
        assert isinstance(result, float)

    def test_add_mixed_types(self):
        """Test adding integer and float."""
        result1 = add_numbers(10, 3.14)
        assert result1 == 13.14
        assert isinstance(result1, float)

        result2 = add_numbers(2.7, 5)
        assert result2 == 7.7
        assert isinstance(result2, float)

    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        result = add_numbers(-5, 3)
        assert result == -2

        result = add_numbers(-2.5, -1.5)
        assert result == -4.0

    def test_add_zero(self):
        """Test adding with zero."""
        assert add_numbers(0, 5) == 5
        assert add_numbers(3.14, 0) == 3.14
        assert add_numbers(0, 0) == 0

    def test_add_large_numbers(self):
        """Test adding large numbers."""
        result = add_numbers(1_000_000, 2_000_000)
        assert result == 3_000_000

        result = add_numbers(1.23e10, 4.56e10)
        assert result == 5.79e10

    def test_add_numbers_type_error(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got str"
        ):
            add_numbers("not a number", 5)

        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got list"
        ):
            add_numbers(5, [1, 2, 3])

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got NoneType"
        ):
            add_numbers(None, 5)

        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got dict"
        ):
            add_numbers(5, {})


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_workflow_example(self, capsys):
        """Test a typical workflow using both functions."""
        # Calculate sum
        result = add_numbers(10.5, 5.3)

        # Print the result
        print_message(f"The sum is: {result}")

        # Verify the calculation
        assert result == 15.8

        # Verify the printed output
        captured = capsys.readouterr()
        assert captured.out.strip() == "The sum is: 15.8"


class TestMultiplyNumbers:
    """Tests for the multiply_numbers function."""

    def test_multiply_integers(self):
        """Test multiplying two integers."""
        result = multiply_numbers(2, 3)
        assert result == 6
        assert isinstance(result, int)

    def test_multiply_floats(self):
        """Test multiplying two floats."""
        result = multiply_numbers(2.5, 4.0)
        assert result == 10.0
        assert isinstance(result, float)

    def test_multiply_mixed_types(self):
        """Test multiplying integer and float."""
        result1 = multiply_numbers(3, 1.5)
        assert result1 == 4.5
        assert isinstance(result1, float)

        result2 = multiply_numbers(2.5, 4)
        assert result2 == 10.0
        assert isinstance(result2, float)

    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        result = multiply_numbers(-2, 3)
        assert result == -6

        result = multiply_numbers(-2.5, -2.0)
        assert result == 5.0

    def test_multiply_with_zero(self):
        """Test multiplying with zero."""
        assert multiply_numbers(0, 5) == 0
        assert multiply_numbers(3.14, 0) == 0.0
        assert multiply_numbers(0, 0) == 0

    def test_multiply_large_numbers(self):
        """Test multiplying large numbers."""
        result = multiply_numbers(1_000, 2_000)
        assert result == 2_000_000

        result = multiply_numbers(1.5e5, 2.0e3)
        assert result == 3.0e8

    def test_multiply_numbers_type_error(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got str"
        ):
            multiply_numbers("not a number", 5)

        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got list"
        ):
            multiply_numbers(5, [1, 2, 3])

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got NoneType"
        ):
            multiply_numbers(None, 5)

        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got dict"
        ):
            multiply_numbers(5, {})


class TestDivideNumbers:
    """Tests for the divide_numbers function."""

    def test_divide_positive_integers(self):
        """Test dividing positive integers."""
        result = divide_numbers(10, 2)
        assert result == 5.0
        assert isinstance(result, float)

    def test_divide_with_remainder(self):
        """Test division that results in a decimal."""
        result = divide_numbers(7, 2)
        assert result == 3.5

    def test_divide_floats(self):
        """Test dividing float numbers."""
        result = divide_numbers(15.0, 3.0)
        assert result == 5.0

    def test_divide_mixed_types(self):
        """Test dividing mixed int and float."""
        result1 = divide_numbers(10, 4.0)
        assert result1 == 2.5

        result2 = divide_numbers(7.5, 3)
        assert result2 == 2.5

    def test_divide_negative_numbers(self):
        """Test dividing with negative numbers."""
        assert divide_numbers(-10, 2) == -5.0
        assert divide_numbers(10, -2) == -5.0
        assert divide_numbers(-10, -2) == 5.0

    def test_divide_by_one(self):
        """Test dividing by one."""
        assert divide_numbers(42, 1) == 42.0
        assert divide_numbers(-42, 1) == -42.0

    def test_divide_one_by_number(self):
        """Test dividing one by a number."""
        result = divide_numbers(1, 3)
        assert abs(result - 0.3333333333333333) < 1e-10

    def test_divide_zero_by_number(self):
        """Test dividing zero by a number."""
        assert divide_numbers(0, 5) == 0.0
        assert divide_numbers(0, -5) == 0.0

    def test_divide_by_zero_error(self):
        """Test that ZeroDivisionError is raised when dividing by zero."""
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            divide_numbers(10, 0)

        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            divide_numbers(-5, 0)

        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            divide_numbers(0, 0)

    def test_divide_type_error_first_argument(self):
        """Test that TypeError is raised for invalid first argument type."""
        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got str"
        ):
            divide_numbers("invalid", 2)

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got list"
        ):
            divide_numbers([1, 2, 3], 2)

    def test_divide_type_error_second_argument(self):
        """Test that TypeError is raised for invalid second argument type."""
        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got str"
        ):
            divide_numbers(10, "invalid")

        with pytest.raises(
            TypeError, match="Argument 'b' must be int or float, got dict"
        ):
            divide_numbers(10, {"key": "value"})


class TestSquareNumbers:
    """Tests for the square_numbers function."""

    def test_square_positive_integer(self):
        """Test squaring positive integers."""
        assert square_numbers(4) == 16
        assert isinstance(square_numbers(4), int)

        assert square_numbers(5) == 25
        assert isinstance(square_numbers(5), int)

    def test_square_negative_integer(self):
        """Test squaring negative integers."""
        assert square_numbers(-3) == 9
        assert isinstance(square_numbers(-3), int)

        assert square_numbers(-7) == 49
        assert isinstance(square_numbers(-7), int)

    def test_square_zero(self):
        """Test squaring zero."""
        assert square_numbers(0) == 0
        assert isinstance(square_numbers(0), int)

    def test_square_one(self):
        """Test squaring one."""
        assert square_numbers(1) == 1
        assert isinstance(square_numbers(1), int)

        assert square_numbers(-1) == 1
        assert isinstance(square_numbers(-1), int)

    def test_square_floats(self):
        """Test squaring float numbers."""
        assert square_numbers(2.5) == 6.25
        assert isinstance(square_numbers(2.5), float)

        assert square_numbers(-1.5) == 2.25
        assert isinstance(square_numbers(-1.5), float)

    def test_square_float_zero(self):
        """Test squaring float zero."""
        assert square_numbers(0.0) == 0.0
        assert isinstance(square_numbers(0.0), float)

    def test_square_decimal_values(self):
        """Test squaring decimal values."""
        result = square_numbers(0.5)
        assert result == 0.25
        assert isinstance(result, float)

        result = square_numbers(0.1)
        assert abs(result - 0.01) < 1e-10
        assert isinstance(result, float)

    def test_square_large_numbers(self):
        """Test squaring large numbers."""
        assert square_numbers(100) == 10000
        assert square_numbers(1000) == 1000000

    def test_square_small_decimals(self):
        """Test squaring very small decimal numbers."""
        result = square_numbers(0.001)
        assert abs(result - 0.000001) < 1e-12
        assert isinstance(result, float)

    def test_square_type_error(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got str"
        ):
            square_numbers("invalid")

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got list"
        ):
            square_numbers([1, 2, 3])

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got NoneType"
        ):
            square_numbers(None)

        with pytest.raises(
            TypeError, match="Argument 'a' must be int or float, got dict"
        ):
            square_numbers({"key": "value"})


class TestMaxNumbers:
    """Tests for the max_numbers function."""

    def test_max_numbers_integers(self):
        """Test max with integer inputs."""
        assert max_numbers(5, 3) == 5
        assert max_numbers(10, 15) == 15
        assert max_numbers(-5, -10) == -5
        assert max_numbers(0, 0) == 0

    def test_max_numbers_floats(self):
        """Test max with float inputs."""
        assert max_numbers(5.5, 3.3) == 5.5
        assert max_numbers(1.1, 1.9) == 1.9
        assert max_numbers(-2.5, -1.5) == -1.5

    def test_max_numbers_mixed_types(self):
        """Test max with mixed int and float inputs."""
        assert max_numbers(5, 3.3) == 5
        assert max_numbers(2.7, 3) == 3
        assert max_numbers(-1.5, -2) == -1.5

    def test_max_numbers_equal_values(self):
        """Test max with equal values."""
        assert max_numbers(42, 42) == 42
        assert max_numbers(3.14, 3.14) == 3.14

    def test_max_numbers_type_errors(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(TypeError, match="Argument 'a' must be int or float"):
            max_numbers("5", 3)

        with pytest.raises(TypeError, match="Argument 'b' must be int or float"):
            max_numbers(5, "3")


class TestMinNumbers:
    """Tests for the min_numbers function."""

    def test_min_numbers_integers(self):
        """Test min with integer inputs."""
        assert min_numbers(5, 3) == 3
        assert min_numbers(10, 15) == 10
        assert min_numbers(-5, -10) == -10
        assert min_numbers(0, 0) == 0

    def test_min_numbers_floats(self):
        """Test min with float inputs."""
        assert min_numbers(5.5, 3.3) == 3.3
        assert min_numbers(1.1, 1.9) == 1.1
        assert min_numbers(-2.5, -1.5) == -2.5

    def test_min_numbers_mixed_types(self):
        """Test min with mixed int and float inputs."""
        assert min_numbers(5, 3.3) == 3.3
        assert min_numbers(2.7, 3) == 2.7
        assert min_numbers(-1.5, -2) == -2

    def test_min_numbers_equal_values(self):
        """Test min with equal values."""
        assert min_numbers(42, 42) == 42
        assert min_numbers(3.14, 3.14) == 3.14

    def test_min_numbers_type_errors(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(TypeError, match="Argument 'a' must be int or float"):
            min_numbers("5", 3)

        with pytest.raises(TypeError, match="Argument 'b' must be int or float"):
            min_numbers(5, "3")


class TestIsEven:
    """Tests for the is_even function."""

    def test_is_even_positive_integers(self):
        """Test with positive integers."""
        assert is_even(2) is True
        assert is_even(4) is True
        assert is_even(100) is True
        assert is_even(1) is False
        assert is_even(3) is False
        assert is_even(101) is False

    def test_is_even_negative_integers(self):
        """Test with negative integers."""
        assert is_even(-2) is True
        assert is_even(-4) is True
        assert is_even(-100) is True
        assert is_even(-1) is False
        assert is_even(-3) is False
        assert is_even(-101) is False

    def test_is_even_zero(self):
        """Test with zero."""
        assert is_even(0) is True

    def test_is_even_large_numbers(self):
        """Test with large numbers."""
        assert is_even(1000000) is True
        assert is_even(1000001) is False

    def test_is_even_type_errors(self):
        """Test that TypeError is raised for non-integer inputs."""
        with pytest.raises(TypeError, match="Argument 'number' must be int"):
            is_even(2.0)

        with pytest.raises(TypeError, match="Argument 'number' must be int"):
            is_even("2")

        with pytest.raises(TypeError, match="Argument 'number' must be int"):
            is_even(None)


class TestFormatCurrency:
    """Tests for the format_currency function."""

    def test_format_currency_usd_default(self):
        """Test USD formatting (default currency)."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(1000) == "$1,000.00"
        assert format_currency(0) == "$0.00"
        assert format_currency(42.5) == "$42.50"

    def test_format_currency_different_currencies(self):
        """Test formatting with different currencies."""
        assert format_currency(1000, "EUR") == "€1,000.00"
        assert format_currency(500.5, "BRL") == "R$500.50"
        assert format_currency(750, "GBP") == "£750.00"

    def test_format_currency_negative_amounts(self):
        """Test formatting negative amounts."""
        assert format_currency(-1234.56) == "$-1,234.56"
        assert format_currency(-100, "EUR") == "€-100.00"

    def test_format_currency_large_amounts(self):
        """Test formatting large amounts."""
        assert format_currency(1234567.89) == "$1,234,567.89"
        assert format_currency(1000000, "BRL") == "R$1,000,000.00"

    def test_format_currency_small_amounts(self):
        """Test formatting small amounts."""
        assert format_currency(0.01) == "$0.01"
        assert format_currency(0.99, "EUR") == "€0.99"

    def test_format_currency_type_errors(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(TypeError, match="Argument 'amount' must be int or float"):
            format_currency("1000")

        with pytest.raises(TypeError, match="Argument 'currency' must be str"):
            format_currency(1000, 123)

    def test_format_currency_unsupported_currency(self):
        """Test that ValueError is raised for unsupported currencies."""
        with pytest.raises(ValueError, match="Unsupported currency 'JPY'"):
            format_currency(1000, "JPY")

        with pytest.raises(ValueError, match="Supported: USD, EUR, BRL, GBP"):
            format_currency(1000, "INVALID")


class TestMultiplyThreeNumbers:
    """Tests for the multiply_three_numbers function."""

    def test_multiply_three_positive_integers(self):
        """Test multiplying three positive integers."""
        assert multiply_three_numbers(2, 3, 4) == 24
        assert multiply_three_numbers(1, 1, 1) == 1
        assert multiply_three_numbers(5, 2, 3) == 30

    def test_multiply_three_positive_floats(self):
        """Test multiplying three positive floats."""
        assert multiply_three_numbers(2.0, 3.0, 4.0) == 24.0
        assert multiply_three_numbers(1.5, 2.0, 3.0) == 9.0
        assert multiply_three_numbers(0.5, 0.5, 0.5) == 0.125

    def test_multiply_three_mixed_types(self):
        """Test multiplying mixed int and float types."""
        assert multiply_three_numbers(2, 3.0, 4) == 24.0
        assert multiply_three_numbers(1.5, 2, 3) == 9.0
        assert multiply_three_numbers(10, 0.1, 5) == 5.0

    def test_multiply_three_with_zero(self):
        """Test multiplying when one number is zero."""
        assert multiply_three_numbers(0, 5, 10) == 0
        assert multiply_three_numbers(2, 0, 8) == 0
        assert multiply_three_numbers(3, 7, 0) == 0
        assert multiply_three_numbers(0, 0, 0) == 0

    def test_multiply_three_with_negative_numbers(self):
        """Test multiplying with negative numbers."""
        assert multiply_three_numbers(-2, 3, 4) == -24
        assert multiply_three_numbers(2, -3, 4) == -24
        assert multiply_three_numbers(2, 3, -4) == -24
        assert multiply_three_numbers(-2, -3, 4) == 24
        assert multiply_three_numbers(-2, -3, -4) == -24

    def test_multiply_three_with_one(self):
        """Test multiplying with the number one."""
        assert multiply_three_numbers(1, 5, 3) == 15
        assert multiply_three_numbers(7, 1, 2) == 14
        assert multiply_three_numbers(4, 6, 1) == 24
        assert multiply_three_numbers(1, 1, 5) == 5

    def test_multiply_three_large_numbers(self):
        """Test multiplying large numbers."""
        assert multiply_three_numbers(1000, 1000, 1000) == 1000000000
        assert multiply_three_numbers(999999, 1, 2) == 1999998

    def test_multiply_three_small_numbers(self):
        """Test multiplying small decimal numbers."""
        result = multiply_three_numbers(0.1, 0.1, 0.1)
        assert abs(result - 0.001) < 1e-10  # Handle floating point precision

    def test_multiply_three_numbers_type_errors(self):
        """Test that TypeError is raised for invalid input types."""
        with pytest.raises(TypeError, match="Argument 'a' must be int or float"):
            multiply_three_numbers("2", 3, 4)

        with pytest.raises(TypeError, match="Argument 'b' must be int or float"):
            multiply_three_numbers(2, "3", 4)

        with pytest.raises(TypeError, match="Argument 'c' must be int or float"):
            multiply_three_numbers(2, 3, "4")

        with pytest.raises(TypeError, match="Argument 'a' must be int or float"):
            multiply_three_numbers(None, 3, 4)

        with pytest.raises(TypeError, match="Argument 'b' must be int or float"):
            multiply_three_numbers(2, [], 4)

        with pytest.raises(TypeError, match="Argument 'c' must be int or float"):
            multiply_three_numbers(2, 3, {})

    def test_multiply_three_numbers_edge_cases(self):
        """Test edge cases and special values."""
        # Very large numbers
        result = multiply_three_numbers(1e10, 1e10, 1e10)
        assert result == 1e30

        # Very small numbers
        result = multiply_three_numbers(1e-5, 1e-5, 1e-5)
        assert abs(result - 1e-15) < 1e-20
