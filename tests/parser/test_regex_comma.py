import re

text = 'item1, "string with, a comma", item2, "another string", item3'

# Regex to find commas not inside double quotes
# This regex works by matching a comma that is NOT followed by an even number of quotes
# until the end of the string.
# It essentially checks if there's an odd number of quotes after the comma,
# implying it's inside a quoted string.
# This pattern is more robust for simple cases without escaped quotes inside strings.
pattern = r',(?=(?:[^"]*"[^"]*")*[^"]*$)'

# Find all matches
commas_outside_quotes = re.findall(pattern, text)

print(f"Commas found outside quotes: {commas_outside_quotes}")

# To split the string by these commas:
parts = re.split(pattern, text)
print(f"Split parts: {parts}")


# Explanation of the regex ,(?=(?:[^"]*"[^"]*")*[^"]*$):
# ,: Matches a literal comma.
# (?=...): This is a positive lookahead assertion. It means "assert that what follows matches the pattern inside, but don't consume characters."
# (?:[^"]*"[^"]*")*: This is a non-capturing group (?:...) that matches an even number of quoted sections.
# [^"]*: Matches any character except a double quote, zero or more times.
# ": Matches a double quote.
# This sequence [^"]*"[^"]*" effectively matches a complete quoted string (e.g., "abc" or "abc,def"). The * after the non-capturing group allows for zero or more such complete quoted sections.
# [^"]*$: Matches any character except a double quote, zero or more times, until the end of the string $.