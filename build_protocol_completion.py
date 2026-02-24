import csv
from pathlib import Path
from collections import defaultdict, Counter
import re

base = Path("C:/Users/18805/Desktop/MCM-clean/MCM-Killer/output/implementation/deep_research_20260223_run_cc")
source_csv = base / "05d_edge_reclassification_v2.csv"
orig_dot = Path("C:/Users/18805/Desktop/MCM-clean/MCM-Killer/flow_chart_original/flow_chart_original.dot")

out_05d = base / "05d_edge_reclassification_v2.csv"
out_05e = base / "05e_reclass_diff_from_05b.csv"
out_05f = base / "05f_edge_reclassification_v2_clean.csv"
out_05g = base / "05g_edge_classification_grouped_by_tag.md"
out_05h = base / "05h_edge_reclassification_v2_colored.dot"
out_05i = base / "05i_logic_gaps_not_covered_by_130_edges.md"

rows = list(csv.DictReader(source_csv.open("r", encoding="utf-8-sig")))

# Remove any previous protocol completion edges for idempotent reruns
# Keep original edges (including E130), only strip synthetic protocol edges E131-E149
filtered = []
for r in rows:
    eid = r.get("edge_id", "")
    try:
        n = int(eid[1:]) if eid.startswith("E") else -1
    except Exception:
        n = -1
    if 131 <= n <= 149:
        continue
    filtered.append(r)
rows = filtered

# Restore original explanatory edge E130 (NOTE->P0) if it was removed by earlier bad rebuilds
if not any(r.get("edge_id") == "E130" for r in rows):
    rows.append({
        "edge_id": "E130",
        "edge_signature": "NOTE->P0",
        "source": "NOTE",
        "target": "P0",
        "label": "",
        "style": "dashed",
        "old_object_class": "AnnotationLinkObject",
        "old_object_type": "explanatory_note_link",
        "v2_primary_class": "MetaTransitionObject",
        "v2_secondary_tag": "meta:annotation",
        "v2_polarity": "neutral",
        "execution_role": "documentation_link",
        "control_direction": "non_executable",
        "constraint_strength": "soft",
        "mandatory": "false",
        "is_executable": "false",
        "side_effect_scope": "documentation",
        "gate_family": "none",
        "loop_family": "none",
        "path_criticality": "low",
        "rationale": "保留原图说明节点到流程入口的注释连线",
        "evidence": "flow_chart_original.dot:227",
    })

