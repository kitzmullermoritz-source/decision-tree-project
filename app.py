from flask import Flask, abort, render_template

from database import get_db, init_db, load_tree, seed_example_analysis
from decision_engine import DecisionTreeError, evaluate, evaluate_tree

app = Flask(__name__)


@app.route("/")
def index():
    connection = get_db()
    analyses = connection.execute(
        "SELECT id, title, description FROM analyses ORDER BY id"
    ).fetchall()
    connection.close()
    return render_template("index.html", analyses=analyses)


@app.route("/analysis/<int:analysis_id>")
def analysis(analysis_id):
    connection = get_db()
    analysis_row = connection.execute(
        "SELECT id, title, description FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    if analysis_row is None:
        connection.close()
        abort(404)

    nodes, root_node_id = load_tree(connection, analysis_id)
    connection.close()

    error = None
    results = {}
    if root_node_id is None:
        error = "This analysis has no root node yet."
    else:
        try:
            evaluate_tree(nodes, root_node_id)
            results = _evaluate_all_nodes(nodes)
        except DecisionTreeError as exc:
            error = str(exc)

    return render_template(
        "analysis.html",
        analysis=analysis_row,
        nodes=nodes,
        root_node_id=root_node_id,
        results=results,
        error=error,
    )


def _evaluate_all_nodes(nodes):
    """Evaluate every node so the template can show a value at each branch."""
    return {node_id: evaluate(nodes, node_id) for node_id in nodes}


if __name__ == "__main__":
    init_db()
    connection = get_db()
    seed_example_analysis(connection)
    connection.close()
    app.run(debug=True)
