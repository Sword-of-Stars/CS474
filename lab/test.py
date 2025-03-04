import itertools

def replace_chars(s, chars_to_replace, replacement_char, max_replacements=None):
    """
    Replaces characters in a string with a replacement character using itertools.

    Args:
        s: The input string.
        chars_to_replace: A list of characters to replace.
        replacement_char: The character to replace with.
        max_replacements: The maximum number of replacements (None for all).

    Returns:
        A list of strings with characters replaced.
    """
    indices_to_replace = [i for i, char in enumerate(s) if char in chars_to_replace]
    results = []

    if not indices_to_replace:
        return []

    if max_replacements is None:
        max_replacements = len(indices_to_replace)

    for r in range(max_replacements + 1):
        for indices in itertools.combinations(indices_to_replace, r):
            new_s = list(s)
            for index in indices:
                new_s[index] = replacement_char
            results.append("".join(new_s))

    return results

# Example usage (original problem)
input_string = "ASA"
result = replace_chars(input_string, ['A'], 'e')
print(result)

# More general examples
input_string2 = "ABAA"
result2 = replace_chars(input_string2, ['A'], 'e')
print(result2)

input_string3 = "ABACA"
result3 = replace_chars(input_string3, ['A'], 'e')
print(result3)

input_string4 = "ABACAD"
result4 = replace_chars(input_string4, ['A'], 'e', max_replacements=2)
print(result4)

input_string5 = "ABACAD"
result5 = replace_chars(input_string5, ['A'], 'e')
print(result5)

input_string6 = "ABCBDBE"
result6 = replace_chars(input_string6, ['B'], 'z')
print(result6)

input_string7 = "ABCBDBE"
result7 = replace_chars(input_string7, ['B', 'C'], 'z')
print(result7)