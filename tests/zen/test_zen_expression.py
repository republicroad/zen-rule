import datetime

import pytest
import zen


def test_zen_template_str():
    inputs = {"a": 10, "b": "cjn","__meta__":{"redispool": "redispool", "httpclient": "httpclient"}}
    template = '{{ a + 10 }}'
    # 如果修改了规则图中的自定义节点的表达式, 需要重新修改这里的断言条件.

    # print("render_template:", zen.render_template("{{ a + 10 }}", inputs)) 
    # print("evaluate_expression:", zen.evaluate_expression("'{{ a + 10 }}'", inputs))  # res["result"]["prop1_raw"]
    aa = zen.render_template("{{ a + 10 }}", inputs)

    assert zen.render_template(template, inputs) == 20, "zen template addition operation return int type"
    assert zen.render_template("{}".format(template), inputs) == 20, "zen template addition operation return int type"
    assert zen.render_template("   {}   ".format(template), inputs) == 20, "zen 模板如果返回一个数字，即使前后都是空格，最后也会被隐式求值为数字"
    assert zen.render_template("a {}".format(template), inputs) == 'a 20', "zen template addition operation return int type"

    assert zen.evaluate_expression("'{}'".format(template), inputs) == '{{ a + 10 }}', "zen template 如果放在表达式中用引号括起来，会阻止模板渲染，仅作为字面字符串表示"  
    with pytest.raises(RuntimeError) as excinfo:
        assert zen.evaluate_expression("brde {{ a + 10 }}", inputs) == 20, "zen 模板不能直接在表达式中使用." 

    assert "parserError" in str(excinfo.value)


# zen expression 表达式语言测试

def test_zen_expression_str():
    '''
    字符串是一种表示文本内容（字符列表、单词）的数据类型。它通过使用单引号'或双引号括住字符来定义"。
    示例：
    "double quote string"
    'single quote string'
    '''
    # 字符串操作符号 +
    assert zen.evaluate_expression("a+b", { "a": "hello ", "b": "world" }) == "hello world"

    # 字符串slice [start, end]满足左闭右闭区间, 与python字符串切片不一样，python为左闭右开区间
    assert zen.evaluate_expression("a[0:5]", { "a": "0123456789abcdef"}) == '012345'

    # 变量等值与不等值判断 == !=
    assert zen.evaluate_expression("a == b", { "a": "hello ", "b": "world" }) == False
    assert zen.evaluate_expression("a != b", { "a": "hello ", "b": "world" }) == True

    # 字符串函数: len 接受一个字符串并返回其中的字符数
    assert zen.evaluate_expression("len(a) == 6", {"a": "string"}) == True

    # 字符串函数: upper 接受一个字符串并返回它的大写版本
    assert zen.evaluate_expression("upper(a)", {"a": "string"}) == 'STRING'

    # 字符串函数: lower 接受一个字符串并返回其小写版本
    assert zen.evaluate_expression("lower(a)", {"a": "StrIng"}) == 'string'

    # 字符串函数: startsWith 接受两个参数，如果字符串以指定值开头，则返回 true
    assert zen.evaluate_expression("startsWith(a, 'Sat')", {"a": "Saturday night plans"}) == True
    assert zen.evaluate_expression("startsWith(a, 'Sun')", {"a": "Saturday night plans"}) == False

    # 字符串函数: endsWith 接受两个参数，如果字符串以指定值结尾，则返回 true
    assert zen.evaluate_expression("endsWith(a, 'plans')", {"a": "Saturday night plans"}) == True
    assert zen.evaluate_expression("endsWith(a, 'night')", {"a": "Saturday night plans"}) == False

    # 字符串函数: contains 接受两个参数，如果字符串包含指定值，则返回 true
    assert zen.evaluate_expression("contains(a, 'night')", {"a": "Saturday night plans"}) == True
    assert zen.evaluate_expression("contains(a, 'plans')", {"a": "Saturday night plans"}) == True
    assert zen.evaluate_expression("contains(a, 'saturday')", {"a": "Saturday night plans"}) == False

    # 字符串函数: matches 接受两个参数，如果字符串与正则表达式匹配，则返回 true
    assert zen.evaluate_expression(r"matches(a, '^\d+$')", {"a": "12345"}) == True
    assert zen.evaluate_expression(r"matches(a, '^\d+$')", {"a": "12345a"}) == False

    # 字符串函数: extract 接受两个参数，返回正则表达式中捕获组的数组
    assert zen.evaluate_expression(r"extract(a, '(\d{4})-(\d{2})-(\d{2})')", {"a": "2022-02-01"}) ==  ['2022-02-01', '2022', '02', '01']
    assert zen.evaluate_expression(r"extract(a, '(\w+).(\w+)')", {"a": "foo.bar"}) == ['foo.bar', 'foo', 'bar']

    # 字符串函数: string 接受一个参数，尝试将变量转换为字符串，失败时抛出错误
    assert zen.evaluate_expression("string(a) == 'abc'", {"a": "abc"}) == True
    assert zen.evaluate_expression("string(a) == '20'", {"a": "20"}) == True
    assert zen.evaluate_expression("string(a) == '20'", {"a": 20}) == True
    assert zen.evaluate_expression("string(a) == 'true'", {"a": True}) == True  # ZEN Bool: true false


