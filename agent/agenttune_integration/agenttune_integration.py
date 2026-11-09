import json

from agenttune.agentic import (
    Project,
    DictToolHarness,
    ReActStrategy,
)

from agent.react_agent import generate_response
from agent.system_prompt import SYSTEM_PROMPT

from database.schema_tool import get_schema
from database.sql_tool import execute_sql


# --------------------------------
# 1. Database tools
# --------------------------------

def schema_tool():
    result = get_schema()
    return json.dumps(result, default=str)


def sql_tool(query: str):
    result = execute_sql(query)
    return json.dumps(result, default=str)


# --------------------------------
# 2. Register tools
# --------------------------------

tools = {
    "get_schema": schema_tool,
    "execute_sql": sql_tool,
}


# --------------------------------
# 3. ReAct policy
# --------------------------------

def datapilot_policy(state):

    observations = [
        event.payload.get("text", "")
        for event in state.events
    ]

    # Enforce schema-first behaviour
    if state.step == 0:
        return {
            "name": "get_schema",
            "arguments": {}
        }

    user_prompt = f"""
Business question:
{state.task}

Available tools:
{list(state.scratch["tools"])}

Previous observations:
{json.dumps(observations, default=str)}

Choose the next action.

Return ONLY JSON:

{{
    "name": "execute_sql",
    "arguments": {{
        "query": "SQL QUERY"
    }}
}}

To finish:

{{
    "name": "finish",
    "arguments": {{
        "answer": "Final business answer"
    }}
}}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    response = generate_response(messages)

    # Parse model response
    try:
        action = json.loads(response)

        if not isinstance(action, dict):
            raise ValueError("Expected JSON object")

        if action.get("name") not in (
            "get_schema",
            "execute_sql",
            "finish"
        ):
            raise ValueError("Unknown action")

        if not isinstance(action.get("arguments", {}), dict):
            raise ValueError("Invalid arguments")

        return action

    except (json.JSONDecodeError, ValueError):
        return {
            "name": "finish",
            "arguments": {
                "answer": "Unable to generate a valid action."
            }
        }


# --------------------------------
# 4. Create AgentTune harness
# --------------------------------

harness = DictToolHarness(
    tools=tools,
    max_steps=6
)


# --------------------------------
# 5. Create ReAct strategy
# --------------------------------

strategy = ReActStrategy(
    policy=datapilot_policy,
    max_steps=6
)


# --------------------------------
# 6. Create AgentTune project
# --------------------------------

project = Project(
    strategy=strategy,
    harness=harness
)