new_edges = [
    {
        "edge_id": "E131",
        "edge_signature": "TG->TV_CALL",
        "source": "TG",
        "target": "TV_CALL",
        "label": "per-phase validation",
        "style": "dashed",
        "old_object_class": "ValidationTransitionObject",
        "old_object_type": "per_phase_time_validator_call",
        "v2_primary_class": "GateTransitionObject",
        "v2_secondary_tag": "gate:handoff:time_validator",
        "v2_polarity": "positive",
        "execution_role": "validator_handoff",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "time",
        "loop_family": "none",
        "path_criticality": "critical",
        "rationale": "显式补全每阶段必须调用time_validator的协议边",
        "evidence": "workspace/2025_C/CLAUDE.md:117",
    },
    {
        "edge_id": "E132",
        "edge_signature": "RR->RERUN_CMD",
        "source": "RR",
        "target": "RERUN_CMD",
        "label": "--rerun",
        "style": "dashed",
        "old_object_class": "LoopTransitionObject",
        "old_object_type": "rerun_command_dispatch",
        "v2_primary_class": "LoopTransitionObject",
        "v2_secondary_tag": "loop:rerun",
        "v2_polarity": "neutral",
        "execution_role": "iterative_control",
        "control_direction": "backward_or_self",
        "constraint_strength": "hard",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "none",
        "loop_family": "rerun_or_retry",
        "path_criticality": "critical",
        "rationale": "补全REJECT后必须以--rerun命令重跑",
        "evidence": "workspace/2025_C/CLAUDE.md:153",
    },
    {
        "edge_id": "E133",
        "edge_signature": "RERUN_CMD->PREV_OUT",
        "source": "RERUN_CMD",
        "target": "PREV_OUT",
        "label": "read previous_output",
        "style": "dashed",
        "old_object_class": "DependencyConstraintObject",
        "old_object_type": "previous_output_dependency",
        "v2_primary_class": "SyncTransitionObject",
        "v2_secondary_tag": "sync:dependency",
        "v2_polarity": "neutral",
        "execution_role": "dependency_control",
        "control_direction": "lateral",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "dependency",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全rerun必须读取previous_output并改进的依赖边",
        "evidence": "workspace/2025_C/CLAUDE.md:154",
    },
    {
        "edge_id": "E134",
        "edge_signature": "TIMEOUT3->ALT",
        "source": "TIMEOUT3",
        "target": "ALT",
        "label": "3x timeout",
        "style": "dashed",
        "old_object_class": "EscalationObject",
        "old_object_type": "timeout_escalation",
        "v2_primary_class": "ExceptionTransitionObject",
        "v2_secondary_tag": "exception:escalation",
        "v2_polarity": "negative",
        "execution_role": "escalation",
        "control_direction": "detour",
        "constraint_strength": "hard",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "timeout",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全3次超时后的替代策略升级入口",
        "evidence": "workspace/2025_C/CLAUDE.md:102",
    },
    {
        "edge_id": "E135",
        "edge_signature": "ALT->SIMPLE",
        "source": "ALT",
        "target": "SIMPLE",
        "label": "fallback",
        "style": "dashed",
        "old_object_class": "ForwardTransitionObject",
        "old_object_type": "fallback_progress",
        "v2_primary_class": "ProgressTransitionObject",
        "v2_secondary_tag": "progress:linear",
        "v2_polarity": "positive",
        "execution_role": "mainline_progress",
        "control_direction": "forward",
        "constraint_strength": "medium",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "none",
        "loop_family": "none",
        "path_criticality": "medium",
        "rationale": "补全超时fallback链：alternative到simplified prompt",
        "evidence": "workspace/2025_C/CLAUDE.md:102",
    },
    {
        "edge_id": "E136",
        "edge_signature": "SIMPLE->CHUNK",
        "source": "SIMPLE",
        "target": "CHUNK",
        "label": "fallback",
        "style": "dashed",
        "old_object_class": "ForwardTransitionObject",
        "old_object_type": "fallback_progress",
        "v2_primary_class": "ProgressTransitionObject",
        "v2_secondary_tag": "progress:linear",
        "v2_polarity": "positive",
        "execution_role": "mainline_progress",
        "control_direction": "forward",
        "constraint_strength": "medium",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "none",
        "loop_family": "none",
        "path_criticality": "medium",
        "rationale": "补全超时fallback链：simplified prompt到smaller chunks",
        "evidence": "workspace/2025_C/CLAUDE.md:102",
    },
    {
        "edge_id": "E137",
        "edge_signature": "ANY_PHASE->KNOWN_ISSUES",
        "source": "ANY_PHASE",
        "target": "KNOWN_ISSUES",
        "label": "log issue",
        "style": "dashed",
        "old_object_class": "AnnotationLinkObject",
        "old_object_type": "known_issues_log_link",
        "v2_primary_class": "MetaTransitionObject",
        "v2_secondary_tag": "meta:annotation",
        "v2_polarity": "neutral",
        "execution_role": "documentation_link",
        "control_direction": "non_executable",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "false",
        "side_effect_scope": "documentation",
        "gate_family": "none",
        "loop_family": "none",
        "path_criticality": "medium",
        "rationale": "补全异常问题需记录到known_issues.md的治理边",
        "evidence": "workspace/2025_C/CLAUDE.md:103",
    },
    {
        "edge_id": "E138",
        "edge_signature": "KNOWN_ISSUES->CONT",
        "source": "KNOWN_ISSUES",
        "target": "CONT",
        "label": "workaround+continue",
        "style": "dashed",
        "old_object_class": "ContinuationObject",
        "old_object_type": "continue_after_workaround",
        "v2_primary_class": "ProgressTransitionObject",
        "v2_secondary_tag": "progress:continued",
        "v2_polarity": "positive",
        "execution_role": "continuation",
        "control_direction": "forward",
        "constraint_strength": "medium",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "none",
        "loop_family": "none",
        "path_criticality": "medium",
        "rationale": "补全记录问题后降级继续执行的协议边",
        "evidence": "workspace/2025_C/CLAUDE.md:103",
    },
    {
        "edge_id": "E139",
        "edge_signature": "P7F->MANIFEST7",
        "source": "P7F",
        "target": "MANIFEST7",
        "label": "update VERSION_MANIFEST",
        "style": "dashed",
        "old_object_class": "DependencyConstraintObject",
        "old_object_type": "manifest_state_update",
        "v2_primary_class": "SyncTransitionObject",
        "v2_secondary_tag": "sync:dependency",
        "v2_polarity": "neutral",
        "execution_role": "dependency_control",
        "control_direction": "lateral",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "dependency",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全7A-7F每子阶段需更新VERSION_MANIFEST的状态流",
        "evidence": "workspace/2025_C/CLAUDE.md:124",
    },
    {
        "edge_id": "E140",
        "edge_signature": "W5->ARTIFACT_CHECK",
        "source": "W5",
        "target": "ARTIFACT_CHECK",
        "label": "results_i.csv exists?",
        "style": "dashed",
        "old_object_class": "QualityGateObject",
        "old_object_type": "artifact_integrity_check_entry",
        "v2_primary_class": "GateTransitionObject",
        "v2_secondary_tag": "gate:entry:data_consistency",
        "v2_polarity": "neutral",
        "execution_role": "quality_gate_entry",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "quality",
        "loop_family": "none",
        "path_criticality": "critical",
        "rationale": "补全Phase5完成前results_i.csv存在性校验",
        "evidence": "workspace/2025_C/CLAUDE.md:101",
    },
    {
        "edge_id": "E141",
        "edge_signature": "ARTIFACT_CHECK->P55",
        "source": "ARTIFACT_CHECK",
        "target": "P55",
        "label": "all present",
        "style": "dashed",
        "old_object_class": "ReleaseTransitionObject",
        "old_object_type": "artifact_check_release",
        "v2_primary_class": "ProgressTransitionObject",
        "v2_secondary_tag": "progress:released",
        "v2_polarity": "positive",
        "execution_role": "gate_release",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "phase_or_global",
        "gate_family": "time_or_quality",
        "loop_family": "none",
        "path_criticality": "critical",
        "rationale": "补全制品校验通过后放行到5.5",
        "evidence": "workspace/2025_C/CLAUDE.md:101",
    },
    {
        "edge_id": "E142",
        "edge_signature": "CONT->CONSULT",
        "source": "CONT",
        "target": "CONSULT",
        "label": "consultation checkpoint",
        "style": "dashed",
        "old_object_class": "AdvisoryDecisionObject",
        "old_object_type": "consultation_escalation",
        "v2_primary_class": "DecisionTransitionObject",
        "v2_secondary_tag": "decision:advisory",
        "v2_polarity": "neutral",
        "execution_role": "advisory_decision",
        "control_direction": "branching",
        "constraint_strength": "soft",
        "mandatory": "conditional",
        "is_executable": "true",
        "side_effect_scope": "phase",
        "gate_family": "advisory",
        "loop_family": "none",
        "path_criticality": "medium",
        "rationale": "补全consultation export与顾问复核检查点",
        "evidence": "workspace/2025_C/CLAUDE.md:24",
    },
    {
        "edge_id": "E143",
        "edge_signature": "AGENT_RUN->TOOL_AUDIT",
        "source": "AGENT_RUN",
        "target": "TOOL_AUDIT",
        "label": "0 tool uses?",
        "style": "dashed",
        "old_object_class": "QualityGateObject",
        "old_object_type": "tool_use_quality_gate",
        "v2_primary_class": "GateTransitionObject",
        "v2_secondary_tag": "gate:entry:quality",
        "v2_polarity": "neutral",
        "execution_role": "quality_gate_entry",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "quality",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全0 tool uses即失败的工具使用合规门",
        "evidence": "workspace/2025_C/CLAUDE.md:130",
    },
    {
        "edge_id": "E144",
        "edge_signature": "DIRECTOR->FILE_BAN",
        "source": "DIRECTOR",
        "target": "FILE_BAN",
        "label": "read-ban enforcement",
        "style": "dashed",
        "old_object_class": "BlockTransitionObject",
        "old_object_type": "director_file_ban",
        "v2_primary_class": "ExceptionTransitionObject",
        "v2_secondary_tag": "exception:block",
        "v2_polarity": "negative",
        "execution_role": "gate_block",
        "control_direction": "halt_or_detour",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "time_or_quality",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全director file-ban权限约束阻断逻辑",
        "evidence": "workspace/2025_C/CLAUDE.md:126",
    },
    {
        "edge_id": "E145",
        "edge_signature": "EXT_RES->TRUST_VERIFY",
        "source": "EXT_RES",
        "target": "TRUST_VERIFY",
        "label": "must verify independently",
        "style": "dashed",
        "old_object_class": "QualityGateObject",
        "old_object_type": "external_trust_boundary_check",
        "v2_primary_class": "GateTransitionObject",
        "v2_secondary_tag": "gate:entry:quality",
        "v2_polarity": "neutral",
        "execution_role": "quality_gate_entry",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "quality",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全external_resources/past_work的信任边界验证",
        "evidence": "workspace/2025_C/CLAUDE.md:122",
    },
    {
        "edge_id": "E146",
        "edge_signature": "REWORK_DONE->REVERIFY_ALL",
        "source": "REWORK_DONE",
        "target": "REVERIFY_ALL",
        "label": "all agents re-verify",
        "style": "dashed",
        "old_object_class": "ValidationTransitionObject",
        "old_object_type": "fanout_revalidation",
        "v2_primary_class": "GateTransitionObject",
        "v2_secondary_tag": "gate:handoff:generic",
        "v2_polarity": "neutral",
        "execution_role": "validator_handoff",
        "control_direction": "forward",
        "constraint_strength": "hard",
        "mandatory": "true",
        "is_executable": "true",
        "side_effect_scope": "global",
        "gate_family": "quality",
        "loop_family": "none",
        "path_criticality": "high",
        "rationale": "补全返工后非拒绝方也必须再验证的广播回路入口",
        "evidence": "workspace/2025_C/CLAUDE.md:134",
    },
]