def test_zen_expression_num():
    '''
    数字可以是整数或小数(浮点数)。可以使用数字0-9, .（小数分隔符）和来定义, 使用_为了便于阅读
    示例：
    100;
    1_000_000;
    1.54;
    '''
    # 数字一元操作符号 -  取负数
    assert zen.evaluate_expression("-a", { "a": 3 }) == -3

    # 数字算术运算符： + - * / ^  %
    assert zen.evaluate_expression("a + b", {"a": 3, "b": -9}) == -6
    assert zen.evaluate_expression("a - b", {"a": 3, "b": 9}) == -6
    assert zen.evaluate_expression("a * b", {"a": 3, "b": 9}) == 27
    assert zen.evaluate_expression("b / a", {"a": 3, "b": 9}) == 3
    assert zen.evaluate_expression("a ^ b", {"a": 3, "b": 3}) == 27
    assert zen.evaluate_expression("a % b", {"a": 10, "b": 3}) == 1

    # 数字比较运算符： == != > < >= <=
    assert zen.evaluate_expression("a == 10", {"a": 10}) == True
    assert zen.evaluate_expression("a != 100", {"a": 10}) == True
    assert zen.evaluate_expression("a < 11", {"a": 10}) == True
    assert zen.evaluate_expression("a > 1", {"a": 10}) == True
    assert zen.evaluate_expression("a >= 10", {"a": 10}) == True
    assert zen.evaluate_expression("a <= 10", {"a": 10}) == True

    # 数字 函数
    # abs 接受一个数字，并返回其绝对值
    assert zen.evaluate_expression("abs(a) == 1.2", {"a": -1.2}) == True
    assert zen.evaluate_expression("abs(a) == 10", {"a": 10}) == True

    # rand 接受一个正数（限制），并返回 0 和提供的限制之间的生成数字
    assert zen.evaluate_expression("rand(a) < 4 ", {"a": 3}) == True
    assert zen.evaluate_expression("rand(a) in [0..3] ", {"a": 3}) == True

    # round 接受一个数字并将该数字四舍六入五取偶为最接近的整数
    assert zen.evaluate_expression("round(a) == 4", {"a":  3.5}) == True
    assert zen.evaluate_expression("round(a) == 3", {"a": 2.5}) == True
    assert zen.evaluate_expression("round(a) == 4", {"a": 4.49}) == True
    assert zen.evaluate_expression("round(a) == 5", {"a": 4.51}) == True

    # ceil 接受一个数字并将其向上舍入。它返回大于或等于给定数字的最小整数
    assert zen.evaluate_expression("ceil(a) == 5", {"a": 4.01}) == True
    assert zen.evaluate_expression("ceil(a) == 5", {"a": 4.9}) == True
    assert zen.evaluate_expression("ceil(a) == 4", {"a": 4.0}) == True

    # floor 接受一个数字并将其向下舍入。它返回小于或等于给定数字的最大整数
    assert zen.evaluate_expression("floor(a) == 4", {"a": 4.01}) == True
    assert zen.evaluate_expression("floor(a) == 4", {"a": 4.9}) == True
    assert zen.evaluate_expression("floor(a) == 4", {"a": 4.0}) == True

    # number 接受一个参数，尝试将数字或字符串转换为数字，失败时抛出错误
    assert zen.evaluate_expression("number(a) == 4", {"a": '4'}) == True
    assert zen.evaluate_expression("number(a) == 4", {"a": 4}) == True
    assert zen.evaluate_expression("number(a) == 1", {"a": True}) == True
    assert zen.evaluate_expression("number(a) == 0", {"a": False}) == True

    # isNumeric 接受一个参数，返回 bool，如果变量是数字或可以转换为数字的字符串则返回 true
    assert zen.evaluate_expression("isNumeric(a)", {"a": '4'}) == True
    assert zen.evaluate_expression("isNumeric(a)", {"a": 'test'}) == False
    assert zen.evaluate_expression("isNumeric(a)", {"a": True}) == False


def test_zen_expression_bool():
    '''
    布尔是一种逻辑数据类型，可以是true也可以是false。
    '''
    # 布尔逻辑运算符： and or ！not
    assert zen.evaluate_expression("a and b", { "a": True, "b": True}) == True
    assert zen.evaluate_expression("a and b", { "a": True, "b": False}) == False
    assert zen.evaluate_expression("a or b", { "a": True, "b": False}) == True
    assert zen.evaluate_expression("!a", { "a": False}) == True
    assert zen.evaluate_expression("not a", { "a": False}) == True
    
    # 布尔操作运算符： == !=
    assert zen.evaluate_expression("a == '10'", {"a": '10'}) == True
    assert zen.evaluate_expression("a != 11", {"a": 10}) == True

    # 三元操作符
    assert zen.evaluate_expression("product.price > 100 ? 'premium' : 'value'", {"product": {"price": 105}}) == 'premium'

    # 函数 bool 接受一个参数，尝试将变量转换为布尔值，失败时抛出错误
    assert zen.evaluate_expression("bool(a)", {"a": 0}) == False
    assert zen.evaluate_expression("bool(a)", {"a": 1}) == True
    assert zen.evaluate_expression("bool(a)", {"a": True}) == True
    assert zen.evaluate_expression("bool(a)", {"a": False}) == False
    assert zen.evaluate_expression("bool(a)", {"a": 'true'}) == True
    assert zen.evaluate_expression("bool(a)", {"a": 'false'}) == False
    assert zen.evaluate_expression("bool(a)", {"a": 'abc'}) == False

    
