"""SeedOS Memory for LangChain

LangChain의 BaseChatMessageHistory를 상속받아 SeedOS를 메모리로 사용합니다.

v0.2: prev_hash 연결 개선, 에러 핸들링 강화
"""

from __future__ import annotations

import json
import time
from typing import List, Optional, Dict, Any
import requests
from datetime import datetime

try:
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback for when LangChain is not installed
    BaseChatMessageHistory = object
    BaseMessage = object
    HumanMessage = object
    AIMessage = object
    SystemMessage = object


class SeedOSMemory(BaseChatMessageHistory):
    """SeedOS를 LangChain의 ChatMessageHistory로 사용
    
    SeedOS API를 통해 대화 기록을 저장하고 조회합니다.
    
    Args:
        agent_id: 에이전트/사용자 고유 ID
        api_url: SeedOS API 서버 URL (기본값: http://localhost:8000)
        api_key: API 인증 키 (선택적)
        session_id: 세션 ID (선택적, agent_id와 함께 사용)
    """
    
    def __init__(
        self,
        agent_id: str,
        api_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is required. Install it with: pip install langchain langchain-core"
            )
        
        super().__init__()
        self.agent_id = agent_id
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.session_id = session_id or agent_id
        
        # 메모리 캐시 (성능 최적화)
        self._messages_cache: Optional[List[BaseMessage]] = None
        self._cache_dirty = True
        
        # 마지막 블록 해시 캐시 (체인 연결 최적화)
        self._last_block_hash: Optional[str] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _message_to_seedos_content(self, message: BaseMessage) -> Dict[str, Any]:
        """LangChain 메시지를 SeedOS 블록 content로 변환"""
        return {
            "type": message.__class__.__name__,
            "content": message.content,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _seedos_block_to_message(self, block_data: Dict[str, Any]) -> BaseMessage:
        """SeedOS 블록을 LangChain 메시지로 변환"""
        content = block_data.get("content", {})
        message_type = content.get("type", "HumanMessage")
        message_content = content.get("content", "")
        
        if message_type == "HumanMessage":
            return HumanMessage(content=message_content)
        elif message_type == "AIMessage":
            return AIMessage(content=message_content)
        elif message_type == "SystemMessage":
            return SystemMessage(content=message_content)
        else:
            # 기본값은 HumanMessage
            return HumanMessage(content=message_content)
    
    @property
    def messages(self) -> List[BaseMessage]:
        """저장된 메시지 목록 조회"""
        if not self._cache_dirty and self._messages_cache is not None:
            return self._messages_cache
        
        try:
            # SeedOS에서 해당 agent_id의 메모리 검색
            search_url = f"{self.api_url}/search"
            search_payload = {
                "query": f"agent_id:{self.agent_id} session_id:{self.session_id}",
                "top_k": 100,  # 최대 100개 메시지
                "min_similarity": 0.0,
            }
            
            # 재시도 로직 (최대 3회)
            max_retries = 3
            retry_delay = 1.0
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        search_url,
                        json=search_payload,
                        headers=self._get_headers(),
                        timeout=10,
                    )
                    break  # 성공 시 루프 종료
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
                        continue
                    else:
                        # 마지막 시도 실패 시 빈 리스트 반환
                        print(f"Error fetching messages from SeedOS after {max_retries} attempts: {e}")
                        self._messages_cache = []
                        return []
            
            if response is None or response.status_code != 200:
                # 검색 실패 시 빈 리스트 반환
                self._messages_cache = []
                return []
            
            results = response.json().get("results", [])
            messages = []
            
            # 결과를 시간순으로 정렬 (timestamp 기준)
            sorted_results = sorted(
                results,
                key=lambda x: x.get("block", {}).get("timestamp", 0),
            )
            
            for result in sorted_results:
                block = result.get("block")
                if block:
                    try:
                        message = self._seedos_block_to_message(block)
                        messages.append(message)
                    except Exception:
                        # 변환 실패 시 스킵
                        continue
            
            self._messages_cache = messages
            self._cache_dirty = False
            return messages
            
        except Exception as e:
            # 에러 발생 시 빈 리스트 반환
            print(f"Error fetching messages from SeedOS: {e}")
            return []
    
    def _get_latest_block_hash(self) -> str:
        """마지막 블록의 해시를 가져오기 (체인 연결용)
        
        캐시된 해시가 있으면 사용하고, 없으면 API 호출하여 가져옵니다.
        """
        # 캐시된 해시가 있으면 사용
        if self._last_block_hash is not None:
            return self._last_block_hash
        
        try:
            # 세션별로 마지막 블록 검색
            search_url = f"{self.api_url}/search"
            search_payload = {
                "query": f"agent_id:{self.agent_id} session_id:{self.session_id}",
                "top_k": 1,
                "min_similarity": 0.0,
            }
            
            response = requests.post(
                search_url,
                json=search_payload,
                headers=self._get_headers(),
                timeout=5,
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    block = results[0].get("block", {})
                    if block:
                        block_hash = block.get("block_hash", "0x00")
                        # 캐시에 저장
                        self._last_block_hash = block_hash
                        return block_hash
            
            # 블록이 없으면 "0x00" 반환
            return "0x00"
            
        except Exception:
            # 에러 발생 시 "0x00" 반환
            return "0x00"
    
    def add_message(self, message: BaseMessage) -> None:
        """새 메시지 추가"""
        try:
            # SeedOS에 블록으로 저장
            write_url = f"{self.api_url}/write"
            content = self._message_to_seedos_content(message)
            
            # 이전 블록의 해시 가져오기 (체인 연결)
            prev_hash = self._get_latest_block_hash()
            
            write_payload = {
                "content": content,
                "phase": "리",  # 대화는 "리" phase
                "consensus_rate": 1.0,
                "conclusion": message.content[:100] if len(message.content) > 100 else message.content,
                "prev_hash": prev_hash,
            }
            
            # 재시도 로직 (최대 3회)
            max_retries = 3
            retry_delay = 1.0
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        write_url,
                        json=write_payload,
                        headers=self._get_headers(),
                        timeout=10,
                    )
                    break  # 성공 시 루프 종료
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
                        continue
                    else:
                        raise  # 마지막 시도 실패 시 예외 발생
            
            if response is None:
                raise Exception("Failed to get response from SeedOS API")
            
            if response.status_code == 201:
                # 응답에서 새 블록 해시 가져오기
                result = response.json()
                # block_hash가 있으면 사용, 없으면 block_id 사용
                new_block_hash = result.get("block_hash") or result.get("block_id")
                if new_block_hash:
                    self._last_block_hash = new_block_hash
                
                # 캐시 무효화
                self._cache_dirty = True
                # 새 메시지를 캐시에 추가
                if self._messages_cache is None:
                    self._messages_cache = []
                self._messages_cache.append(message)
            else:
                raise Exception(f"Failed to store message: {response.text}")
                
        except Exception as e:
            print(f"Error storing message to SeedOS: {e}")
            # 에러가 발생해도 메시지는 캐시에 추가 (로컬 동작 보장)
            if self._messages_cache is None:
                self._messages_cache = []
            self._messages_cache.append(message)
    
    def clear(self) -> None:
        """메시지 기록 삭제 (SeedOS에서는 실제 삭제하지 않고 캐시만 클리어)"""
        self._messages_cache = []
        self._cache_dirty = True
        # Note: SeedOS는 불변 저장소이므로 실제 블록 삭제는 하지 않음
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """메모리 요약 정보 반환"""
        messages = self.messages
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "message_count": len(messages),
            "human_messages": sum(1 for m in messages if isinstance(m, HumanMessage)),
            "ai_messages": sum(1 for m in messages if isinstance(m, AIMessage)),
            "system_messages": sum(1 for m in messages if isinstance(m, SystemMessage)),
        }
