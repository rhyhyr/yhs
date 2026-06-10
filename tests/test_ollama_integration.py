"""
tests/test_ollama_integration.py

Ollama 연동 통합 테스트.
- Ollama 서버가 실행 중이어야 함 (ollama serve)
- 모델이 설치되어 있어야 함 (ollama pull exaone3.5:7.8b)

마킹: @pytest.mark.integration
CI에서 건너뛰려면: pytest -m "not integration"
"""

import importlib
import importlib.util
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 프로젝트 루트 경로 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── conftest가 mock한 neo4j에 .exceptions 서브모듈을 추가한다.
# graph_store.py가 "from neo4j.exceptions import ..." 할 때 실패하지 않도록.
if "neo4j.exceptions" not in sys.modules:
    _exc = types.ModuleType("neo4j.exceptions")
    _exc.ClientError = type("ClientError", (Exception,), {})
    _exc.ServiceUnavailable = type("ServiceUnavailable", (Exception,), {})
    sys.modules["neo4j.exceptions"] = _exc

# ── 실제 모듈이 필요한 항목만 mock에서 해제한다.
# (neo4j, faiss, sentence_transformers 같은 무거운 의존성은 계속 mock 유지)
_UNMOCK = [
    "requests",
    "graph_rag",
    "graph_rag.config",
    "graph_rag.schema",
    "graph_rag.schema.types",
    "graph_rag.llm",
    "graph_rag.llm.ollama_kb_client",
    "graph_rag.llm.gemini_client",
    "graph_rag.llm.openai_client",
    "graph_rag.llm.exaone_kb_client",
]
for _mod in _UNMOCK:
    if _mod in sys.modules and isinstance(sys.modules[_mod], MagicMock):
        del sys.modules[_mod]


