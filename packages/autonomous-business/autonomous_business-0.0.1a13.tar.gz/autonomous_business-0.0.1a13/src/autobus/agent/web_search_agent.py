from agents import Agent, WebSearchTool

LLM = "gpt-5-mini"
AGENT_NAME = "web_search_agent"

INSTRUCTIONS = """
You are a web research agent. 
The user will provide the instruction on what to search for and output specification.
"""

web_search_agent = Agent(
    name="AGENT_NAME",
    model=LLM,
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool()]
)