Pyparsing uses a specific parse order based on how grammar elements are combined and defined. Understanding this order is crucial for building effective parsers and avoiding unexpected behavior.
Key aspects of pyparsing's parse order:

## Sequential Parsing:
When combining expressions with the + operator (Sequence), pyparsing attempts to match them in the order they are defined. For instance, expr1 + expr2 + expr3 will first try to match expr1, then expr2 after expr1 is matched, and finally expr3 after expr2 is matched.
## Alternatives (| operator):
When using the | operator (MatchFirst), pyparsing attempts to match the alternatives in the order they are listed. The first alternative that successfully matches the input string is chosen, and subsequent alternatives are not attempted. This means the order of alternatives can be significant, especially if there are overlapping matches. For example, if you have Literal("long_word") | Literal("word"), and the input is "long_word", long_word will be matched. If the order was Literal("word") | Literal("long_word"), "word" would be matched, which might not be the desired outcome.
## oneOf and Ambiguity:
The oneOf helper method takes a list of strings and reorders them internally to avoid ambiguity, prioritizing longer matches to prevent shorter, overlapping strings from being matched first. This helps ensure that the most specific match is found.
## Each (& operator):
The & operator (Each) allows expressions to be matched in any order. This is useful when the sequence of elements in the input is not fixed, but all specified elements must be present.
## Recursive Parsing and Forward:
For handling nested or recursive structures, Forward is used as a placeholder. The definition of the Forward expression is completed later, allowing the parser to handle self-referential grammar rules.
## Whitespace Handling:
By default, pyparsing skips whitespace between tokens. This behavior can be modified if necessary.
## Parse Actions:
Parse actions are executed immediately after a token or expression is successfully matched. This allows for real-time processing and transformation of parsed elements.



Pyparsing expression parse order is determined by several factors, primarily the order in which expressions are defined and combined, and the specific operators used to combine them.
1. Operator Precedence and Associativity:
infixNotation:
For common expression parsing (like arithmetic or logical expressions), pyparsing offers the infixNotation helper. This method simplifies defining operator precedence and associativity by taking a list of tuples, where each tuple defines a level of precedence. Operators within a higher precedence level are evaluated before those in lower levels.
Default Operator Behavior:
When not using infixNotation, pyparsing's default operators like | (MatchFirst) and & (Each) have inherent behaviors that influence parsing order.
2. Order of Definition (for MatchFirst):
| (MatchFirst): When using the | operator, pyparsing attempts to match expressions in the order they are defined. The first expression that successfully matches a portion of the input string is chosen. This means that if you have overlapping patterns, the order of definition is crucial. For example, if you define Keyword("if") before Literal("iffy") and use | to combine them, "if" will always be matched first in "iffy", leading to a partial match if not handled carefully.
3. Specific Parsers and Helpers:
Keyword vs. Literal:
Using Keyword instead of Literal for keywords is recommended because Keyword looks at surrounding text to ensure a full word match, preventing partial matches within longer words (e.g., Keyword("if") will not match "iffy").
oneOf:
The oneOf helper takes a list of strings and reorders them to avoid ambiguity, while still allowing some control over the general sequence of evaluation if overlapping is not an issue.
Each (& operator):
The Each class allows you to specify that a set of expressions can occur in any order within a given context, as long as all specified expressions are present.
4. Recursion and Left-Recursion:
Recursive Definitions:
Pyparsing supports recursive grammar definitions, where an expression can refer to itself.
Left-Recursion:
Direct left-recursion (e.g., exp <<= exp + op + operand) can lead to infinite recursion errors. This is a common pitfall and requires restructuring the grammar to avoid it, typically by factoring out the left-recursive part or using techniques like ZeroOrMore.
In summary, the parse order in pyparsing is a combination of explicit precedence rules (especially with infixNotation), the order of definition for MatchFirst alternatives, and the specific behavior of various parser elements and helpers. Understanding these factors is key to building robust and predictable grammars.


# infix nontaion 递归解析性能

