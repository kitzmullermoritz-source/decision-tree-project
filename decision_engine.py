"""Framework-independent decision tree evaluator.

A tree is described with plain dictionaries so this module has no
dependency on Flask or SQLite and can be tested in isolation.

Node dict shape:
    {
        "id": <hashable>,
        "type": "decision" | "chance" | "outcome",
        "utility": float | None,   # required only for "outcome"
        "children": [
            {"child_id": <hashable>, "probability": float | None},
            ...
        ],
    }

"probability" is required (and must be a number in [0, 1]) only on the
children of a "chance" node. It is ignored for "decision" node children.

Probabilities are compared with a fixed tolerance because floating point
sums of user-entered percentages rarely land on exactly 1.0.
"""

PROBABILITY_TOLERANCE = 1e-6


class DecisionTreeError(ValueError):
    """Raised when a tree is structurally or numerically invalid."""


def validate_tree(nodes, root_id):
    """Check structural and numerical validity of a tree.

    `nodes` is a dict mapping node id -> node dict (see module docstring).
    Raises DecisionTreeError on the first problem found. Returns None on
    success.
    """
    if root_id not in nodes:
        raise DecisionTreeError(f"Root node '{root_id}' is not in the tree.")

    _check_node_shapes(nodes)
    _check_reachability_and_cycles(nodes, root_id)


def _check_node_shapes(nodes):
    for node_id, node in nodes.items():
        node_type = node.get("type")
        children = node.get("children", [])

        if node_type not in ("decision", "chance", "outcome"):
            raise DecisionTreeError(
                f"Node '{node_id}' has unknown type '{node_type}'."
            )

        if node_type == "outcome":
            if children:
                raise DecisionTreeError(
                    f"Outcome node '{node_id}' must not have children."
                )
            if node.get("utility") is None:
                raise DecisionTreeError(
                    f"Outcome node '{node_id}' is missing a utility value."
                )
        else:
            if not children:
                raise DecisionTreeError(
                    f"{node_type.capitalize()} node '{node_id}' "
                    "must have at least one child."
                )
            for child in children:
                child_id = child.get("child_id")
                if child_id not in nodes:
                    raise DecisionTreeError(
                        f"Node '{node_id}' references missing child "
                        f"'{child_id}'."
                    )

        if node_type == "chance":
            _check_chance_probabilities(node_id, children)


def _check_chance_probabilities(node_id, children):
    total = 0.0
    for child in children:
        probability = child.get("probability")
        if probability is None:
            raise DecisionTreeError(
                f"Chance node '{node_id}' has a child with no "
                "probability assigned."
            )
        if not (0.0 <= probability <= 1.0):
            raise DecisionTreeError(
                f"Chance node '{node_id}' has an out-of-range probability "
                f"({probability}); probabilities must be within [0, 1]."
            )
        total += probability

    if abs(total - 1.0) > PROBABILITY_TOLERANCE:
        raise DecisionTreeError(
            f"Chance node '{node_id}' outgoing probabilities sum to "
            f"{total}, not 1."
        )


def _check_reachability_and_cycles(nodes, root_id):
    visited = set()
    in_progress = set()

    def visit(node_id):
        if node_id in in_progress:
            raise DecisionTreeError(
                f"Cycle detected: node '{node_id}' is its own ancestor."
            )
        if node_id in visited:
            return
        in_progress.add(node_id)
        for child in nodes[node_id].get("children", []):
            visit(child["child_id"])
        in_progress.remove(node_id)
        visited.add(node_id)

    visit(root_id)

    unreachable = set(nodes.keys()) - visited
    if unreachable:
        raise DecisionTreeError(
            f"Unreachable node(s) from root: {sorted(unreachable)}."
        )


def evaluate(nodes, node_id):
    """Recursively evaluate the expected utility of a node.

    Returns a dict:
        {
            "value": float,
            "best_children": [child_id, ...],  # decision nodes only,
                                                # empty list otherwise
        }

    Assumes `validate_tree` has already been called on this tree; this
    function does not re-check structure or probability sums.
    """
    node = nodes[node_id]
    node_type = node["type"]

    if node_type == "outcome":
        return {"value": float(node["utility"]), "best_children": []}

    if node_type == "chance":
        total = 0.0
        for child in node["children"]:
            child_value = evaluate(nodes, child["child_id"])["value"]
            total += child["probability"] * child_value
        return {"value": total, "best_children": []}

    if node_type == "decision":
        child_values = [
            (child["child_id"], evaluate(nodes, child["child_id"])["value"])
            for child in node["children"]
        ]
        best_value = max(value for _, value in child_values)
        best_children = [
            child_id
            for child_id, value in child_values
            if abs(value - best_value) <= PROBABILITY_TOLERANCE
        ]
        return {"value": best_value, "best_children": best_children}

    raise DecisionTreeError(f"Node '{node_id}' has unknown type '{node_type}'.")


def evaluate_tree(nodes, root_id):
    """Validate and evaluate an entire tree from its root.

    Convenience wrapper combining validate_tree() and evaluate() that
    callers (e.g. the Flask routes) should generally use instead of
    calling evaluate() directly on unvalidated data.
    """
    validate_tree(nodes, root_id)
    return evaluate(nodes, root_id)
