# DataPilot AI

**Agentic Business Intelligence and Database Assistant**\
Hackathon Track: **Agentic Fine-tuning --- Data and Database Agents**\

> DataPilot AI is a proposed agentic system that answers business
> questions by inspecting a database, selecting appropriate tools,
> generating and executing safe SQL, verifying query results, and
> presenting answers. The project will use the required
> **AgentTune** and **AuditKIT** repositories and one permitted **Aya**
> model.

------------------------------------------------------------------------

## 1. Problem

Business users often need information from structured databases but may
not know SQL. A conventional chatbot can generate plausible answers
without actually querying the database. A reliable database agent must
do more:

1.  Understand the user's business question.
2.  Inspect the available database schema when needed.
3.  Select the appropriate database tool.
4.  Generate a valid query.
5.  Execute the query safely.
6.  Verify the returned result against expected or independently
    computed outcomes.
7.  Explain the result with appropriate context.

The hackathon objective is not simply to build a natural-language-to-SQL
demo. It is to investigate whether **agentic fine-tuning** improves the
model's ability to use database tools and complete database tasks
reliably.

## 2. Proposed solution

DataPilot AI will provide a natural-language interface to a sample
business database. The initial use case is an e-commerce business
containing customers, products, orders, order items, payments, and
optionally employees.

<!-- Example questions:

-   What was our total revenue during October?
-   Which five products generated the highest revenue?
-   Which customers spent more than ₹50,000?
-   How many orders were cancelled?
-   Which products had the largest month-over-month sales decline?
-   Which orders have failed payments? -->

The agent should answer using executed database queries, not unsupported
guesses. Where a question is ambiguous or cannot be answered from the
available data, it should explain the limitation or ask for
clarification.

## 3. Required repositories and their roles

The hackathon instructions specify these repositories for Agentic
Fine-tuning:

