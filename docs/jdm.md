
# JDM Standard

The JSON Decision Model format used by GoRules for portable, version-controllable business rules.

JDM (JSON Decision Model) is the file format used by GoRules to represent decision graphs. It’s a human-readable JSON structure that captures nodes, edges, and configuration in a portable format.

# json decision model 规范

Json decision graph 规范以 json 格式定义，用于编辑器和执行引擎之间的规约。

最外层级由规则id, 规则元信息，规则节点和节点之间的有向无环图的拓扑排序(dag)边组成。

*代码块*
```javascript
{
  "nodes": [...],
  "edges": [...],
  "metadata": {...},
  "id": "710c5ba6752bdb626cda40a65079d382",
}
```

id 表示规则的唯一编号. 可以用于规则区分和命名空间划分.

## 元数据定义(metadata)

元数据用于 zen-engine 基于规则的元信息，比如版本, 用户等. 执行引擎在运行时可以获取的全局信息。

*代码块*
```json
{
  "metadata": {
    "version": "1.0.0",
    "author": "wanghao@geetest.com",
    "description": "login risk check",
    "tags": ["login", "risk control"]
  }
}
```

## 节点(nodes)

决策引擎编辑器节点的规范如下所示:

*代码块*
```json
{
  "id": "node-1",
  "type": "decisionTableNode",
  "name": "Customer Discount",
  "position": { "x": 200, "y": 100 },
  "content": {
    // Node-specific configuration
  }
}
```

节点的类型由type字段可以是这8个类型:`inputNode`, `outputNode`, `functionNode`, `decisionNode`, `decisionTableNode`, `expressionNode`, `switchNode`, `customNode`

`inputNode`请求节点只能定义输出参数，`outputNode`的输入参数就是整个规则的输出参数.其他节点分别可以输入参数和向下一个节点输出参数。

### 请求节点(`inputNode`)

定义规则的输入参数示例，一个规则只能有一个请求节点。

*代码块*
```json
{
  "type": "inputNode",
```

参考文档如下:

### 响应节点(`outputNode`)

表示规则执行流在此节点输出，输出内容为上一个节点的输出参数。一个规则可以用一个或者多个响应节点。

*代码块*
```json
{
  "type": "outputNode",
  "content": {
    "schema": ""
  },
  "id": "73eaadcd-ce5b-4e4d-b072-2b42c329aa9c",
  "name": "response",
  "position": {
    "x": 650,
    "y": 280
  }
}
```

### 表达式节点(`expressionNode`)

1. $.xxx 可以在表达式中交叉引用当前节点的其他字段
2. passThrough: **true/false**， 用于控制是否透传入参。
3. inputField， 用于控制表达式中的变量所在的命名空间， inputField 设置为 **foo**， 表达式 是 **bar。*****baz****， 那么实际的变量取值层级就是**** foo。bar。baz****， 这样方便去设置变量的层级。*
4. outputPath， 用于控制输出字段的命名空间。
5. executionMode: single/loop， 用于控制是否循环执行
表达式中循环一般会和inputField字段联动， inputField 字段必须是数组类型，这样才能用于循环。

*代码块*
```json
{
  "type": "expressionNode",
  "content": {
    "expressions": [],
    "passThrough": true,
    "inputField": null,
    "outputPath": null,
    "executionMode": "single"
  },
  "id": "dc07e495-d3cf-47ca-a642-e700abd103ec",
  "name": "expression1",
  "position": {
    "x": 330,
    "y": 405
  }
}
```

### 决策表节点(`decisionTableNode`)

决策表一般用于一个或多个字段的决策匹配， 有如下配置属性:

1. hitPolicy: **first / collect**， 用于控制决策表中条件的匹配顺序， first 是指从上往下匹配的第一个， collect 表示返回所有规则的匹配结果。 Collect 整个决策表会返回一个数组， 需要配置 outPath 以便将数组放在此键下面。
2. passThrough: **true/false**， 用于控制是否透传入参。
3. inputField，用于控制表达式中的变量所在的命名空间，inputField 设置为 **foo**， 表达式 是 **bar。*****baz****， 那么实际的变量取值层级就是**** foo。bar。baz****， 这样方便去设置变量的层级。*
4. outputPath， 用于控制输出字段的命名空间。
5. executionMode: single/loop
决策表中循环一般会和inputField字段联动， inputField 字段必须是数组类型，这样才能用于循环。

*代码块*
```json
{
  "type": "decisionTableNode",
  "content": {
    "hitPolicy": "first",
    "rules": [],
    "inputs": [
      {
        "id": "4a121f68-dfac-4564-a5d5-00302e0a7871",
        "name": "Input"
      }
    ],
    "outputs": [
      {
        "id": "34d5306f-2b55-4a82-a541-75daffb4eed5",
        "name": "Output",
        "field": "output"
      }
    ],
    "passThrough": true,
    "inputField": null,
    "outputPath": null,
    "executionMode": "single"
  },
  "id": "bbae67c5-99d1-4a5c-81ee-bc187d27ead6",
  "name": "decisionTable1",
```

