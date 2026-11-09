from agent.agenttune_integration import project


questions = [
    "How many orders are present?",
    "How many customers are registered?",
    "Which five products have generated the highest revenue?",
]

report = project.evaluate_agentic(questions)

print("\n========== EVALUATION ==========\n")

print(report)