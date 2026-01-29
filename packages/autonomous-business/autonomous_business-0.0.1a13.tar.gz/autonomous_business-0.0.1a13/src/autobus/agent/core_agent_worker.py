import asyncio
from autobus.config import config
from temporalio.worker import Worker
import asyncio
from datetime import timedelta
from temporalio.client import Client
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from agents.extensions.models.litellm_provider import LitellmProvider
from autobus.agent.core_agent import CoreAgent
from autobus.agent.activity import get_config, get_db_schema, get_prolog_template, save_text_to_file

"""
Start Temporal worker
"""

# Load api keys from .env file
from dotenv import load_dotenv
load_dotenv()


async def worker_main():
    # Use the plugin to configure Temporal for use with OpenAI Agents SDK
    client = await Client.connect(
        config['temporal']['uri'],
        plugins=[
            OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=30)
                ),
                model_provider=LitellmProvider(),
            ),
        ],
    )

    worker = Worker(
        client,
        task_queue=config['temporal']['core_agent_q'],
        workflows=[CoreAgent],
        activities=[get_config, get_db_schema, get_prolog_template, save_text_to_file]
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(worker_main())