def test_zen_expression_date_and_time():
    '''
    日期、时间和持续时间是一组虚拟数据类型，内部使用 unix 时间戳（数字）表示为数字。
    '''
    # 日期时间函数： date time duration dayOfWeek dayOfMonth weekOfMonth weekOfYear seasonOfYear
    # date 接受格式化的字符串作为输入并以秒为单位返回 unix 时间戳
    assert zen.evaluate_expression("date('2022-01-01')") == 1640995200  # 2022-01-01对应的时间戳
    assert zen.evaluate_expression("date('2022-04-04T21:48:30Z')") == 1649108910  # 2022-04-04T21:48:30Z对应的时间戳
    assert zen.evaluate_expression("date('now')") == datetime.datetime.now().timestamp().__floor__()    # 当前时间戳

    # time 接受格式化的字符串作为输入并返回表示午夜(midnight)秒数的数字
    assert zen.evaluate_expression("time('21:49')") == 78540                    # 78540  从0时开始到21:49之间的秒数
    assert zen.evaluate_expression("time('21:48:20')") == 78500                 # 78500  从0时开始到21:48:20之间的秒数
    assert zen.evaluate_expression("time('2022-04-04T21:48:30Z')") == 78510     # 78510  从0时开始到21:48:30之间的秒数

    # duration 接受格式化的字符串（从秒到小时）作为输入并以秒为单位返回持续时间
    assert zen.evaluate_expression("duration('1h')") == 3600    # 3600    1小时包含的秒数
    assert zen.evaluate_expression("duration('30m')") == 1800   # 1800   30分钟包含的秒数
    assert zen.evaluate_expression("duration('10h')") == 36000  # 36000  10小时包含的秒数

    # dayOfWeek 接受时间戳并以数字形式返回星期几
    assert zen.evaluate_expression("dayOfWeek(date('2022-11-08'))") == 2  # 2   返回值为int

    # dayOfMonth 接受时间戳并以数字形式返回月份中的日期
    assert zen.evaluate_expression("dayOfMonth(date('2022-11-09'))") == 9  # 9   返回值为int

    # dayOfYear 接受时间戳并以数字形式返回一年中的某一天
    assert zen.evaluate_expression("dayOfYear(date('2022-11-10'))") == 314  # 314   返回值为int

    # weekOfMonth 接受时间戳并以数字形式返回月份的周数
    # zen-engine==0.24.2不支持内置的weekOfMonth方法
    # assert zen.evaluate_expression("weekOfMonth(date('2022-11-11'))") == 2  # 2   返回值为int

    # weekOfYear 接受时间戳并以数字形式返回一年中的第几周
    assert zen.evaluate_expression("weekOfYear(date('2022-11-12'))") == 45  # 2   返回值为int

    # seasonOfYear 接受 unix 时间戳并以字符串形式返回一年中的季节
    # zen-engine==0.24.2不支持内置的seasonOfYear方法
    # assert zen.evaluate_expression("seasonOfYear(date('2022-11-13'))") == 'Autumn'  # Autumn  返回值为str

    # monthString 接受时间戳并以字符串形式返回月份
    assert zen.evaluate_expression("monthString(date('2022-11-14'))") == 'Nov'  # Nov  返回值为str

    # weekdayString 接受时间戳并以字符串形式返回星期几
    assert zen.evaluate_expression("weekdayString(date('2022-11-14'))") == 'Mon'  # Mon  返回值为str

    # startOf 接受时间戳和单位。根据指定单位返回日期的开始时间
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'second')") == 1668440712     # 1668440712  2022-11-14 15:45:12对应的时间戳 传递参数: "s" | "second" | "seconds"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'minute')") == 1668440700     # 1668384000  2022-11-14 15:45:00对应的时间戳 传递参数: "m" | "minute" | "minutes"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'hour')") == 1668438000       # 1668438000  2022-11-14 15:00:00对应的时间戳 传递参数: "h" | "hour" | "hours"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'day')") == 1668384000        # 1668384000  2022-11-14 00:00:00对应的时间戳 传递参数: "d" | "day" | "days"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'week')") == 1668384000       # 1668384000  2022-11-14 00:00:00对应的时间戳 传递参数: "w" | "week" | "weeks"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'month')") == 1667260800      # 1667260800  2022-11-01 00:00:00对应的时间戳 传递参数: "M" | "month" | "months"
    assert zen.evaluate_expression(
        "startOf(date('2022-11-14 15:45:12'), 'year')") == 1640995200       # 1640995200  2022-01-01 00:00:00对应的时间戳 传递参数: "y" | "year" | "years"

    # endOf 接受时间戳和单位。根据指定单位返回日期的结束时间
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'second')") == 1668440712       # 1668440712  2022-11-14 15:45:12对应的时间戳 传递参数: "s" | "second" | "seconds"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'minute')") == 1668440759       # 1668440759  2022-11-14 15:45:59对应的时间戳 传递参数: "m" | "minute" | "minutes"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'hour')") == 1668441599         # 1668441599  2022-11-14 15:59:59对应的时间戳 传递参数: "h" | "hour" | "hours"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'day')") == 1668470399          # 1668470399  2022-11-14 23:59:59对应的时间戳 传递参数: "d" | "day" | "days"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'week')") == 1668988799         # 1668988799  2022-11-20 23:59:59对应的时间戳 传递参数: "w" | "week" | "weeks"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'month')") == 1669852799        # 1669852799  2022-11-30 23:59:59对应的时间戳 传递参数: "M" | "month" | "months"
    assert zen.evaluate_expression(
        "endOf(date('2022-11-14 15:45:12'), 'year')") == 1672444799         # 1672444799  2022-12-30 23:59:59对应的时间戳 传递参数: "y" | "year" | "years"

    # 将时间戳转化为日期字符串
    assert zen.evaluate_expression("dateString(date('2023-10-15'))") == '2023-10-15 00:00:00'
    assert zen.evaluate_expression("dateString(date('2023-10-15') + duration('12h'))") == '2023-10-15 12:00:00'
    assert zen.evaluate_expression("dateString(startOf('2023-01-01 15:45:01', 'day'))") == '2023-01-01 00:00:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-01 15:45:01', 'd'))") == '2023-01-01 23:59:59'
    assert zen.evaluate_expression("dateString(startOf('2023-01-01 15:45:01', 'hour'))") == '2023-01-01 15:00:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-01 15:45:01', 'h'))") == '2023-01-01 15:59:59'
    assert zen.evaluate_expression("dateString(startOf('2023-01-01 15:45:01', 'minute'))") == '2023-01-01 15:45:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-01 15:45:01', 'm'))") == '2023-01-01 15:45:59'
    assert zen.evaluate_expression("dateString(startOf('2023-01-04 15:45:01', 'week'))") == '2023-01-02 00:00:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-04 15:45:01', 'w'))") == '2023-01-08 23:59:59'
    assert zen.evaluate_expression("dateString(startOf('2023-01-04 15:45:01', 'month'))") == '2023-01-01 00:00:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-04 15:45:01', 'M'))") == '2023-01-31 23:59:59'
    assert zen.evaluate_expression("dateString(startOf('2023-01-04 15:45:01', 'year'))") == '2023-01-01 00:00:00'
    assert zen.evaluate_expression("dateString(endOf('2023-01-04 15:45:01', 'y'))") == '2023-12-31 23:59:59'


    # Date function basics zen-enign新增的时间函数
    assert zen.evaluate_expression("d('2023-10-15 14:30')") == '2023-10-15T14:30:00+08:00'    # 当前时区为
    assert zen.evaluate_expression("d('2023-10-15')") == '2023-10-15T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15 14:30:45')") == '2023-10-15T14:30:45+08:00'
    assert zen.evaluate_expression("d('2023-10-15', 'Europe/Berlin')") == '2023-10-15T00:00:00+02:00'
    assert zen.evaluate_expression("d('2023-10-15 14:30', 'Europe/Berlin')") == '2023-10-15T14:30:00+02:00'
    assert zen.evaluate_expression("d('2023-10-15 14:30:45', 'Europe/Berlin')") == '2023-10-15T14:30:45+02:00'
    assert zen.evaluate_expression("d('Europe/Berlin').isValid() and d('Europe/Berlin').isToday()") == True

    # Date manipulation
    assert zen.evaluate_expression("d('2023-10-15').add('1d')") == '2023-10-16T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').add('1d 5h')") == '2023-10-16T05:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').add(1, 'd')") == '2023-10-16T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').sub('2d')") == '2023-10-13T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').sub(1, 'M')") == '2023-09-15T00:00:00+08:00'

    # Date comparisons
    assert zen.evaluate_expression("d('2023-10-15').isBefore(d('2023-10-16'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isBefore(d('2023-10-16'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isBefore(d('2023-10-15'))") == False
    assert zen.evaluate_expression("d('2023-10-15').isAfter(d('2023-10-14'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isAfter(d('2023-10-15'))") == False
    assert zen.evaluate_expression("d('2023-10-15').isSame(d('2023-10-15'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isSame(d('2023-10-16'))") == False
    assert zen.evaluate_expression("d('2023-10-15').isSameOrBefore(d('2023-10-15'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isSameOrBefore(d('2023-10-16'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isSameOrBefore(d('2023-10-14'))") == False
    assert zen.evaluate_expression("d('2023-10-15').isSameOrAfter(d('2023-10-15'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isSameOrAfter(d('2023-10-14'))") == True
    assert zen.evaluate_expression("d('2023-10-15').isSameOrAfter(d('2023-10-16'))") == False
    assert zen.evaluate_expression("d('2025-02-01').isAfter(d('2025-01-05'), 'year')") == False
    assert zen.evaluate_expression("d('2025-02-01').isAfter(d('2024-12-31'), 'year')") == True
    assert zen.evaluate_expression("d('2025-02-01').isBefore(d('2025-03-01'), 'year')") == False
    assert zen.evaluate_expression("d('2025-02-01').isBefore(d('2026-01-01'), 'year')") == True
    assert zen.evaluate_expression("d('2025-02-01').isSame(d('2025-12-31'), 'year')") == True
    assert zen.evaluate_expression("d('2025-02-01').isSame(d('2026-01-01'), 'year')") == False
    assert zen.evaluate_expression("d('2025-02-15').isAfter(d('2025-01-05'), 'month')") == True
    assert zen.evaluate_expression("d('2025-02-15').isAfter(d('2025-02-05'), 'month')") == False
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-03-01'), 'month')") == True
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-02-28'), 'month')") == False
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-02-28'), 'month')") == True
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-03-01'), 'month')") == False
    assert zen.evaluate_expression("d('2025-04-15').isAfter(d('2025-01-01'), 'quarter')") == True
    assert zen.evaluate_expression("d('2025-02-15').isAfter(d('2025-03-31'), 'quarter')") == False
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-04-01'), 'quarter')") == True
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-03-31'), 'quarter')") == False
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-03-15'), 'quarter')") == True
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-04-01'), 'quarter')") == False
    assert zen.evaluate_expression("d('2025-02-15').isAfter(d('2025-02-14'), 'day')") == True
    assert zen.evaluate_expression("d('2025-02-15').isAfter(d('2025-02-15'), 'day')") == False
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-02-16'), 'day')") == True
    assert zen.evaluate_expression("d('2025-02-15').isBefore(d('2025-02-15'), 'day')") == False
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-02-15 12:00:00'), 'day')") == True
    assert zen.evaluate_expression("d('2025-02-15').isSame(d('2025-02-16'), 'day')") == False

    # Date getters
    assert zen.evaluate_expression("d('2023-10-15').year()") == 2023
    assert zen.evaluate_expression("d('2023-10-15').month()") == 10
    assert zen.evaluate_expression("d('2023-10-15').day()") == 15
    assert zen.evaluate_expression("d('2023-10-15').weekday()") == 7
    assert zen.evaluate_expression("d('2023-10-16').weekday()") == 1
    assert zen.evaluate_expression("d('2023-10-15').hour()") == 0
    assert zen.evaluate_expression("d('2023-10-15').minute()") == 0
    assert zen.evaluate_expression("d('2023-10-15').second()") == 0
    assert zen.evaluate_expression("d('2023-10-15').dayOfYear()") == 288
    assert zen.evaluate_expression("d('2023-01-01').dayOfYear()") == 1
    assert zen.evaluate_expression("d('2023-12-31').dayOfYear()") == 365
    assert zen.evaluate_expression("d('2024-12-31').dayOfYear()") == 366
    assert zen.evaluate_expression("d('2023-10-15').quarter()") == 4
    assert zen.evaluate_expression("d('2023-01-15').quarter()") == 1
    assert zen.evaluate_expression("d('2023-04-15').quarter()") == 2
    assert zen.evaluate_expression("d('2023-07-15').quarter()") == 3
    # assert zen.evaluate_expression("d('2023-10-15').timestamp()") == 1697328000000   # 这个默认是系统的时区
    # assert zen.evaluate_expression("d('2023-10-15','UTC').timestamp()") == 1697328000000
    assert zen.evaluate_expression("d('2023-10-15', 'Europe/Berlin').offsetName()") == 'Europe/Berlin'
    assert zen.evaluate_expression("d('2023-10-15', 'America/Los_Angeles').offsetName()") == 'America/Los_Angeles'
    assert zen.evaluate_expression("d('2023-10-15').isLeapYear()") == False
    assert zen.evaluate_expression("d('2024-10-15').isLeapYear()") == True
    assert zen.evaluate_expression("d('2000-10-15').isLeapYear()") == True
    assert zen.evaluate_expression("d('1900-10-15').isLeapYear()") == False

    # Date setters
    assert zen.evaluate_expression("d('2023-10-15','UTC').set('year', 2024)") == '2024-10-15T00:00:00Z'    # 默认是当前系统时区 或者设为utc
    assert zen.evaluate_expression("d('2023-10-15','UTC').set('month', 5)") == '2023-05-15T00:00:00Z'
    assert zen.evaluate_expression("d('2023-10-15','UTC').set('day', 20)") == '2023-10-20T00:00:00Z'
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('hour', 15)") == '2023-10-15T15:30:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('minute', 45)") == '2023-10-15T10:45:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('second', 30)") == '2023-10-15T10:30:30+08:00'

    # Special date checks
    assert zen.evaluate_expression("d().isSame(d(), 'day')") == True
    assert zen.evaluate_expression("d('2023-10-15').startOf('day')") == '2023-10-15T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15T10:30:45Z').startOf('hour')") == '2023-10-15T10:00:00+08:00'   # 这个要注意
    assert zen.evaluate_expression("d('2023-10-15').endOf('day')") == '2023-10-15T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-10-15T10:30:45Z').endOf('hour')") == '2023-10-15T10:59:59+08:00'
    assert zen.evaluate_expression("d('2023-10-15').startOf('month')") == '2023-10-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').endOf('month')") == '2023-10-31T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-10-15').startOf('year')") == '2023-01-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').endOf('year')") == '2023-12-31T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-10-15').startOf('week')") == '2023-10-09T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').endOf('week')") == '2023-10-15T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-10-15').startOf('quarter')") == '2023-10-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15').endOf('quarter')") == '2023-12-31T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-03-15').startOf('quarter')") == '2023-01-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-03-15').endOf('quarter')") == '2023-03-31T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-06-15').startOf('quarter')") == '2023-04-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-06-15').endOf('quarter')") == '2023-06-30T23:59:59+08:00'
    assert zen.evaluate_expression("d('2023-09-15').startOf('quarter')") == '2023-07-01T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-09-15').endOf('quarter')") == '2023-09-30T23:59:59+08:00'

    # Timezone operations
    assert zen.evaluate_expression("d('2023-10-15T00:00:00Z').tz('America/New_York')") == '2023-10-14T12:00:00-04:00'
    assert zen.evaluate_expression("d('2023-10-15T00:00:00Z').tz('Europe/London')") == '2023-10-14T17:00:00+01:00'
    assert zen.evaluate_expression("d('2023-10-15T00:00:00Z').tz('Asia/Shanghai')") == '2023-10-15T00:00:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15T00:00:00+00:00').tz('UTC')") == '2023-10-14T16:00:00Z'
    assert zen.evaluate_expression("d('2023-10-15T12:00:00+02:00', 'Etc/GMT-2').tz('UTC')") == '2023-10-15T10:00:00Z'

    # Relative date methods
    assert zen.evaluate_expression("d().sub(1, 'd').isYesterday()") == True
    assert zen.evaluate_expression("d().add(1, 'd').isTomorrow()") == True
    assert zen.evaluate_expression("d('2023-10-15').isToday()") == False

    # Diff
    assert zen.evaluate_expression("d('2023-10-15').diff(d('2023-10-10'), 'day')") == 5
    assert zen.evaluate_expression("d('2023-10-15T10:00:00Z').diff(d('2023-10-15T08:30:00Z'), 'hour')") == 1
    assert zen.evaluate_expression("d('2023-10-15').diff(d('2023-09-15'), 'month')") == 1
    assert zen.evaluate_expression("d('2023-12-31').diff(d('2023-01-01'), 'year')") == 0
    assert zen.evaluate_expression("d('2023-12-31').diff(d('2022-01-01'), 'year')") == 1
    assert zen.evaluate_expression("d('2023-10-10').diff(d('2023-10-15'), 'day')") == -5
    assert zen.evaluate_expression("d('2023-09-15').diff(d('2023-10-15'), 'month')") == -1
    assert zen.evaluate_expression("d('2022-01-01').diff(d('2023-12-31'), 'year')") == -1
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').diff(d('2023-10-15T10:00:00Z'), 'minute')") == 30
    assert zen.evaluate_expression("d('2023-10-15T10:00:30Z').diff(d('2023-10-15T10:00:00Z'), 'second')") == 30
    assert zen.evaluate_expression("d('2023-10-22').diff(d('2023-10-15'), 'week')") == 1
    assert zen.evaluate_expression("d('2023-10-29').diff(d('2023-10-15'), 'week')") == 2
    assert zen.evaluate_expression("d('2023-07-01').diff(d('2023-01-01'), 'quarter')") == 2
    assert zen.evaluate_expression("d('2023-12-31').diff(d('2023-01-01'), 'quarter')") == 3
    assert zen.evaluate_expression("d('2023-10-15').diff(d('2023-10-15'), 'day')") == 0
    assert zen.evaluate_expression("d('2023-10-15').diff(d('2023-10-15'), 'month')") == 0
    assert zen.evaluate_expression("d('2023-10-15').diff(d('2023-10-15'), 'year')") == 0
    assert zen.evaluate_expression("d('2023-03-31').diff(d('2023-02-28'), 'month')") == 1
    assert zen.evaluate_expression("d('2024-02-29').diff(d('2024-01-31'), 'month')") == 1
    assert zen.evaluate_expression("d('2023-05-31').diff(d('2023-04-30'), 'month')") == 1
    assert zen.evaluate_expression("d('2023-03-31').diff(d('2023-02-28'), 'month')") == 1
    assert zen.evaluate_expression("d('2023-02-28').diff(d('2023-01-31'), 'month')") == 1
    assert zen.evaluate_expression("d('2023-04-30').diff(d('2023-03-31'), 'month')") == 1
    assert zen.evaluate_expression("d('2024-02-29').diff(d('2023-02-28'), 'year')") == 1
    assert zen.evaluate_expression("d('2023-12-31').diff(d('2023-01-01'), 'year')") == 0
    assert zen.evaluate_expression("d('2024-01-01').diff(d('2023-01-01'), 'year')") == 1
    assert zen.evaluate_expression("d('2025-01-01').diff(d('2020-01-01'), 'year')") == 5
    assert zen.evaluate_expression("d('2023-12-01').diff(d('2023-01-01'), 'month')") == 11
    assert zen.evaluate_expression("d('2023-12-31').diff(d('2023-01-01'), 'day')") == 364
    assert zen.evaluate_expression("d('2023-10-15T12:00:00Z').diff(d('2023-10-15T10:30:00Z'), 'hour')") == 1
    assert zen.evaluate_expression("d('2023-10-16T12:00:00Z').diff(d('2023-10-15T18:00:00Z'), 'day')") == 0

    # Formatting
    assert zen.evaluate_expression("d('2023-10-15').format('%Y-%m-%d')") == '2023-10-15'
    assert zen.evaluate_expression("d('2023-10-15').format('%Y/%m/%d')") == '2023/10/15'
    assert zen.evaluate_expression(
        "d('2023-10-15T14:30:45Z').format('%A, %B %d %Y, %H:%M:%S')") == 'Sunday, October 15 2023, 14:30:45'
    assert zen.evaluate_expression("d('2023-10-15T14:30:45Z').format('%a %b %d %H:%M')") == 'Sun Oct 15 14:30'
    assert zen.evaluate_expression("d('2023-10-15T14:30:45Z').format('Day %j of year %Y')") == 'Day 288 of year 2023'
    assert zen.evaluate_expression("d('2023-10-15T14:30:45.123Z').format('%H:%M:%S.%f')") == '14:30:45.123000000'

    # Date validations
    assert zen.evaluate_expression("d(null).isValid()") == False
    assert zen.evaluate_expression("d('foo').isValid()") == False
    assert zen.evaluate_expression("d('2023-13-01').isValid()") == False
    assert zen.evaluate_expression("d('2023-02-30').isValid()") == False

    # Date comparison operators
    assert zen.evaluate_expression("d('2023-10-15') == d('2023-10-15')") == True
    assert zen.evaluate_expression("d('2023-10-15') == d('2023-10-16')") == False
    assert zen.evaluate_expression("d('2023-10-15') != d('2023-10-16')") == True
    assert zen.evaluate_expression("d('2023-10-15') != d('2023-10-15')") == False
    assert zen.evaluate_expression("d('2023-10-15') < d('2023-10-16')") == True
    assert zen.evaluate_expression("d('2023-10-15') < d('2023-10-15')") == False
    assert zen.evaluate_expression("d('2023-10-15') <= d('2023-10-15')") == True
    assert zen.evaluate_expression("d('2023-10-16') <= d('2023-10-15')") == False
    assert zen.evaluate_expression("d('2023-10-16') > d('2023-10-15')") == True
    assert zen.evaluate_expression("d('2023-10-15') > d('2023-10-15')") == False
    assert zen.evaluate_expression("d('2023-10-15') >= d('2023-10-15')") == True
    assert zen.evaluate_expression("d('2023-10-15') >= d('2023-10-16')") == False

    # Date range operators
    assert zen.evaluate_expression("d('2023-10-15') in [d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-01') in [d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-31') in [d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-09-30') in [d('2023-10-01')..d('2023-10-31')]") == False
    assert zen.evaluate_expression("d('2023-11-01') in [d('2023-10-01')..d('2023-10-31')]") == False
    assert zen.evaluate_expression("d('2023-10-15') in (d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-01') in (d('2023-10-01')..d('2023-10-31'))") == False
    assert zen.evaluate_expression("d('2023-10-31') in (d('2023-10-01')..d('2023-10-31'))") == False
    assert zen.evaluate_expression("d('2023-10-02') in (d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-30') in (d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-15') in [d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-01') in [d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-31') in [d('2023-10-01')..d('2023-10-31'))") == False
    assert zen.evaluate_expression("d('2023-10-30') in [d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-15') in (d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-01') in (d('2023-10-01')..d('2023-10-31')]") == False
    assert zen.evaluate_expression("d('2023-10-31') in (d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-02') in (d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-15') not in [d('2023-10-01')..d('2023-10-31')]") == False
    assert zen.evaluate_expression("d('2023-09-30') not in [d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-11-01') not in [d('2023-10-01')..d('2023-10-31')]") == True
    assert zen.evaluate_expression("d('2023-10-01') not in (d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-31') not in (d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-15') not in (d('2023-10-01')..d('2023-10-31'))") == False
    assert zen.evaluate_expression("d('2023-10-31') not in [d('2023-10-01')..d('2023-10-31'))") == True
    assert zen.evaluate_expression("d('2023-10-01') not in (d('2023-10-01')..d('2023-10-31')]") == True

    assert zen.evaluate_expression("min([d('2023-01-15'), d('2023-03-20'), d('2023-02-10')])") != '2023-01-15T00:00:00Z'
    assert zen.evaluate_expression("max([d('2023-01-15'), d('2023-03-20'), d('2023-02-10')])") != '2023-03-20T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-10-15'), d('2023-10-01'), d('2023-10-31')])") != '2023-10-01T00:00:00Z'
    assert zen.evaluate_expression("max([d('2023-10-15'), d('2023-10-01'), d('2023-10-31')])") != '2023-10-31T00:00:00Z'
    assert zen.evaluate_expression(
        "min([d('2023-10-15T10:30:00Z'), d('2023-10-15T08:15:00Z'), d('2023-10-15T14:45:00Z')])") != '2023-10-15T08:15:00Z'
    assert zen.evaluate_expression(
        "max([d('2023-10-15T10:30:00Z'), d('2023-10-15T08:15:00Z'), d('2023-10-15T14:45:00Z')])") != '2023-10-15T14:45:00Z'
    assert zen.evaluate_expression("min([d('2022-12-31'), d('2023-01-01'), d('2024-01-01')])") != '2022-12-31T00:00:00Z'
    assert zen.evaluate_expression("max([d('2022-12-31'), d('2023-01-01'), d('2024-01-01')])") != '2024-01-01T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-10-15'), d('2023-10-15'), d('2023-10-15')])") != '2023-10-15T00:00:00Z'
    assert zen.evaluate_expression("max([d('2023-10-15'), d('2023-10-15'), d('2023-10-15')])") != '2023-10-15T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-10-15')])") != '2023-10-15T00:00:00Z'
    assert zen.evaluate_expression("max([d('2023-10-15')])") != '2023-10-15T00:00:00Z'
    assert zen.evaluate_expression(
        "min([d('2023-10-15T10:00:00Z'), d('2023-10-15T12:00:00Z')])") != '2023-10-15T10:00:00Z'
    assert zen.evaluate_expression(
        "max([d('2023-10-15T10:00:00Z'), d('2023-10-15T12:00:00Z')])") != '2023-10-15T12:00:00Z'
    assert zen.evaluate_expression("min([d('1900-01-01'), d('2000-01-01'), d('1950-06-15')])") != '1900-01-01T00:00:00Z'
    assert zen.evaluate_expression("max([d('1900-01-01'), d('2000-01-01'), d('1950-06-15')])") != '2000-01-01T00:00:00Z'
    assert zen.evaluate_expression("min([d('2024-02-29'), d('2023-02-28'), d('2024-03-01')])") != '2023-02-28T00:00:00Z'
    assert zen.evaluate_expression("max([d('2024-02-29'), d('2023-02-28'), d('2024-03-01')])") != '2024-03-01T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-01-31'), d('2023-02-28'), d('2023-03-31')])") != '2023-01-31T00:00:00Z'
    assert zen.evaluate_expression("max([d('2023-01-31'), d('2023-02-28'), d('2023-03-31')])") != '2023-03-31T00:00:00Z'
    assert zen.evaluate_expression(
        "min([d('2023-10-15').add(1, 'd'), d('2023-10-15').sub(1, 'd'), d('2023-10-15')])") != '2023-10-14T00:00:00Z'
    assert zen.evaluate_expression(
        "max([d('2023-10-15').add(1, 'd'), d('2023-10-15').sub(1, 'd'), d('2023-10-15')])") != '2023-10-16T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-01-01'), d('2023-12-31')]).isBefore(d('2023-06-01'))") == True
    assert zen.evaluate_expression("max([d('2023-01-01'), d('2023-12-31')]).isAfter(d('2023-06-01'))") == True

    assert zen.evaluate_expression("date('2023-10-15') + duration('1d')") == 1697414400

    assert zen.evaluate_expression("date('2023-10-15 00:00:00+08:00')") == 1697299200
    assert zen.evaluate_expression("date('2023-10-15 08:00:00+08:00')") == 1697328000
    assert zen.evaluate_expression("date('2023-10-15')") == 1697328000

    assert zen.evaluate_expression("year(date('2023-10-15'))") == 2023
    assert zen.evaluate_expression("monthOfYear(date('2023-10-15'))") == 10
    assert zen.evaluate_expression("dayOfMonth(date('2023-10-15'))") == 15
    assert zen.evaluate_expression("dayOfWeek(date('2023-10-15'))") == 7
    assert zen.evaluate_expression("weekOfYear(date('2023-10-15'))") == 41


    assert zen.evaluate_expression("dateString(date('2023-10-15'))") == '2023-10-15 00:00:00'
    assert zen.evaluate_expression("dateString(date('2023-10-15') + duration('12h'))") == '2023-10-15 12:00:00'


