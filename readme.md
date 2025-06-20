
# 沉思录




## vscode config

[使用环境变量在终端中激活环境](https://github.com/microsoft/vscode-python/wiki/Activate-Environments-in-Terminal-Using-Environment-Variables)  


## 参数解构

```python
def foo(*args,**kwargs):
    print("args:", args)
    print("kwargs:", kwargs)

d = {"a": 1, "b":2, "c3":"ccc"}
foo(*d, **d)

# 输出:
# args: ('a', 'b', 'c3')
# kwargs: {'a': 1, 'b': 2, 'c3': 'ccc'}
```