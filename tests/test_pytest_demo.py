
#  pytest tests/zen/test_zen.py -sl
#  -s 捕获标准输出
#  -l 显示出错的测试用例中的局部变量
#  -k 指定某一个测试用例执行
#  --setup-show  展示的单元测试 SETUP 和 TEARDOWN 的细节，展示测试依赖的加载和销毁顺序


def test_passing():
    assert (1, 2, 3) == (1, 2, 3)
    # assert {"d": 1, "a":2} == {"d":1}, "两个字典不同"

