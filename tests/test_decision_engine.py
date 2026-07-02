import pytest

from decision_engine import DecisionTreeError, evaluate, evaluate_tree, validate_tree


def outcome(node_id, utility):
    return {"id": node_id, "type": "outcome", "utility": utility, "children": []}


def chance(node_id, children):
    """children: list of (child_id, probability)."""
    return {
        "id": node_id,
        "type": "chance",
        "utility": None,
        "children": [
            {"child_id": child_id, "probability": probability}
            for child_id, probability in children
        ],
    }


def decision(node_id, child_ids):
    return {
        "id": node_id,
        "type": "decision",
        "utility": None,
        "children": [{"child_id": child_id, "probability": None} for child_id in child_ids],
    }


def by_id(*nodes):
    return {node["id"]: node for node in nodes}


# --- basic evaluation -------------------------------------------------


def test_outcome_evaluates_to_its_utility():
    nodes = by_id(outcome("o1", 42))
    assert evaluate(nodes, "o1")["value"] == 42


def test_outcome_utility_may_be_negative():
    nodes = by_id(outcome("o1", -10))
    assert evaluate(nodes, "o1")["value"] == -10


def test_chance_node_computes_expected_value():
    nodes = by_id(
        chance("c1", [("o1", 0.5), ("o2", 0.5)]),
        outcome("o1", 100),
        outcome("o2", 0),
    )
    assert evaluate(nodes, "c1")["value"] == pytest.approx(50)


def test_decision_node_picks_max_and_reports_best_child():
    nodes = by_id(
        decision("d1", ["o1", "o2"]),
        outcome("o1", 10),
        outcome("o2", 30),
    )
    result = evaluate(nodes, "d1")
    assert result["value"] == 30
    assert result["best_children"] == ["o2"]


def test_decision_node_reports_ties():
    nodes = by_id(
        decision("d1", ["o1", "o2"]),
        outcome("o1", 20),
        outcome("o2", 20),
    )
    result = evaluate(nodes, "d1")
    assert result["value"] == 20
    assert set(result["best_children"]) == {"o1", "o2"}


def test_nested_tree_evaluates_recursively():
    # Decision between a sure thing and a gamble.
    nodes = by_id(
        decision("d1", ["o_sure", "c_gamble"]),
        outcome("o_sure", 50),
        chance("c_gamble", [("o_win", 0.5), ("o_lose", 0.5)]),
        outcome("o_win", 200),
        outcome("o_lose", 0),
    )
    result = evaluate(nodes, "d1")
    assert result["value"] == 100
    assert result["best_children"] == ["c_gamble"]


def test_evaluate_tree_validates_before_evaluating():
    nodes = by_id(outcome("o1", 10))
    result = evaluate_tree(nodes, "o1")
    assert result["value"] == 10


# --- validation: structure --------------------------------------------


def test_missing_root_is_rejected():
    nodes = by_id(outcome("o1", 10))
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "does_not_exist")


def test_cycle_is_rejected():
    nodes = {
        "d1": {"id": "d1", "type": "decision", "utility": None,
               "children": [{"child_id": "d2", "probability": None}]},
        "d2": {"id": "d2", "type": "decision", "utility": None,
               "children": [{"child_id": "d1", "probability": None}]},
    }
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "d1")


def test_unreachable_node_is_rejected():
    nodes = by_id(
        outcome("o1", 10),
        outcome("o2", 20),  # not connected to root
    )
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "o1")


def test_outcome_node_with_children_is_rejected():
    nodes = {
        "o1": {"id": "o1", "type": "outcome", "utility": 10,
               "children": [{"child_id": "o2", "probability": None}]},
        "o2": {"id": "o2", "type": "outcome", "utility": 20, "children": []},
    }
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "o1")


def test_non_outcome_node_without_children_is_rejected():
    nodes = by_id(decision("d1", []))
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "d1")


def test_outcome_missing_utility_is_rejected():
    nodes = by_id(outcome("o1", None))
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "o1")


def test_missing_child_reference_is_rejected():
    nodes = by_id(decision("d1", ["ghost"]))
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "d1")


# --- validation: probabilities -----------------------------------------


def test_chance_probabilities_must_sum_to_one():
    nodes = by_id(
        chance("c1", [("o1", 0.5), ("o2", 0.4)]),
        outcome("o1", 10),
        outcome("o2", 20),
    )
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "c1")


def test_chance_probabilities_within_tolerance_are_accepted():
    nodes = by_id(
        chance("c1", [("o1", 0.5 + 1e-9), ("o2", 0.5 - 1e-9)]),
        outcome("o1", 10),
        outcome("o2", 20),
    )
    validate_tree(nodes, "c1")  # should not raise


def test_chance_probability_out_of_range_is_rejected():
    nodes = by_id(
        chance("c1", [("o1", 1.5), ("o2", -0.5)]),
        outcome("o1", 10),
        outcome("o2", 20),
    )
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "c1")


def test_chance_child_missing_probability_is_rejected():
    nodes = {
        "c1": {"id": "c1", "type": "chance", "utility": None,
               "children": [{"child_id": "o1", "probability": None}]},
        "o1": {"id": "o1", "type": "outcome", "utility": 10, "children": []},
    }
    with pytest.raises(DecisionTreeError):
        validate_tree(nodes, "c1")