-   [AgentTune](https://github.com/Lexsi-Labs/AgentTune)
-   [AuditKIT](https://github.com/Lexsi-Labs/AuditKIT)

### AgentTune --- training and agent framework

AgentTune will be used for the agentic training workflow. The project
will investigate and use the repository's supported interfaces for:

-   Agentic training and rollout generation.
-   GRPO as the initial reinforcement-learning algorithm, subject to
    compatibility checks.
-   A ReAct-style tool-using agent, where supported by the selected
    example/configuration.
-   The repository's SQL database tool/example as the starting point for
    database integration.
-   EventLog or the repository's supported trajectory-recording
    mechanism.
-   Custom reward functions for database task performance.
-   Saving and loading training checkpoints.

<!-- **Important:** Exact imports, configuration keys, function signatures,
and supported options must be taken from the checked-out repository
version and its examples. This README does not assume that illustrative
component names are stable public APIs. -->

### AuditKIT --- evaluation and verification

AuditKIT will be used to evaluate agent behavior and task outcomes. We
will inspect and use the repository's supported interfaces for:

-   Defining evaluation cases and specifications.
-   Running agent evaluations.
-   Evaluating tool-call behavior and validity.
-   Evaluating task completion and trajectories.
-   Verifying final answers or database state with assertions, where
    supported.
-   Producing reproducible evaluation results.

Where compatible, AgentTune execution traces will be passed through the
documented AuditKIT integration or converted using the repository's
supported trace format.

### Separation of responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  AgentTune                           Agent execution, rollouts, training
                                      and checkpointing

  Aya model                           Language model used by the agent
                                      and training workflow

  Business database                   Source of structured business data

  SQL/database tools                  Controlled access to the database

  Custom reward functions             Training feedback for
                                      database-agent behavior

  AuditKIT                            Evaluation and outcome verification

  Streamlit (proposed)                User interface and results
                                      dashboard
  -----------------------------------------------------------------------

AuditKIT is primarily the evaluation layer. Its metrics should not be
described as automatically driving GRPO updates unless that integration
is explicitly implemented and verified.

## 4. Permitted Aya model choices

The project must use one of the seven Aya models listed by the hackathon
organizers:

1.  [Tiny Aya Base](https://huggingface.co/CohereLabs/tiny-aya-base)
2.  [Tiny Aya Global](https://huggingface.co/CohereLabs/tiny-aya-global)
3.  [Tiny Aya Fire](https://huggingface.co/CohereLabs/tiny-aya-fire)
4.  [Tiny Aya Water](https://huggingface.co/CohereLabs/tiny-aya-water)
5.  [Tiny Aya Earth](https://huggingface.co/CohereLabs/tiny-aya-earth)
6.  [Aya Expanse 8B](https://huggingface.co/CohereLabs/aya-expanse-8b)
7.  [Aya Expanse 32B](https://huggingface.co/CohereLabs/aya-expanse-32b)

Official documentation:

-   [Tiny Aya documentation](https://docs.cohere.com/docs/tiny-aya)
-   [Aya Expanse
    documentation](https://docs.cohere.com/docs/aya-expanse)

<!-- **Model selection is pending a hardware and compatibility test.** The
final choice must be one of the permitted models and must work with the
selected AgentTune training path. Do not assume that every model can be
trained on the available hardware. -->

## 5. Proposed architecture

``` text
Business user
     |
     v
Streamlit interface (proposed)
     |
     v
Aya model + agent runtime
     |
     v
AgentTune-supported agent/tool workflow
     |
     +------ Schema inspection tool
     |
     +------ Read-only SQL execution tool
     |
     +------ Result verification
     |
     v
Business database (initially SQLite)
     |
     v
Evidence-backed answer

Training and evaluation:
Training questions + environment + reward functions
     |
     v
AgentTune rollouts and GRPO training (if compatible)
     |
     v
Fine-tuned Aya checkpoint
     |
     v
AuditKIT evaluation on held-out cases
     |
     v
Baseline-versus-fine-tuned report
```

The exact runtime arrangement will follow the repository examples. The
diagram describes the intended system, not a claim that all components
are already implemented.

## 6. Initial database design

The first prototype will use SQLite to reduce setup overhead. PostgreSQL
may be considered if required by the implementation or demonstration
environment.

  -----------------------------------------------------------------------
  Table                               Example fields
  ----------------------------------- -----------------------------------
  `customers`                         customer ID, name, email,
                                      registration date

  `products`                          product ID, product name, category,
                                      unit price

  `orders`                            order ID, customer ID, order date,
                                      status

  `order_items`                       order item ID, order ID, product
                                      ID, quantity, unit price

  `payments`                          payment ID, order ID, amount,
                                      payment status, payment date

  `employees` (optional)              employee ID, name, department, role
  -----------------------------------------------------------------------

Primary keys, foreign keys, data types, and relationships will be
documented in the schema. Synthetic records will be generated for the
prototype. Expected answers for benchmark questions will be computed
directly from the database and checked before use.

<!-- ## 7. Agent tools and safety

The initial tool set is expected to include:

-   **Schema inspection:** return permitted table and column
    information.
-   **SQL execution:** execute validated, read-only queries.
-   **Result verification:** compare query output with expected or
    independently calculated results in evaluation cases.
-   **Business summary:** optionally provide a constrained helper for
    common aggregates, if useful.

Safety requirements:

-   Use a read-only database connection or equivalent database
    permissions.
-   Reject destructive statements such as `DROP`, `DELETE`, `UPDATE`,
    `INSERT`, and schema modifications in the agent query path.
-   Prefer parameterized queries for values supplied separately from SQL
    text.
-   Apply query timeouts and result-size limits where feasible.
-   Limit agent iterations and tool retries.
-   Do not expose credentials, private data, or unrestricted filesystem
    access.
-   Treat database contents and tool outputs as data, not as
    instructions to override system rules.
-   Log tool calls and errors without logging secrets.

A simple keyword blocklist alone is not a sufficient SQL security
boundary. Use read-only permissions and a constrained SQL execution
layer. -->

## 8. Training data

The training dataset will contain business questions and the information
needed to assess successful execution. Depending on AgentTune's required
data format, examples may include:

-   User question.
-   Relevant schema context.
-   Expected tool or tool sequence.
-   SQL query or acceptable query behavior.
-   Expected result or result assertion.
-   Expected final answer characteristics.

Planned question categories:

1.  Simple lookups and filters.
2.  Aggregations such as `SUM`, `COUNT`, and `AVG`.
3.  Joins across related tables.
4.  Date ranges and month-over-month comparisons.
5.  Multi-step questions requiring schema inspection and query
    execution.
6.  Recoverable SQL errors.
7.  Ambiguous or unsupported questions.
8.  Safety tests involving disallowed operations.

Split data into training, validation, and held-out test sets. Keep test
questions and their expected outcomes out of training and reward tuning.
Validate expected answers against the actual database before using them.

## 9. Reward design

The initial training experiment will investigate GRPO and a verifiable,
task-specific reward. The final reward implementation must follow
AgentTune's actual reward-function interface.

Candidate reward components:

  -----------------------------------------------------------------------
  Reward dimension                    Desired behavior
  ----------------------------------- -----------------------------------
  Result correctness                  Query result matches the verified
                                      expected result

  SQL execution                       Query executes successfully

  Tool selection                      Appropriate tool is selected

  Tool arguments                      Arguments follow the tool schema

  Task completion                     User's requested task is completed

  Efficiency                          Avoid unnecessary or repeated calls

  Safety                              Respect read-only and query
                                      restrictions
  -----------------------------------------------------------------------

<!-- Rewards should be designed and tested to discourage reward hacking. For
example, syntactically valid SQL should not receive full task-success
reward if it returns the wrong records. A final answer that merely
claims success should not count as success without supporting execution
evidence.

Weights, reward ranges, and penalties are **to be determined
experimentally**. They will be documented in the training configuration 
and report.-->

## 10. Evaluation plan

Evaluation will compare:

-   **Baseline:** the selected permitted Aya model before the project's
    agentic fine-tuning.
-   **Fine-tuned:** the same model after the training experiment.

Both systems should use the same tool definitions, database snapshot,
execution limits, and held-out test cases wherever possible. Record
model and configuration differences that cannot be held constant.

Candidate measurements:

-   SQL result correctness, checked deterministically.
-   Tool-call validity.
-   Tool selection or tool-call precision/recall/F1, where supported by
    the evaluator.
-   Task completion.
-   Trajectory quality or trajectory match, where applicable.
-   Redundant tool calls.
-   Failed executions.
-   Safety violations.
-   Latency and token usage, where measurable.

Use AuditKIT's documented evaluators and assertions that match the
installed repository version. Supplement framework metrics with
deterministic SQL-result checks where necessary.

No performance improvement is claimed in advance. Report actual measured
values, test-set size, evaluation conditions, and failures. If a metric
is unavailable or not applicable, state that rather than inventing a
value.

## 11. User interface

A Streamlit interface is proposed for the demonstration. It may display:

-   Natural-language question input.
-   Agent status and tool-call sequence.
-   Generated SQL.
-   Query results in a table.
-   Verification outcome.
-   Final business explanation.
-   Baseline-versus-fine-tuned evaluation charts.

The UI is a presentation layer; it must not bypass the agent's safety
checks or fabricate evaluation results.

 ## 12. Proposed project structure

<!--``` text
DataPilot-AI/
├── app/
│   └── streamlit_app.py
├── agent/
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── verification.py
├── database/
│   ├── schema.sql
│   ├── seed_data.py
│   └── business.db
├── training/
│   ├── dataset.py
│   ├── rewards.py
│   ├── train.py
│   └── config.yaml
├── evaluation/
│   ├── benchmark.py
│   ├── audit.py
│   └── compare_results.py
├── data/
│   ├── train.jsonl
│   ├── validation.jsonl
│   └── test.jsonl
├── results/
│   ├── baseline/
│   └── finetuned/
├── notebooks/
├── requirements.txt
├── .gitignore
└── README.md
``` -->

This is the proposed DataPilot AI project structure. AgentTune and
AuditKIT should remain separate dependencies or checked-out repositories
rather than being copied wholesale into this project.



## 13. Reproducibility and reporting

For each training/evaluation run, record:

-   Aya model ID and revision.
-   AgentTune and AuditKIT commit/version.
-   Python, PyTorch, CUDA, Transformers, and TRL versions.
-   Training configuration and random seed.
-   Dataset version and split.
-   Reward implementation and weights.
-   Checkpoint identifier.
-   Evaluation cases and database snapshot.
-   Raw metrics, logs, and known failures.

Do not include API keys, Hugging Face tokens, private datasets, or other
secrets in the repository.



------------------------------------------------------------------------

## References

-   [AgentTune GitHub
    repository](https://github.com/Lexsi-Labs/AgentTune)
-   [AuditKIT GitHub repository](https://github.com/Lexsi-Labs/AuditKIT)
-   [Tiny Aya models and
    documentation](https://docs.cohere.com/docs/tiny-aya)
-   [Aya Expanse models and
    documentation](https://docs.cohere.com/docs/aya-expanse)
