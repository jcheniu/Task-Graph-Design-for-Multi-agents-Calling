# node_edge_6_object_oop_spec（Python伪代码）

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import uuid
import re


# =========================
# Enums / Types
# =========================

class OutputKind(str, Enum):
    TRUE = "TRUE"
    PSEUDO = "PSEUDO"


class NodeKind(str, Enum):
    WORK = "WORK"
    CHECKPOINT = "CHECKPOINT"


class EdgeKind(str, Enum):
    GATE = "GATE"
    DECISION = "DECISION"
    ROLLBACK = "ROLLBACK"
    SYNC = "SYNC"


class Verdict(str, Enum):
    APPROVED = "APPROVED"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECTED = "REJECTED"
    REJECT_INSUFFICIENT_TIME = "REJECT_INSUFFICIENT_TIME"
    REJECT_NO_TOOL_USE = "REJECT_NO_TOOL_USE"
    REJECT_FILE_BAN = "REJECT_FILE_BAN"
    REJECT_UNVERIFIED_EXTERNAL = "REJECT_UNVERIFIED_EXTERNAL"
    REJECT_POLICY_VIOLATION = "REJECT_POLICY_VIOLATION"
    REQUIRE_REWIND = "REQUIRE_REWIND"


class FailureAction(str, Enum):
    BLOCK = "BLOCK"
    RERUN = "RERUN"
    ROLLBACK = "ROLLBACK"
    ESCALATE = "ESCALATE"


class PhaseRuntimeStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED_FOR_REWIND = "PAUSED_FOR_REWIND"
    RESUMED = "RESUMED"
    COMPLETED = "COMPLETED"


class InputJoinMode(str, Enum):
    ALL = "ALL"
    SELECT = "SELECT"


class SyncMode(str, Enum):
    DEPENDENCY = "DEPENDENCY"
    JOIN_ALL = "JOIN_ALL"
    STATE_SYNC = "STATE_SYNC"


class ValidatorLockState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class ExecState(str, Enum):
    WAITING_INPUTS = "WAITING_INPUTS"
    READY_PARTIAL = "READY_PARTIAL"
    READY_FINAL = "READY_FINAL"
    RUNNING = "RUNNING"
    EVALUATING_OUTPUT = "EVALUATING_OUTPUT"
    PARTIAL_DONE = "PARTIAL_DONE"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class EvidenceItem:
    file_path: str
    line_refs: List[str]
    check_type: str
    result: str
    detail: str


@dataclass
class PolicyRule:
    id: str
    priority: int
    exclusive_group: str
    override_of: List[str]
    condition_kind: str
    condition_params: Dict[str, Any] = field(default_factory=dict)
    action_kind: str = "TRACE_ONLY"
    action_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OutputContract:
    output_name: str
    output_kind: OutputKind
    guard_kind: str = "ALWAYS"
    guard_params: Dict[str, Any] = field(default_factory=dict)
    edge_allowlist: Set[EdgeKind] = field(default_factory=set)
    priority: int = 0


@dataclass
class EdgeRuntimeState:
    enabled: bool = True
    attempt_counter: int = 0
    max_attempts: int = 1
    last_edge_event: str = ""


@dataclass
class AccessRequest:
    actor: str
    resource: str
    action: str


@dataclass
class ClaimRecord:
    claim_id: str
    source: str
    status: ClaimStatus
    verifier: str = ""
    evidence_refs: List[str] = field(default_factory=list)


@dataclass
class NodeResult:
    success: bool
    verdict: Verdict
    failure_action: Optional[FailureAction]
    selected_true_outputs: List[str]
    selected_pseudo_outputs: List[str]
    artifacts: Dict[str, Any]
    evidence_items: List[EvidenceItem]
    regression_check_passed: bool


# =========================
# Common Functions (Policy / Compliance / Audit)
# =========================

def names(contracts: List[OutputContract]) -> List[str]:
    return [c.output_name for c in contracts]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def policy_conflict_resolver(
    policy_rules: List[PolicyRule],
    state: Any,
    evidence_items: List[EvidenceItem],
    decision_trace: List[str],
) -> None:
    matched = [r for r in policy_rules if state._eval_policy_condition(r)]
    if not matched:
        return

    # 显式优先级（值越小优先级越高）
    matched.sort(key=lambda r: (r.priority, r.id))
    winner = matched[0]

    covered: List[str] = []
    for r in matched[1:]:
        same_group = (r.exclusive_group != "" and r.exclusive_group == winner.exclusive_group)
        explicit = (r.id in winner.override_of)
        if same_group or explicit or r.priority >= winner.priority:
            covered.append(r.id)

    state._apply_policy_action(winner)

    decision_trace.append(f"policy_winner={winner.id}")
    decision_trace.append(f"policy_covered={','.join(covered)}")
    evidence_items.append(EvidenceItem(
        file_path="policy_engine",
        line_refs=[],
        check_type="policy_conflict_resolver",
        result="pass",
        detail=f"winner={winner.id}; covered={','.join(covered)}",
    ))


def check_rationalization_violation(text: str) -> bool:
    patterns = [
        r"合理化",
        r"justification",
        r"rationalize",
        r"虽然违规但",
    ]
    low = text.lower()
    return any(re.search(p, low) for p in patterns)


def interaction_policy_scan(text: str) -> bool:
    patterns = [
        r"是否继续",
        r"要不要继续",
        r"should i continue",
        r"continue\?",
    ]
    low = text.lower()
    return any(re.search(p, low) for p in patterns)


def required_files_present(required_md_files: List[str], artifacts: Dict[str, Any]) -> Dict[str, Any]:
    generated = set(artifacts.get("generated_files", []))
    missing = [f for f in required_md_files if f not in generated]
    return {"ok": len(missing) == 0, "missing_files": missing}


def check_tool_use_nonzero(tool_calls: int) -> bool:
    return tool_calls > 0


def enforce_file_ban(request: AccessRequest, policy: Dict[str, Any]) -> bool:
    # policy["file_ban_rules"]: [{"actor": str, "resource_prefix": str, "action": str}]
    for r in policy.get("file_ban_rules", []):
        if (
            request.actor == r.get("actor", "")
            and request.resource.startswith(r.get("resource_prefix", ""))
            and request.action == r.get("action", "")
        ):
            return False
    return True


def verify_external_claim(claim: ClaimRecord) -> bool:
    return claim.status == ClaimStatus.VERIFIED


def compute_delta(previous_output: Dict[str, Any], current_output: Dict[str, Any]) -> Dict[str, Any]:
    prev_score = int(previous_output.get("quality_score", 0))
    curr_score = int(current_output.get("quality_score", 0))
    return {
        "improved": curr_score > prev_score,
        "delta": curr_score - prev_score,
    }




# =========================
# Connection Matrix
# =========================

