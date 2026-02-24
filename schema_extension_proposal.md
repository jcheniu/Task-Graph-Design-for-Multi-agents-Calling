# 05k Schema Extension Proposal

基准：`05d_edge_reclassification_v2.csv`（146 edges）+ `05i_logic_gaps_not_covered_by_130_edges.md`（12 项协议缺口已落边）。

目标：**不改动现有 8 类 taxonomy**（Progress/Gate/Decision/Exception/Loop/Rollback/Sync/Meta），仅通过“增量字段 + 运行时校验层”补齐当前边模型无法完整表达的协议语义。

---

## 1. Problem Statement

当前边模型擅长表达“结构流向”，但对以下语义表达不足：

1. 数值/区间门槛（如 `cumulative_duration >= MINIMUM`）
2. 规则冲突优先级（如 Rule 6 覆盖 Rule 7）
3. 会话与策略禁令（如不允许询问用户是否继续）
4. 多条件合取完成标准（文件存在 + gate pass + validator approve）
5. 运行时计数与审计（tool_calls、rejection_count、即时日志写入）
6. 权限与可信边界（file-ban、external_resources 独立验证）

结论：需要“**Edge + State + Policy + Audit**”四层协同。

---

## 2. Design Principles

- **P1. Backward compatible**：现有 05d 字段与 8 类不变。
- **P2. Minimal invasive**：优先加字段，不重构 DOT 主体。
- **P3. Machine-checkable**：所有关键协议可程序化验证。
- **P4. Phase-aware**：支持 phase/subphase/attempt 粒度。
- **P5. Evidence-first**：关键判断保留证据与审计链。

---

## 3. Proposed Extension Layers

## 3.1 Layer A — Edge Guard Extension（边条件扩展）

为边增加可执行 guard（布尔表达式），使边不再仅是“可见连接”，而是“带条件的连接”。

### New fields (edge-level)

- `guard_expr` (string)
  - 示例：`state.cumulative_duration >= state.minimum_duration`
- `guard_scope` (enum)
  - `phase | subphase | global | attempt`
- `guard_type` (enum)
  - `numeric | boolean | enum_match | set_membership`
- `on_guard_fail` (enum)
  - `block | reroute | rerun | escalate`
- `guard_evidence_source` (string)
  - 示例：`output/implementation/logs/phase_5_timing.json:cumulative_duration`

### Example

```yaml
affected_edge: E131
v2_primary_class: GateTransitionObject
guard_expr: state.phase_completed && state.cumulative_duration >= state.minimum_duration
guard_scope: phase
guard_type: numeric
on_guard_fail: rerun
guard_evidence_source: output/implementation/logs/phase_{X}_timing.json:cumulative_duration
```

---

## 3.2 Layer B — Runtime State Schema（运行时状态层）

建立统一状态对象，承载边无法表达的动态信息。

### New runtime state fields

```yaml
state:
  phase_id: string
  subphase_id: string|null
  attempt_count: integer
  cumulative_duration: number
  minimum_duration: number
  validator_verdict: APPROVE|REJECT|PENDING
  gate_passed: boolean
  required_files_exist: boolean
  tool_calls: integer
  rejection_count: integer
  score: number|null
  previous_output_path: string|null
  log_updated_after_phase: boolean
```

### Why needed

- 支持累计时长、重试次数、评分区间、工具调用次数等动态约束。
- 为 guard 与 policy 提供单一事实源（single source of truth）。

---

## 3.3 Layer C — Policy Priority & Conflict Rules（策略优先级层）

把“文字规则”转成可执行 policy，并可解决冲突。

### New policy fields

- `policy_id` (string)
- `policy_expr` (string)
- `priority` (integer, 越大优先级越高)
- `conflicts_with` (array[string])
- `override_mode` (enum: `hard_override | soft_override | merge`)
- `violation_action` (enum: `reject | rerun | block | alert`)

### Example (Rule 6 > Rule 7)

```yaml
- policy_id: TIME_HARD_FLOOR
  policy_expr: state.cumulative_duration < state.minimum_duration
  priority: 100
  conflicts_with: [PIPELINE_CONTINUITY]
  override_mode: hard_override
  violation_action: rerun

- policy_id: PIPELINE_CONTINUITY
  policy_expr: state.non_time_issue == true
  priority: 60
  conflicts_with: [TIME_HARD_FLOOR]
  override_mode: soft_override
  violation_action: continue_with_workaround
```

---

## 3.4 Layer D — Compliance & Provenance（合规与溯源层）

用于表达 file-ban 与 external_resources 信任边界。

### New fields