rows.extend(new_edges)


def edge_num(r):
    try:
        return int(r.get("edge_id", "E0")[1:])
    except Exception:
        return 10**9

rows = sorted(rows, key=edge_num)

# Write updated 05d
fieldnames_05d = [
    "edge_id","edge_signature","source","target","label","style",
    "old_object_class","old_object_type",
    "v2_primary_class","v2_secondary_tag","v2_polarity",
    "execution_role","control_direction","constraint_strength","mandatory",
    "is_executable","side_effect_scope","gate_family","loop_family",
    "path_criticality","rationale","evidence"
]
with out_05d.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames_05d)
    w.writeheader()
    w.writerows(rows)

# Write updated clean 05f
fieldnames_05f = [f for f in fieldnames_05d if f not in {"old_object_class", "old_object_type"}]
with out_05f.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames_05f)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fieldnames_05f})

# Write updated 05e diff
fieldnames_05e = [
    "edge_id","edge_signature","old_object_class","old_object_type",
    "new_primary_class","new_secondary_tag","changed_primary","changed_level_note",
    "old_decision_polarity","new_decision_polarity","polarity_changed","evidence"
]
out_rows_e = []
for r in rows:
    old_cls = r.get("old_object_class", "")
    new_cls = r.get("v2_primary_class", "")
    changed = "yes" if old_cls != new_cls else "no"
    if r["edge_id"] >= "E131":
        changed = "yes"
    out_rows_e.append({
        "edge_id": r["edge_id"],
        "edge_signature": r.get("edge_signature", ""),
        "old_object_class": old_cls,
        "old_object_type": r.get("old_object_type", ""),
        "new_primary_class": new_cls,
        "new_secondary_tag": r.get("v2_secondary_tag", ""),
        "changed_primary": changed,
        "changed_level_note": "added_protocol_edge" if r["edge_id"] >= "E131" else ("coarsened_to_v2_primary" if changed == "yes" else "same_primary_name"),
        "old_decision_polarity": "",
        "new_decision_polarity": r.get("v2_polarity", ""),
        "polarity_changed": "n/a" if r["edge_id"] >= "E131" else "no",
        "evidence": r.get("evidence", ""),
    })