pyparsing.ParserElement.enablePackrat() is a class method in the pyparsing library that enables packrat parsing, a performance optimization technique.
Purpose:
Packrat parsing (also known as memoization) stores the results of parsing sub-expressions. When the parser encounters the same sub-expression again, it retrieves the previously stored result instead of re-parsing it. This can significantly improve performance, especially for recursive grammars or grammars where certain elements may be parsed multiple times in different contexts.
Usage:
To enable packrat parsing, you call the enablePackrat() method on the ParserElement class. It is recommended to call this method immediately after importing pyparsing for best results.

```python
import pyparsing
pyparsing.ParserElement.enablePackrat()
# Define your grammar and parse your input string
```

Considerations:
Side Effects:
Packrat parsing should be used with caution if your parse actions have side effects (e.g., modifying global state), as the memoized results might not reflect the desired behavior.
Memory Usage:
Packrat parsing can increase memory usage, as it stores the results of parsed sub-expressions.
Not Always Faster:
While often beneficial, packrat parsing might not always lead to performance improvements for all grammars, and in some cases, it might even make parsing slower if the overhead of memoization outweighs the benefits.


# 资料链接

[Parse mathematical expressions with pyparsing](https://stackoverflow.com/questions/23879784/parse-mathematical-expressions-with-pyparsing)  

[pyparsing how to express functions inside an infixNotation](https://stackoverflow.com/questions/77317117/pyparsing-how-to-express-functions-inside-an-infixnotation)  
[pyparsing how to express functions inside an infixNotation](https://stackoverflow.com/questions/77317117/pyparsing-how-to-express-functions-inside-an-infixnotation)  
[pyparsing how to use infixNotation for representing iif(cond, if true, if false)](https://stackoverflow.com/questions/56408430/pyparsing-how-to-use-infixnotation-for-representing-iifcond-if-true-if-false)  


[pyparsing arithmetic or logical expressions](https://www.google.com/search?q=pyparsing+arithmetic+or+logical+expressions+&sca_esv=0091f1adde5afd41&biw=1850&bih=932&sxsrf=AE3TifOf4VPje9nlf2_FFBgPeqzgJm3KOw%3A1755587499012&ei=qyOkaO9DytDV7w-E1aLoAQ&ved=0ahUKEwivxYCKqZaPAxVKaPUHHYSqCB0Q4dUDCBA&uact=5&oq=pyparsing+arithmetic+or+logical+expressions+&gs_lp=Egxnd3Mtd2l6LXNlcnAiLHB5cGFyc2luZyBhcml0aG1ldGljIG9yIGxvZ2ljYWwgZXhwcmVzc2lvbnMgMgUQIRifBTIFECEYnwVIhgNQP1g_cAF4AZABAJgBrQGgAa0BqgEDMC4xuAEDyAEA-AEBmAICoALGAcICChAAGLADGNYEGEeYAwCIBgGQBgiSBwMxLjGgB_8CsgcDMC4xuAe5AcIHBTItMS4xyAcP&sclient=gws-wiz-serp)  

[Operator Precedence in C](https://www.tutorialspoint.com/cprogramming/c_operators_precedence.htm)

[DelimitedList with combine=True for dot-qualified variable names such as "namespace.var.attribute"](https://github.com/pyparsing/pyparsing/wiki/Common-Pitfalls-When-Writing-Parsers#identifier--wordalphanums--_-should-be-delimitedlistwordalphas-alphanums--_--combinetrue)  
[Pyparsing实战](https://zhuanlan.zhihu.com/p/259638397)  


[Parser-Debugging-and-Diagnostics](https://github.com/pyparsing/pyparsing/wiki/Parser-Debugging-and-Diagnostics)

[A Guide to Parsing: Algorithms and Terminology](https://tomassetti.me/guide-parsing-algorithms-terminology/)  
[PEG 和 CFG 之间的区别](https://tomassetti.me/parsing-in-javascript/)  
[parsing-in-javascript](https://tomassetti.me/parsing-in-javascript/)  

[incremental-parsing-using-tree-sitter](https://tomassetti.me/incremental-parsing-using-tree-sitter/)  
[Parsing 101: Best Practices & Tips](https://medium.com/@thatsiemguy/parsing-101-best-practices-tips-c2e8b7ce9db8)  