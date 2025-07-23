
# zen-rule

[zen-rule github](https://github.com/republicroad/zen-rule)  

- 补充 zen-rule 的测试用例.
- 补充只有除了输入输出外的单一节点类型(决策表，表达式, 分支节点, 自定义节点, javascript节点)的测试用例.
- 补充全类型节点(决策表，表达式, 分支节点, 自定义节点, javascript节点)的测试用例.



## 后续思考

函数调用三种字面量语法, 以后需要考虑那种函数调用方法更适合:
```python
        "func1": "ratelimit_by10s(ip)",
        "func2": "(ratelimit_by10s ip)",
        "func3": "ratelimit_by10s;ip,phone",
```