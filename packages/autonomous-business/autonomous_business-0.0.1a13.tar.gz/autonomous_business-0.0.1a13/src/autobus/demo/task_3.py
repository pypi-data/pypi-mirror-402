import asyncio
from autobus.agent.agent_session import AgentContext, AgentSession
from autobus.agent.core_agent import CoreAgent
from autobus.agent.agent_starter import start_agent_workflow
from autobus.config import config

"""
Task 3: Find the target subscriptions that are potentially savable churns and the subscribers' household incomes are more than
the median of the city.
"""

# Load api keys from .env file
from dotenv import load_dotenv
load_dotenv()

async def main():
    instruction = """
        Task ID: task_3
        Find the target subscriptions that are potentially savable churns and the subscribers' household incomes are more 
        than the median of the city. Then send it to the marketing campaign 'campaign 123'.
        Action specification:
        1. Save the outcome to the database table 'target_subscription'. Include these fields:
            subscription_id, status, product_name, risk_level, subscription_rate, household_income, median_household_income.
        2. Call the tool 'autobus.demo.tool_simulation':send_to_marketing_campaign with takes two arguments:
            i. campaign id = 'campaign 123'
            ii. a list of the target subscription ids 
    """

    handle = await start_agent_workflow(CoreAgent, instruction, config['temporal']['core_agent_q'])
    result = await handle.result()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())