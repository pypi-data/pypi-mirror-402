from uuid import uuid4
from autobus.config import config
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin, ModelActivityParameters
from temporalio.client import Client
from datetime import timedelta
from agents.extensions.models.litellm_provider import LitellmProvider


async def start_agent_workflow(agent_class, instruction: str, task_queue:str) -> str:
    """
    Start Temporal workflow for the agent.
    """
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
    
    run_id = f"{agent_class.__name__}_{uuid4().hex}"
    handle = await client.start_workflow(
        agent_class.run,
        instruction,
        id=run_id,
        task_queue=task_queue,
    )
    return handle

