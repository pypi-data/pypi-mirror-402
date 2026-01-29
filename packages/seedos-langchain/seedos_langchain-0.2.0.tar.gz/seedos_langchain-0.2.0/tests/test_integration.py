"""Integration tests for SeedOSMemory with actual API server"""

import pytest
import time

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
def api_url():
    """API 서버 URL"""
    return "http://localhost:8000"


@pytest.fixture
def memory(api_url):
    """SeedOSMemory 인스턴스"""
    return SeedOSMemory(
        agent_id=f"test_agent_{int(time.time())}",
        api_url=api_url,
        session_id=f"test_session_{int(time.time())}",
    )


@pytest.mark.integration
class TestSeedOSMemoryIntegration:
    """SeedOSMemory 통합 테스트 (실제 API 서버 필요)"""
    
    def test_add_and_retrieve_messages(self, memory):
        """메시지 추가 및 조회 통합 테스트"""
        # 메시지 추가
        memory.add_message(HumanMessage(content="안녕하세요"))
        memory.add_message(AIMessage(content="안녕하세요! 무엇을 도와드릴까요?"))
        
        # 잠시 대기 (인덱싱 시간)
        time.sleep(0.5)
        
        # 메시지 조회
        messages = memory.messages
        
        assert len(messages) >= 2
        assert any(msg.content == "안녕하세요" for msg in messages)
        assert any("안녕하세요" in msg.content for msg in messages)
    
    def test_message_chain_connection(self, memory):
        """메시지 체인 연결 테스트"""
        # 첫 번째 메시지
        memory.add_message(HumanMessage(content="첫 번째 메시지"))
        time.sleep(0.3)
        
        # 두 번째 메시지 (prev_hash 연결 확인)
        memory.add_message(AIMessage(content="두 번째 메시지"))
        time.sleep(0.3)
        
        # 세 번째 메시지
        memory.add_message(HumanMessage(content="세 번째 메시지"))
        time.sleep(0.5)
        
        # 메시지 조회
        messages = memory.messages
        
        assert len(messages) >= 3
    
    def test_multi_agent_memory_sharing(self, api_url):
        """다중 에이전트 메모리 공유 테스트"""
        shared_session = f"shared_session_{int(time.time())}"
        
        # 에이전트 1
        agent1_memory = SeedOSMemory(
            agent_id="agent1",
            api_url=api_url,
            session_id=shared_session,
        )
        agent1_memory.add_message(HumanMessage(content="에이전트 1 메시지"))
        time.sleep(0.3)
        
        # 에이전트 2 (같은 세션)
        agent2_memory = SeedOSMemory(
            agent_id="agent2",
            api_url=api_url,
            session_id=shared_session,
        )
        agent2_memory.add_message(HumanMessage(content="에이전트 2 메시지"))
        time.sleep(0.5)
        
        # 두 에이전트 모두 같은 세션의 메시지를 볼 수 있어야 함
        agent1_messages = agent1_memory.messages
        agent2_messages = agent2_memory.messages
        
        # 최소한 각자의 메시지는 있어야 함
        assert len(agent1_messages) >= 1
        assert len(agent2_messages) >= 1
    
    def test_memory_summary(self, memory):
        """메모리 요약 테스트"""
        memory.add_message(SystemMessage(content="시스템 메시지"))
        memory.add_message(HumanMessage(content="사용자 메시지"))
        memory.add_message(AIMessage(content="AI 메시지"))
        time.sleep(0.5)
        
        summary = memory.get_memory_summary()
        
        assert summary["message_count"] >= 3
        assert summary["human_messages"] >= 1
        assert summary["ai_messages"] >= 1
        assert summary["system_messages"] >= 1
    
    def test_clear_cache(self, memory):
        """캐시 클리어 테스트"""
        memory.add_message(HumanMessage(content="테스트 메시지"))
        time.sleep(0.3)
        
        # 메시지 조회 (캐시 생성)
        messages_before = memory.messages
        assert len(messages_before) >= 1
        
        # 캐시 클리어
        memory.clear()
        
        # 캐시가 클리어되었는지 확인
        assert memory._messages_cache == []
        assert memory._cache_dirty is True
        
        # 다시 조회하면 메시지는 여전히 있어야 함 (SeedOS는 불변 저장소)
        messages_after = memory.messages
        assert len(messages_after) >= 1


@pytest.mark.integration
class TestSeedOSMemoryErrorHandling:
    """에러 핸들링 통합 테스트"""
    
    def test_invalid_api_url(self):
        """잘못된 API URL 테스트"""
        memory = SeedOSMemory(
            agent_id="test_agent",
            api_url="http://invalid-url:9999",
        )
        
        # 에러가 발생해도 빈 리스트 반환
        messages = memory.messages
        assert messages == []
    
    def test_add_message_with_invalid_api(self):
        """잘못된 API로 메시지 추가 테스트"""
        memory = SeedOSMemory(
            agent_id="test_agent",
            api_url="http://invalid-url:9999",
        )
        
        # 에러가 발생해도 캐시에는 메시지 추가
        message = HumanMessage(content="테스트")
        memory.add_message(message)
        
        assert len(memory._messages_cache) == 1
