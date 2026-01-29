"""SeedOS LangChain Integration

SeedOS Memory를 LangChain의 ChatMessageHistory로 사용할 수 있게 해주는 패키지입니다.

사용 예시:
    from seedos_langchain import SeedOSMemory
    from langchain.agents import AgentExecutor, create_react_agent
    
    memory = SeedOSMemory(
        agent_id="user_123",
        api_url="http://localhost:8000"
    )
    
    agent = create_react_agent(llm, tools, system_prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory
    )
"""

from .memory import SeedOSMemory

__version__ = "0.2.0"
__all__ = ["SeedOSMemory"]
