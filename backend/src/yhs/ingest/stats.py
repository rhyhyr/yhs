"""
yhs/ingest/stats.py

인제스트 한 번 동안의 성공·실패 집계.

왜 필요한가:
    이 파이프라인은 실패를 삼키는 지점이 많다. LLM 로딩이 실패해도 규칙 기반
    폴백이 동작하고, 파싱이 실패해도 그 항목만 건너뛰고, 관계 저장은 Cypher
    MATCH 가 0행이면 예외 없이 그냥 아무 일도 일어나지 않는다.

    그래서 인제스트가 "정상 종료" 하고도 관계가 0건일 수 있다. 실제로
    그런 일이 네 번 있었다 — PDF 경로 오인, HF 캐시 권한, 모델 호환성,
    C 컴파일러 부재. 전부 로그를 뒤지기 전에는 알 수 없었다.

    요약을 마지막에 강제로 출력해서, 조용한 실패가 조용히 지나가지 않게 한다.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class IngestStats:
    """인제스트 실행 1회의 집계. 모듈 전역 싱글턴으로 쓴다."""

    # ── LLM 호출 ────────────────────────────────────────────────────────
    llm_success_chunks: int = 0
    llm_failed_chunks: int = 0
    llm_error_kinds: Counter = field(default_factory=Counter)

    # ── 파싱 ────────────────────────────────────────────────────────────
    parsed_entities: int = 0
    parsed_relations: int = 0
    entity_parse_failed: int = 0
    relation_parse_failed: int = 0
    entity_fail_reasons: Counter = field(default_factory=Counter)
    relation_fail_reasons: Counter = field(default_factory=Counter)

    # ── predicate 정책 ──────────────────────────────────────────────────
    predicate_seen: Counter = field(default_factory=Counter)
    predicate_rejected: int = 0
    rejected_predicates: Counter = field(default_factory=Counter)

    # ── 검증(validation.py) ─────────────────────────────────────────────
    chunk_types: Counter = field(default_factory=Counter)
    entity_type_invalid: int = 0
    invalid_entity_types: Counter = field(default_factory=Counter)
    entity_blocked: int = 0
    entity_block_reasons: Counter = field(default_factory=Counter)
    entity_name_merged: int = 0
    relation_orphan_endpoint: int = 0
    orphan_endpoint_names: Counter = field(default_factory=Counter)
    relation_descriptive_blocked: int = 0
    descriptive_blocked_samples: list = field(default_factory=list)
    relation_type_mismatch: int = 0
    type_mismatch_samples: list = field(default_factory=list)
    relation_no_evidence: int = 0
    chunk_type_unknown: int = 0
    unknown_chunk_types: Counter = field(default_factory=Counter)
    json_repaired: int = 0
    chunk_retried: int = 0
    retry_succeeded: int = 0

    # ── 병합/적재 ───────────────────────────────────────────────────────
    rule_entities: int = 0
    merged_entities: int = 0          # 정규화·중복 제거 후 실제 적재 대상
    dropped_entities: int = 0         # 식별자를 못 만들어 버린 것
    stored_relations: int = 0
    relation_match_failed: int = 0    # 양 끝 엔티티가 없어 저장 못 한 관계
    match_failed_samples: list = field(default_factory=list)

    def reset(self) -> None:
        self.__init__()  # type: ignore[misc]

    # ── 요약 출력 ───────────────────────────────────────────────────────
    def summary_lines(self) -> list[str]:
        ent_keep = (
            f"{self.merged_entities}/{self.parsed_entities + self.rule_entities}"
            if (self.parsed_entities + self.rule_entities) else "0/0"
        )
        rel_keep = (
            f"{self.stored_relations}/{self.parsed_relations}"
            if self.parsed_relations else "0/0"
        )
        lines = [
            "── 인제스트 집계 ───────────────────────────────────────────",
            f"  LLM 호출        성공 {self.llm_success_chunks}청크 / "
            f"실패 {self.llm_failed_chunks}청크",
        ]
        if self.llm_error_kinds:
            lines.append(f"    실패 유형     {dict(self.llm_error_kinds)}")

        lines += [
            f"  파싱            엔티티 {self.parsed_entities} "
            f"(실패 {self.entity_parse_failed}) / "
            f"관계 {self.parsed_relations} (실패 {self.relation_parse_failed})",
        ]
        if self.entity_fail_reasons:
            lines.append(f"    엔티티 실패   {dict(self.entity_fail_reasons)}")
        if self.relation_fail_reasons:
            lines.append(f"    관계 실패     {dict(self.relation_fail_reasons)}")

        lines += [
            f"  predicate       채택 {sum(self.predicate_seen.values())} / "
            f"폐기 {self.predicate_rejected}",
        ]
        if self.predicate_seen:
            top = ", ".join(f"{k}:{v}" for k, v in self.predicate_seen.most_common())
            lines.append(f"    채택 분포     {top}")
        if self.rejected_predicates:
            top = ", ".join(f"{k}:{v}" for k, v in self.rejected_predicates.most_common(10))
            lines.append(f"    폐기 목록     {top}")

        if self.chunk_types:
            top = ", ".join(f"{k}:{v}" for k, v in self.chunk_types.most_common())
            lines.append(f"  문단 유형       {top}")

        lines.append(
            f"  검증 폐기       엔티티 {self.entity_blocked}"
            f"(타입무효 {self.entity_type_invalid}, 표기병합 {self.entity_name_merged})"
            f" / 관계 endpoint누락 {self.relation_orphan_endpoint}"
            f", 설명문단차단 {self.relation_descriptive_blocked}"
            f", 타입불일치 {self.relation_type_mismatch}"
            f", 근거없음 {self.relation_no_evidence}"
        )
        if self.chunk_type_unknown:
            lines.append(
                f"    chunk_type    목록 밖 {self.chunk_type_unknown}건 "
                f"{dict(self.unknown_chunk_types)} → descriptive 로 처리")
        if self.json_repaired or self.chunk_retried:
            lines.append(
                f"    복구/재시도   JSON 복구 {self.json_repaired}, "
                f"청크 재시도 {self.chunk_retried} (성공 {self.retry_succeeded})")
        if self.entity_block_reasons:
            lines.append(f"    엔티티 차단   {dict(self.entity_block_reasons)}")
        if self.type_mismatch_samples:
            lines.append("    타입 불일치 예시")
            for s in self.type_mismatch_samples:
                lines.append(f"      {s}")
        if self.descriptive_blocked_samples:
            lines.append("    설명문단 차단 예시")
            for s in self.descriptive_blocked_samples:
                lines.append(f"      {s}")

        lines += [
            f"  엔티티 유지율   {ent_keep}  (규칙 {self.rule_entities} + "
            f"LLM {self.parsed_entities} → 병합 {self.merged_entities}, "
            f"버림 {self.dropped_entities})",
            f"  관계 유지율     {rel_keep}  "
            f"(엔티티 부재로 저장 실패 {self.relation_match_failed})",
        ]
        if self.match_failed_samples:
            lines.append("    저장 실패 예시")
            for s in self.match_failed_samples[:5]:
                lines.append(f"      {s}")
        lines.append("───────────────────────────────────────────────────────────")
        return lines

    def has_problems(self) -> bool:
        return bool(
            self.llm_failed_chunks
            or self.entity_parse_failed
            or self.relation_parse_failed
            or self.predicate_rejected
            or self.relation_match_failed
            or self.relation_orphan_endpoint
            or self.relation_type_mismatch
        )


# 인제스트 실행 1회당 하나. runner 가 시작할 때 reset() 한다.
STATS = IngestStats()
