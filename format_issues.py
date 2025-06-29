import os
import sys

def function_with_extremely_long_name_that_definitely_exceeds_one_hundred_twenty_characters_limit_and_should_be_shortened():
    print("This line uses tabs instead of spaces for indentation")  # Tab issue
    mixed_indentation = "This line uses spaces after tab line"

def another_function():
    print("Double tab indentation issue")  # Multiple tabs
    return "inconsistent indentation"

class TestClass:
    def method_with_very_very_very_very_very_very_very_very_very_very_long_method_name_over_120_chars(self):
        print("Long method name")

    def mixed_method(self):
        print("Tab in method")  # Tab issue
        print("Space after tab")  # Mixed indentation

    # Long line comment that goes way beyond the recommended 120 character limit and should be wrapped or shortened according to style guidelines
variable_with_extremely_long_name_that_should_probably_be_shortened_for_better_readability = "test"

def normal_function():
    """This is a normal function with proper formatting."""
    return "This should not be changed"