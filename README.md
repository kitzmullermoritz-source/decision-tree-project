# decision-tree-project

A visual decision-tree and expected-utility assistant for complex decisions

## What this is (Milestone 1)

A Flask app that stores decision trees (decision nodes, chance nodes, and
outcome nodes) in SQLite, evaluates them with expected utility and
backward induction, and shows the recommended action at every decision
node in a readable, non-graphical page. One example analysis ("Launch a
new product?") is seeded automatically.

The evaluator itself (`decision_engine.py`) has no dependency on Flask or
SQLite, so it can be tested and reasoned about on its own.

## Setup

Requires Python 3. From the project root:

```
python -m venv venv
```

Activate the virtual environment:

- Windows (PowerShell): `venv\Scripts\Activate.ps1`
- Windows (Git Bash / bash): `source venv/Scripts/activate`
- macOS/Linux: `source venv/bin/activate`

Install dependencies:

```
pip install -r requirements.txt
```

## Run the tests

```
python -m pytest tests/
```

All 18 evaluator tests should pass.

## Run the app

```
python app.py
```

This creates `decisions.db` (a SQLite file, ignored by git) if it does
not already exist, seeds the example analysis the first time, and starts
the Flask development server. Visit http://127.0.0.1:5000/ in a browser.

The home page lists analyses; clicking one shows the full tree with each
node's expected value and the recommended choice highlighted at every
decision point.

## Project structure

```
decision-tree-project/
|-- app.py                       Flask routes
|-- decision_engine.py           Framework-independent evaluator
|-- database.py                  SQLite connection, schema init, seed data
|-- schema.sql                   Idempotent table definitions
|-- requirements.txt
|-- templates/                   Jinja templates
|-- static/                      CSS
|-- tests/
|   `-- test_decision_engine.py  Evaluator unit tests
`-- CLAUDE.md                    Project brief and working rules
```

## Status

Milestone 1 (working vertical slice) is complete: the evaluator is
implemented and tested, the schema and seed data exist, and the app
starts locally and displays the example analysis with its computed
expected values and recommended strategy.

Not yet implemented: creating/editing analyses through the UI (Milestone
2), the visual Cytoscape.js tree editor (Milestone 3), plain-language
explanations and sensitivity analysis (Milestone 4).
