# 05l_edge_model_logic_vulnerabilities_for_point_design.md

基准：
- `05d_edge_reclassification_v2.csv`（146 edges，8类边）
- `05i_logic_gaps_not_covered_by_130_edges.md`（12项缺口已“落边”）
- `05k_schema_extension_proposal.md`（State/Policy/Audit 扩展方案）
- `build_protocol_completion.py`（当前补边实现逻辑）

---

## 1. 结论（先给设计决策）

仅依赖现有 8 类边（Progress/Gate/Decision/Exception/Loop/Rollback/Sync/Meta）可以高效表达**结构流向**，但对“协议正确性”仍存在系统性漏洞：

1. **可连通 ≠ 可执行**：图上可走通，不代表满足运行时门槛与策略约束。
2. **离散转移 ≠ 连续状态**：边是瞬时关系，难承载累计量（时长、重试、工具调用计数）。
3. **局部分类 ≠ 全局治理**：单条边分类正确，不代表全局冲突规则、权限边界、审计纪律正确。
4. **静态映射 ≠ 动态合规**：补边可“描述”协议，但无法“证明并阻断”违规推进。

因此，未来“点（节点）设计/分类/功能实现”需要采用：

> **边负责拓扑，点负责语义执行；再叠加状态机、策略优先级与审计不变量。**

---

## 2. 已保留的漏洞清单（来自前序任务，全部保留）

以下漏洞已在前一轮识别，现按“为何8类边仍不足”重述，供后续点设计直接使用。

| 漏洞ID | 逻辑漏洞 | 仅靠边的不足 | 失效后果 |
|---|---|---|---|
| V01 | 累计时长硬门槛（`cumulative_duration >= minimum`） | 边可表示“检查发生”，但不能稳定表达累计值与比较真值 | 未达时长仍推进 |
| V02 | Rule6 覆盖 Rule7（冲突优先级） | 图可画两条规则路径，不能原生表达覆盖序关系 | 低优先规则误生效 |
| V03 | 禁止“合理化语句”类策略 | 语义/语言约束属于策略层，不是拓扑关系 | 违规话术被当作正常分支 |
| V04 | 不得询问用户是否继续 | 交互禁令是会话策略，不是流向关系 | 违反协议的人机交互 |
| V05 | 多条件合取完成标准（文件+gate+validator） | 边更像“或式可达”，合取依赖需状态聚合 | 条件未齐全却放行 |
| V06 | `validator=REJECT` 必须持续阻断至 `APPROVE` | 边可画回路，但难保证状态单调与锁定 | REJECT 被旁路绕过 |
| V07 | `tool_calls == 0` 必判失败 | 计数器属于运行时状态，不是边属性 | 形式完成、实质未执行 |
| V08 | director file-ban 权限禁令 | 权限判定依赖 actor/resource/action 三元组，不是单边可判 | 非法读取未被硬阻断 |
| V09 | external_resources 必须独立验证 | 可信度/证据链是溯源问题，边无法自证 | 外部主张直接入链 |
| V10 | rerun 必须基于 previous_output 增量改进 | “读了旧输出”可落边，但“确有改进”需差分判定 | 空转重跑、无增益循环 |
| V11 | phase 结束后日志必须即时更新 | 时序纪律是事件不变量，非拓扑连接 | 审计断点、责任不可追 |
| V12 | 7A-7F 子阶段 manifest + resume 纪律 | 子阶段状态机与恢复点需要持久状态 | 恢复错位、版本漂移 |

对应来源：`05i_logic_gaps_not_covered_by_130_edges.md:20-31`、`05k_schema_extension_proposal.md:207-218`。

---

## 3. 多学科视角下的“根因”

### 3.1 形式化方法（Formal Methods）
- 当前边模型更接近 **LTS 的转移关系**，但缺少充分的**状态变量与不变量**。
- 结果：可证明“可达”，难证明“安全（Safety）/活性（Liveness）”。

### 3.2 分布式系统与工作流理论
- 子阶段并行、汇合、重跑涉及**部分有序事件**与**一致性约束**。
- 仅用边表示依赖，会遗漏“读旧状态/写后可见性/幂等重放”问题。

### 3.3 软件可靠性工程
- 协议执行依赖可观测性（日志、计数、证据链）。
- 无审计不变量时，系统容易“看似成功、实则违规”。

### 3.4 安全与合规工程
- file-ban、外部资源可信边界、claim验证都属于**访问控制 + 溯源验证**。
- 这类控制需要 Actor-Resource-Action 与证据状态，不是单条边能承载。