with out_05e.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames_05e)
    w.writeheader()
    w.writerows(out_rows_e)

# Updated grouped MD
by_secondary = defaultdict(list)
for r in rows:
    by_secondary[r["v2_secondary_tag"]].append(r)

primary_counter = Counter(r["v2_primary_class"] for r in rows)
secondary_counter = Counter(r["v2_secondary_tag"] for r in rows)

with out_05g.open("w", encoding="utf-8") as f:
    f.write("# 05g Edge Classification (Grouped by v2_secondary_tag)\n\n")
    f.write("Data source: `05d_edge_reclassification_v2.csv` (protocol-completed)\n\n")
    f.write(f"Total edges: **{len(rows)}**\n\n")
    f.write("## Primary Class Distribution\n\n")
    for k, v in sorted(primary_counter.items(), key=lambda x: (-x[1], x[0])):
        f.write(f"- `{k}`: **{v}**\n")

    f.write("\n## Secondary Tag Distribution\n\n")
    for k, v in sorted(secondary_counter.items(), key=lambda x: (-x[1], x[0])):
        f.write(f"- `{k}`: **{v}**\n")

    for tag in sorted(by_secondary.keys()):
        items = sorted(by_secondary[tag], key=edge_num)
        primary_set = sorted(set(i["v2_primary_class"] for i in items))
        f.write(f"\n## {tag}\n\n")
        f.write(f"- Primary class: `{', '.join(primary_set)}`\n")
        f.write(f"- Edge count: **{len(items)}**\n\n")
        f.write("| edge_id | edge_signature | label | primary | polarity | evidence |\n")
        f.write("|---|---|---|---|---|---|\n")
        for i in items:
            label = (i.get("label") or "").replace("|", "\\|")
            sig = (i.get("edge_signature") or "").replace("|", "\\|")
            evidence = (i.get("evidence") or "").replace("|", "\\|")
            f.write(f"| {i['edge_id']} | {sig} | {label} | {i['v2_primary_class']} | {i['v2_polarity']} | {evidence} |\n")

