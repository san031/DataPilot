
import json
import re
import torch

from agenttune.agentic import (
    DictToolHarness,
    ReActStrategy,
    run_episode
)

from agent.tools import TOOLS


SYSTEM_PROMPT = """
You are DataPilot AI, an intelligent retail database analyst.

You have access to the following tools:

1. get_schema()
   Returns the database tables and columns.

2. execute_sql(query)
   Executes a read-only SQL query and returns results.

You must follow the ReAct process.

At every step, select exactly one action.

To inspect the schema, respond:

{"action": "get_schema", "arguments": {}}

To execute SQL, respond:

{"action": "execute_sql",
 "arguments": {"query": "SELECT COUNT(*) FROM orders"}}

When you have sufficient information, respond:

{"action": "finish",
 "arguments": {"answer": "Your final business answer"}}

Rules:

- Never invent database values.
- Inspect schema before using unknown columns.
- Use actual tool observations.
- Only generate read-only SQL.
- If SQL fails, correct it and retry.
- Do not call tools unnecessarily.
- Finish when you have sufficient information.

Return ONLY valid JSON.
"""


def generate_response(model, tokenizer, messages):

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():

        output = model.generate(
            inputs,
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id
                or tokenizer.eos_token_id
        )

    response = tokenizer.decode(
        output[0][inputs.shape[-1]:],
        skip_special_tokens=True
    )

    return response.strip()


def parse_action(response):

    # Extract JSON if the model adds surrounding text.
    match = re.search(r"\{.*\}", response, re.DOTALL)

    if not match:
        return None

    try:
        data = json.loads(match.group())

        action = data.get("action")
        arguments = data.get("arguments", {})

        if action not in ["get_schema", "execute_sql", "finish"]:
            return None

        if not isinstance(arguments, dict):
            return None

        if action == "get_schema" and arguments:
            return None

        if action == "execute_sql":
            if not isinstance(arguments.get("query"), str):
                return None

        if action == "finish":
            if not isinstance(arguments.get("answer"), str):
                return None

        return {
            "name": action,
            "arguments": arguments,
            "thought": f"Selected action: {action}"
        }

    except (json.JSONDecodeError, TypeError):
        return None


def format_action(action):
    """Serialise a parsed action as the JSON the model is asked to emit."""

    return json.dumps({
        "action": action["name"],
        "arguments": action["arguments"]
    })


def build_messages(observations, past_actions):
    """Build the chat history with strict user/assistant alternation.

    observations: [task, obs_1, obs_2, ...]  (from state.events)
    past_actions: [action_json_1, action_json_2, ...]  (the policy's own
                  earlier actions); observation i+1 is the result of
                  action i.

    Result: system, user(question), assistant(action), user(observation),
    ... ending with a user message (the aya chat template rejects two
    consecutive messages of the same role).
    """

    if len(observations) != len(past_actions) + 1:
        raise ValueError(
            f"Expected {len(past_actions) + 1} observations for "
            f"{len(past_actions)} past actions, got {len(observations)}."
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Business question: " + observations[0]},
    ]

    for action_json, observation in zip(past_actions, observations[1:]):
        messages.append({"role": "assistant", "content": action_json})
        messages.append({
            "role": "user",
            "content": "Tool observation: " + observation
        })

    # Fold the instruction into the last user message instead of adding
    # another user turn.
    messages[-1]["content"] += "\n\nChoose your next action. Return JSON only."

    return messages


def make_react_policy(model, tokenizer):

    def policy(state):

        # state.events holds only observations; the policy's own actions
        # are kept in state.scratch (one list per episode).
        observations = [
            event.payload.get("text", "")
            for event in state.events
        ]
        past_actions = state.scratch.setdefault("actions", [])

        messages = build_messages(observations, past_actions)

        response = generate_response(
            model,
            tokenizer,
            messages
        )

        action = parse_action(response)

        if action is None:

            # Bounded recovery: retry with a correction prompt.
            correction = messages + [
                {
                    "role": "assistant",
                    "content": response
                },
                {
                    "role": "user",
                    "content": (
                        "Your previous response was invalid. "
                        "Return a valid JSON tool action."
                    )
                }
            ]

            response = generate_response(
                model,
                tokenizer,
                correction
            )

            action = parse_action(response)

        if action is None:
            return {
                "name": "finish",
                "arguments": {
                    "answer": "Unable to generate a valid tool action."
                }
            }

        # Remember the action so the next prompt can replay it as an
        # assistant turn.
        past_actions.append(format_action(action))

        return action

    return policy


def create_agent(model, tokenizer):

    harness = DictToolHarness(
        tools=TOOLS,
        max_steps=6
    )

    strategy = ReActStrategy(
        policy=make_react_policy(model, tokenizer),
        max_steps=6
    )

    return strategy, harness


def ask_datapilot(model, tokenizer, question):

    strategy, harness = create_agent(
        model,
        tokenizer
    )

    event_log = run_episode(
        strategy,
        harness,
        question
    )

    return event_log