def test_special_zen_expression_date_and_time():
    # 特殊 特别注意 涉及到时区的时候，默认是系统的时区

    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('hour', 15)") != '2023-10-15T15:30:00Z'
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('hour', 15)") == '2023-10-15T15:30:00+08:00'

    assert zen.evaluate_expression("date('2023-10-15 00:00:00+08:00')") == 1697299200
    assert zen.evaluate_expression("date('2023-10-15 08:00:00+08:00')") == 1697328000
    # 系统是东八区
    assert zen.evaluate_expression("date('2023-10-15')") == 1697328000


    # 就算原时区带了Z 表示零时区 带只会取系统的时区
    assert zen.evaluate_expression("d('2023-10-15 14:30')") == '2023-10-15T14:30:00+08:00'  # 当前系统时区为东八区
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('hour', 15)") == '2023-10-15T15:30:00+08:00'
    assert zen.evaluate_expression("d('2023-10-15T10:30:00Z').set('hour', 15)") != '2023-10-15T15:30:00Z'

    assert zen.evaluate_expression("min([d('2023-01-15'), d('2023-03-20'), d('2023-02-10')])") != '2023-01-15T00:00:00Z'
    assert zen.evaluate_expression("min([d('2023-01-15'), d('2023-03-20'), d('2023-02-10')])") == '2023-01-15T00:00:00+08:00'


