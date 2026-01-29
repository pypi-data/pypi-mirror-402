from agents import Agent, Runner, gen_trace_id, trace
from datetime import timedelta
from temporalio import workflow
from temporalio.contrib import openai_agents

with workflow.unsafe.imports_passed_through():
    from autobus.agent.activity import get_config, get_db_schema, get_prolog_template, save_text_to_file


#LLM = "gpt-5.2"
LLM = "gemini/gemini-3-flash-preview"

@workflow.defn
class CoreAgent:
    @workflow.run
    async def run(self, task_instruction: str) -> str:

        generated_dir = await workflow.execute_activity(
            get_config,
            args=["directory", "generated_dir"],
            start_to_close_timeout=timedelta(seconds=10)
        )

        core_agent = Agent(
            name=type(self).__name__,
            instructions=f"""
            You are an expert in logic programming in SWI-Prolog. Generate prolog programs with facts and 
            foundational rules based on the database schema and task specific rules from the user prompt.
            Use the Prolog template 'facts_tools_rules_actions.pl'. Do not place string in multiple lines.
            Get the Task ID from the user prompt and save the program to a file with path {generated_dir}/<Task ID>_logic.pl.
            If you fail to get the prolog template or the database schema, stop and output error message.
            """,
            tools=[
                openai_agents.workflow.activity_as_tool(
                    get_db_schema, 
                    start_to_close_timeout=timedelta(seconds=10)
                ), 
                openai_agents.workflow.activity_as_tool(
                    get_prolog_template, 
                    start_to_close_timeout=timedelta(seconds=10)
                ),
                openai_agents.workflow.activity_as_tool(
                    save_text_to_file, 
                    start_to_close_timeout=timedelta(seconds=10)
                )],
            model = LLM
        )

        trace_id = gen_trace_id()
        with trace(workflow_name=type(self).__name__, trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            r = await Runner.run(starting_agent=core_agent, input=task_instruction)
            return r.final_output
        
