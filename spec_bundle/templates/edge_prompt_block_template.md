# 边消息块（供下游 Agents 阅读）

下游节点会把来自多条输入边的消息拼接成一个 prompt。每条边消息都包在结构化块中。

格式：
```
[[EDGE:{edge_id} TYPE:{edge_type} TS:{ts}]]
{content}
[[/EDGE]]
```

说明：
- `edge_id`：边/子边 ID
- `edge_type`：Normal / ChooseSub / BackSub / Gate 等
- `ts`：该条消息的时间戳
- `content`：上游节点/agents 输出正文