### 分支节点(`switchNode`)

根据输入参数进行表达式求值判定是否执行后面的分支，表达式求值为布尔 true，那么执行对应的分支。

*代码块*
```json
{
  "type": "switchNode",
  "content": {
    "hitPolicy": "first",
    "statements": [
      {
        "id": "9e247480-d939-4f84-9069-de7b82ee9953",
        "condition": "",
        "isDefault": false
      }
    ]
  },
  "id": "fb4a58dd-a50c-4f49-91e1-d75ebc573275",
  "name": "switch1",
  "position": {
    "x": 615,
    "y": 550
  }
}
```

配置属性如下:

1. hitPolicy: **first / collect**， 用于控制决策表中条件的匹配顺序， first 是指从上往下匹配的第一个， collect 表示执行所有分支。默认是 first。
![Image Placeholder - 图片占位符]

![Image Placeholder - 图片占位符]

### js函数节点(`functionNode`)

使用 javascript 对输入参数进行转化并输出。

*代码块*
```json
{
  "type": "functionNode",
  "content": {
    "source": "import zen from 'zen';\n\n/** @type {Handler} **/\nexport const handler = async (input) => {\n  return input;\n};\n"
  },
  "id": "865b997d-8309-49a1-8de4-cff5f9bb1eb6",
  "name": "function1",
  "position": {
    "x": 315,
    "y": 535
  }
}
```

### 自定义节点(`customNode`)

决策流程中需要使用 zen 表达式不支持的功能，或者查询外部数据时，需要提供一种机制去引入外部的实现。现在拟实现在决策流程中添加一种可以使用代码扩展的自定义节点。

*代码块*
```json

```

自定义节点包含如下属性:

1. passThrough: **true/false**， 用于控制是否透传入参。
2. inputField， 用于控制表达式中的变量所在的命名空间， inputField 设置为 **foo**， 表达式 是 **bar。*****baz****， 那么实际的变量取值层级就是**** foo。bar。baz****， 这样方便去设置变量的层级。*
3. outputPath， 用于控制输出字段的命名空间。
![Image Placeholder - 图片占位符]

自定义节点有如下分类，每个分类中包含相关的算子，这些算子可以在编排规则及其流程时和外部系统交互，可以保存一些规则状态，也可以去查询外部的参考数据，以便强化风控的能力和效果。

#### 名单

用于在决策引擎用于某种查询逻辑的判定，一般用于各种属性和维度的黑名单，白名单等。在决策引擎中可以根据相关的逻辑去编排节点的顺序，在特定的条件下实现名单的添加，删除，查询逻辑，甚至支持把相关名单拉黑一段时间(ttl名单)。

名单也可以视作由客户根据业务逻辑快速构造的“业务画像”。

#### ip画像

一般用于解析ip地理位置，ip 段(未来会支持cidr)。公司沉淀了很多ip库， 未来也会以画像的方式来提供查询函数。

#### 手机号画像

用于解析手机号是否是虚拟号，以及将公司的手机号库沉淀为画像提供查询函数。

#### 计数器

用于滑动窗口计数和滑动窗口去重计数。比如统计手机号或者IP在距离当前请求10秒钟，1分钟，5分钟，1小时，1天，7天的计数量，这是滑动窗口计数。或者统计ip在某个手机号下的**去重个数**， 时间窗口也是10秒钟，1分钟，5分钟，1小时，1天，7天。

![Image Placeholder - 图片占位符]

这是发现时间维度上异常模式最有效的手段。高频率表示时间维度上的聚集，这往往是需要进行业务异常的前兆，利用滑动窗口的计数器可以实时监控这些异常模式。

#### 共享计数器

共享计数器的功能同上，只是可以跨节点，跨规则共享某个计数器。一般用于多个场景监控共享一个业务指标。

比如航司的ibe业务的查询订比。

#### http请求

在决策引擎中的某个节点发送http请求并接收返回值。一般用于在决策引擎的规则中查询外部数据，信息，画像；或者和规则判定结合在一起去触发外部的执行动作。返回值必须是json。

#### 通知

决策引擎中用于向外部发送邮件，飞书，叮叮，或者提供一个webhook的url(由决策引擎去触发)的一种通知机制。此功能是监控触发外部动作的执行模块。

#### 默认算子

如果某个函数不属于其他自定义节点类别，那么就会放在此默认算子节点中。

## 边(edges)

决策引擎编辑器节点的边的规范如下所示:

*代码块*
```json
{
  "id": "edge-1",
  "sourceId": "input-node",
  "targetId": "decision-table-node",
  "sourceHandle": "output",
  "targetHandle": "input"
}
```

一份完整的 json decision graph 定义如下:

*代码块*
```json

```


## reference

[JSON Decision Model format](https://docs.gorules.io/developers/jdm/standard)  