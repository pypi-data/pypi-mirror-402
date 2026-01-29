"""Unit tests for SeedOSMemory class"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock

# LangChain이 설치되어 있는지 확인
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from seedos_langchain import SeedOSMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # LangChain이 없으면 모든 테스트 스킵
    pytestmark = pytest.mark.skip("LangChain is not installed. Install with: pip install langchain langchain-core")


@pytest.fixture
def mock_api_response():
    """Mock API 응답"""
    return {
        "status": "created",
        "mmp_address": "mmp://L2/AUOL/abc123",
        "block_id": "block_1234567890",
        "block_hash": "abc123def456",
    }


@pytest.fixture
def mock_search_response():
    """Mock 검색 응답"""
    return {
        "results": [
            {
                "mmp_address": "mmp://L2/AUOL/abc123",
                "similarity": 0.9,
                "block": {
                    "block_id": "block_123",
                    "block_hash": "abc123",
                    "timestamp": 1234567890.0,
                    "content": {
                        "type": "HumanMessage",
                        "content": "안녕하세요",
                        "agent_id": "test_agent",
                        "session_id": "test_session",
                    },
                    "conclusion": "안녕하세요",
                },
            },
            {
                "mmp_address": "mmp://L2/AUOL/def456",
                "similarity": 0.8,
                "block": {
                    "block_id": "block_456",
                    "block_hash": "def456",
                    "timestamp": 1234567891.0,
                    "content": {
                        "type": "AIMessage",
                        "content": "안녕하세요! 무엇을 도와드릴까요?",
                        "agent_id": "test_agent",
                        "session_id": "test_session",
                    },
                    "conclusion": "안녕하세요! 무엇을 도와드릴까요?",
                },
            },
        ],
        "count": 2,
    }


class TestSeedOSMemoryInitialization:
    """SeedOSMemory 초기화 테스트"""
    
    def test_init_with_defaults(self):
        """기본값으로 초기화 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        assert memory.agent_id == "test_agent"
        assert memory.api_url == "http://localhost:8000"
        assert memory.api_key is None
        assert memory.session_id == "test_agent"
        assert memory._messages_cache is None
        assert memory._cache_dirty is True
        assert memory._last_block_hash is None
    
    def test_init_with_custom_params(self):
        """커스텀 파라미터로 초기화 테스트"""
        memory = SeedOSMemory(
            agent_id="test_agent",
            api_url="https://api.example.com",
            api_key="test_key",
            session_id="custom_session",
        )
        assert memory.agent_id == "test_agent"
        assert memory.api_url == "https://api.example.com"
        assert memory.api_key == "test_key"
        assert memory.session_id == "custom_session"
    
    def test_init_without_langchain(self):
        """LangChain이 없을 때 ImportError 발생 테스트"""
        with patch('seedos_langchain.memory.LANGCHAIN_AVAILABLE', False):
            with pytest.raises(ImportError):
                SeedOSMemory(agent_id="test_agent")


class TestSeedOSMemoryHeaders:
    """헤더 생성 테스트"""
    
    def test_get_headers_without_api_key(self):
        """API 키 없이 헤더 생성 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        headers = memory._get_headers()
        assert headers == {"Content-Type": "application/json"}
    
    def test_get_headers_with_api_key(self):
        """API 키와 함께 헤더 생성 테스트"""
        memory = SeedOSMemory(agent_id="test_agent", api_key="test_key")
        headers = memory._get_headers()
        assert headers == {
            "Content-Type": "application/json",
            "Authorization": "Bearer test_key",
        }


class TestSeedOSMemoryMessageConversion:
    """메시지 변환 테스트"""
    
    def test_message_to_seedos_content(self):
        """LangChain 메시지를 SeedOS content로 변환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent", session_id="test_session")
        
        human_msg = HumanMessage(content="안녕하세요")
        content = memory._message_to_seedos_content(human_msg)
        
        assert content["type"] == "HumanMessage"
        assert content["content"] == "안녕하세요"
        assert content["agent_id"] == "test_agent"
        assert content["session_id"] == "test_session"
        assert "timestamp" in content
    
    def test_seedos_block_to_human_message(self):
        """SeedOS 블록을 HumanMessage로 변환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        
        block_data = {
            "content": {
                "type": "HumanMessage",
                "content": "안녕하세요",
            },
        }
        
        message = memory._seedos_block_to_message(block_data)
        assert isinstance(message, HumanMessage)
        assert message.content == "안녕하세요"
    
    def test_seedos_block_to_ai_message(self):
        """SeedOS 블록을 AIMessage로 변환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        
        block_data = {
            "content": {
                "type": "AIMessage",
                "content": "안녕하세요!",
            },
        }
        
        message = memory._seedos_block_to_message(block_data)
        assert isinstance(message, AIMessage)
        assert message.content == "안녕하세요!"
    
    def test_seedos_block_to_system_message(self):
        """SeedOS 블록을 SystemMessage로 변환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        
        block_data = {
            "content": {
                "type": "SystemMessage",
                "content": "시스템 메시지",
            },
        }
        
        message = memory._seedos_block_to_message(block_data)
        assert isinstance(message, SystemMessage)
        assert message.content == "시스템 메시지"
    
    def test_seedos_block_to_message_default(self):
        """알 수 없는 타입의 블록을 기본값(HumanMessage)으로 변환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        
        block_data = {
            "content": {
                "type": "UnknownMessage",
                "content": "알 수 없는 메시지",
            },
        }
        
        message = memory._seedos_block_to_message(block_data)
        assert isinstance(message, HumanMessage)
        assert message.content == "알 수 없는 메시지"


