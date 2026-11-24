import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from expense_tracker.models import Expense


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("food", "food"), ("Food", "food"), ("  TRANSPORT  ", "transport"), ("Bills\n", "bills")],
)
def test_category_is_stripped_and_lowercased(raw: str, expected: str) -> None:
    expense = Expense(id=1, amount=Decimal("10"), category=raw)
    assert expense.category == expected


def test_empty_category_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Expense(id=1, amount=Decimal("10"), category="   ")


@pytest.mark.parametrize("amount", ["0", "-5", "-0.01"])
def test_zero_and_negative_amounts_are_rejected(amount: str) -> None:
    with pytest.raises(ValidationError):
        Expense(id=1, amount=Decimal(amount), category="food")


def test_three_decimal_places_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Expense(id=1, amount=Decimal("1.234"), category="food")


def test_amount_is_stored_with_two_decimal_places() -> None:
    expense = Expense(id=1, amount=Decimal("45"), category="food")
    assert str(expense.amount) == "45.00"


def test_description_is_stripped() -> None:
    expense = Expense(id=1, amount=Decimal("1"), category="food", description="  Lunch  ")
    assert expense.description == "Lunch"


def test_month_property() -> None:
    expense = Expense(id=1, amount=Decimal("1"), category="food", date=datetime.date(2026, 3, 9))
    assert expense.month == "2026-03"


def test_default_date_is_today() -> None:
    expense = Expense(id=1, amount=Decimal("1"), category="food")
    assert expense.date == datetime.date.today()
