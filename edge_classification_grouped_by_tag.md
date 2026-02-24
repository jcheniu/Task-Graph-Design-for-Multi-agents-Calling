# 05g Edge Classification (Grouped by v2_secondary_tag)

Data source: `05d_edge_reclassification_v2.csv` (protocol-completed)

Total edges: **146**

## Primary Class Distribution

- `GateTransitionObject`: **44**
- `ProgressTransitionObject`: **42**
- `DecisionTransitionObject`: **13**
- `ExceptionTransitionObject`: **12**
- `LoopTransitionObject`: **10**
- `MetaTransitionObject`: **9**
- `RollbackTransitionObject`: **9**
- `SyncTransitionObject`: **7**

## Secondary Tag Distribution

- `progress:linear`: **31**
- `gate:hook:time`: **28**
- `exception:block`: **9**
- `progress:released`: **9**
- `meta:suggestion_ingress`: **7**
- `decision:dispatch`: **5**
- `gate:entry:editor_review`: **5**
- `decision:advisory`: **4**
- `rollback:dispatch`: **4**
- `rollback:return`: **4**
- `sync:dependency`: **4**
- `decision:judging`: **3**
- `loop:generic`: **3**
- `sync:join`: **3**
- `exception:escalation`: **2**
- `gate:entry:data_consistency`: **2**
- `gate:entry:quality`: **2**
- `gate:handoff:time_validator`: **2**
- `loop:fix`: **2**
- `loop:rerun`: **2**
- `meta:annotation`: **2**
- `progress:continued`: **2**
- `decision:emergency`: **1**
- `exception:bypass`: **1**
- `gate:entry:asset`: **1**
- `gate:entry:compile`: **1**
- `gate:entry:mock_judging`: **1**
- `gate:handoff:generic`: **1**
- `gate:rejoin:time`: **1**
- `loop:reject_cycle`: **1**
- `loop:retry`: **1**
- `loop:revision`: **1**
- `rollback:trigger`: **1**

## decision:advisory

- Primary class: `DecisionTransitionObject`
- Edge count: **4**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E047 | SUG->DM |  | DecisionTransitionObject | neutral | flow_chart_original.dot:92 |
| E048 | DM->PAUSE | Accept | DecisionTransitionObject | neutral | flow_chart_original.dot:93 |
| E049 | DM->TG | Reject | DecisionTransitionObject | negative | flow_chart_original.dot:94 |
| E142 | CONT->CONSULT | consultation checkpoint | DecisionTransitionObject | neutral | workspace/2025_C/CLAUDE.md:24 |

## decision:dispatch

- Primary class: `DecisionTransitionObject`
- Edge count: **5**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E057 | P5->D5 |  | DecisionTransitionObject | neutral | flow_chart_original.dot:114 |
| E058 | D5->I5 |  | DecisionTransitionObject | neutral | flow_chart_original.dot:115 |
| E059 | D5->S5 |  | DecisionTransitionObject | neutral | flow_chart_original.dot:116 |
| E060 | D5->M5 |  | DecisionTransitionObject | neutral | flow_chart_original.dot:117 |
| E068 | EM->D5 | No | DecisionTransitionObject | negative | flow_chart_original.dot:129 |

## decision:emergency

- Primary class: `DecisionTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E065 | P5->EM |  | DecisionTransitionObject | neutral | flow_chart_original.dot:126 |

## decision:judging

- Primary class: `DecisionTransitionObject`
- Edge count: **3**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E093 | DEF->J1 | No | DecisionTransitionObject | negative | flow_chart_original.dot:185 |
| E095 | J1->J2 | No | DecisionTransitionObject | negative | flow_chart_original.dot:187 |
| E098 | J2->J3 | No | DecisionTransitionObject | negative | flow_chart_original.dot:190 |

## exception:block

- Primary class: `ExceptionTransitionObject`
- Edge count: **9**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E028 | TG->RR | No | ExceptionTransitionObject | negative | flow_chart_original.dot:55 |
| E031 | TV->RR | REJECT | ExceptionTransitionObject | negative | flow_chart_original.dot:58 |
| E070 | APC->VFIX | No | ExceptionTransitionObject | negative | flow_chart_original.dot:135 |
| E078 | EDR->WREV | No | ExceptionTransitionObject | negative | flow_chart_original.dot:149 |
| E081 | CMP->RET | No, 可修复 | ExceptionTransitionObject | negative | flow_chart_original.dot:158 |
| E087 | DC->FIX | No | ExceptionTransitionObject | negative | flow_chart_original.dot:169 |
| E091 | DEF->RJ | Yes(自动拒绝) | ExceptionTransitionObject | negative | flow_chart_original.dot:183 |
| E094 | J1->RJ | Yes | ExceptionTransitionObject | negative | flow_chart_original.dot:186 |
| E144 | DIRECTOR->FILE_BAN | read-ban enforcement | ExceptionTransitionObject | negative | workspace/2025_C/CLAUDE.md:126 |

## exception:bypass

- Primary class: `ExceptionTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E066 | EM->BP | Yes | ExceptionTransitionObject | negative | flow_chart_original.dot:127 |