def validate_connection(
    source_node_kind: NodeKind,
    source_port_kind: OutputKind,
    edge_kind: EdgeKind,
    target_node_kind: NodeKind,
    target_input_port_kind: OutputKind,
) -> bool:

    if source_node_kind == NodeKind.WORK and source_port_kind == OutputKind.TRUE:
        if edge_kind not in {EdgeKind.GATE, EdgeKind.DECISION, EdgeKind.SYNC}:
            return False
        if target_input_port_kind != OutputKind.TRUE:
            return False
        return target_node_kind in {NodeKind.WORK, NodeKind.CHECKPOINT}

    if source_node_kind == NodeKind.WORK and source_port_kind == OutputKind.PSEUDO:
        if edge_kind not in {EdgeKind.ROLLBACK}:
            return False
        if target_input_port_kind != OutputKind.PSEUDO:
            return False
        return target_node_kind in {NodeKind.WORK, NodeKind.CHECKPOINT}

    if source_node_kind == NodeKind.CHECKPOINT and source_port_kind == OutputKind.TRUE:
        if edge_kind not in {EdgeKind.GATE, EdgeKind.DECISION, EdgeKind.SYNC}:
            return False
        return target_node_kind == NodeKind.WORK and target_input_port_kind == OutputKind.TRUE

    if source_node_kind == NodeKind.CHECKPOINT and source_port_kind == OutputKind.PSEUDO:
        if edge_kind not in {EdgeKind.ROLLBACK}:
            return False
        return target_node_kind == NodeKind.WORK and target_input_port_kind == OutputKind.PSEUDO

    return False


# =========================
# 4 Edge Objects
# =========================

