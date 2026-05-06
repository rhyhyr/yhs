# Inner Source 도입 로드맵

## Inner Source란?

오픈소스 개발 방식(공개 기여, 코드 리뷰, 문서화)을 조직 내부에 적용하는 소프트웨어 개발 전략입니다. 부서 간 사일로를 줄이고 코드 재사용성과 협업 품질을 높입니다.

## 현재 상태 진단

| 항목 | 현황 |
|---|---|
| 버전 관리 | GitHub 사용 중 ✅ |
| 브랜치 전략 | GitHub Flow 적용 중 ✅ |
| 코드 리뷰 | PR 기반 리뷰 운영 중 ✅ |
| 문서화 | README, CONTRIBUTING, Wiki 구축 ✅ |
| 이슈 트래킹 | GitHub Issues + Projects 운영 중 ✅ |
| 내부 공개 범위 | 단일 팀 운영 (개선 필요) |

## 단계별 로드맵

### Phase 1 — 기반 구축 (현재 ~ W8)

- [x] Public 저장소 전환 및 OSS 기본 구조 완성 (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT)
- [x] GitHub Flow 브랜치 전략 적용
- [x] PR 템플릿 및 코드 리뷰 가이드 작성
- [x] Wiki 문서화 (Getting Started, Development Guide, Troubleshooting)
- [x] DORA 메트릭 자동 수집

### Phase 2 — 내부 협업 확대 (W9 ~ W12)

- [ ] CODEOWNERS 파일 설정 → 모듈별 담당자 명시
- [ ] 브랜치 보호 규칙 적용 (main 직접 push 금지, 리뷰 1명 이상 필수)
- [ ] GitHub Discussions 활성화 → RFC 기반 기술 결정 논의
- [ ] ADR 작성 문화 정착 → 주요 결정마다 ADR 등록
- [ ] 이슈 라벨 표준화 및 마일스톤 관리 고도화

### Phase 3 — Inner Source 성숙 (W13 ~ W16)

- [ ] 모듈별 독립 기여 가이드 작성 (agent/, graph_rag/ 등)
- [ ] 기여자 온보딩 프로세스 표준화
- [ ] 회귀 테스트 자동화로 안전한 외부 기여 수용
- [ ] 주간 요약 워크플로우로 팀 전체 가시성 확보
- [ ] Inner Source 지표 측정: 외부 기여 PR 수, 리뷰 응답 시간, 문서 활용률

## 기대 효과

| 효과 | 설명 |
|---|---|
| 코드 재사용성 향상 | 모듈화된 구조로 다른 팀도 활용 가능 |
| 기술 부채 감소 | 코드 리뷰와 ADR로 결정 근거 추적 가능 |
| 온보딩 시간 단축 | 문서화된 가이드로 새 기여자 빠르게 합류 |
| 투명한 의사결정 | RFC + ADR로 기술 결정 과정 공개 |
| 품질 향상 | DORA 메트릭 기반 지속적 개선 |

## 참고 자료

- [InnerSource Commons](https://innersourcecommons.org/)
- [GitHub InnerSource Guide](https://resources.github.com/innersource/fundamentals/)

---

> 📝 이 문서는 작성 과정에서 생성형 AI(Claude)의 도움을 받아 작성되었습니다.
