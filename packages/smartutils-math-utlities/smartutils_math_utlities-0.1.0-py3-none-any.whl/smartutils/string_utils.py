def reverse_string(text):
    """Returns the reverse of a string"""
    return text[::-1]


def count_vowels(text):
    """Counts vowels in a string"""
    vowels = "aeiouAEIOU"
    return sum(1 for char in text if char in vowels)


def is_palindrome(text):
    """Checks if a string is a palindrome"""
    cleaned = text.replace(" ", "").lower()
    return cleaned == cleaned[::-1]


def capitalize_words(text):
    """Capitalizes the first letter of each word"""
    return text.title()
