"""Loading, saving and querying expenses in a JSON file."""

import datetime
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from pydantic import ValidationError

from .errors import ExpenseNotFoundError, StoreError
from .models import Expense


class ExpenseStore:
    """All expenses in one JSON file. Changes are saved immediately."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._expenses: list[Expense] = self._load()

    def _load(self) -> list[Expense]:
        """Read expenses from the JSON file. A missing file means no expenses yet."""
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError as e:
            raise StoreError(self.path, f"could not read file ({e.strerror})") from e
        except json.JSONDecodeError as e:
            raise StoreError(self.path, f"invalid JSON ({e})") from e

        if not isinstance(raw, list):
            raise StoreError(self.path, "invalid expense data (expected a JSON list)")
        try:
            return [Expense.model_validate(item) for item in raw]
        except ValidationError as e:
            raise StoreError(self.path, f"invalid expense data ({e.errors()[0]['msg']})") from e

    def _save(self) -> None:
        """Write all expenses to the JSON file safely (atomic write)."""
        data = [expense.model_dump(mode="json") for expense in self._expenses]
        tmp = self.path.with_suffix(".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            tmp.replace(self.path)
        except OSError as e:
            raise StoreError(self.path, f"could not write file ({e.strerror})") from e

    def _next_id(self) -> int:
        """Return one more than the highest existing id, or 1 if there are none."""
        return max((e.id for e in self._expenses), default=0) + 1

    def add(
        self,
        amount: Decimal,
        category: str,
        description: str = "",
        date: datetime.date | None = None,
    ) -> Expense:
        """Create, save and return a new expense. The date defaults to today."""
        expense = Expense(
            id=self._next_id(),
            amount=amount,
            category=category,
            description=description,
            date=date or datetime.date.today(),
        )
        self._expenses.append(expense)
        self._save()
        return expense

    def list(self, *, category: str | None = None, month: str | None = None) -> list[Expense]:
        """Return expenses sorted by date, optionally filtered by category and/or month."""
        result = self._expenses
        if category:
            wanted = category.strip().lower()
            result = [e for e in result if e.category == wanted]
        if month:
            result = [e for e in result if e.month == month]
        return sorted(result, key=lambda e: (e.date, e.id))

    def delete(self, expense_id: int) -> Expense:
        """Remove and return the expense with this id, or raise ExpenseNotFoundError."""
        for index, expense in enumerate(self._expenses):
            if expense.id == expense_id:
                removed = self._expenses.pop(index)
                self._save()
                return removed
        raise ExpenseNotFoundError(expense_id)

    def summary(self, *, month: str | None = None) -> dict[str, Decimal]:
        """Return the total per category, highest first."""
        totals: defaultdict[str, Decimal] = defaultdict(Decimal)
        for expense in self.list(month=month):
            totals[expense.category] += expense.amount
        return dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    def total(self, *, month: str | None = None) -> Decimal:
        """Return the sum of all expenses, optionally for one month."""
        return sum((e.amount for e in self.list(month=month)), Decimal("0.00"))
