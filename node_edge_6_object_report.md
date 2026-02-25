# node_edge_6_object 详解报告

基于文件：`node_edge_6_object_oop_spec_python_pseudocode.md`

---

## 1. 总览：什么是“6个对象”

该规格把运行时图抽象为 **2个节点对象 + 4个边对象 = 6个核心对象**：

- 节点对象（Node）
  1. `WorkVertexObject`
  2. `CheckPointObject`
- 边对象（Edge）
  3. `GateTransitionObject`
  4. `DecisionTransitionObject`
  5. `RollbackTransitionObject`
  6. `SyncTransitionObject`

其中，节点负责“执行与判定”，边负责“路由与约束”。整体目标是：

- 将 TRUE / PSEUDO 两类输出严格分流；
- 用 Gate/Decision/Sync/Rollback 四种语义边控制流程；
- 用策略、证据、规则、全局不变量确保可审计和可验证。

---

## 2. 共同基础（所有对象共享的运行时语义）

### 2.1 关键类型

- `OutputKind`: `TRUE` / `PSEUDO`
- `NodeKind`: `WORK` / `CHECKPOINT`
- `EdgeKind`: `GATE` / `DECISION` / `ROLLBACK` / `SYNC`
- `FailureAction`: `BLOCK` / `RERUN` / `ROLLBACK` / `ESCALATE`
- `ExecState`: 从 `WAITING_INPUTS` 到 `DONE/FAILED` 的完整状态机

### 2.2 公共审计与策略机制

两个节点对象都依赖：

- `PolicyRule`：声明式策略（条件 + 动作）
- `OutputContract`：声明式输出守卫
- `EvidenceItem`：证据记录
- `policy_conflict_resolver(...)`：优先级冲突解析（低 priority 值优先）

### 2.3 BaseEdge 统一抽象

四类边都继承 `BaseEdge`，统一字段：

- `id`, `from_node_id`, `to_node_id`
- `from_output_name`, `from_output_kind`, `to_input_kind`
- `enabled`, `kind`

默认行为：

- `can_fire(ctx)`：仅检查 `enabled`
- `transmit(payload, ctx)`：原样透传

子类在此基础上覆写约束逻辑。

---

## 3. 对象一：WorkVertexObject（工作节点）

## 3.1 角色定位

`WorkVertexObject` 是主要业务执行单元，负责：

1. 接收输入（TRUE/PSEUDO）；
2. 按 join 模式判断是否可执行；
3. 执行业务逻辑并计算 rerun delta；
4. 通过策略与守卫选择输出；
5. 将结果路由到后续边。

### 3.2 输入聚合语义

- `input_join_mode = ALL`：必须达到 `true_input_expected_count` 才 `READY_FINAL`
- `input_join_mode = SELECT`：采用“n选k（默认选1）”
  - `arrived == early_select_exact_count` 才可执行
  - 若 `early_reject_multi_select=True` 且超出k，直接 `FAILED`

这是一个**严格单选/定选**语义，不是“达到阈值就放行”。

### 3.3 执行与状态机

主流程：

- `run_cycle_if_ready()`
  - 从 `READY_PARTIAL/READY_FINAL` 进入 `RUNNING`
  - `execute_business_logic(partial_mode)`
  - `evaluate_delta_for_rerun()`
  - 输出评估（`EVALUATING_OUTPUT`）
  - 结束态：`DONE / FAILED / PARTIAL_DONE`

### 3.4 核心合规检查

在 `select_outputs()` 中依次执行：

1. 文件禁用策略（`enforce_access_requests_or_fail`）
2. 外部 claim 验证（`enforce_external_claims_or_fail`）
3. 文本策略（禁止“合理化违规”、禁止“是否继续”式提示）
4. 工具调用非零（`tool_calls > 0`）

任何一项失败都会返回失败 `NodeResult` 并给出 `Verdict` + `FailureAction` + pseudo 输出。

### 3.5 输出选择

- 根据 `OutputContract.guard_kind` 过滤 TRUE/PSEUDO 候选
- 按 `priority` 排序
- 若 TRUE 候选不足 `min_true_outputs`，失败并触发 rerun 类伪输出
- 否则批准输出

结论：`WorkVertexObject` 是“执行 + 合规 + 输出决策”的核心对象。

---

## 4. 对象二：CheckPointObject（检查点节点）

### 4.1 角色定位

`CheckPointObject` 是质量闸门与放行控制节点，负责：

- 聚合多个 gate 结果；
- 控制 validator 锁；
- 判定是否允许 TRUE 输出继续传播；
- 在不达标时阻断并返回原因。

### 4.2 与 Work 的差异

- `node_kind = CHECKPOINT`
- 自带 gate 体系：`TIME` / `VALIDATOR` / `TOOL_USE` / `REQUIRED_FILES` / `REQUIRED_GATES`
- 有 `validator_lock_state`，且 `_block_true_output_routing()` 在 `LOCKED` 时阻断 TRUE 路由
- 能通过策略动作动态启停 gate 类边（`SET_GATE_EDGE_ENABLED`）

### 4.3 核心判定流程

`evaluate_and_decide(...)` 关键步骤：

1. `policy_conflict_resolver(...)`
2. 时间门：`check_time_gate()`
3. 验证器门：`check_validator_gate()`（仅 verdict=`APPROVE` 才解锁）
4. 工具门：`check_tool_use_gate()`
5. 必需文件门：`check_required_files_gate()`
6. 聚合门：`aggregate_required_gates()`
7. 应用 `fail_rule_kind` / `pass_rule_kind`

