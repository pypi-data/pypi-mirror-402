def reverse_string(text):
    """Reverse a string"""
    return text[::-1]

def to_upper(text):
    """Convert string to uppercase"""
    return text.upper()

def word_count(text):
    """Count words in a string"""
    return len(text.split())

def is_palindrome(text):
    """Check if string is palindrome"""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]