@dataclass
class BaseEdge:
    id: str
    from_node_id: str
    to_node_id: str
    from_output_name: str
    from_output_kind: OutputKind
    to_input_kind: OutputKind
    enabled: bool
    kind: EdgeKind

    def can_fire(self, ctx: Dict[str, Any]) -> bool:
        return self.enabled

    def transmit(self, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        return payload


@dataclass
class GateTransitionObject(BaseEdge):
    kind: EdgeKind = EdgeKind.GATE
    from_output_kind: OutputKind = OutputKind.TRUE
    to_input_kind: OutputKind = OutputKind.TRUE
    enabled: bool = True
    gate_family: str = ""
    mandatory: bool = True
    gate_signal_key: str = "gate_passed"

    def can_fire(self, ctx: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        if not self.mandatory:
            return True
        return bool(ctx.get(self.gate_signal_key, False))

    def transmit(self, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        out["gate_family"] = self.gate_family
        out["gate_checked"] = True
        return out


@dataclass
class DecisionTransitionObject(BaseEdge):
    kind: EdgeKind = EdgeKind.DECISION
    from_output_kind: OutputKind = OutputKind.TRUE
    to_input_kind: OutputKind = OutputKind.TRUE
    enabled: bool = True
    route_name: str = ""
    decision_basis_key: str = "decision_basis"
    tie_break_order: int = 999
    require_all_upstream_done: bool = True
    upstream_done_key: str = "decision_ready"
    selected_count_key: str = "decision_selected_count"

    def can_fire(self, ctx: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        # 决策边强制“先完成再选择”
        if not bool(ctx.get(self.upstream_done_key, False)):
            return False
        if int(ctx.get(self.selected_count_key, 1)) != 1:
            return False
        return ctx.get("chosen_route", "") == self.route_name

    def transmit(self, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        out["decision_route"] = self.route_name
        out["decision_basis"] = ctx.get(self.decision_basis_key, "")
        return out


@dataclass
class RollbackTransitionObject(BaseEdge):
    kind: EdgeKind = EdgeKind.ROLLBACK
    from_output_kind: OutputKind = OutputKind.PSEUDO
    to_input_kind: OutputKind = OutputKind.PSEUDO
    enabled: bool = True
    attempt_counter: int = 0
    max_attempts: int = 2
    last_edge_event: str = ""
    rewind_target_phase: str = ""
    require_pause_before_rollback: bool = True
    rollback_reason: str = "REWIND"
    rollback_mode: FailureAction = FailureAction.ROLLBACK

    def can_fire(self, ctx: Dict[str, Any]) -> bool:
        if not self.enabled or self.attempt_counter >= self.max_attempts:
            return False
        if self.require_pause_before_rollback:
            return ctx.get("phase_runtime_status", "") == PhaseRuntimeStatus.PAUSED_FOR_REWIND.value
        return True

    def on_fire(self) -> None:
        self.attempt_counter += 1
        self.last_edge_event = f"rollback:{self.rollback_reason}:to:{self.rewind_target_phase}"
        if self.attempt_counter >= self.max_attempts:
            self.enabled = False

    def transmit(self, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        self.on_fire()
        out = dict(payload)
        out["rollback"] = True
        out["rewind_target_phase"] = self.rewind_target_phase
        out["rollback_reason"] = payload.get("failure_action", self.rollback_reason)
        out["rollback_mode"] = self.rollback_mode.value
        return out


@dataclass
class SyncTransitionObject(BaseEdge):
    kind: EdgeKind = EdgeKind.SYNC
    from_output_kind: OutputKind = OutputKind.TRUE
    to_input_kind: OutputKind = OutputKind.TRUE
    enabled: bool = True
    sync_mode: SyncMode = SyncMode.JOIN_ALL
    required_tokens: Set[str] = field(default_factory=set)
    state_key: str = ""
    min_upstream_sources: int = 2

    def can_fire(self, ctx: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        if self.sync_mode == SyncMode.DEPENDENCY:
            # 保留兼容，但建议仅在多前驱汇合处使用 JOIN_ALL
            return bool(ctx.get("dependency_ready", False))
        if self.sync_mode == SyncMode.JOIN_ALL:
            arrived = set(ctx.get("arrived_tokens", []))
            if len(arrived) < self.min_upstream_sources:
                return False
            return self.required_tokens.issubset(arrived)
        if self.sync_mode == SyncMode.STATE_SYNC:
            return bool(ctx.get("state_version_ok", False))
        return False

    def transmit(self, payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(payload)
        out["sync_mode"] = self.sync_mode.value
        out["state_key"] = self.state_key
        return out


class RuntimeNodeBase:
    def bind_runtime(self, nodes: Dict[str, Any], edges: List[BaseEdge], strict_mode: bool = True) -> None:
        self.runtime_nodes = nodes
        self.runtime_edges = edges
        self.strict_mode = strict_mode

    def _find_edges_by_output(self, output_name: str) -> List[BaseEdge]:
        return [e for e in self.runtime_edges if e.from_node_id == self.id and e.from_output_name == output_name]

    def _build_edge_ctx(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        artifacts = payload.get("artifacts", {})
        return {
            "gate_passed": bool(payload.get("gate_passed", artifacts.get("gate_passed", False))),
            "dependency_ready": bool(payload.get("dependency_ready", artifacts.get("dependency_ready", False))),
            "state_version_ok": bool(payload.get("state_version_ok", artifacts.get("state_version_ok", False))),
            "decision_basis": payload.get("decision_basis", artifacts.get("decision_basis", "")),
            "phase_runtime_status": payload.get("phase_runtime_status", PhaseRuntimeStatus.RUNNING.value),
            "previous_output_path": payload.get("previous_output_path", artifacts.get("previous_output_path", "")),
            "arrived_tokens": payload.get("arrived_tokens", artifacts.get("arrived_tokens", [])),
            "chosen_route": payload.get("chosen_route", artifacts.get("chosen_route", "")),
            "decision_ready": bool(payload.get("decision_ready", artifacts.get("decision_ready", False))),
            "decision_selected_count": int(payload.get("decision_selected_count", artifacts.get("decision_selected_count", 1))),
            "delta_improved": bool(payload.get("delta_improved", artifacts.get("delta_improved", False))),
        }

    def _block_true_output_routing(self) -> bool:
        return False

    def _route_output_internal(self, source_output_name: str, source_output_kind: OutputKind, payload: Dict[str, Any]) -> int:
        if source_output_kind == OutputKind.TRUE and self._block_true_output_routing():
            return 0

        delivered_count = 0
        edges = self._find_edges_by_output(source_output_name)
        for e in edges:
            target_node = self.runtime_nodes.get(e.to_node_id)
            if target_node is None:
                continue

            if not validate_connection(
                self.node_kind,
                source_output_kind,
                e.kind,
                target_node.node_kind,
                e.to_input_kind,
            ):
                continue

            edge_ctx = self._build_edge_ctx(payload)
            if not e.can_fire(edge_ctx):
                continue

            delivered = e.transmit(payload, edge_ctx)
            token = delivered.get("token", str(uuid.uuid4()))
            if e.to_input_kind == OutputKind.TRUE:
                target_node.on_true_input_arrive(token, delivered)
            else:
                target_node.on_pseudo_input_arrive(delivered)
            delivered_count += 1

        return delivered_count

    def _build_true_emit_payload(self, result: NodeResult, out_name: str) -> Dict[str, Any]:
        return {
            "token": str(uuid.uuid4()),
            "verdict": result.verdict.value,
            "artifacts": result.artifacts,
            "evidence_items": result.evidence_items,
            "chosen_route": result.artifacts.get("chosen_route", out_name),
            "decision_ready": bool(result.artifacts.get("decision_ready", True)),
            "decision_selected_count": int(result.artifacts.get("decision_selected_count", 1)),
            "delta_improved": result.artifacts.get("delta_improved", False),
        }

    def _build_pseudo_emit_payload(self, result: NodeResult) -> Dict[str, Any]:
        return {
            "token": str(uuid.uuid4()),
            "verdict": result.verdict.value,
            "failure_action": result.failure_action.value if result.failure_action else None,
            "artifacts": result.artifacts,
            "evidence_items": result.evidence_items,
            "previous_output_path": result.artifacts.get("previous_output_path", ""),
            "delta_improved": result.artifacts.get("delta_improved", False),
        }

    def _emit_node_result(self, result: NodeResult) -> int:
        delivered_count = 0
        for out_name in result.selected_true_outputs:
            delivered_count += self._route_output_internal(
                out_name,
                OutputKind.TRUE,
                self._build_true_emit_payload(result, out_name),
            )

        for out_name in result.selected_pseudo_outputs:
            delivered_count += self._route_output_internal(
                out_name,
                OutputKind.PSEUDO,
                self._build_pseudo_emit_payload(result),
            )
        return delivered_count

    def run_until_quiescent(self, max_rounds: int = 64, enforce_invariants: bool = True) -> Dict[str, Any]:
        if enforce_invariants:
            assert_global_invariants({"nodes": self.runtime_nodes, "edges": self.runtime_edges, "strict_mode": self.strict_mode})

        rounds = 0
        progressed = True
        while progressed and rounds < max_rounds:
            rounds += 1
            progressed = False
            for node in self.runtime_nodes.values():
                if hasattr(node, "step") and node.step():
                    progressed = True

        report = finalize_graph_or_raise(self.runtime_nodes, self.runtime_edges, strict_mode=self.strict_mode)
        if enforce_invariants:
            assert_global_invariants({"nodes": self.runtime_nodes, "edges": self.runtime_edges, "strict_mode": self.strict_mode})
        report["quiescent_rounds"] = rounds
        return report


# =========================
# Node 1: WorkVertexObject
# =========================

@dataclass
class WorkVertexObject(RuntimeNodeBase):
    id: str
    phase_id: str
    secondary_tag: str

    node_kind: NodeKind = NodeKind.WORK

    input_join_mode: InputJoinMode = InputJoinMode.ALL
    true_input_expected_count: int = 1
    # SELECT 语义改为“n选k（默认 n选1）”，而非“到达>=阈值即可放行”
    early_select_exact_count: int = 1
    early_reject_multi_select: bool = True

    true_input_arrived_tokens: Set[str] = field(default_factory=set)
    true_inputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pseudo_inputs: List[Dict[str, Any]] = field(default_factory=list)

    min_true_outputs: int = 1
    max_pseudo_outputs: int = 10
    output_contracts: List[OutputContract] = field(default_factory=list)

    required_agents: List[str] = field(default_factory=list)
    optional_agents: List[str] = field(default_factory=list)
    min_participants: int = 0
    discussion_room_path: str = ""
    required_md_files: List[str] = field(default_factory=list)

    exec_state: str = ExecState.WAITING_INPUTS.value
    has_final_run_completed: bool = False
    artifacts: Dict[str, Any] = field(default_factory=lambda: {"generated_files": []})
    decision_trace: List[str] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)

    tool_calls: int = 0
    output_text_buffer: str = ""
    access_requests: List[AccessRequest] = field(default_factory=list)
    access_policy: Dict[str, Any] = field(default_factory=dict)
    claims: List[ClaimRecord] = field(default_factory=list)
    previous_output: Dict[str, Any] = field(default_factory=dict)
    current_output: Dict[str, Any] = field(default_factory=dict)
    policy_rules: List[PolicyRule] = field(default_factory=list)

    runtime_nodes: Dict[str, Any] = field(default_factory=dict)
    runtime_edges: List[BaseEdge] = field(default_factory=list)
    strict_mode: bool = True

    def _set_exec_state(self, state: ExecState) -> None:
        self.exec_state = state.value

    def _fail_result(
        self,
        verdict: Verdict,
        failure_action: FailureAction,
        pseudo_outputs: List[str],
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> NodeResult:
        return NodeResult(
            success=False,
            verdict=verdict,
            failure_action=failure_action,
            selected_true_outputs=[],
            selected_pseudo_outputs=pseudo_outputs,
            artifacts=self.artifacts if artifacts is None else artifacts,
            evidence_items=self.evidence_items,
            regression_check_passed=False,
        )

    def _ok_result(self, true_outputs: List[str], pseudo_outputs: List[str]) -> NodeResult:
        return NodeResult(
            success=True,
            verdict=Verdict.APPROVED,
            failure_action=None,
            selected_true_outputs=true_outputs,
            selected_pseudo_outputs=pseudo_outputs,
            artifacts=self.artifacts,
            evidence_items=self.evidence_items,
            regression_check_passed=True,
        )

    def on_true_input_arrive(self, token: str, payload: Dict[str, Any]) -> None:
        if token in self.true_input_arrived_tokens:
            return
        self.true_input_arrived_tokens.add(token)
        self.true_inputs[token] = payload
        self.update_readiness_after_new_input()

    def on_pseudo_input_arrive(self, payload: Dict[str, Any]) -> None:
        self.pseudo_inputs.append(payload)

    def update_readiness_after_new_input(self) -> None:
        arrived = len(self.true_input_arrived_tokens)
        if self.input_join_mode == InputJoinMode.ALL:
            self._set_exec_state(ExecState.READY_FINAL if arrived == self.true_input_expected_count else ExecState.WAITING_INPUTS)
            return

        if self.has_final_run_completed:
            return

        # SELECT: n选k（默认 n选1），仅在“恰好 k”时就绪；若要求单选且超出则标记失败
        if arrived == self.early_select_exact_count:
            self._set_exec_state(ExecState.READY_PARTIAL if arrived < self.true_input_expected_count else ExecState.READY_FINAL)
            return

        if self.early_reject_multi_select and arrived > self.early_select_exact_count:
            self._set_exec_state(ExecState.FAILED)
            self.decision_trace.append(
                f"early_multi_select_violation:arrived={arrived},exact={self.early_select_exact_count}"
            )

    def _eval_policy_condition(self, rule: PolicyRule) -> bool:
        kind = rule.condition_kind
        params = rule.condition_params
        if kind == "ALWAYS":
            return True
        if kind == "ARTIFACT_EQUALS":
            return self.artifacts.get(params.get("key", "")) == params.get("value")
        if kind == "HAS_TRUE_INPUTS":
            return len(self.true_input_arrived_tokens) >= int(params.get("min", 1))
        if kind == "TOOL_CALLS_AT_LEAST":
            return self.tool_calls >= int(params.get("min", 1))
        if kind == "TEXT_CONTAINS":
            return str(params.get("needle", "")).lower() in self.output_text_buffer.lower()
        return False

    def _apply_policy_action(self, rule: PolicyRule) -> None:
        kind = rule.action_kind
        params = rule.action_params
        if kind == "TRACE_ONLY":
            self.decision_trace.append(f"policy_action={rule.id}:trace_only")
            return
        if kind == "SET_ARTIFACT":
            self.artifacts[str(params.get("key", ""))] = params.get("value")
            self.decision_trace.append(f"policy_action={rule.id}:set_artifact")
            return
        if kind == "SET_EXEC_STATE":
            self.exec_state = str(params.get("exec_state", self.exec_state))
            self.decision_trace.append(f"policy_action={rule.id}:set_exec_state")
            return
        if kind == "APPEND_TRACE":
            self.decision_trace.append(str(params.get("message", f"policy_action={rule.id}")))

    def _eval_output_guard(self, contract: OutputContract) -> bool:
        kind = contract.guard_kind
        params = contract.guard_params
        if kind == "ALWAYS":
            return True
        if kind == "ARTIFACT_EQUALS":
            return self.artifacts.get(params.get("key", "")) == params.get("value")
        if kind == "ARTIFACT_BOOL":
            return bool(self.artifacts.get(params.get("key", ""), False))
        if kind == "MIN_TRUE_INPUTS":
            return len(self.true_input_arrived_tokens) >= int(params.get("min", 1))
        if kind == "PSEUDO_INPUTS_AT_LEAST":
            return len(self.pseudo_inputs) >= int(params.get("min", 1))
        if kind == "VERDICT_IN_TRUE_INPUTS":
            expect = str(params.get("verdict", ""))
            return any(v.get("verdict", "") == expect for v in self.true_inputs.values())
        return False

    def enforce_access_requests_or_fail(self) -> Optional[NodeResult]:
        for req in self.access_requests:
            ok = enforce_file_ban(req, self.access_policy)
            self.evidence_items.append(EvidenceItem(
                file_path=req.resource,
                line_refs=[],
                check_type="file_ban",
                result="pass" if ok else "fail",
                detail=f"{req.actor}:{req.action}",
            ))
            if not ok:
                return self._fail_result(
                    verdict=Verdict.REJECT_FILE_BAN,
                    failure_action=FailureAction.ESCALATE,
                    pseudo_outputs=["file_ban_violation"],
                )
        return None

    def enforce_external_claims_or_fail(self) -> Optional[NodeResult]:
        for c in self.claims:
            if not verify_external_claim(c):
                self.evidence_items.append(EvidenceItem(
                    file_path=c.source,
                    line_refs=[],
                    check_type="external_claim_verification",
                    result="fail",
                    detail=f"claim_id={c.claim_id}, status={c.status.value}",
                ))
                return self._fail_result(
                    verdict=Verdict.REJECT_UNVERIFIED_EXTERNAL,
                    failure_action=FailureAction.BLOCK,
                    pseudo_outputs=["unverified_external_claim"],
                )
        return None

    def enforce_text_policies_or_fail(self) -> Optional[NodeResult]:
        if check_rationalization_violation(self.output_text_buffer):
            self.evidence_items.append(EvidenceItem(
                file_path="response_text",
                line_refs=[],
                check_type="rationalization_ban",
                result="fail",
                detail="pattern hit",
            ))
            return self._fail_result(
                verdict=Verdict.REJECT_POLICY_VIOLATION,
                failure_action=FailureAction.BLOCK,
                pseudo_outputs=["policy_violation_rationalization"],
            )

        if interaction_policy_scan(self.output_text_buffer):
            self.evidence_items.append(EvidenceItem(
                file_path="response_text",
                line_refs=[],
                check_type="no_continue_prompt",
                result="fail",
                detail="pattern hit",
            ))
            return self._fail_result(
                verdict=Verdict.REJECT_POLICY_VIOLATION,
                failure_action=FailureAction.BLOCK,
                pseudo_outputs=["policy_violation_continue_prompt"],
            )

        return None

    def check_tool_use_or_fail(self) -> Optional[NodeResult]:
        if not check_tool_use_nonzero(self.tool_calls):
            self.evidence_items.append(EvidenceItem(
                file_path="runtime",
                line_refs=[],
                check_type="tool_use_nonzero",
                result="fail",
                detail="tool_calls=0",
            ))
            return self._fail_result(
                verdict=Verdict.REJECT_NO_TOOL_USE,
                failure_action=FailureAction.RERUN,
                pseudo_outputs=["reject_no_tool_use"],
            )

        self.evidence_items.append(EvidenceItem(
            file_path="runtime",
            line_refs=[],
            check_type="tool_use_nonzero",
            result="pass",
            detail=f"tool_calls={self.tool_calls}",
        ))
        return None

    def execute_business_logic(self, partial_mode: bool) -> None:
        self.artifacts["phase_result"] = "partial" if partial_mode else "ok"
        self.current_output = {"quality_score": int(self.artifacts.get("quality_score", 0))}

    def evaluate_delta_for_rerun(self) -> None:
        d = compute_delta(self.previous_output, self.current_output)
        self.artifacts["delta_improved"] = d["improved"]
        self.artifacts["delta_value"] = d["delta"]

    def select_outputs(self) -> NodeResult:
        policy_conflict_resolver(self.policy_rules, self, self.evidence_items, self.decision_trace)

        bad = self.enforce_access_requests_or_fail()
        if bad:
            return bad

        bad = self.enforce_external_claims_or_fail()
        if bad:
            return bad

        bad = self.enforce_text_policies_or_fail()
        if bad:
            return bad

        bad = self.check_tool_use_or_fail()
        if bad:
            return bad

        true_candidates: List[OutputContract] = []
        pseudo_candidates: List[OutputContract] = []
        for c in self.output_contracts:
            if self._eval_output_guard(c):
                if c.output_kind == OutputKind.TRUE:
                    true_candidates.append(c)
                else:
                    pseudo_candidates.append(c)

        true_candidates.sort(key=lambda c: c.priority)
        pseudo_candidates.sort(key=lambda c: c.priority)

        if len(true_candidates) < self.min_true_outputs:
            return self._fail_result(
                verdict=Verdict.REJECTED,
                failure_action=FailureAction.RERUN,
                pseudo_outputs=names(pseudo_candidates),
            )

        return self._ok_result(
            true_outputs=names(true_candidates),
            pseudo_outputs=names(pseudo_candidates),
        )

    def run_cycle_if_ready(self) -> Optional[NodeResult]:
        if self.exec_state not in {ExecState.READY_PARTIAL.value, ExecState.READY_FINAL.value}:
            return None

        partial_mode = self.exec_state == ExecState.READY_PARTIAL.value
        self._set_exec_state(ExecState.RUNNING)
        self.execute_business_logic(partial_mode)
        self.evaluate_delta_for_rerun()

        if not partial_mode:
            self.has_final_run_completed = True

        self._set_exec_state(ExecState.EVALUATING_OUTPUT)
        r = self.select_outputs()
        if r.success and not partial_mode:
            self._set_exec_state(ExecState.DONE)
        elif not r.success:
            self._set_exec_state(ExecState.FAILED)
        else:
            self._set_exec_state(ExecState.PARTIAL_DONE)
        return r

    def step(self) -> bool:
        prev_state = self.exec_state
        result = self.run_cycle_if_ready()
        if result is None:
            return False
        emitted = self._emit_node_result(result)
        state_progressed = self.exec_state != prev_state
        return (emitted > 0) or state_progressed


# =========================
# Node 2: CheckPointObject
# =========================

@dataclass
class CheckPointObject(RuntimeNodeBase):
    id: str
    phase_id: str
    secondary_tag: str

    node_kind: NodeKind = NodeKind.CHECKPOINT

    input_join_mode: InputJoinMode = InputJoinMode.ALL
    true_input_expected_count: int = 1
    # SELECT 语义改为“n选k（默认 n选1）”，而非“到达>=阈值即可放行”
    early_select_exact_count: int = 1
    early_reject_multi_select: bool = True

    true_input_arrived_tokens: Set[str] = field(default_factory=set)
    true_inputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pseudo_inputs: List[Dict[str, Any]] = field(default_factory=list)

    pass_rule_kind: str = "AGGREGATED_TRUE"
    pass_rule_params: Dict[str, Any] = field(default_factory=dict)
    fail_rule_kind: str = "AGGREGATED_FALSE"
    fail_rule_params: Dict[str, Any] = field(default_factory=dict)
    failure_action: FailureAction = FailureAction.BLOCK

    # deprecated callables, no longer used for core decision
    pass_condition: Optional[Any] = None
    fail_condition: Optional[Any] = None

    min_true_outputs: int = 1
    max_pseudo_outputs: int = 10
    output_contracts: List[OutputContract] = field(default_factory=list)

    minimum_duration: int = 0
    cumulative_duration: int = 0
    validator_verdict: str = "UNKNOWN"
    validator_lock_state: ValidatorLockState = ValidatorLockState.LOCKED
    tool_calls: int = 0
    required_gate_set: Set[str] = field(default_factory=set)
    required_md_files: List[str] = field(default_factory=list)
    gate_status: Dict[str, bool] = field(default_factory=dict)
    missing_gates: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)

    policy_rules: List[PolicyRule] = field(default_factory=list)
    decision_trace: List[str] = field(default_factory=list)
    evidence_items: List[EvidenceItem] = field(default_factory=list)

    runtime_nodes: Dict[str, Any] = field(default_factory=dict)
    runtime_edges: List[BaseEdge] = field(default_factory=list)
    strict_mode: bool = True

    last_evaluated_snapshot_key: str = ""

    def _fail_result(
        self,
        verdict: Verdict,
        failure_action: FailureAction,
        pseudo_outputs: List[str],
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> NodeResult:
        return NodeResult(
            success=False,
            verdict=verdict,
            failure_action=failure_action,
            selected_true_outputs=[],
            selected_pseudo_outputs=pseudo_outputs,
            artifacts={} if artifacts is None else artifacts,
            evidence_items=self.evidence_items,
            regression_check_passed=False,
        )

    def _ok_result(self, true_outputs: List[str], artifacts: Optional[Dict[str, Any]] = None) -> NodeResult:
        return NodeResult(
            success=True,
            verdict=Verdict.APPROVED,
            failure_action=None,
            selected_true_outputs=true_outputs,
            selected_pseudo_outputs=[],
            artifacts={} if artifacts is None else artifacts,
            evidence_items=self.evidence_items,
            regression_check_passed=True,
        )

    def _block_true_output_routing(self) -> bool:
        return self.validator_lock_state == ValidatorLockState.LOCKED

    def _build_true_emit_payload(self, result: NodeResult, out_name: str) -> Dict[str, Any]:
        payload = super()._build_true_emit_payload(result, out_name)
        payload["gate_passed"] = bool(result.verdict == Verdict.APPROVED)
        return payload

    def _current_input_snapshot_key(self) -> str:
        tokens = sorted(self.true_input_arrived_tokens)
        return sha256_text("|".join(tokens))

    def _can_evaluate_current_snapshot(self) -> bool:
        return self._current_input_snapshot_key() != self.last_evaluated_snapshot_key

    def _mark_snapshot_evaluated(self) -> None:
        self.last_evaluated_snapshot_key = self._current_input_snapshot_key()

    def on_true_input_arrive(self, token: str, payload: Dict[str, Any]) -> None:
        if token in self.true_input_arrived_tokens:
            return
        self.true_input_arrived_tokens.add(token)
        self.true_inputs[token] = payload

    def on_pseudo_input_arrive(self, payload: Dict[str, Any]) -> None:
        self.pseudo_inputs.append(payload)

    def ready_to_evaluate(self) -> bool:
        arrived = len(self.true_input_arrived_tokens)
        if self.input_join_mode == InputJoinMode.ALL:
            return arrived == self.true_input_expected_count

        # SELECT: n选k（默认 n选1），只在恰好 k 时触发；若要求单选且超出则拒绝评估
        if arrived == self.early_select_exact_count:
            return True
        if self.early_reject_multi_select and arrived > self.early_select_exact_count:
            self.decision_trace.append(
                f"early_multi_select_violation:arrived={arrived},exact={self.early_select_exact_count}"
            )
            return False
        return False

    def update_validator_lock(self) -> None:
        if self.validator_verdict == "APPROVE":
            self.validator_lock_state = ValidatorLockState.UNLOCKED
        else:
            self.validator_lock_state = ValidatorLockState.LOCKED

    def _eval_policy_condition(self, rule: PolicyRule) -> bool:
        kind = rule.condition_kind
        params = rule.condition_params
        if kind == "ALWAYS":
            return True
        if kind == "GATE_STATUS_EQUALS":
            return bool(self.gate_status.get(str(params.get("gate", "")), False)) == bool(params.get("value", True))
        if kind == "VALIDATOR_UNLOCKED":
            return self.validator_lock_state == ValidatorLockState.UNLOCKED
        if kind == "TIME_AT_LEAST":
            return self.cumulative_duration >= int(params.get("minimum", self.minimum_duration))
        return False

    def _apply_policy_action(self, rule: PolicyRule) -> None:
        kind = rule.action_kind
        params = rule.action_params
        if kind == "TRACE_ONLY":
            self.decision_trace.append(f"policy_action={rule.id}:trace_only")
            return
        if kind == "SET_GATE_STATUS":
            self.gate_status[str(params.get("gate", ""))] = bool(params.get("value", True))
            self.decision_trace.append(f"policy_action={rule.id}:set_gate_status")
            return
        if kind == "SET_GATE_EDGE_ENABLED":
            target_edge_id = str(params.get("edge_id", ""))
            target_gate_family = str(params.get("gate_family", ""))
            target_from_node_id = str(params.get("from_node_id", ""))
            target_to_node_id = str(params.get("to_node_id", ""))
            target_from_output_name = str(params.get("from_output_name", ""))
            enabled_value = bool(params.get("value", True))

            changed = 0
            for e in self.runtime_edges:
                if e.kind != EdgeKind.GATE:
                    continue
                if target_edge_id and getattr(e, "id", "") != target_edge_id:
                    continue
                if target_gate_family and getattr(e, "gate_family", "") != target_gate_family:
                    continue
                if target_from_node_id and getattr(e, "from_node_id", "") != target_from_node_id:
                    continue
                if target_to_node_id and getattr(e, "to_node_id", "") != target_to_node_id:
                    continue
                if target_from_output_name and getattr(e, "from_output_name", "") != target_from_output_name:
                    continue
                e.enabled = enabled_value
                changed += 1

            self.decision_trace.append(
                f"policy_action={rule.id}:set_gate_edge_enabled:changed={changed}:value={enabled_value}"
            )
            self.evidence_items.append(EvidenceItem(
                file_path="runtime_edges",
                line_refs=[],
                check_type="set_gate_edge_enabled",
                result="pass" if changed > 0 else "fail",
                detail=f"changed={changed}, edge_id={target_edge_id}, gate_family={target_gate_family}, value={enabled_value}",
            ))
            return
        if kind == "APPEND_TRACE":
            self.decision_trace.append(str(params.get("message", f"policy_action={rule.id}")))

    def _eval_output_guard(self, contract: OutputContract) -> bool:
        kind = contract.guard_kind
        params = contract.guard_params
        if kind == "ALWAYS":
            return True
        if kind == "GATE_STATUS_TRUE":
            return bool(self.gate_status.get(str(params.get("gate", "")), False))
        if kind == "AGGREGATED_TRUE":
            return bool(self.gate_status.get("AGGREGATED", False))
        if kind == "AGGREGATED_FALSE":
            return not bool(self.gate_status.get("AGGREGATED", False))
        return False

    def _eval_checkpoint_rule(self, kind: str, params: Dict[str, Any]) -> bool:
        if kind == "ALWAYS":
            return True
        if kind == "NEVER":
            return False
        if kind == "AGGREGATED_TRUE":
            return bool(self.gate_status.get("AGGREGATED", False))
        if kind == "AGGREGATED_FALSE":
            return not bool(self.gate_status.get("AGGREGATED", False))
        if kind == "MISSING_GATES_NONEMPTY":
            return len(self.missing_gates) > 0
        if kind == "MISSING_FILES_NONEMPTY":
            return len(self.missing_files) > 0
        if kind == "GATE_STATUS_EQUALS":
            return bool(self.gate_status.get(str(params.get("gate", "")), False)) == bool(params.get("value", True))
        return False

    def check_time_gate(self) -> bool:
        ok = self.cumulative_duration >= self.minimum_duration
        self.gate_status["TIME"] = ok
        self.evidence_items.append(EvidenceItem(
            file_path="timing_log",
            line_refs=[],
            check_type="time_gate",
            result="pass" if ok else "fail",
            detail=f"cumulative={self.cumulative_duration}, minimum={self.minimum_duration}",
        ))
        return ok

    def check_validator_gate(self) -> bool:
        self.update_validator_lock()
        ok = self.validator_lock_state == ValidatorLockState.UNLOCKED
        self.gate_status["VALIDATOR"] = ok
        self.evidence_items.append(EvidenceItem(
            file_path="validator_verdict",
            line_refs=[],
            check_type="validator_gate",
            result="pass" if ok else "fail",
            detail=f"verdict={self.validator_verdict}, lock={self.validator_lock_state.value}",
        ))
        return ok

    def check_tool_use_gate(self) -> bool:
        ok = check_tool_use_nonzero(self.tool_calls)
        self.gate_status["TOOL_USE"] = ok
        self.evidence_items.append(EvidenceItem(
            file_path="runtime",
            line_refs=[],
            check_type="tool_use_nonzero",
            result="pass" if ok else "fail",
            detail=f"tool_calls={self.tool_calls}",
        ))
        return ok

    def check_required_files_gate(self, artifacts: Dict[str, Any]) -> bool:
        r = required_files_present(self.required_md_files, artifacts)
        self.missing_files = r["missing_files"]
        self.gate_status["REQUIRED_FILES"] = r["ok"]
        self.evidence_items.append(EvidenceItem(
            file_path="artifact_index",
            line_refs=[],
            check_type="required_files",
            result="pass" if r["ok"] else "fail",
            detail=f"missing={','.join(self.missing_files)}",
        ))
        return bool(r["ok"])

    def aggregate_required_gates(self) -> bool:
        self.missing_gates = [g for g in self.required_gate_set if not self.gate_status.get(g, False)]
        self.gate_status["REQUIRED_GATES"] = len(self.missing_gates) == 0
        self.gate_status["AGGREGATED"] = (
            self.gate_status.get("TIME", False)
            and self.gate_status.get("VALIDATOR", False)
            and self.gate_status.get("TOOL_USE", False)
            and self.gate_status.get("REQUIRED_FILES", False)
            and self.gate_status.get("REQUIRED_GATES", False)
        )
        return self.gate_status["AGGREGATED"]

    def evaluate_and_decide(self, artifacts: Dict[str, Any]) -> Optional[NodeResult]:
        if not self.ready_to_evaluate():
            return None

        policy_conflict_resolver(self.policy_rules, self, self.evidence_items, self.decision_trace)

        if not self.check_time_gate():
            return self._fail_result(
                verdict=Verdict.REJECT_INSUFFICIENT_TIME,
                failure_action=FailureAction.RERUN,
                pseudo_outputs=["reject_rerun"],
                artifacts={"missing_gates": [], "missing_files": []},
            )

        if not self.check_validator_gate():
            return self._fail_result(
                verdict=Verdict.REJECTED,
                failure_action=FailureAction.BLOCK,
                pseudo_outputs=["validator_locked"],
            )

        if not self.check_tool_use_gate():
            return self._fail_result(
                verdict=Verdict.REJECT_NO_TOOL_USE,
                failure_action=FailureAction.RERUN,
                pseudo_outputs=["reject_no_tool_use"],
            )

        self.check_required_files_gate(artifacts)
        if not self.aggregate_required_gates():
            return self._fail_result(
                verdict=Verdict.NEEDS_REVISION,
                failure_action=FailureAction.BLOCK,
                pseudo_outputs=["block_due_to_missing_requirements"],
                artifacts={"missing_gates": self.missing_gates, "missing_files": self.missing_files},
            )

        if self._eval_checkpoint_rule(self.fail_rule_kind, self.fail_rule_params):
            return self._fail_result(
                verdict=Verdict.REJECTED,
                failure_action=self.failure_action,
                pseudo_outputs=["checkpoint_fail"],
            )

        if self._eval_checkpoint_rule(self.pass_rule_kind, self.pass_rule_params):
            return self._ok_result(true_outputs=["gate_pass"])

        return self._fail_result(
            verdict=Verdict.NEEDS_REVISION,
            failure_action=FailureAction.BLOCK,
            pseudo_outputs=["checkpoint_uncertain"],
        )

    def step(self) -> bool:
        if not self.ready_to_evaluate() or not self._can_evaluate_current_snapshot():
            return False

        any_input = next(iter(self.true_inputs.values()), {})
        result = self.evaluate_and_decide(any_input.get("artifacts", {}))
        if result is None:
            return False

        self._mark_snapshot_evaluated()
        emitted = self._emit_node_result(result)
        snapshot_progressed = True
        return (emitted > 0) or snapshot_progressed


# =========================
# Runtime Dispatch
# =========================

graph_nodes: Dict[str, Any] = {}
graph_edges: List[BaseEdge] = []


def find_edges_by_output(source_node_id: str, output_name: str, strict_mode: bool = False) -> List[BaseEdge]:
    node = graph_nodes.get(source_node_id)
    if node is None:
        return []
    if strict_mode:
        raise RuntimeError({"code": "STRICT_MODE_EXTERNAL_DISPATCH_FORBIDDEN", "function": "find_edges_by_output"})
    if hasattr(node, "_find_edges_by_output"):
        return node._find_edges_by_output(output_name)
    return []


def route_output(source_node: Any, source_output_name: str, source_output_kind: OutputKind, payload: Dict[str, Any], strict_mode: bool = False) -> None:
    if strict_mode:
        raise RuntimeError({"code": "STRICT_MODE_EXTERNAL_DISPATCH_FORBIDDEN", "function": "route_output"})
    source_node._route_output_internal(source_output_name, source_output_kind, payload)


def execute_node(node: Any, strict_mode: bool = False) -> None:
    if strict_mode:
        raise RuntimeError({"code": "STRICT_MODE_EXTERNAL_DISPATCH_FORBIDDEN", "function": "execute_node"})
    node.step()


# =========================
# Global Invariants
# =========================

def assert_global_invariants(runtime: Dict[str, Any]) -> None:
    nodes: Dict[str, Any] = runtime.get("nodes", {})
    edges: List[BaseEdge] = runtime.get("edges", [])
    strict_mode: bool = bool(runtime.get("strict_mode", False))

    # SYNC 必须用于多前驱汇合：至少 2 个不同前节点汇入同一后节点
    sync_incoming: Dict[str, Set[str]] = {}
    for e in edges:
        if e.kind == EdgeKind.SYNC:
            sync_incoming.setdefault(e.to_node_id, set()).add(e.from_node_id)

    for to_node_id, from_nodes in sync_incoming.items():
        if len(from_nodes) < 2:
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "SYNC_REQUIRES_MULTI_UPSTREAM", "to_node_id": to_node_id})

    # DECISION 必须是分叉或汇聚（1->n 或 n->1），禁止 1->1 同构直连
    decision_outgoing: Dict[str, Set[str]] = {}
    decision_incoming: Dict[str, Set[str]] = {}
    for e in edges:
        if e.kind == EdgeKind.DECISION:
            decision_outgoing.setdefault(e.from_node_id, set()).add(e.to_node_id)
            decision_incoming.setdefault(e.to_node_id, set()).add(e.from_node_id)

    for e in edges:
        if e.kind != EdgeKind.DECISION:
            continue
        out_degree = len(decision_outgoing.get(e.from_node_id, set()))
        in_degree = len(decision_incoming.get(e.to_node_id, set()))
        if not ((out_degree >= 2 and in_degree == 1) or (out_degree == 1 and in_degree >= 2)):
            raise RuntimeError({
                "code": "INVARIANT_FAILED",
                "invariant": "DECISION_MUST_BE_ONE_TO_MANY_OR_MANY_TO_ONE",
                "edge_id": e.id,
                "from_node_id": e.from_node_id,
                "to_node_id": e.to_node_id,
                "decision_out_degree": out_degree,
                "decision_in_degree": in_degree,
            })

    for e in edges:
        if e.from_output_kind == OutputKind.TRUE and e.kind not in {EdgeKind.GATE, EdgeKind.DECISION, EdgeKind.SYNC}:
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "TRUE_OUTPUT_EDGE_KIND", "edge_id": e.id})
        if e.from_output_kind == OutputKind.PSEUDO and e.kind not in {EdgeKind.ROLLBACK}:
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "PSEUDO_OUTPUT_EDGE_KIND", "edge_id": e.id})

        src = nodes.get(e.from_node_id)
        dst = nodes.get(e.to_node_id)
        if src is None or dst is None:
            continue
        if src.node_kind == NodeKind.CHECKPOINT and dst.node_kind != NodeKind.WORK:
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "CHECKPOINT_TARGET_WORK_ONLY", "edge_id": e.id})
        if not validate_connection(src.node_kind, e.from_output_kind, e.kind, dst.node_kind, e.to_input_kind):
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "CONNECTION_MATRIX", "edge_id": e.id})

    for n in nodes.values():
        if getattr(n, "node_kind", None) == NodeKind.CHECKPOINT:
            if getattr(n, "minimum_duration", 0) < 0:
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "TIME_HARD_FLOOR", "node_id": n.id})
            if getattr(n, "validator_verdict", "UNKNOWN") != "APPROVE" and getattr(n, "validator_lock_state", None) != ValidatorLockState.LOCKED:
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "VALIDATOR_LOCK_UNTIL_APPROVE", "node_id": n.id})
        if getattr(n, "tool_calls", 0) < 0:
            raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "TOOL_USE_NONZERO", "node_id": n.id})

        if getattr(n, "node_kind", None) == NodeKind.WORK:
            for req in getattr(n, "access_requests", []):
                if not enforce_file_ban(req, getattr(n, "access_policy", {})):
                    raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "FILE_BAN_ENFORCED", "node_id": n.id, "resource": req.resource})
            for c in getattr(n, "claims", []):
                if not verify_external_claim(c):
                    raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "EXTERNAL_CLAIM_VERIFIED_BEFORE_USE", "node_id": n.id, "claim_id": c.claim_id})
            if getattr(n, "previous_output", {}) and "delta_improved" not in getattr(n, "artifacts", {}):
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "RERUN_DELTA_REQUIRED", "node_id": n.id})
            if check_rationalization_violation(getattr(n, "output_text_buffer", "")):
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "POLICY_NO_RATIONALIZATION", "node_id": n.id})
            if interaction_policy_scan(getattr(n, "output_text_buffer", "")):
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "POLICY_NO_CONTINUE_PROMPT", "node_id": n.id})

    if strict_mode:
        for n in nodes.values():
            if not hasattr(n, "bind_runtime") or not hasattr(n, "step"):
                raise RuntimeError({"code": "INVARIANT_FAILED", "invariant": "STRICT_INTERNAL_SCHEDULER_REQUIRED", "node_id": getattr(n, "id", "<unknown>")})


