"""The Expense data model."""

import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class Expense(BaseModel):
    """A single expense. Validated on creation and when loaded from disk."""

    id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, decimal_places=2)
    category: str
    description: str = ""
    date: datetime.date = Field(default_factory=datetime.date.today)

    @field_validator("amount")
    @classmethod
    def two_decimal_places(cls, value: Decimal) -> Decimal:
        """Always store exactly 2 decimal places (45 -> 45.00)."""
        return value.quantize(Decimal("0.01"))

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("category must not be empty")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return value.strip()

    @property
    def month(self) -> str:
        """The expense's month as 'YYYY-MM'."""
        return self.date.strftime("%Y-%m")