若全部通过，输出 `gate_pass`。

### 4.4 快照防重复评估

- 使用输入 token 哈希作为 `last_evaluated_snapshot_key`
- 相同输入快照不重复评估（避免重复放行/重复副作用）

结论：`CheckPointObject` 是“闸门编排 + 质量放行 + 锁控制”的治理对象。

---

## 5. 对象三：GateTransitionObject（门控边）

### 5.1 语义

用于标准门控流转（TRUE→TRUE），适合“是否通过某类 gate”场景。

### 5.2 触发条件

- `enabled=False` -> 不触发
- 若 `mandatory=False` -> 直接允许
- 若 `mandatory=True` -> 要求 `ctx[gate_signal_key]` 为真（默认 `gate_passed`）

### 5.3 传输增强

`transmit` 会在 payload 中附加：

- `gate_family`
- `gate_checked=True`

结论：Gate 边是“显式门控语义”的轻量载体。

---

## 6. 对象四：DecisionTransitionObject（决策边）

### 6.1 语义

用于分支/汇聚决策（TRUE→TRUE），强调“先完成，再单选路由”。

### 6.2 触发条件（严格）

- 上游完成标志：`ctx[upstream_done_key]` 为真（默认 `decision_ready`）
- 只允许单选：`ctx[selected_count_key] == 1`
- 当前边路由名与 `ctx[chosen_route]` 相等

### 6.3 传输增强

输出附加：

- `decision_route`
- `decision_basis`

结论：Decision 边把“决策完成 + 路由唯一性”作为强约束，避免多路并发误放行。

---

## 7. 对象五：RollbackTransitionObject（回滚边）

### 7.1 语义

唯一承载 PSEUDO→PSEUDO 的回退机制，用于“失败后重绕/回滚”。

### 7.2 触发与限次

- 次数上限：`attempt_counter < max_attempts`
- 可选暂停前置：`require_pause_before_rollback=True` 时，要求 `phase_runtime_status == PAUSED_FOR_REWIND`

### 7.3 触发副作用

`on_fire()` 会：

- `attempt_counter += 1`
- 记录 `last_edge_event`
- 达到上限后自动 `enabled=False`

### 7.4 传输内容

附加：

- `rollback=True`
- `rewind_target_phase`
- `rollback_reason`
- `rollback_mode`

结论：Rollback 边是“受控重试/回退”的安全阀，防无限循环。

---

## 8. 对象六：SyncTransitionObject（同步边）

### 8.1 语义

用于多前驱同步，保证汇合节点在满足同步条件后才继续。

### 8.2 三种模式

- `DEPENDENCY`：兼容模式，依赖 `dependency_ready`
- `JOIN_ALL`：主模式，要求
  - `arrived_tokens` 数量达到 `min_upstream_sources`（默认>=2）
  - 且包含 `required_tokens`
- `STATE_SYNC`：版本态同步，要求 `state_version_ok`

### 8.3 传输增强

附加：

- `sync_mode`
- `state_key`

结论：Sync 边把“并行汇合完整性”从业务代码中抽离为边语义。

---

## 9. 六对象协作关系（运行时）

1. 节点生成 `NodeResult`
2. `RuntimeNodeBase._emit_node_result` 按 TRUE/PSEUDO 输出遍历边
3. 每条边先过 `validate_connection(...)` 再 `can_fire(...)`
4. `transmit(...)` 可增强 payload
5. 目标节点接收：
   - TRUE -> `on_true_input_arrive(token, payload)`
   - PSEUDO -> `on_pseudo_input_arrive(payload)`

这形成了“**节点做决策，边做约束，图做调度**”的结构。

---

## 10. 全局不变量如何保护六对象

`assert_global_invariants(...)` 关键约束：

- SYNC 必须用于“至少2个不同上游”汇合
- DECISION 必须是 1→n 或 n→1，禁止 1→1 同构直连
- TRUE 输出只能走 GATE/DECISION/SYNC
- PSEUDO 输出只能走 ROLLBACK
- CHECKPOINT 只能指向 WORK
- CHECKPOINT 相关硬约束：时间下限、未批准前必须锁定
- WORK 相关硬约束：文件禁用、外部 claim 验证、rerun delta、文本政策

最终由 `finalize_graph_or_raise(...)` 做收口校验。

---

## 11. 设计价值总结

这 6 个对象实现了以下分层：

- **执行层（Work）**：业务运行与结果生产
- **治理层（Checkpoint）**：质量闸门、锁与放行
- **流控层（4边）**：门控、决策、回滚、同步

其优势是：

1. 语义清晰：每类对象单一职责明确；
2. 可审计：证据链、策略轨迹、最终自检齐全；
3. 可扩展：通过 `PolicyRule` / `OutputContract` 扩展行为，无需重写核心调度。

---

## 12. 六对象一句话速记

- `WorkVertexObject`：执行并产出结果的工作节点。
- `CheckPointObject`：把关并决定是否放行的检查点节点。
- `GateTransitionObject`：基于 gate 信号放行 TRUE 流。
- `DecisionTransitionObject`：在单选决策后路由 TRUE 流。
- `RollbackTransitionObject`：受限次数地回滚 PSEUDO 流。
- `SyncTransitionObject`：等待多上游对齐后再同步 TRUE 流。
