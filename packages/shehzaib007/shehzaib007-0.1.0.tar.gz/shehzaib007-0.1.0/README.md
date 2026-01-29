# shehzaib007

A simple utility package providing basic math and string operations.

## Features

- **Math Operations Module**: Functions for basic mathematical calculations
  - `square(x)` - Calculate the square of a number
  - `cube(x)` - Calculate the cube of a number
  - `add(a, b)` - Add two numbers
  - `multiply(a, b)` - Multiply two numbers

- **String Operations Module**: Functions for basic string manipulation
  - `reverse_string(text)` - Reverse a string
  - `count_vowels(text)` - Count vowels in a string
  - `to_uppercase(text)` - Convert string to uppercase
  - `word_count(text)` - Count words in a string

## Installation

You can install shehzaib007 from PyPI using pip:

```bash
pip install shehzaib007
```

## Usage

### Math Operations

```python
from shehzaib007 import square, cube, add, multiply

# Calculate square
result = square(5)  # Returns 25

# Calculate cube
result = cube(3)  # Returns 27

# Add numbers
result = add(10, 5)  # Returns 15

# Multiply numbers
result = multiply(4, 7)  # Returns 28
```

### String Operations

```python
from shehzaib007 import reverse_string, count_vowels, to_uppercase, word_count

# Reverse a string
result = reverse_string("hello")  # Returns "olleh"

# Count vowels
result = count_vowels("hello world")  # Returns 3

# Convert to uppercase
result = to_uppercase("hello")  # Returns "HELLO"

# Count words
result = word_count("hello world python")  # Returns 3
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Shehzaib

## Version

0.1.0
