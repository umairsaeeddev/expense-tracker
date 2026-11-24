import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from expense_tracker.errors import ExpenseNotFoundError, StoreError
from expense_tracker.store import ExpenseStore


@pytest.fixture
def path(tmp_path: Path) -> Path:
    return tmp_path / "expenses.json"


@pytest.fixture
def store(path: Path) -> ExpenseStore:
    store = ExpenseStore(path)
    store.add(Decimal("12.50"), "food", "Lunch", datetime.date(2026, 11, 2))
    store.add(Decimal("45"), "transport", "Fuel", datetime.date(2026, 11, 3))
    store.add(Decimal("8.75"), "food", "Coffee beans", datetime.date(2026, 11, 5))
    store.add(Decimal("120"), "bills", "Internet", datetime.date(2026, 10, 28))
    return store


def test_new_store_on_missing_file_is_empty(path: Path) -> None:
    store = ExpenseStore(path)
    assert store.list() == []
    assert not path.exists()


def test_add_assigns_ids_1_2_3(path: Path) -> None:
    store = ExpenseStore(path)
    ids = [store.add(Decimal("1"), "food").id for _ in range(3)]
    assert ids == [1, 2, 3]


def test_add_defaults_date_to_today(path: Path) -> None:
    expense = ExpenseStore(path).add(Decimal("1"), "food")
    assert expense.date == datetime.date.today()


def test_ids_are_not_reused_after_delete(path: Path) -> None:
    store = ExpenseStore(path)
    for _ in range(3):
        store.add(Decimal("1"), "food")
    store.delete(2)
    assert store.add(Decimal("1"), "food").id == 4


def test_data_survives_reload(store: ExpenseStore, path: Path) -> None:
    reloaded = ExpenseStore(path)
    assert reloaded.list() == store.list()
    assert len(reloaded.list()) == 4


def test_atomic_write_leaves_no_temp_file(store: ExpenseStore, path: Path) -> None:
    assert path.exists()
    assert not path.with_suffix(".tmp").exists()


def test_list_is_sorted_by_date(store: ExpenseStore) -> None:
    assert [e.id for e in store.list()] == [4, 1, 2, 3]


def test_list_filters_by_month(store: ExpenseStore) -> None:
    assert [e.id for e in store.list(month="2026-11")] == [1, 2, 3]


def test_list_filters_by_category(store: ExpenseStore) -> None:
    assert [e.id for e in store.list(category="FOOD")] == [1, 3]


def test_list_filters_by_month_and_category(store: ExpenseStore) -> None:
    assert store.list(category="bills", month="2026-11") == []


def test_summary_is_highest_first(store: ExpenseStore) -> None:
    assert store.summary() == {
        "bills": Decimal("120.00"),
        "transport": Decimal("45.00"),
        "food": Decimal("21.25"),
    }
    assert list(store.summary(month="2026-11")) == ["transport", "food"]


def test_total_uses_exact_decimal_arithmetic(store: ExpenseStore) -> None:
    assert store.total() == Decimal("186.25")
    assert store.total(month="2026-11") == Decimal("66.25")


def test_total_of_empty_store_is_zero(path: Path) -> None:
    assert ExpenseStore(path).total() == Decimal("0")


def test_delete_returns_and_removes_expense(store: ExpenseStore, path: Path) -> None:
    removed = store.delete(2)
    assert removed.description == "Fuel"
    assert 2 not in [e.id for e in ExpenseStore(path).list()]


def test_delete_unknown_id_raises(store: ExpenseStore) -> None:
    with pytest.raises(ExpenseNotFoundError):
        store.delete(99)


def test_corrupt_json_raises_store_error(path: Path) -> None:
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(StoreError):
        ExpenseStore(path)


def test_invalid_data_raises_store_error(path: Path) -> None:
    path.write_text('[{"id": 1, "amount": "-5", "category": "food"}]', encoding="utf-8")
    with pytest.raises(StoreError):
        ExpenseStore(path)
