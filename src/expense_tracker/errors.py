"""Exceptions raised by the expense tracker."""

from pathlib import Path


class TrackerError(Exception):
    """Base class for all expense tracker errors.

    Catch this to handle any tracker failure in one place (e.g. in the CLI).
    """


class StoreError(TrackerError):
    """The expense file could not be read or written, or holds invalid data (e.g. corrupt JSON)."""

    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = Path(path)
        self.reason = reason
        super().__init__(f"{reason} in {self.path}")


class ExpenseNotFoundError(TrackerError):
    """No expense exists with the requested id (raised by ExpenseStore.delete)."""

    def __init__(self, expense_id: int) -> None:
        self.expense_id = expense_id
        super().__init__(f"expense #{expense_id} not found")
