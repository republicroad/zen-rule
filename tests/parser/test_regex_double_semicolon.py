
# ; is semicolon
import re

text = r"""foo;;myvar ;;max([5,8,2,11, 7]);;rand(100)+120;;3+4;; 'singel;;quote' ;;"double;;quote" ;;`backquote;; ${bar}`"""

# Regex to find commas not inside double quotes
# This regex works by matching a comma that is NOT followed by an even number of quotes
# until the end of the string.
# It essentially checks if there's an odd number of quotes after the comma,
# implying it's inside a quoted string.
# This pattern is more robust for simple cases without escaped quotes inside strings.
pattern = r""";;(?=(?:[^"'`]*["'`][^"'`]*["'`])*[^"'`]*$)"""

# Find all matches
double_semicolon_outside_quotes = re.findall(pattern, text)
print(double_semicolon_outside_quotes)
print(f"Commas found outside quotes: {double_semicolon_outside_quotes}")

# To split the string by these semicolon:
parts = re.split(pattern, text)
print(f"double semicolon Split parts: {parts}")