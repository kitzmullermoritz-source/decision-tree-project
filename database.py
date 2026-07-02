"""SQLite access layer: connection handling, schema init, and the
translation between database rows and the plain-dict tree shape that
decision_engine.py expects.
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "decisions.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    connection = get_db()
    with open(SCHEMA_PATH) as schema_file:
        connection.executescript(schema_file.read())
    connection.commit()
    connection.close()


def load_tree(connection, analysis_id):
    """Load one analysis's nodes/edges into the dict shape decision_engine expects.

    Returns (nodes, root_node_id) where nodes maps node id -> node dict.
    """
    node_rows = connection.execute(
        "SELECT id, node_type, label, utility FROM nodes WHERE analysis_id = ?",
        (analysis_id,),
    ).fetchall()

    nodes = {
        row["id"]: {
            "id": row["id"],
            "type": row["node_type"],
            "label": row["label"],
            "utility": row["utility"],
            "children": [],
        }
        for row in node_rows
    }

    edge_rows = connection.execute(
        "SELECT source_node_id, target_node_id, label, probability "
        "FROM edges WHERE analysis_id = ?",
        (analysis_id,),
    ).fetchall()

    for row in edge_rows:
        nodes[row["source_node_id"]]["children"].append(
            {
                "child_id": row["target_node_id"],
                "probability": row["probability"],
                "label": row["label"],
            }
        )

    analysis_row = connection.execute(
        "SELECT root_node_id FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    root_node_id = analysis_row["root_node_id"] if analysis_row else None

    return nodes, root_node_id


def seed_example_analysis(connection):
    """Insert one small example analysis if the database is otherwise empty.

    Example: whether to launch a new product now, launch after more
    testing, or not launch at all. Modeled as a decision node whose
    "launch now" branch is a chance node over market reception.
    """
    existing = connection.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()
    if existing["n"] > 0:
        return

    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO analyses (title, description) VALUES (?, ?)",
        (
            "Launch a new product?",
            "Should we launch now, delay for more testing, or not launch at all?",
        ),
    )
    analysis_id = cursor.lastrowid

    def add_node(node_type, label, utility=None):
        cursor.execute(
            "INSERT INTO nodes (analysis_id, node_type, label, utility) "
            "VALUES (?, ?, ?, ?)",
            (analysis_id, node_type, label, utility),
        )
        return cursor.lastrowid

    def add_edge(source_id, target_id, label=None, probability=None):
        cursor.execute(
            "INSERT INTO edges (analysis_id, source_node_id, target_node_id, "
            "label, probability) VALUES (?, ?, ?, ?, ?)",
            (analysis_id, source_id, target_id, label, probability),
        )

    root = add_node("decision", "Launch decision")

    launch_now = add_node("chance", "Market reaction if launched now")
    strong_reception = add_node("outcome", "Strong reception", utility=80)
    weak_reception = add_node("outcome", "Weak reception", utility=-20)

    delay = add_node("chance", "Market reaction if launched after more testing")
    strong_reception_delayed = add_node("outcome", "Strong reception (delayed)", utility=60)
    weak_reception_delayed = add_node("outcome", "Weak reception (delayed)", utility=10)

    no_launch = add_node("outcome", "Do not launch", utility=0)

    add_edge(root, launch_now, label="Launch now")
    add_edge(root, delay, label="Delay and test more")
    add_edge(root, no_launch, label="Do not launch")

    add_edge(launch_now, strong_reception, probability=0.6)
    add_edge(launch_now, weak_reception, probability=0.4)

    add_edge(delay, strong_reception_delayed, probability=0.8)
    add_edge(delay, weak_reception_delayed, probability=0.2)

    cursor.execute(
        "UPDATE analyses SET root_node_id = ? WHERE id = ?", (root, analysis_id)
    )

    connection.commit()