## exception:escalation

- Primary class: `ExceptionTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E083 | CMP->ESC | No, 环境问题 | ExceptionTransitionObject | negative | flow_chart_original.dot:160 |
| E134 | TIMEOUT3->ALT | 3x timeout | ExceptionTransitionObject | negative | workspace/2025_C/CLAUDE.md:102 |

## gate:entry:asset

- Primary class: `GateTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E069 | P65->APC |  | GateTransitionObject | neutral | flow_chart_original.dot:134 |

## gate:entry:compile

- Primary class: `GateTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E080 | P7F->CMP |  | GateTransitionObject | neutral | flow_chart_original.dot:157 |

## gate:entry:data_consistency

- Primary class: `GateTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E086 | P75->DC |  | GateTransitionObject | neutral | flow_chart_original.dot:168 |
| E140 | W5->ARTIFACT_CHECK | results_i.csv exists? | GateTransitionObject | neutral | workspace/2025_C/CLAUDE.md:101 |

## gate:entry:editor_review

- Primary class: `GateTransitionObject`
- Edge count: **5**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E073 | P7A->EDR |  | GateTransitionObject | neutral | flow_chart_original.dot:143 |
| E074 | P7B->EDR |  | GateTransitionObject | neutral | flow_chart_original.dot:144 |
| E075 | P7C->EDR |  | GateTransitionObject | neutral | flow_chart_original.dot:145 |
| E076 | P7D->EDR |  | GateTransitionObject | neutral | flow_chart_original.dot:146 |
| E077 | P7E->EDR |  | GateTransitionObject | neutral | flow_chart_original.dot:147 |

## gate:entry:mock_judging

- Primary class: `GateTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E090 | P91->DEF |  | GateTransitionObject | neutral | flow_chart_original.dot:182 |

## gate:entry:quality

- Primary class: `GateTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E143 | AGENT_RUN->TOOL_AUDIT | 0 tool uses? | GateTransitionObject | neutral | workspace/2025_C/CLAUDE.md:130 |
| E145 | EXT_RES->TRUST_VERIFY | must verify independently | GateTransitionObject | neutral | workspace/2025_C/CLAUDE.md:122 |

## gate:handoff:generic

- Primary class: `GateTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E146 | REWORK_DONE->REVERIFY_ALL | all agents re-verify | GateTransitionObject | neutral | workspace/2025_C/CLAUDE.md:134 |

## gate:handoff:time_validator

- Primary class: `GateTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E030 | TG->TV | Yes | GateTransitionObject | positive | flow_chart_original.dot:57 |
| E131 | TG->TV_CALL | per-phase validation | GateTransitionObject | positive | workspace/2025_C/CLAUDE.md:117 |

## gate:hook:time

