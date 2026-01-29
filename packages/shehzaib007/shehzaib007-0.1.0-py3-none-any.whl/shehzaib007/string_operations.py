"""
String operations module - provides basic string manipulation functions.
"""


def reverse_string(text):
    """
    Reverse a string.
    
    Args:
        text (str): The string to reverse
        
    Returns:
        str: The reversed string
    """
    return text[::-1]


def count_vowels(text):
    """
    Count the number of vowels in a string.
    
    Args:
        text (str): The string to count vowels in
        
    Returns:
        int: Number of vowels found
    """
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)


def to_uppercase(text):
    """
    Convert a string to uppercase.
    
    Args:
        text (str): The string to convert
        
    Returns:
        str: The uppercase string
    """
    return text.upper()


def word_count(text):
    """
    Count the number of words in a string.
    
    Args:
        text (str): The string to count words in
        
    Returns:
        int: Number of words found
    """
    return len(text.split())