- `actor` (string)
- `resource_path` (string)
- `access_mode` (`read|write|exec`)
- `access_allowed` (boolean)
- `trust_level` (`internal_authoritative|external_unverified|verified_independent`)
- `claim_id` (string)
- `evidence_ids` (array[string])
- `verification_status` (`pending|verified|rejected`)

### Example

```yaml
access_rule:
  actor: director
  resource_path: output/phase_x/agent_output.md
  access_mode: read
  access_allowed: false
  reason: file-ban

claim_verification:
  claim_id: C-EXT-023
  trust_level: external_unverified
  evidence_ids: [EVID-112, EVID-209]
  verification_status: verified
```

---

## 3.5 Layer E — Audit Invariants（审计不变量）

把“必须立即更新日志”等流程纪律做成硬校验。

### New invariant fields

- `invariant_id` (string)
- `invariant_expr` (string)
- `check_timing` (`post_phase|pre_phase|on_transition|periodic`)
- `severity` (`critical|high|medium|low`)
- `fail_action` (`block|rerun|alert`)

### Example

```yaml
- invariant_id: ORCH_LOG_IMMEDIATE_UPDATE
  invariant_expr: event.phase_end -> state.log_updated_after_phase == true
  check_timing: post_phase
  severity: high
  fail_action: block
```

---

## 4. Minimal CSV/JSON Additions

建议采用“双轨”：
- 05d 继续保持边主表；
- 新增 `05k_policy_runtime_schema.json` 管理运行时/策略字段。

若必须直接扩展 05d，可先加入以下最小列：

- `guard_expr`
- `on_guard_fail`
- `policy_refs`（如 `TIME_HARD_FLOOR;PIPELINE_CONTINUITY`）
- `audit_invariant_refs`
- `trust_requirement`（`none|independent_verification_required`）

---

## 5. Mapping: uncovered logic → extension

| Uncovered logic | Recommended extension |
|---|---|
| 累计时长硬门槛 | Layer A + B |
| Rule6 覆盖 Rule7 | Layer C |
| 禁止合理化语句 | Layer C（policy lint） |
| 不得询问用户继续 | Layer C（interaction policy） |
| 完成条件多重合取 | Layer A + B + E |
| validator REJECT 直至 APPROVE | Layer B + E（state machine invariant） |
| 0 tool uses = failure | Layer B + E |
| director file-ban | Layer D |
| external_resources 独立验证 | Layer D |
| rerun 必须基于 previous_output 改进 | Layer B + E（delta invariant） |
| 每阶段后立即更新 orchestration_log | Layer E |
| 7A-7F 每子阶段 manifest + resume | Layer B + E |

---

## 6. Implementation Roadmap (phased)

## Phase 1 (Quick Win)

1. 新增 `05k_policy_runtime_schema.json`（不改 05d）
2. 接入最小 state 字段：`cumulative_duration`, `minimum_duration`, `tool_calls`, `validator_verdict`
3. 实现 4 个 critical invariants：
   - TIME_HARD_FLOOR
   - VALIDATOR_APPROVAL_REQUIRED
   - TOOL_USE_NONZERO
   - ORCH_LOG_IMMEDIATE_UPDATE

## Phase 2

1. 接入 policy priority/conflict resolver
2. 接入 file-ban 与 trust-boundary 检查
3. 引入 claim-evidence 追踪

## Phase 3

1. 子阶段级（7A-7F）状态机
2. rerun 增量改进检测（delta checks）
3. 全量审计报告输出（machine-readable）

---

## 7. Acceptance Criteria

扩展生效判定标准：

1. 能程序化阻断 `cumulative_duration < minimum` 的推进。
2. 能证明 Rule 6 在冲突时覆盖 Rule 7。
3. 能检测并拒绝 `tool_calls == 0`。
4. 能在 file-ban 场景下拒绝非法 read。
5. 能对 external claim 给出独立验证状态。
6. 能验证每 phase 结束后日志已立即更新。

---

## 8. Risks & Mitigations

- 风险：字段过多导致维护成本上升
  - 缓解：先只启用 critical 字段与 4 条高优先 invariant。

- 风险：规则表达不一致
  - 缓解：统一 `policy_expr` DSL，提供 schema 校验。

- 风险：历史数据不兼容
  - 缓解：保持 05d 不变，先做旁路 schema 文件。

---

## 9. Final Recommendation

采用“**边保留 + 语义外挂**”路线：

- 图结构继续用现有 8 类边（可视化与沟通效率高）；
- 协议硬约束放入 `State + Policy + Audit` 层（执行正确性高）。

这能在不推翻现有成果的前提下，补齐当前最关键的不可边化语义缺口。