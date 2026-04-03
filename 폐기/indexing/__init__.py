"""indexing 패키지 공개 진입점.

역할:
- 외부에서 필요한 최소 객체(PDF_DIR, IndexingPipeline)만 노출
- 실행 파일은 이 패키지를 import 해서 파이프라인을 시작
"""

from .config import PDF_DIR
from .pipeline import IndexingPipeline

__all__ = ["PDF_DIR", "IndexingPipeline"]