# ── extractor.py를 __init__.py 없이 직접 로드 (ingestor→graph_store 체인 우회)
def _load_extractor():
    spec = importlib.util.spec_from_file_location(
        "graph_rag.pipeline.extractor",
        str(ROOT / "graph_rag" / "pipeline" / "extractor.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["graph_rag.pipeline.extractor"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── ollama_runtime_client.py를 agent/__init__.py 체인 없이 직접 로드
def _load_ollama_runtime():
    spec = importlib.util.spec_from_file_location(
        "agent.ollama_runtime_client",
        str(ROOT / "agent" / "ollama_runtime_client.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["agent.ollama_runtime_client"] = mod
    spec.loader.exec_module(mod)
    return mod


TARGET_MODEL = os.environ.get("OLLAMA_MODEL", "exaone3.5:7.8b")
OLLAMA_URL   = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


# ── Ollama 서버/모델 가용성 확인 ─────────────────────────────────────
def _ollama_running() -> bool:
    try:
        import requests as _req
        r = _req.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _model_available(name: str) -> bool:
    try:
        import requests as _req
        r = _req.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        tags = r.json().get("models", [])
        prefix = name.split(":")[0]
        return any(m.get("name", "").startswith(prefix) for m in tags)
    except Exception:
        return False


skip_no_ollama = pytest.mark.skipif(
    not _ollama_running(),
    reason="Ollama 서버가 실행 중이지 않습니다 (ollama serve)",
)
skip_no_model = pytest.mark.skipif(
    not _model_available(TARGET_MODEL),
    reason=f"모델 {TARGET_MODEL}이 설치되어 있지 않습니다 (ollama pull {TARGET_MODEL})",
)


# ════════════════════════════════════════════════════════════════════
# 1. OllamaRuntimeClient 테스트
# ════════════════════════════════════════════════════════════════════

class TestOllamaRuntimeClient:

    @skip_no_ollama
    def test_is_available_returns_true(self):
        """Ollama 서버가 실행 중이면 is_available()은 True."""
        mod = _load_ollama_runtime()
        client = mod.OllamaRuntimeClient()
        assert client.is_available() is True
        client.close()

    @skip_no_ollama
    @skip_no_model
    def test_generate_answer_returns_string(self):
        """간단한 질문에 비어있지 않은 문자열을 반환한다."""
        from agent.ollama_runtime_client import OllamaRuntimeClient
        from graph_rag.schema.types import RetrievalResult

        client = OllamaRuntimeClient()
        dummy_result = RetrievalResult(triples=[], chunks=[], retrieval_method="vector")
        context = "D-2 비자는 학위 과정 유학생을 위한 체류 자격입니다."

        answer = client.generate_answer("D-2 비자가 무엇인가요?", context, dummy_result)
        assert isinstance(answer, str)
        assert len(answer) > 10
        client.close()

    @skip_no_ollama
    @skip_no_model
    def test_generate_answer_no_context_returns_fallback(self):
        """컨텍스트가 비어있으면 안내 문구를 반환한다."""
        from agent.ollama_runtime_client import OllamaRuntimeClient
        from graph_rag.schema.types import RetrievalResult

        client = OllamaRuntimeClient()
        dummy_result = RetrievalResult(triples=[], chunks=[], retrieval_method="no_answer")

        answer = client.generate_answer("아무 질문", "", dummy_result)
        assert "확인할 수 없습니다" in answer or "문의" in answer
        client.close()

    @skip_no_ollama
    @skip_no_model
    def test_normalize_question_returns_string(self):
        """질문 정규화가 문자열을 반환한다."""
        from agent.ollama_runtime_client import OllamaRuntimeClient

        client = OllamaRuntimeClient()
        result = client.normalize_question("비자 늘리기 어떻게 해요?")
        assert isinstance(result, str)
        client.close()

    def test_unavailable_gracefully(self):
        """존재하지 않는 포트면 is_available()이 False를 반환한다."""
        import requests
        mod = _load_ollama_runtime()
        client = mod.OllamaRuntimeClient.__new__(mod.OllamaRuntimeClient)
        client._base_url = "http://localhost:19999"
        client._model = TARGET_MODEL
        client._chat_url = "http://localhost:19999/api/chat"
        client._tags_url = "http://localhost:19999/api/tags"
        client._session = requests.Session()

        assert client.is_available() is False


# ════════════════════════════════════════════════════════════════════
# 2. OllamaKBClient 테스트
# ════════════════════════════════════════════════════════════════════

class TestOllamaKBClient:

    @skip_no_ollama
    @skip_no_model
    def test_extract_returns_dict_with_keys(self):
        """엔티티/관계 추출 결과가 올바른 키를 포함한다."""
        from graph_rag.llm.ollama_kb_client import OllamaKBClient

        client = OllamaKBClient()
        result = client.extract_entities_and_relations(
            "D-2 비자를 연장하려면 건강보험에 가입해야 합니다.",
            source_file="test.pdf",
        )
        assert isinstance(result, dict)
        assert "entities" in result
        assert "relations" in result
        assert isinstance(result["entities"], list)
        assert isinstance(result["relations"], list)

    @skip_no_ollama
    @skip_no_model
    def test_extract_entities_not_empty(self):
        """비자 관련 텍스트에서 최소 1개 이상의 엔티티를 추출한다."""
        from graph_rag.llm.ollama_kb_client import OllamaKBClient

        client = OllamaKBClient()
        result = client.extract_entities_and_relations(
            "외국인 유학생이 D-2 비자에서 D-4 비자로 전환하려면 출입국관리사무소에 신청해야 합니다.",
            source_file="test.pdf",
        )
        assert len(result.get("entities", [])) > 0

    def test_parse_flowchart_image_returns_empty(self, tmp_path):
        """이미지 파싱 미지원 시 빈 결과를 반환한다."""
        from graph_rag.llm.ollama_kb_client import OllamaKBClient

        client = OllamaKBClient()
        fake_img = tmp_path / "test.png"
        fake_img.write_bytes(b"fake")
        result = client.parse_flowchart_image(fake_img)
        assert result == {"entities": [], "relations": []}


# ════════════════════════════════════════════════════════════════════
# 3. 환경변수 라우팅 테스트
# ════════════════════════════════════════════════════════════════════

class TestEnvRouting:

    def test_llm_provider_ollama_loads_correct_client(self, monkeypatch):
        """LLM_PROVIDER=ollama 시 OllamaKBClient가 선택된다."""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")

        ext_mod = _load_extractor()
        # 캐시된 클라이언트 없이 새 인스턴스 생성
        extractor = ext_mod.LLMExtractor()
        client = extractor._get_client()

        from graph_rag.llm.ollama_kb_client import OllamaKBClient
        assert isinstance(client, OllamaKBClient)

    def test_llm_provider_gemini_loads_gemini_client(self, monkeypatch):
        """LLM_PROVIDER=gemini 시 GeminiKBClient가 선택된다."""
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

        # extractor 모듈 캐시 삭제 후 재로드
        sys.modules.pop("graph_rag.pipeline.extractor", None)
        ext_mod = _load_extractor()
        extractor = ext_mod.LLMExtractor()
        client = extractor._get_client()

        from graph_rag.llm.gemini_client import GeminiKBClient
        assert isinstance(client, GeminiKBClient)

    def test_default_provider_is_ollama(self, monkeypatch):
        """LLM_PROVIDER 미설정 시 기본값은 ollama이다."""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        sys.modules.pop("graph_rag.pipeline.extractor", None)
        ext_mod = _load_extractor()
        extractor = ext_mod.LLMExtractor()
        client = extractor._get_client()

        from graph_rag.llm.ollama_kb_client import OllamaKBClient
        assert isinstance(client, OllamaKBClient)
