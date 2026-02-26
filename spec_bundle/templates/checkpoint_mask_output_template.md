# Checkpoint 控制输出模板（系统解析）

当你是 **NODE2: checkpoint** 的 agent 时，你的最终输出会被系统解析，用来决定下一步走哪些分支。

## 你必须输出（仅输出 JSON）
- 不要 Markdown
- 不要解释
- 不要代码块
- 不要多余字段

输出格式：
```json
{
  "true_successors_mask":  [bool, bool, ...],
  "false_successors_mask": [bool, bool, ...]
}
```

## 字段含义
- `true_successors_mask`：ChooseEdge 子边选择（真后继）
- `false_successors_mask`：BackEdge 子边选择（回滚/假后继）

## 硬规则
1) mask 的元素顺序必须对齐系统给出的后继列表顺序。
2) mask 长度必须等于对应后继列表长度。
3) 值必须是 true/false 布尔值。
4) 全不选：输出全 false。