def test_zen_expression_array():
    '''
    数组表示其他数据类型的列表（数字、字符串、布尔值列表）
    示例：
    ['a', 'b', 'c'];
    [1, 2, 3]; 
    [true, false];
    '''
    # 数组目前不支持字面量等值判断
    assert not zen.evaluate_expression("[1,2,3]==[1,2,3]") 
    assert not zen.evaluate_expression("['a', 'b', 'c']==['a', 'b', 'c']")

    # 数组成员访问
    assert zen.evaluate_expression("a[1]", { "a": [1, 2, 3, 4]}) == 2

    # 数组关系运算符 in not in
    assert zen.evaluate_expression("1 in a", { "a": [1, 2, 3, 4]}) == True
    assert zen.evaluate_expression("5 not in a", { "a": [1, 2, 3, 4]}) == True

    # 数组范围运算符
    # 闭区间
    assert zen.evaluate_expression("a in [0..2]", {"a": 0}) == True     # 等价 a >= 0 and a <= 2
    assert zen.evaluate_expression("a in (0..2)", {"a": 0}) == False     # 等价 a > 0 and a < 2
    assert zen.evaluate_expression("a in [0..2)", {"a": 1}) == True     # 等价 a >= 0 and a < 2
    assert zen.evaluate_expression("a in (0..2]", {"a": 2}) == True     # 等价 a = 0 and a <= 2

    # 开区间 ]4..6[ 及 )4..6[ 不支持
    assert zen.evaluate_expression("a in )4..6(", {"a": 3}) == True  # 等价 a < 4 or a > 6
    assert zen.evaluate_expression("a in )4..6(", {"a": 7}) == True  # 等价 a < 4 or a > 6
    assert zen.evaluate_expression("a in ]4..6(", {"a": 4}) == True  # 等价 a <= 4 or a > 6
    assert zen.evaluate_expression("a in ]4..6(", {"a": 7}) == True  # 等价 a <= 4 or a > 6

    # 数组函数
    # len 接受一个数字数组并返回所有元素的总和
    assert zen.evaluate_expression("len(a)", {"a": [1, 2, 3]}) == 3

    # sum 接受一个数字数组并返回所有元素的总和
    assert zen.evaluate_expression("sum(a)", {"a": [1, 2, 3]}) == 6
    assert zen.evaluate_expression("sum(a)", {"a": [1.1, 2.53, 3]}) == 6.63

    # avg 接受一个数字数组并返回所有元素的平均值
    assert zen.evaluate_expression("avg(a)", {"a": [1, 2, 3]}) == 2

    # min 接受一个数字数组并返回最小元素
    assert zen.evaluate_expression("min(a)", {"a": [1, 2, 3]}) == 1

    # max 接受一个数字数组并返回最大元素
    assert zen.evaluate_expression("max(a)", {"a": [1, 2, 3]}) == 3

    # zen-engine==0.24.2不支持内置的 mean 方法
    # mean 接受一个数字数组并返回平均值
    # assert zen.evaluate_expression("mean(a)", {"a": [1, 2, 3]}) == 2

    # mode 接受一个数字数组并返回出现最多的元素(众数)
    assert zen.evaluate_expression("mode(a)", {"a": [1, 1, 2, 2, 2, 2, 3, 3]}) == 2

    # contains 接受一个数组和一个搜索参数。如果元素存在于数组中，则返回 true
    assert zen.evaluate_expression("contains(a, b)", {"a": [1, 2, 3], "b": 3}) == True
    assert zen.evaluate_expression("contains(a, b)", {"a": ["a", "b", "c"], "b": "c"}) == True

    # flatten 接受数组并通过单个级别展平参数
    assert zen.evaluate_expression("flatten([1, 'a', ['b', 'c'], [4]])") == [1, "a", "b", "c", 4]
    assert zen.evaluate_expression("flatten([  [1, 2, 3],  [4, 5, 6],])") == [1, 2, 3, 4, 5, 6]

    # 闭包函数
    # all 如果数组的所有元素都满足条件，则返回 true
    assert zen.evaluate_expression("all(a, # in [1..3])", {"a": [1, 2, 3]}) == True
    assert zen.evaluate_expression("all(a, # == 'a')", {"a": ["b", "c"]}) == False

    # some 如果数组中至少有一个元素满足条件，则返回 true
    assert zen.evaluate_expression("some(a, # == 3)", {"a": [1, 2, 3]}) == True
    assert zen.evaluate_expression("some(a, # > 5)", {"a": [1, 2, 3]}) == False

    # none 如果数组中没有元素满足条件，则返回 true
    assert zen.evaluate_expression("none(a, # > 5)", {"a": [1, 2, 3]}) == True
    assert zen.evaluate_expression("none(a, # == 'c')", {"a": ["b", "c"]}) == False

    # filter 返回一个仅包含满足条件的元素的新数组
    assert zen.evaluate_expression("filter(a, # > 1)", {"a": [1, 2, 3]}) == [2, 3]

    # map 返回具有重新映射值的新数组
    assert zen.evaluate_expression("map(a, 'hello ' + #)", {"a": ["world", "user"]}) == ["hello world", "hello user"]
    assert zen.evaluate_expression("map(a, # + 1)", {"a": [1, 2, 3]}) == [2, 3, 4]

    # flatMap 返回具有重新映射值的新数组并将其展平
    assert zen.evaluate_expression("flatMap(a, map(#, # + 1))", {"a": [[1, 2, 3], [4, 5, 6]]}) == [2, 3, 4, 5, 6, 7]

    # count 对数组中的元素按照过滤条件计数
    assert zen.evaluate_expression("count(a, # > 1)", {"a": [1, 2, 3]}) == 2

    # 数组函数复合使用
    assert zen.evaluate_expression("map(filter([1, 2, 3, 4, 5], # > 2), # * 2)") == [6, 8, 10]
    assert zen.evaluate_expression("len(filter([1, 2, 3, 4, 5], # % 2 == 0))")  == 2
    assert zen.evaluate_expression("sum(filter([1, 2, 3, 4, 5], # % 2 == 0))" ) == 6
    assert zen.evaluate_expression("sum(map(filter([1, 2, 3, 4, 5], # > 3), # ^ 2))") == 41

    assert zen.evaluate_expression("some(map([1, 2, 3], # * 2), # > 5)") == True
    assert zen.evaluate_expression("all(map([1, 2, 3], # + 2), # > 2)" ) == True
    assert zen.evaluate_expression("contains(map([1, 2, 3], # * 2), 6)") == True


    
