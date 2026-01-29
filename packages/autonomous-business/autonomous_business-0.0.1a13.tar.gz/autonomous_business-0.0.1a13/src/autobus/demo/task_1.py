import asyncio
from autobus.agent.agent_session import AgentContext, AgentSession
from autobus.agent.core_agent import CoreAgent
from autobus.agent.agent_starter import start_agent_workflow
from autobus.config import config

"""
Task 1: Identify potentially savable churns.
"""
# Load api keys from .env file
from dotenv import load_dotenv
load_dotenv()

async def main():

    instruction = """
        Task ID: task_1
        Find savable churn. A subscription is a savable churn if all of the following criteria are met:
        1. The subscription's churn risk level is 4.
        2. The subscription rate is $10 or more.
        3. The subscription is for 'Premium Plan' or 'Family Plan'.
        4. The subscription is active.
        Outcome specification:
        The outcome has two fields: subscription_id, consumer_id
        Save the outcome to the database table 'savable_churn'
    """

    handle = await start_agent_workflow(CoreAgent, instruction, config['temporal']['core_agent_q'])
    result = await handle.result()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