# =========================
# Final Self-Check
# =========================

def push_issue(issues: List[Dict[str, Any]], level: str, scope: str, object_id: str, field: str, message: str) -> None:
    issues.append({"level": level, "scope": scope, "object_id": object_id, "field": field, "message": message})


def ensure_field(obj: Any, field_name: str, scope: str, object_id: str, issues: List[Dict[str, Any]]) -> bool:
    if not hasattr(obj, field_name):
        push_issue(issues, "ERROR", scope, object_id, field_name, "missing required field")
        return False
    return True


def validate_edge_object_integrity(e: BaseEdge, issues: List[Dict[str, Any]]) -> None:
    base_fields = ["id", "from_node_id", "to_node_id", "from_output_name", "from_output_kind", "to_input_kind", "enabled", "kind"]
    for f in base_fields:
        ensure_field(e, f, "EDGE", getattr(e, "id", "<unknown-edge>"), issues)

    if hasattr(e, "kind") and e.kind not in {
        EdgeKind.GATE, EdgeKind.DECISION, EdgeKind.ROLLBACK, EdgeKind.SYNC,
    }:
        push_issue(issues, "ERROR", "EDGE", str(getattr(e, "id", "<unknown-edge>")), "kind", "kind out of 4-edge taxonomy")


def validate_node_object_integrity(n: Any, issues: List[Dict[str, Any]]) -> None:
    base_fields = [
        "id", "node_kind", "phase_id", "secondary_tag", "input_join_mode",
        "true_input_expected_count", "early_select_exact_count", "min_true_outputs",
        "max_pseudo_outputs", "output_contracts",
    ]
    for f in base_fields:
        ensure_field(n, f, "NODE", str(getattr(n, "id", "<unknown-node>")), issues)

    ensure_field(n, "tool_calls", "NODE", str(getattr(n, "id", "<unknown-node>")), issues)
    ensure_field(n, "policy_rules", "NODE", str(getattr(n, "id", "<unknown-node>")), issues)

    if getattr(n, "node_kind", None) == NodeKind.CHECKPOINT:
        for f in ["minimum_duration", "cumulative_duration", "validator_lock_state", "required_md_files"]:
            ensure_field(n, f, "NODE", str(getattr(n, "id", "<unknown-node>")), issues)

    if getattr(n, "node_kind", None) == NodeKind.WORK:
        for f in ["access_requests", "claims"]:
            ensure_field(n, f, "NODE", str(getattr(n, "id", "<unknown-node>")), issues)


