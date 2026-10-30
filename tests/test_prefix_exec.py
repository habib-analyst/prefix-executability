"""Tests for prefix-executability: scorer formulas, checker repair, arms."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prefix_exec.agents import inject_defects, run_checked, run_policy
from prefix_exec.run import run_experiment
from prefix_exec.scorer import aggregate, replay
from prefix_exec.tasks import generate_tasks, make_goal
from prefix_exec.tools import execute, validate
from prefix_exec.world import new_world


def _world():
    return new_world(7)


def test_schema_violation_fed_1():
    w = _world()
    traj = [{"tool": "create_order", "args": {"product_id": "PR-001", "qty": "2"}}]
    fed, _, kinds = replay(w, traj)
    assert fed == 1 and kinds[0] == "schema"


def test_stale_ref_fed_2():
    w = _world()
    traj = [{"tool": "search_flights", "args": {"origin": "JFK", "dest": "LAX", "date": "2026-12-01"}},
            {"tool": "get_flight", "args": {"flight_id": "FL-9999"}}]
    fed, _, kinds = replay(w, traj)
    assert fed == 2 and kinds[1] == "unknown_ref"


def test_precondition_violation():
    # pay before confirm: booking held, not confirmed.
    w = _world()
    ok, out, _ = execute(w, "create_booking", {"flight_id": "FL-001", "passenger": "PAX1"})
    assert ok
    ok, _ = validate(w, "pay_booking", {"booking_id": out["booking_id"], "amount": 100})
    assert not ok
    fed, _, kinds = replay(_world(), [
        {"tool": "create_booking", "args": {"flight_id": "FL-001", "passenger": "PAX1"}},
        {"tool": "pay_booking", "args": {"booking_id": "BK-001", "amount": 100}}])
    assert fed == 2 and kinds[1] == "precondition"


def test_fully_valid_fed_is_T_plus_1():
    w = _world()
    traj = [{"tool": "search_flights", "args": {"origin": "JFK", "dest": "LAX", "date": "2026-12-01"}},
            {"tool": "get_flight", "args": {"flight_id": "FL-001"}}]
    fed, _, _ = replay(w, traj)
    assert fed == 3


def test_metric_formulas_hand_computed():
    # Rows: (T=4, FED=5, Y=1), (T=4, FED=2, Y=0), (T=2, FED=1, Y=1)
    rows = [{"T": 4, "fed": 5, "success": True},
            {"T": 4, "fed": 2, "success": False},
            {"T": 2, "fed": 1, "success": True}]
    m = aggregate(rows)
    assert m["TER"] == 1 / 3
    assert abs(m["AUC_PEC"] - ((4 / 4) + (1 / 4) + (0 / 2)) / 3) < 1e-12
    assert m["success"] == 2 / 3
    assert m["PEC"][0] == 1.0 and m["PEC"][1] == 2 / 3 and m["PEC"][4] == 1 / 3
    assert m["RR"] == 0.5 and m["RR_eligible"] == 2


def test_checker_repairs_skip_defect():
    tasks = generate_tasks(20, 101)
    task = next(t for t in tasks if t["family"] == "oneway")
    world = new_world(task["world_seed"])
    plan = run_policy(task, world, coordinated=True)
    # Drop the confirm step manually (a skip defect).
    defective = [c for c in plan if c["tool"] != "confirm_booking"]
    assert len(defective) == len(plan) - 1
    executed = run_checked(task, world, defective, repair=True)
    goal = make_goal(task)
    fed, final, _ = replay(world, executed)
    assert fed == len(executed) + 1  # fully executable after repair
    assert goal(final) is True


def test_checker_repairs_stale_ref():
    tasks = generate_tasks(20, 101)
    task = next(t for t in tasks if t["family"] == "oneway")
    world = new_world(task["world_seed"])
    plan = run_policy(task, world, coordinated=True)
    defective = []
    for c in plan:
        c2 = dict(c, args=dict(c["args"]))
        if c2["tool"] == "create_booking":
            c2["args"]["flight_id"] = "FL-9999"
        defective.append(c2)
    executed = run_checked(task, world, defective, repair=True)
    goal = make_goal(task)
    fed, final, _ = replay(world, executed)
    assert fed == len(executed) + 1
    assert goal(final) is True


def test_check_drop_drops_invalid():
    tasks = generate_tasks(20, 101)
    task = next(t for t in tasks if t["family"] == "oneway")
    world = new_world(task["world_seed"])
    plan = run_policy(task, world, coordinated=True)
    defective = [dict(c, args=dict(c["args"])) for c in plan]
    for c in defective:
        if c["tool"] == "create_booking":
            c["args"]["flight_id"] = "FL-9999"
    executed = run_checked(task, world, defective, repair=False)
    fed, _, _ = replay(world, executed)
    assert fed == len(executed) + 1  # dropped invalids -> executed is clean
    assert len(executed) < len(defective)


def test_baseline_trajectories_fully_executable():
    tasks = generate_tasks(50, 55)
    for task in tasks:
        world = new_world(task["world_seed"])
        traj = run_policy(task, world, coordinated=False)
        fed, _, _ = replay(world, traj)
        assert fed == len(traj) + 1


def test_small_experiment_runs_and_is_deterministic():
    r1 = run_experiment(40, 999)
    r2 = run_experiment(40, 999)
    assert r1 == r2
    assert set(r1["arms"]) == {"baseline", "plan", "check_drop", "check_repair"}
    for arm in r1["arms"]:
        assert 0.0 <= r1["arms"][arm]["TER"] <= 1.0
        assert 0.0 <= r1["arms"][arm]["success"] <= 1.0


def test_defect_injection_deterministic():
    import random
    traj = [{"tool": "create_order", "args": {"product_id": "PR-001", "qty": 2}},
            {"tool": "pay_order", "args": {"order_id": "OR-001", "amount": 40}}]
    a, _ = inject_defects(traj, random.Random(3), 1.0, 1.0, 1.0)
    b, _ = inject_defects(traj, random.Random(3), 1.0, 1.0, 1.0)
    assert a == b