- Primary class: `GateTransitionObject`
- Edge count: **28**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E102 | P0->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:196 |
| E103 | P01->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:197 |
| E104 | P02->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:198 |
| E105 | P05->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:199 |
| E106 | P1->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:200 |
| E107 | P15->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:201 |
| E108 | P2->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:202 |
| E109 | P3->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:203 |
| E110 | P4->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:204 |
| E111 | P45->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:205 |
| E112 | P5->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:206 |
| E113 | P55->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:207 |
| E114 | P58->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:208 |
| E115 | P6->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:209 |
| E116 | P65->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:210 |
| E117 | P7A->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:211 |
| E118 | P7B->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:212 |
| E119 | P7C->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:213 |
| E120 | P7D->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:214 |
| E121 | P7E->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:215 |
| E122 | P7F->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:216 |
| E123 | P75->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:217 |
| E124 | P8->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:218 |
| E125 | P9->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:219 |
| E126 | P91->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:220 |
| E127 | P95->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:221 |
| E128 | P10->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:222 |
| E129 | P11->TG |  | GateTransitionObject | neutral | flow_chart_original.dot:223 |

## gate:rejoin:time

- Primary class: `GateTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E046 | RESUME->TG | 回到时间门禁 | GateTransitionObject | neutral | flow_chart_original.dot:87 |

## loop:fix

- Primary class: `LoopTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E071 | VFIX->APC | 循环 | LoopTransitionObject | neutral | flow_chart_original.dot:136 |
| E088 | FIX->P75 | 循环 | LoopTransitionObject | neutral | flow_chart_original.dot:170 |

## loop:generic

- Primary class: `LoopTransitionObject`
- Edge count: **3**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E067 | BP->P5 | 回到训练 | LoopTransitionObject | neutral | flow_chart_original.dot:128 |
| E084 | ESC->CMP |  | LoopTransitionObject | neutral | flow_chart_original.dot:161 |
| E092 | RJ->P91 |  | LoopTransitionObject | neutral | flow_chart_original.dot:184 |

## loop:reject_cycle

- Primary class: `LoopTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E101 | J3->RJ | No | LoopTransitionObject | neutral | flow_chart_original.dot:193 |

## loop:rerun

- Primary class: `LoopTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E029 | RR->TG | 循环 | LoopTransitionObject | neutral | flow_chart_original.dot:56 |
| E132 | RR->RERUN_CMD | --rerun | LoopTransitionObject | neutral | workspace/2025_C/CLAUDE.md:153 |

## loop:retry

- Primary class: `LoopTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E082 | RET->CMP |  | LoopTransitionObject | neutral | flow_chart_original.dot:159 |

## loop:revision

- Primary class: `LoopTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E079 | WREV->EDR | 重复审查 | LoopTransitionObject | neutral | flow_chart_original.dot:150 |

## meta:annotation

