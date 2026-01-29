def reverse_string(text):
    return text[::-1]

def count_vowels(text):
    vowels = "aeiouAEIOU"
    return sum(1 for c in text if c in vowels)

def to_uppercase(text):
    return text.upper()

def is_palindrome(text):
    return text == text[::-1]
