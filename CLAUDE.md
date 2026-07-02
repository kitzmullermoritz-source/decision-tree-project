# Decision Tree Project: Instructions for Claude Code

## Project goal

Build a web application that helps users structure complex decisions under uncertainty. Users create a visual decision tree containing choices, uncertain events, and final outcomes. The application evaluates the tree with expected utility and backward induction, identifies the preferred strategy, and explains the result.

This is a CS50 final project. Keep the implementation understandable to a student who knows Python, Flask, SQLite, HTML, CSS, and basic JavaScript. Prefer clear code and explicit reasoning over clever abstractions.

## Product scope

The first complete version should let a user:

1. Create and name a decision analysis.
2. Add three kinds of nodes:
   - **Decision node:** the user can choose one child action.
   - **Chance node:** one child outcome occurs with an assigned probability.
   - **Outcome node:** a terminal result with a utility value.
3. Connect nodes into a valid rooted tree.
4. Evaluate the tree recursively.
5. See the expected utility of each branch and the recommended action at every decision node.
6. Save and reopen analyses.
7. See clear validation errors, especially when probabilities do not total 100%.

Sensitivity analysis is a later feature. Authentication, multiplayer game theory, Nash equilibria, Monte Carlo simulation, and external game-theory engines are explicitly outside the initial MVP.

## Technology

- Python 3
- Flask
- SQLite using Python's `sqlite3` module
- Jinja templates, semantic HTML, and ordinary CSS
- Vanilla JavaScript for interactive behavior
- Cytoscape.js later for the visual tree editor
- pytest for tests

Do not introduce React, TypeScript, SQLAlchemy, Docker, or a large frontend framework unless the user later requests and approves the change.

## Core evaluation rules

Implement the mathematical engine independently of Flask so it is easy to test.

- An **outcome node** evaluates to its utility.
- A **chance node** evaluates to the sum of each child's probability multiplied by that child's recursively evaluated value.
- A **decision node** evaluates to the maximum recursively evaluated child value. Also return which child or children attain that maximum.

The evaluator must detect and reject:

- cycles;
- missing roots or unreachable nodes;
- chance nodes whose outgoing probabilities do not sum to 1 within a small documented tolerance;
- probabilities outside `[0, 1]`;
- outcome nodes with children;
- non-outcome nodes without children;
- missing utility values.

Keep full precision internally and round only for display. Utilities may be negative.

## Proposed data model

Use migrations or an idempotent schema initialization file. Start with these concepts and adjust only when implementation evidence requires it:

### `analyses`

- `id`
- `title`
- `description`
- `root_node_id`
- `created_at`
- `updated_at`

### `nodes`

- `id`
- `analysis_id`
- `node_type` (`decision`, `chance`, or `outcome`)
- `label`
- `utility` (nullable except for outcomes)
- optional visual position fields for the later editor

### `edges`

- `id`
- `analysis_id`
- `source_node_id`
- `target_node_id`
- `label`
- `probability` (used only for edges leaving chance nodes)

Use foreign keys, parameterized SQL queries, and sensible cascade behavior.

## Suggested project structure

Keep the initial structure compact:

```text
decision-tree-project/
|-- app.py
|-- decision_engine.py
|-- database.py
|-- schema.sql
|-- requirements.txt
|-- templates/
|   |-- layout.html
|   |-- index.html
|   `-- analysis.html
|-- static/
|   |-- styles.css
|   `-- app.js
|-- tests/
|   `-- test_decision_engine.py
|-- README.md
`-- CLAUDE.md
```

Split files further only after their responsibilities genuinely become too large.

## Development milestones

### Milestone 1: working vertical slice

Start here. Do not attempt the visual editor yet.

- Create the Flask skeleton and dependency file.
- Implement the framework-independent recursive evaluator.
- Add focused evaluator tests.
- Create an idempotent SQLite schema and database initialization.
- Seed or construct one small example decision tree.
- Add a home page and an analysis page that display the example, its calculated values, and its recommended action in a readable non-graphical format.
- Document exact local setup and run commands in `README.md`.

Milestone 1 is complete only when the app starts locally and all tests pass.

### Milestone 2: create and edit analyses

- Forms or JSON endpoints for adding, editing, connecting, and deleting nodes.
- Server-side validation for every write.
- Save and reopen multiple analyses.

### Milestone 3: visual tree editor

- Render the tree with Cytoscape.js.
- Add node creation, selection, movement, editing, and connection controls.
- Keep the server/database as the source of truth.

### Milestone 4: explanation and sensitivity

- Highlight recommended branches.
- Explain calculations in plain language.
- Show which probabilities or utilities most strongly affect the recommendation.

### Milestone 5: polish

- Responsive design and accessibility review.
- Helpful empty states and validation messages.
- Expanded tests, example analyses, and final documentation.

## Working rules

When asked to begin development:

1. Inspect the repository and this file first.
2. State a short implementation plan for the current milestone.
3. Implement Milestone 1 in small, coherent steps.
4. Run the tests and start the application long enough to verify it launches.
5. Report what works, any limitations, and the exact next step.

Additional rules:

- Do not commit or push to GitHub unless the user explicitly asks.
- Do not add API keys, credentials, personal data, virtual environments, caches, or generated databases to Git.
- Avoid silently changing the agreed feature scope or technology stack.
- Validate data on the server even if it is also validated in JavaScript.
- Add comments for non-obvious reasoning, not for self-evident syntax.
- Keep user-facing language cautious: the application supports reflection and does not guarantee that a real-world decision is objectively optimal.
- Prioritize a working, testable slice over placeholders for many unfinished features.

## First instruction

Begin with **Milestone 1 only**. Before editing, briefly describe the files you will create and how the evaluator will work. Then implement the milestone, test it, and update the README. Stop after reporting the verified Milestone 1 result and proposed next step.
