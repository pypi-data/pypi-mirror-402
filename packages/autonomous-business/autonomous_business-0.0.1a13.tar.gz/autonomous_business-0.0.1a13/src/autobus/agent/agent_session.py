from dataclasses import dataclass
from typing import Any
import json
from agents import Agent, Runner


@dataclass
class AgentContext:
    def __init__(self, state: dict[str, Any] = None):
        self.state = state if state else {}


class AgentSession:
    def __init__(self, starting_agent:Agent[AgentContext], agent_context:AgentContext=AgentContext()):
        #self.session = SQLiteSession(session_name)
        self.agent_context = agent_context
        self.starting_agent = starting_agent

    async def run(self, message:str) -> list[str]:
        msg = json.dumps({"role": "user", "content": message})
        run_result = await Runner.run(context=self.agent_context, starting_agent=self.starting_agent, input=msg)

        return run_result.final_output