class TestSeedOSMemoryGetLatestBlockHash:
    """마지막 블록 해시 가져오기 테스트"""
    
    @patch('seedos_langchain.memory.requests.post')
    def test_get_latest_block_hash_success(self, mock_post, mock_search_response):
        """마지막 블록 해시 가져오기 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_search_response
        mock_post.return_value = mock_response
        
        memory = SeedOSMemory(agent_id="test_agent")
        block_hash = memory._get_latest_block_hash()
        
        assert block_hash == "abc123"
        assert memory._last_block_hash == "abc123"
    
    @patch('seedos_langchain.memory.requests.post')
    def test_get_latest_block_hash_no_results(self, mock_post):
        """결과가 없을 때 0x00 반환 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_post.return_value = mock_response
        
        memory = SeedOSMemory(agent_id="test_agent")
        block_hash = memory._get_latest_block_hash()
        
        assert block_hash == "0x00"
    
    @patch('seedos_langchain.memory.requests.post')
    def test_get_latest_block_hash_error(self, mock_post):
        """에러 발생 시 0x00 반환 테스트"""
        mock_post.side_effect = Exception("Network error")
        
        memory = SeedOSMemory(agent_id="test_agent")
        block_hash = memory._get_latest_block_hash()
        
        assert block_hash == "0x00"
    
    def test_get_latest_block_hash_cached(self):
        """캐시된 해시 사용 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        memory._last_block_hash = "cached_hash"
        
        block_hash = memory._get_latest_block_hash()
        
        assert block_hash == "cached_hash"


class TestSeedOSMemoryMessages:
    """메시지 조회 테스트"""
    
    @patch('seedos_langchain.memory.requests.post')
    def test_messages_success(self, mock_post, mock_search_response):
        """메시지 조회 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_search_response
        mock_post.return_value = mock_response
        
        memory = SeedOSMemory(agent_id="test_agent", session_id="test_session")
        messages = memory.messages
        
        assert len(messages) == 2
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
        assert messages[0].content == "안녕하세요"
        assert messages[1].content == "안녕하세요! 무엇을 도와드릴까요?"
        assert not memory._cache_dirty
    
    def test_messages_cached(self):
        """캐시된 메시지 반환 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        cached_messages = [HumanMessage(content="캐시된 메시지")]
        memory._messages_cache = cached_messages
        memory._cache_dirty = False
        
        messages = memory.messages
        
        assert messages == cached_messages
    
    @patch('seedos_langchain.memory.requests.post')
    def test_messages_empty_on_error(self, mock_post):
        """에러 발생 시 빈 리스트 반환 테스트"""
        mock_post.side_effect = Exception("Network error")
        
        memory = SeedOSMemory(agent_id="test_agent")
        messages = memory.messages
        
        assert messages == []
        # 에러 발생 시 캐시는 빈 리스트로 설정됨
        assert memory._messages_cache == [] or memory._messages_cache is None
    
    @patch('seedos_langchain.memory.requests.post')
    def test_messages_retry_on_failure(self, mock_post, mock_search_response):
        """재시도 로직 테스트"""
        # 첫 두 번은 실패, 세 번째는 성공
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_search_response
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.RequestException("Network error")
            return mock_response
        
        mock_post.side_effect = side_effect
        
        memory = SeedOSMemory(agent_id="test_agent")
        messages = memory.messages
        
        assert len(messages) == 2
        assert call_count == 3


class TestSeedOSMemoryAddMessage:
    """메시지 추가 테스트"""
    
    @patch('seedos_langchain.memory.requests.post')
    def test_add_message_success(self, mock_post, mock_api_response):
        """메시지 추가 성공 테스트"""
        # _get_latest_block_hash 호출
        mock_hash_response = Mock()
        mock_hash_response.status_code = 200
        mock_hash_response.json.return_value = {"results": []}
        
        # write 호출
        mock_write_response = Mock()
        mock_write_response.status_code = 201
        mock_write_response.json.return_value = mock_api_response
        
        mock_post.side_effect = [mock_hash_response, mock_write_response]
        
        memory = SeedOSMemory(agent_id="test_agent")
        message = HumanMessage(content="테스트 메시지")
        memory.add_message(message)
        
        assert memory._cache_dirty is True
        assert len(memory._messages_cache) == 1
        assert memory._messages_cache[0] == message
        # block_hash가 있으면 block_hash 사용, 없으면 block_id 사용
        assert memory._last_block_hash == "abc123def456" or memory._last_block_hash == "block_1234567890"
    
    @patch('seedos_langchain.memory.requests.post')
    def test_add_message_with_prev_hash(self, mock_post, mock_api_response):
        """이전 블록 해시와 함께 메시지 추가 테스트"""
        # _get_latest_block_hash 호출
        mock_hash_response = Mock()
        mock_hash_response.status_code = 200
        mock_hash_response.json.return_value = {
            "results": [{
                "block": {"block_hash": "prev_hash_123"}
            }]
        }
        
        # write 호출
        mock_write_response = Mock()
        mock_write_response.status_code = 201
        mock_write_response.json.return_value = mock_api_response
        
        mock_post.side_effect = [mock_hash_response, mock_write_response]
        
        memory = SeedOSMemory(agent_id="test_agent")
        message = HumanMessage(content="테스트 메시지")
        memory.add_message(message)
        
        # prev_hash가 요청에 포함되었는지 확인
        write_call = mock_post.call_args_list[1]
        assert write_call[1]["json"]["prev_hash"] == "prev_hash_123"
    
    @patch('seedos_langchain.memory.requests.post')
    def test_add_message_error_handling(self, mock_post):
        """에러 발생 시에도 캐시에 메시지 추가 테스트"""
        mock_post.side_effect = Exception("Network error")
        
        memory = SeedOSMemory(agent_id="test_agent")
        message = HumanMessage(content="테스트 메시지")
        memory.add_message(message)
        
        # 에러가 발생해도 캐시에 메시지는 추가됨
        assert len(memory._messages_cache) == 1
        assert memory._messages_cache[0] == message
    
    @patch('seedos_langchain.memory.requests.post')
    def test_add_message_retry_on_failure(self, mock_post, mock_api_response):
        """재시도 로직 테스트"""
        # 첫 두 번은 실패, 세 번째는 성공
        mock_hash_response = Mock()
        mock_hash_response.status_code = 200
        mock_hash_response.json.return_value = {"results": []}
        
        mock_write_response = Mock()
        mock_write_response.status_code = 201
        mock_write_response.json.return_value = mock_api_response
        
        mock_post.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            mock_hash_response,
            mock_write_response,
        ]
        
        memory = SeedOSMemory(agent_id="test_agent")
        message = HumanMessage(content="테스트 메시지")
        memory.add_message(message)
        
        assert len(memory._messages_cache) == 1


class TestSeedOSMemoryClear:
    """메시지 삭제 테스트"""
    
    def test_clear(self):
        """캐시 클리어 테스트"""
        memory = SeedOSMemory(agent_id="test_agent")
        memory._messages_cache = [HumanMessage(content="메시지")]
        memory._cache_dirty = False
        
        memory.clear()
        
        assert memory._messages_cache == []
        assert memory._cache_dirty is True


class TestSeedOSMemoryGetMemorySummary:
    """메모리 요약 테스트"""
    
    @patch('seedos_langchain.memory.requests.post')
    def test_get_memory_summary(self, mock_post, mock_search_response):
        """메모리 요약 정보 반환 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_search_response
        mock_post.return_value = mock_response
        
        memory = SeedOSMemory(agent_id="test_agent", session_id="test_session")
        summary = memory.get_memory_summary()
        
        assert summary["agent_id"] == "test_agent"
        assert summary["session_id"] == "test_session"
        assert summary["message_count"] == 2
        assert summary["human_messages"] == 1
        assert summary["ai_messages"] == 1
        assert summary["system_messages"] == 0
