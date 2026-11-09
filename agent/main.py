
from agent.model import load_model
from agent.react_agent import ask_datapilot

model, tokenizer = load_model()

question = """
How many orders exist?
"""

event_log = ask_datapilot(
    model,
    tokenizer,
    question
)

print("\n========== AGENT TRAJECTORY ==========\n")

for event in event_log:
    print(event.kind, event.payload)

print("\n========== COMPLETE ==========")