def test_zen_expression_context():
    '''
    Context 是一种特殊的全局数据类型，其结构与节点接收到的 JSON 输入相同。
    示例：
    {  "customer": {    
       "firstName": "John",    
       "lastName": "Doe",    
       "groups": ["admin", "user"],    
       "age": 34  
        }
    }
    '''
    assert zen.evaluate_expression("{a:1}")   == {'a': 1}
    assert zen.evaluate_expression("{'a':1}") == {'a': 1}
    assert zen.evaluate_expression('{"a":1}') == {'a': 1}

    # 注意, object(context) 不支持字面量判断.
    assert not zen.evaluate_expression('{"a":1}=={"a":1}')

    # 属性访问
    assert zen.evaluate_expression("customer.firstName", {"customer": 
      {    
       "firstName": "John",    
       "lastName": "Doe",    
       "groups": ["admin", "user"],    
       "age": 34  
        }
    }) == "John"

    # 运用上述不同数据类型生成表达式
    assert zen.evaluate_expression("customer.firstName + customer.lastName", {"customer":
       {    
       "firstName": "John",    
       "lastName": "Doe",    
       "groups": ["admin", "user"],    
       "age": 34  
        }
    }) == "JohnDoe"

    assert zen.evaluate_expression("customer.age in [30..40]", {"customer":
       {    
       "firstName": "John",    
       "lastName": "Doe",    
       "groups": ["admin", "user"],    
       "age": 34  
        }
    }) == True

    # 多层嵌套
    assert zen.evaluate_expression("user.address.city", {"user":{"address":{"city":"New York"}}}) == "New York"
    assert zen.evaluate_expression("user.contacts[0].phone", {"user":{"contacts":[{"phone":"123-456-7890"}]}}) == "123-456-7890"


def test_zen_expression_ternary_operators():
    assert zen.evaluate_expression("score > 70 ? 'Pass' : 'Fail'", {"score":85}) == 'Pass'
    assert zen.evaluate_expression("score > 90 ? 'A' : score > 80 ? 'B' : score > 70 ? 'C' : 'D'", {"score":85}) == 'B'