
import json
import re

from agenttune.agentic import (
    Project,
    DictToolHarness,
    ReActStrategy,
)

from agent.react_agent import generate_response
from agent.system_prompt import SYSTEM_PROMPT

from database.schema_tool import get_schema
from database.sql_tool import execute_sql


# =====================================================
# 1. DATABASE TOOLS
# =====================================================

def schema_tool():
    """Retrieve the complete database schema."""

    result = get_schema()

    return json.dumps(result, default=str)


def sql_tool(query: str):
    """Execute a SQL query against the retail database."""

    result = execute_sql(query)

    return json.dumps(result, default=str)


# =====================================================
# 2. REGISTER AGENTTUNE TOOLS
# =====================================================

tools = {
    "get_schema": schema_tool,
    "execute_sql": sql_tool,
}


# =====================================================
# 3. MODEL OUTPUT PARSER
# =====================================================

def extract_json(text):
    """
    Extract JSON action from model response.
    Handles JSON enclosed in markdown code blocks.
    """

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"```(?:json)?", "", text)
    text = text.replace("```", "").strip()

    # Extract JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in model response")

    return json.loads(match.group())


# =====================================================
# 4. REACT POLICY
# =====================================================

def make_datapilot_policy(model, tokenizer):
    """
    Creates an Aya-powered ReAct policy.
    """

    def datapilot_policy(state):

        return decide_next_action(
            state,
            model,
            tokenizer
        )

    return datapilot_policy


def decide_next_action(state, model, tokenizer):

    # -------------------------------------------------
    # Extract observations
    # -------------------------------------------------

    observations = [
        event.payload.get("text", "")
        for event in state.events
    ]

    # -------------------------------------------------
    # Enforce schema-first behaviour
    # -------------------------------------------------

    if state.step == 0:

        return {
            "name": "get_schema",
            "arguments": {}
        }

    # -------------------------------------------------
    # Construct next prompt
    # -------------------------------------------------

    user_prompt = f"""
You are DataPilot AI, an intelligent retail database analyst.

BUSINESS QUESTION:
{state.task}

AVAILABLE TOOLS:
{list(state.scratch["tools"])}

PREVIOUS OBSERVATIONS:
{json.dumps(observations, default=str)}

INSTRUCTIONS:

1. Use the retrieved database schema.
2. Use only tables and columns that exist in the schema.
3. Generate valid SQLite SQL.
4. Use JOIN operations when required.
5. Never invent database values.
6. If SQL execution fails, inspect the error and correct
   the query.
7. Do not repeat an unsuccessful query without changes.
8. Finish only after obtaining sufficient information.

Return ONLY one valid JSON object.

For SQL execution:

{{
    "name": "execute_sql",
    "arguments": {{
        "query": "SELECT ..."
    }}
}}

For completing the task:

{{
    "name": "finish",
    "arguments": {{
        "answer": "Your final business answer"
    }}
}}
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    # -------------------------------------------------
    # Generate response using Aya
    # -------------------------------------------------

    response = generate_response(
        model,
        tokenizer,
        messages
    )

    # -------------------------------------------------
    # Parse action
    # -------------------------------------------------

    try:

        action = extract_json(response)

        if not isinstance(action, dict):
            raise ValueError("Expected a JSON dictionary")

        name = action.get("name")
        arguments = action.get("arguments", {})

        if name not in (
            "get_schema",
            "execute_sql",
            "finish"
        ):
            raise ValueError(f"Invalid action: {name}")

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        if name == "execute_sql":
            if not isinstance(arguments.get("query"), str):
                raise ValueError("SQL query is missing")

        if name == "finish":
            if not isinstance(arguments.get("answer"), str):
                raise ValueError("Final answer is missing")

        return action

    except (json.JSONDecodeError, ValueError) as error:

        print("Action parsing error:", error)

        return {
            "name": "finish",
            "arguments": {
                "answer": (
                    "Unable to generate a valid action. "
                    "Please try again."
                )
            }
        }


# =====================================================
# 5. BUILD AGENTTUNE PROJECT
# =====================================================

def build_project(model, tokenizer):
    """
    Connects Aya + ReAct + database tools + AgentTune.
    """

    # Create tool execution harness
    harness = DictToolHarness(
        tools=tools,
        max_steps=6
    )

    # Create ReAct strategy
    strategy = ReActStrategy(
        policy=make_datapilot_policy(model, tokenizer),
        max_steps=6
    )

    # Create AgentTune Project
    project = Project(
        strategy=strategy,
        harness=harness
    )

    return project


# =====================================================
# 6. RUN DATAPILOT QUESTION
# =====================================================

def ask_datapilot(project, question):
    """
    Executes a business question and returns its EventLog.
    """

    event_log = project.infer(question)

    return event_log


# =====================================================
# 7. DISPLAY AGENT EXECUTION
# =====================================================

def display_trajectory(event_log):

    print("\n========== DATAPILOT EXECUTION ==========\n")

    for event in event_log:

        print(f"\nEVENT: {event.kind.value}")

        print(
            json.dumps(
                event.payload,
                indent=4,
                default=str
            )
        )

    print("\n========== EXECUTION COMPLETED ==========\n")
