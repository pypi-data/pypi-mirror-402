"""Core utilities for simple Python operations.

This module provides basic utility functions for common operations
like printing messages and performing arithmetic calculations.
"""

from typing import Union


def print_message(message: str) -> None:
    """Print a message to stdout.

    This function takes a string message and prints it to the standard output.
    It's a simple wrapper around the built-in print function with type safety.

    Args:
        message (str): The message to be printed.

    Returns:
        None

    Raises:
        TypeError: If message is not a string.

    Examples:
        >>> print_message("Hello, World!")
        Hello, World!

        >>> print_message("Welcome to Simple Utils!")
        Welcome to Simple Utils!
    """
    if not isinstance(message, str):
        raise TypeError(f"Expected str, got {type(message).__name__}")

    print(message)


def add_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Add two numbers and return the result.

    This function performs basic addition of two numeric values.
    It accepts both integers and floats and returns the appropriate type.

    Args:
        a (Union[int, float]): The first number.
        b (Union[int, float]): The second number.

    Returns:
        Union[int, float]: The sum of a and b. Returns int if both inputs
                          are int, otherwise returns float.

    Raises:
        TypeError: If either argument is not a number (int or float).

    Examples:
        >>> add_numbers(2, 3)
        5

        >>> add_numbers(2.5, 1.5)
        4.0

        >>> add_numbers(10, 3.14)
        13.14
    """
    # Validate input types
    for num, name in [(a, "a"), (b, "b")]:
        if not isinstance(num, (int, float)):
            raise TypeError(
                f"Argument '{name}' must be int or float, got " f"{type(num).__name__}"
            )

    return a + b


def multiply_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
    """Multiply two numbers and return the result.

    This function performs basic multiplication of two numeric values.
    It accepts both integers and floats and returns the appropriate type.

    Args:
        a (Union[int, float]): The first number.
        b (Union[int, float]): The second number.

    Returns:
        Union[int, float]: The product of a and b. Returns int if both inputs
                          are int, otherwise returns float.

    Raises:
        TypeError: If either argument is not a number (int or float).

    Examples:
        >>> multiply_numbers(2, 3)
        6

        >>> multiply_numbers(2.5, 4.0)
        10.0

        >>> multiply_numbers(3, 1.5)
        4.5
    """
    # Validate input types
    for num, name in [(a, "a"), (b, "b")]:
        if not isinstance(num, (int, float)):
            raise TypeError(
                f"Argument '{name}' must be int or float, got " f"{type(num).__name__}"
            )

    return a * b


def divide_numbers(a: Union[int, float], b: Union[int, float]) -> float:
    """Divide two numbers and return the result.

    This function performs basic division of two numeric values.
    It accepts both integers and floats and always returns a float.

    Args:
        a (Union[int, float]): The dividend (number to be divided).
        b (Union[int, float]): The divisor (number to divide by).

    Returns:
        float: The quotient of a divided by b.

    Raises:
        TypeError: If either argument is not a number (int or float).
        ZeroDivisionError: If the divisor (b) is zero.

    Examples:
        >>> divide_numbers(10, 2)
        5.0

        >>> divide_numbers(7, 2)
        3.5

        >>> divide_numbers(15.0, 3.0)
        5.0

        >>> divide_numbers(1, 3)
        0.3333333333333333
    """
    # Validate input types
    for num, name in [(a, "a"), (b, "b")]:
        if not isinstance(num, (int, float)):
            raise TypeError(
                f"Argument '{name}' must be int or float, got " f"{type(num).__name__}"
            )

    # Check for division by zero
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")

    return float(a / b)


def square_numbers(a: Union[int, float]) -> Union[int, float]:
    """Calculate the square of a number.

    This function takes a numeric value and returns its square (a²).
    It accepts both integers and floats and preserves the input type
    where appropriate.

    Args:
        a (Union[int, float]): The number to be squared.

    Returns:
        Union[int, float]: The square of a. Returns int if input is int
                          and result fits in int range, otherwise returns float.

    Raises:
        TypeError: If argument is not a number (int or float).

    Examples:
        >>> square_numbers(4)
        16

        >>> square_numbers(-3)
        9

        >>> square_numbers(2.5)
        6.25

        >>> square_numbers(0)
        0
    """
    # Validate input type
    if not isinstance(a, (int, float)):
        raise TypeError(
            f"Argument 'a' must be int or float, got " f"{type(a).__name__}"
        )

    result = a * a

    # Return int if input was int and result is in int range
    if isinstance(a, int) and isinstance(result, int):
        return result

    return float(result)
