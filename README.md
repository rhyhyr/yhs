## 🐳 Docker 기반 배포 파이프라인 전략

### ai로 작성한 문서입니다
본 프로젝트는 GitHub Actions와 GitHub Container Registry(GHCR), 그리고 클라우드 컨테이너 서비스(GCP Cloud Run)를 활용하여 완전 자동화된 무중단 배포(CI/CD) 파이프라인을 구축합니다.

### 🔄 전체 배포 흐름도 (Pipeline Flow)

[Local 개발 환경] 
   └── 1. Git Push (main 브랜치)
        ⬇️
[GitHub Repository]
   └── 2. GitHub Actions 워크플로우 자동 트리거
        ⬇️
[CI: Build & Test]
   └── 3. Dockerfile을 기반으로 최신 컨테이너 이미지 빌드
        ⬇️
[Registry: Push]
   └── 4. 빌드된 이미지를 GHCR (GitHub Container Registry)에 업로드 및 태깅 (latest)
        ⬇️
[CD: Deploy (서버리스 클라우드)]
   └── 5. GCP Cloud Run이 GHCR의 최신 이미지를 Pull 받아 새로운 컨테이너 인스턴스 실행
        ⬇️
[Monitoring]
   └── 6. /health 엔드포인트를 통한 주기적인 상태 점검(Health Check) 및 정상 트래픽 전환 (무중단 배포)

### 🛡️ 핵심 설계 포인트
1. **일관성 확보:** 환경 불일치 문제를 해결하기 위해 Node.js/Python 실행 환경을 Docker 이미지로 완전히 패키징합니다.
2. **보안성:** 암호 및 인증 정보는 GitHub Secrets에 안전하게 보관하여 코드에 노출되지 않도록 주입합니다.
3. **효율성 및 비용 절감:** 트래픽이 없을 때는 컨테이너를 0개로 축소(Scale-to-Zero)하는 서버리스 환경(Cloud Run)을 타겟으로 하여 리소스 낭비를 방지합니다.