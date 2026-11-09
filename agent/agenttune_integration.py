
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


def parse_and_validate(response):
    """Parse a model reply into an action dict, or raise ValueError."""

    action = extract_json(response)

    if not isinstance(action, dict):
        raise ValueError("Expected a JSON dictionary")

    name = action.get("name")
    arguments = action.get("arguments", {})

    if name not in ("get_schema", "execute_sql", "finish"):
        raise ValueError(f"Invalid action: {name}")

    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a dictionary")

    if name == "execute_sql" and not isinstance(arguments.get("query"), str):
        raise ValueError("SQL query is missing")

    if name == "finish" and not isinstance(arguments.get("answer"), str):
        raise ValueError("Final answer is missing")

    return action


# =====================================================
# 4. REACT POLICY
# =====================================================

def format_action(action):
    """Serialise an action the way the model is asked to write it."""

    return json.dumps({
        "name": action["name"],
        "arguments": action.get("arguments", {})
    })


def build_messages(user_prompt, observations, actions):
    """
    Chat history: system, user(task + rules), then one
    assistant(action) / user(observation) pair per step taken.
    Roles strictly alternate, as the Aya chat template requires.
    """

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for action_json, observation in zip(actions, observations[1:]):
        messages.append({"role": "assistant", "content": action_json})
        messages.append({
            "role": "user",
            "content": f"Tool observation:\n{observation}"
        })

    messages[-1]["content"] += (
        "\n\nChoose your next action. Return JSON only."
    )

    return messages


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

    # Actions already taken this episode (kept in the per-episode scratch dict).
    actions = state.scratch.setdefault("actions", [])

    if state.step == 0:

        action = {
            "name": "get_schema",
            "arguments": {}
        }

        actions.append(format_action(action))

        return action

    # Observation 0 is the task itself, then one result per action taken.
    if len(observations) != len(actions) + 1:
        raise ValueError(
            f"History out of sync: {len(observations)} observations "
            f"but {len(actions)} actions"
        )

    # -------------------------------------------------
    # Construct next prompt
    # -------------------------------------------------

    user_prompt = f"""
You are DataPilot AI, an intelligent retail database analyst.

BUSINESS QUESTION:
{state.task}

AVAILABLE TOOLS:
{list(state.scratch["tools"])}

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
9. If your last execute_sql succeeded and its rows answer the
   question, your next action MUST be finish.

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

    messages = build_messages(
        user_prompt,
        observations,
        actions
    )

    # -------------------------------------------------
    # Generate response using Aya
    # -------------------------------------------------

    # -------------------------------------------------
    # Generate and parse, retrying once on an invalid reply
    # -------------------------------------------------

    MAX_ATTEMPTS = 2
    attempt_messages = messages

    for attempt in range(MAX_ATTEMPTS):

        response = generate_response(
            model,
            tokenizer,
            attempt_messages
        )

        try:
            action = parse_and_validate(response)

            # Remember what we did, so the next prompt can show it.
            actions.append(format_action(action))

            return action

        except (json.JSONDecodeError, ValueError) as error:

            print(f"Action parsing error (attempt {attempt + 1}):", error)

            # Show the model its own bad reply, then ask again.
            attempt_messages = messages + [
                {"role": "assistant", "content": response},
                {
                    "role": "user",
                    "content": (
                        f"Your previous response was invalid: {error}. "
                        "Return exactly one valid JSON action with "
                        "name and arguments fields."
                    )
                }
            ]

    return {
        "name": "finish",
        "arguments": {
            "answer": "Unable to generate a valid action."
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