# Updated DOT
primary_color = {
    "ProgressTransitionObject": "#2E8B57",
    "GateTransitionObject": "#D39B2A",
    "DecisionTransitionObject": "#8D6AC8",
    "RollbackTransitionObject": "#C95A5A",
    "LoopTransitionObject": "#1F77B4",
    "ExceptionTransitionObject": "#B22222",
    "SyncTransitionObject": "#2AA198",
    "MetaTransitionObject": "#7F8C8D",
}

node_decl = {}
node_pattern = re.compile(r"^\s*([A-Za-z0-9_]+)\s*\[(.+)\];\s*$")
for line in orig_dot.read_text(encoding="utf-8").splitlines():
    m = node_pattern.match(line)
    if m and "->" not in line:
        nid = m.group(1)
        attrs = m.group(2)
        if nid not in {"graph", "node", "edge"}:
            node_decl[nid] = attrs

protocol_nodes = {
    "TV_CALL": 'shape=diamond, fillcolor="#FFF7E6", color="#D39B2A", label="per-phase\ntime_validator call"',
    "RERUN_CMD": 'shape=box, fillcolor="#FFECEC", color="#C95A5A", label="python tools/time_tracker.py\nstart --rerun"',
    "PREV_OUT": 'shape=note, fillcolor="#F2F2F2", color="#888888", label="read previous_output_path\nand improve"',
    "TIMEOUT3": 'shape=diamond, fillcolor="#FFECEC", color="#C95A5A", label="3x timeout?"',
    "ALT": 'shape=box, fillcolor="#FFECEC", color="#C95A5A", label="alternative approach"',
    "SIMPLE": 'shape=box, fillcolor="#FFECEC", color="#C95A5A", label="simplified prompt"',
    "CHUNK": 'shape=box, fillcolor="#FFECEC", color="#C95A5A", label="smaller chunks"',
    "ANY_PHASE": 'shape=box, fillcolor="#F2F2F2", color="#888888", label="any phase"',
    "KNOWN_ISSUES": 'shape=note, fillcolor="#F2F2F2", color="#888888", label="known_issues.md"',
    "MANIFEST7": 'shape=note, fillcolor="#F2F2F2", color="#888888", label="VERSION_MANIFEST.json"',
    "ARTIFACT_CHECK": 'shape=diamond, fillcolor="#FFF7E6", color="#D39B2A", label="results_{i}.csv\nall exist?"',
    "CONSULT": 'shape=diamond, fillcolor="#F5F0FF", color="#8D6AC8", label="consultation export\ncheckpoint"',
    "AGENT_RUN": 'shape=box, fillcolor="#EEF5FF", color="#6D8FB8", label="agent run"',
    "TOOL_AUDIT": 'shape=diamond, fillcolor="#FFF7E6", color="#D39B2A", label="tool uses > 0?"',
    "DIRECTOR": 'shape=box, fillcolor="#EEF5FF", color="#6D8FB8", label="director"',
    "FILE_BAN": 'shape=box, fillcolor="#FFECEC", color="#C95A5A", label="file-ban enforcement"',
    "EXT_RES": 'shape=box, fillcolor="#EEF5FF", color="#6D8FB8", label="external_resources/past_work"',
    "TRUST_VERIFY": 'shape=diamond, fillcolor="#FFF7E6", color="#D39B2A", label="independent verification"',
    "REWORK_DONE": 'shape=box, fillcolor="#EEF5FF", color="#6D8FB8", label="rework done"',
    "REVERIFY_ALL": 'shape=box, fillcolor="#F5F0FF", color="#8D6AC8", label="all agents re-verify"',
}