def run_final_self_check(graph_nodes_: Dict[str, Any], graph_edges_: List[BaseEdge], strict_mode: bool = False) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    for e in graph_edges_:
        validate_edge_object_integrity(e, issues)

    for n in graph_nodes_.values():
        validate_node_object_integrity(n, issues)

    for n in graph_nodes_.values():
        for r in getattr(n, "policy_rules", []):
            if not hasattr(r, "condition_kind"):
                push_issue(issues, "ERROR", "POLICY_RULE", str(getattr(n, "id", "<unknown-node>")), "condition_kind", "missing declarative condition kind")
            if not hasattr(r, "action_kind"):
                push_issue(issues, "ERROR", "POLICY_RULE", str(getattr(n, "id", "<unknown-node>")), "action_kind", "missing declarative action kind")

        for c in getattr(n, "output_contracts", []):
            if not hasattr(c, "guard_kind"):
                push_issue(issues, "ERROR", "OUTPUT_CONTRACT", str(getattr(n, "id", "<unknown-node>")), "guard_kind", "missing declarative guard kind")

        if getattr(n, "node_kind", None) == NodeKind.CHECKPOINT:
            if not hasattr(n, "pass_rule_kind"):
                push_issue(issues, "ERROR", "NODE", str(getattr(n, "id", "<unknown-node>")), "pass_rule_kind", "missing pass rule kind")
            if not hasattr(n, "fail_rule_kind"):
                push_issue(issues, "ERROR", "NODE", str(getattr(n, "id", "<unknown-node>")), "fail_rule_kind", "missing fail rule kind")
            if getattr(n, "pass_condition", None) is not None:
                push_issue(issues, "WARN", "NODE", str(getattr(n, "id", "<unknown-node>")), "pass_condition", "deprecated callable field present but ignored")
            if getattr(n, "fail_condition", None) is not None:
                push_issue(issues, "WARN", "NODE", str(getattr(n, "id", "<unknown-node>")), "fail_condition", "deprecated callable field present but ignored")

    if strict_mode:
        if len(graph_nodes_) != 2:
            push_issue(issues, "ERROR", "GRAPH", "global", "node_count", "strict mode requires exactly 2 node objects")
        if len(graph_edges_) != 4:
            push_issue(issues, "ERROR", "GRAPH", "global", "edge_count", "strict mode requires exactly 4 edge objects")

    errors = [x for x in issues if x["level"] == "ERROR"]
    warns = [x for x in issues if x["level"] == "WARN"]

    return {
        "ok": len(errors) == 0,
        "total_errors": len(errors),
        "total_warnings": len(warns),
        "issues": issues,
    }


def finalize_graph_or_raise(graph_nodes_: Dict[str, Any], graph_edges_: List[BaseEdge], strict_mode: bool = False) -> Dict[str, Any]:
    report = run_final_self_check(graph_nodes_, graph_edges_, strict_mode=strict_mode)
    if strict_mode:
        assert_global_invariants({"nodes": graph_nodes_, "edges": graph_edges_, "strict_mode": True})
    if not report["ok"]:
        raise RuntimeError({"code": "FINAL_SELF_CHECK_FAILED", "report": report})
    return report
```
