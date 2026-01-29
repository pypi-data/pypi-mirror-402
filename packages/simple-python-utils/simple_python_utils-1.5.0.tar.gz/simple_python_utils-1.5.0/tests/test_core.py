"""Tests for core utility functions."""

import pytest

from simple_utils.core import (
    add_numbers,
    divide_numbers,
    multiply_numbers,
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
