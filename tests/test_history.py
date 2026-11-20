import pytest
import os
from aibenchmark.history import init_db, create_run, insert_result, get_runs, get_results_for_run, get_latest_run_id, get_trend_data


def test_init_db():
    test_db = "test_history.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    assert os.path.exists(test_db)
    os.remove(test_db)


def test_create_run_and_get_runs():
    test_db = "test_history.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    run_id = create_run(test_db, "test notes")
    assert run_id is not None
    runs = get_runs(test_db)
    assert len(runs) == 1
    assert runs[0].notes == "test notes"
    os.remove(test_db)


def test_insert_result_and_get_results():
    test_db = "test_history.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    run_id = create_run(test_db, "test")
    insert_result(
        test_db, run_id, "ollama", "llama3.2", "coding", "coding_001",
        0.8, 1500, "passed", None,
    )
    results = get_results_for_run(test_db, run_id)
    assert len(results) == 1
    assert results[0].provider == "ollama"
    assert results[0].model == "llama3.2"
    assert results[0].score == 0.8
    os.remove(test_db)


def test_get_latest_run_id_empty():
    test_db = "test_history.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    assert get_latest_run_id(test_db) is None
    os.remove(test_db)


def test_trend_data():
    test_db = "test_history.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    run_id1 = create_run(test_db, "run1")
    run_id2 = create_run(test_db, "run2")
    insert_result(test_db, run_id1, "ollama", "llama3.2", "coding", "coding_001", 0.6, 100, "passed", None)
    insert_result(test_db, run_id2, "ollama", "llama3.2", "coding", "coding_001", 0.8, 120, "passed", None)
    trend = get_trend_data(test_db, "coding", "llama3.2", "ollama")
    assert len(trend) == 2
    assert trend[0].score == 0.6
    assert trend[1].score == 0.8
    os.remove(test_db)