- Primary class: `MetaTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E130 | NOTE->P0 |  | MetaTransitionObject | neutral | flow_chart_original.dot:227 |
| E137 | ANY_PHASE->KNOWN_ISSUES | log issue | MetaTransitionObject | neutral | workspace/2025_C/CLAUDE.md:103 |

## meta:suggestion_ingress

- Primary class: `MetaTransitionObject`
- Edge count: **7**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E050 | CT->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E051 | DE->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E052 | FC->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E053 | MT->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E054 | VZ->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E055 | WR->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |
| E056 | AD->SUG |  | MetaTransitionObject | neutral | flow_chart_original.dot:105 |

## progress:continued

- Primary class: `ProgressTransitionObject`
- Edge count: **2**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E037 | VR->CONT | No | ProgressTransitionObject | positive | flow_chart_original.dot:78 |
| E138 | KNOWN_ISSUES->CONT | workaround+continue | ProgressTransitionObject | positive | workspace/2025_C/CLAUDE.md:103 |

## progress:linear

- Primary class: `ProgressTransitionObject`
- Edge count: **31**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E001 | P0->P01 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E002 | P01->P02 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E003 | P02->P05 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E004 | P05->P1 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E005 | P1->P15 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E006 | P15->P2 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E007 | P2->P3 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E008 | P3->P4 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E009 | P4->P45 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E010 | P45->P5 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E011 | P5->P55 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E012 | P55->P58 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E013 | P58->P6 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E014 | P6->P65 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E015 | P65->P7A |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E016 | P7A->P7B |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E017 | P7B->P7C |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E018 | P7C->P7D |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E019 | P7D->P7E |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E020 | P7E->P7F |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E021 | P7F->P75 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E022 | P75->P8 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E023 | P8->P9 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E024 | P9->P91 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E025 | P91->P95 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E026 | P95->P10 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E027 | P10->P11 |  | ProgressTransitionObject | positive | flow_chart_original.dot:47 |
| E097 | PP->P95 |  | ProgressTransitionObject | positive | flow_chart_original.dot:189 |
| E100 | FP->P95 |  | ProgressTransitionObject | positive | flow_chart_original.dot:192 |
| E135 | ALT->SIMPLE | fallback | ProgressTransitionObject | positive | workspace/2025_C/CLAUDE.md:102 |
| E136 | SIMPLE->CHUNK | fallback | ProgressTransitionObject | positive | workspace/2025_C/CLAUDE.md:102 |

## progress:released

- Primary class: `ProgressTransitionObject`
- Edge count: **9**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E032 | TV->NX | APPROVE | ProgressTransitionObject | positive | flow_chart_original.dot:59 |
| E033 | NX->CONT |  | ProgressTransitionObject | positive | flow_chart_original.dot:60 |
| E064 | W5->P55 |  | ProgressTransitionObject | positive | flow_chart_original.dot:121 |
| E072 | APC->P7A | Yes | ProgressTransitionObject | positive | flow_chart_original.dot:137 |
| E085 | CMP->P75 | Yes | ProgressTransitionObject | positive | flow_chart_original.dot:162 |
| E089 | DC->P8 | Yes | ProgressTransitionObject | positive | flow_chart_original.dot:171 |
| E096 | J2->PP | Yes | ProgressTransitionObject | positive | flow_chart_original.dot:188 |
| E099 | J3->FP | Yes | ProgressTransitionObject | positive | flow_chart_original.dot:191 |
| E141 | ARTIFACT_CHECK->P55 | all present | ProgressTransitionObject | positive | workspace/2025_C/CLAUDE.md:101 |

## rollback:dispatch

- Primary class: `RollbackTransitionObject`
- Edge count: **4**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E038 | PAUSE->RW1 |  | RollbackTransitionObject | negative | flow_chart_original.dot:79 |
| E039 | PAUSE->RW3 |  | RollbackTransitionObject | negative | flow_chart_original.dot:80 |
| E040 | PAUSE->RW4 |  | RollbackTransitionObject | negative | flow_chart_original.dot:81 |
| E041 | PAUSE->RW5 |  | RollbackTransitionObject | negative | flow_chart_original.dot:82 |

## rollback:return

- Primary class: `RollbackTransitionObject`
- Edge count: **4**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E042 | RW1->RESUME |  | RollbackTransitionObject | negative | flow_chart_original.dot:83 |
| E043 | RW3->RESUME |  | RollbackTransitionObject | negative | flow_chart_original.dot:84 |
| E044 | RW4->RESUME |  | RollbackTransitionObject | negative | flow_chart_original.dot:85 |
| E045 | RW5->RESUME |  | RollbackTransitionObject | negative | flow_chart_original.dot:86 |

## rollback:trigger

- Primary class: `RollbackTransitionObject`
- Edge count: **1**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E036 | VR->PAUSE | Yes | RollbackTransitionObject | negative | flow_chart_original.dot:77 |

## sync:dependency

- Primary class: `SyncTransitionObject`
- Edge count: **4**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E034 | P01->B01 |  | SyncTransitionObject | neutral | flow_chart_original.dot:64 |
| E035 | B01->P02 | 解锁后 | SyncTransitionObject | neutral | flow_chart_original.dot:65 |
| E133 | RERUN_CMD->PREV_OUT | read previous_output | SyncTransitionObject | neutral | workspace/2025_C/CLAUDE.md:154 |
| E139 | P7F->MANIFEST7 | update VERSION_MANIFEST | SyncTransitionObject | neutral | workspace/2025_C/CLAUDE.md:124 |

## sync:join

- Primary class: `SyncTransitionObject`
- Edge count: **3**

| edge_id | edge_signature | label | primary | polarity | evidence |
|---|---|---|---|---|---|
| E061 | I5->W5 |  | SyncTransitionObject | neutral | flow_chart_original.dot:118 |
| E062 | S5->W5 |  | SyncTransitionObject | neutral | flow_chart_original.dot:119 |
| E063 | M5->W5 |  | SyncTransitionObject | neutral | flow_chart_original.dot:120 |
