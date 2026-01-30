from package_creation_tutorial.string_ops import reverse_string, count_vowels, capitalize_words
import os

def main():
    """
    Main function to demonstrate the string operations.
    """
    test_string: str = "hello world"
    print("Hi! PARIS")
    print(f"Original string: {test_string}")
    print(f"Reversed: {reverse_string(test_string)}")
    print(f"Vowel count: {count_vowels(test_string)}")
    print(f"Capitalized: {capitalize_words(test_string)}")


if __name__ == "__main__":
    main()
