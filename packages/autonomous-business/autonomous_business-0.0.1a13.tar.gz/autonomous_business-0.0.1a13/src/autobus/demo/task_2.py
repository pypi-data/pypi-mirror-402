import asyncio
from autobus.agent.agent_session import AgentContext, AgentSession
from autobus.agent.core_agent import CoreAgent
from autobus.agent.agent_starter import start_agent_workflow
from autobus.config import config

"""
Task 2: Find the median household incomes of the cities of the subscribers
"""

# Load api keys from .env file
from dotenv import load_dotenv
load_dotenv()

async def main():

    instruction = """
        Task ID: task_2
        Find the median household incomes of the cities in which our subscribers reside.
        Obtain the median household income of cities by calling the tool 'autobus.demo.tool_simulation':median_household_income, 
        passing in the city, expecting an integer returned.
        Outcome specification:
        The outcome has two fields: city, median_household_income.
        Save the outcome to the database table 'median_household_income'.
    """

    handle = await start_agent_workflow(CoreAgent, instruction, config['temporal']['core_agent_q'])
    result = await handle.result()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())