def esc(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


with out_05h.open("w", encoding="utf-8") as f:
    f.write("digraph MCMKillerWorkflowV2Classified {\n")
    f.write("    graph [rankdir=LR, fontname=\"Microsoft YaHei\", fontsize=12, labelloc=\"t\",\n")
    f.write("           label=\"MCM-Killer Workflow (146 edges, protocol-completed, v2 classes color-coded)\",\n")
    f.write("           bgcolor=\"white\", splines=true, overlap=false];\n")
    f.write("    node [shape=box, style=\"rounded,filled\", fillcolor=\"#F8FBFF\", color=\"#5B8DB8\", fontname=\"Microsoft YaHei\", fontsize=10];\n")
    f.write("    edge [fontname=\"Microsoft YaHei\", fontsize=9, arrowsize=0.8];\n\n")

    f.write("    // Original nodes\n")
    for nid in sorted(node_decl.keys()):
        f.write(f"    {nid} [{node_decl[nid]}];\n")

    f.write("\n    // Protocol completion nodes (from workspace/2025_C/CLAUDE.md)\n")
    for nid in sorted(protocol_nodes.keys()):
        f.write(f"    {nid} [{protocol_nodes[nid]}];\n")

    f.write("\n    // Colored edges from updated 05d_edge_reclassification_v2.csv\n")
    for r in rows:
        src = r["source"]
        tgt = r["target"]
        label = esc(r.get("label", ""))
        style = r.get("style") or "solid"
        primary = r.get("v2_primary_class", "")
        color = primary_color.get(primary, "#4A6C8C")
        tooltip = esc(f"{r.get('edge_id','')} | {primary} | {r.get('v2_secondary_tag','')}")

        attrs = [
            f"color=\"{color}\"",
            f"fontcolor=\"{color}\"",
            f"style=\"{style}\"",
            "penwidth=2.0",
            f"tooltip=\"{tooltip}\"",
        ]
        if label:
            attrs.append(f"label=\"{label}\"")

        if r.get("edge_signature") in {"P01->B01", "NOTE->P0"}:
            attrs.append("arrowhead=none")

        f.write(f"    {src} -> {tgt} [{', '.join(attrs)}];\n")

    f.write("\n    subgraph cluster_legend {\n")
    f.write("        label=\"V2 Primary Class Color Legend\";\n")
    f.write("        style=\"rounded,dashed\";\n")
    f.write("        color=\"#999999\";\n")
    f.write("        LEG_P [label=\"ProgressTransitionObject\", shape=plaintext, fontcolor=\"#2E8B57\"];\n")
    f.write("        LEG_G [label=\"GateTransitionObject\", shape=plaintext, fontcolor=\"#D39B2A\"];\n")
    f.write("        LEG_D [label=\"DecisionTransitionObject\", shape=plaintext, fontcolor=\"#8D6AC8\"];\n")
    f.write("        LEG_R [label=\"RollbackTransitionObject\", shape=plaintext, fontcolor=\"#C95A5A\"];\n")
    f.write("        LEG_L [label=\"LoopTransitionObject\", shape=plaintext, fontcolor=\"#1F77B4\"];\n")
    f.write("        LEG_E [label=\"ExceptionTransitionObject\", shape=plaintext, fontcolor=\"#B22222\"];\n")
    f.write("        LEG_S [label=\"SyncTransitionObject\", shape=plaintext, fontcolor=\"#2AA198\"];\n")
    f.write("        LEG_M [label=\"MetaTransitionObject\", shape=plaintext, fontcolor=\"#7F8C8D\"];\n")
    f.write("    }\n")

    f.write("}\n")

# Replace gap report with closure report + classification boundary
classification_map = [
    ("L001", "E131", "GateTransitionObject", "gate:handoff:time_validator", "补全每阶段显式time_validator调用"),
    ("L002", "E132", "LoopTransitionObject", "loop:rerun", "补全--rerun命令语义"),
    ("L003", "E133", "SyncTransitionObject", "sync:dependency", "补全previous_output依赖"),
    ("L004", "E134,E135,E136", "Exception/Progress", "exception:escalation + progress:linear", "补全3x timeout fallback链"),
    ("L005", "E137,E138", "Meta/Progress", "meta:annotation + progress:continued", "补全known_issues记录与继续"),
    ("L006", "E139", "SyncTransitionObject", "sync:dependency", "补全VERSION_MANIFEST更新流"),
    ("L007", "E142", "DecisionTransitionObject", "decision:advisory", "补全consultation检查点"),
    ("L008", "E140,E141", "Gate/Progress", "gate:entry:data_consistency + progress:released", "补全results_i.csv制品校验"),
    ("L009", "E143", "GateTransitionObject", "gate:entry:quality", "补全tool-use合规门"),
    ("L010", "E144", "ExceptionTransitionObject", "exception:block", "补全director file-ban阻断"),
    ("L011", "E145", "GateTransitionObject", "gate:entry:quality", "补全外部资源信任边界验证"),
    ("L012", "E146", "GateTransitionObject", "gate:handoff:generic", "补全返工后全员再验证入口"),
]

with out_05i.open("w", encoding="utf-8") as f:
    f.write("# 05i Protocol Completion Classification and Coverage\n\n")
    f.write("Reference baseline: `flow_chart_original/flow_chart_original.dot` + `workspace/2025_C/CLAUDE.md`\n\n")
    f.write("## Classification Boundary (先界定分类)\n\n")
    f.write("All newly补全 protocol edges are constrained to existing v2 taxonomy:\n\n")
    f.write("- `GateTransitionObject`: mandatory validation handoff / quality gates\n")
    f.write("- `LoopTransitionObject`: rerun/retry command loop control\n")
    f.write("- `SyncTransitionObject`: explicit data/state dependency linkage\n")
    f.write("- `ExceptionTransitionObject`: timeout/file-ban escalation blocks\n")
    f.write("- `DecisionTransitionObject`: advisory consultation branching\n")
    f.write("- `ProgressTransitionObject`: protocol continuation/release transitions\n")
    f.write("- `MetaTransitionObject`: governance/documentation linkage\n\n")

    f.write("## Gap-to-Edge Completion Map\n\n")
    f.write("| gap_id | added_edges | classification | secondary_tag | completion_note |\n")
    f.write("|---|---|---|---|---|\n")
    for gid, eids, cls, tag, note in classification_map:
        f.write(f"| {gid} | {eids} | {cls} | {tag} | {note} |\n")

    f.write("\n## Coverage Result\n\n")
    f.write("- Previously identified protocol-level gaps: **12**\n")
    f.write("- Added protocol-completion edges: **16** (`E131`-`E146`)\n")
    f.write(f"- Updated total edge count in `05d`: **{len(rows)}**\n")
    f.write("- Status: **All 12 listed protocol gaps have explicit edge-level representations.**\n")

print(f"Updated {out_05d} (rows={len(rows)})")
print(f"Updated {out_05e}")
print(f"Updated {out_05f}")
print(f"Updated {out_05g}")
print(f"Updated {out_05h}")
print(f"Updated {out_05i}")