### 3.5 人机交互与治理
- “不得询问用户继续”与“禁止合理化表述”属于交互策略。
- 若不进入策略引擎，模型会把它误降维为普通分支判断。

---

## 4. 结合 MCM-killer 当前实现的漏洞证据

### 4.1 证据A：补边脚本已能“描述协议”，但尚未“运行时证明”
- `build_protocol_completion.py` 通过新增 `E131-E146` 把缺口映射进图：`build_protocol_completion.py:59-444`。
- 但这些新增边主要是**分类与语义标注**，未引入统一 runtime state 与 invariant evaluator。

### 4.2 证据B：已有“补全覆盖”结论，但覆盖语义仍以边级表示为主
- `05i` 明确“12项缺口均已边级表示”：`05i_logic_gaps_not_covered_by_130_edges.md:35-38`。
- 这说明“表达层”已补齐，不等同“执行层”已闭环。

### 4.3 证据C：`05k` 已指出边模型上限并给出扩展层
- 关键不足与扩展方案已列明：`05k_schema_extension_proposal.md:10-19`、`05k_schema_extension_proposal.md:35-183`。
- 也即：当前主要风险不在“分类是否够8类”，而在“语义是否具备可机检执行层”。

---

## 5. 对未来“点设计/分类/功能实现”的直接要求

## 5.1 点（Node）分类建议：从“拓扑节点”升级为“语义节点”

建议至少新增以下点角色（不替换8类边，而是与边正交）：

1. **StateNode**：承载 phase/subphase/attempt/counters。
2. **GateEvalNode**：执行 guard_expr 与合取条件。
3. **PolicyNode**：处理 priority/conflict/override。
4. **ComplianceNode**：执行 actor-resource-action 与 trust 验证。
5. **AuditNode**：执行 invariant 校验与失败动作。
6. **EvidenceNode**：记录 claim-evidence-verification 生命周期。

## 5.2 点功能硬要求（最小闭环）

- 必须支持状态字段：`cumulative_duration`、`minimum_duration`、`tool_calls`、`validator_verdict`。
- 必须支持四条关键不变量：
  - TIME_HARD_FLOOR
  - VALIDATOR_APPROVAL_REQUIRED
  - TOOL_USE_NONZERO
  - ORCH_LOG_IMMEDIATE_UPDATE

这些要求与 `05k` Phase 1 对齐：`05k_schema_extension_proposal.md:226-233`。

## 5.3 设计原则

- **不改8类边 taxonomy**（保留可视化和沟通稳定性）。
- **执行正确性前移到点+状态+审计层**。
- **边负责“去哪”，点负责“能不能去/凭什么去/留下什么证据”。**

---

## 6. 风险优先级（用于实现排期）

| 优先级 | 漏洞 | 原因 |
|---|---|---|
| P0 | V01/V06/V07（时长、验证器、tool_calls） | 直接决定是否错误放行 |
| P0 | V08/V09（file-ban、外部信任） | 涉及权限与可信边界 |
| P1 | V05/V11（合取完成、日志时序） | 影响可审计性与回放正确性 |
| P1 | V10/V12（rerun增量、子阶段恢复） | 影响迭代质量与恢复稳定性 |
| P2 | V02/V03/V04（冲突优先、策略禁令、交互禁令） | 决策治理一致性风险 |

---

## 7. 可验证验收标准（面向功能实现）

1. 能阻断 `cumulative_duration < minimum_duration` 的推进。
2. 在 Rule6/Rule7 冲突时可给出优先级决议与证据。
3. `tool_calls == 0` 时必须失败并记录审计事件。
4. file-ban 场景下，非法 read 必须被拒绝且可追踪。
5. external claim 必须有独立验证状态（pending/verified/rejected）。
6. 每 phase 结束后可程序化验证日志已即时更新。

与既有提案一致：`05k_schema_extension_proposal.md:252-257`。

---

## 8. 最终建议

当前 8 类边模型应继续保留，作为**结构层标准**；但未来设计重心必须转向：

- 点的语义职责（State/Policy/Compliance/Audit）
- 运行时状态机与不变量校验
- claim-evidence 溯源链

即采用：

> **Graph Topology（边） + Semantic Runtime（点） + Verifiable Governance（策略/审计）**

这条路线能保留现有成果，同时实质性消除“图上完整、执行不完整”的逻辑漏洞。
