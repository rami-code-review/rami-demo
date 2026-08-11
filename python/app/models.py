"""Request and response schemas for the ledger API."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """A transaction category."""

    income = "income"
    food = "food"
    housing = "housing"
    transport = "transport"
    utilities = "utilities"
    entertainment = "entertainment"
    health = "health"
    other = "other"


def to_cents(amount: Decimal) -> int:
    """Convert a decimal amount to integer cents, rounding half up to the nearest cent."""
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def from_cents(cents: int) -> Decimal:
    """Convert integer cents back to a decimal amount."""
    return (Decimal(cents) / 100).quantize(Decimal("0.01"))


class TransactionIn(BaseModel):
    """An incoming transaction to record."""

    amount: Decimal = Field(..., description="Amount in the major currency unit, e.g. 12.50.")
    category: Category
    description: str = Field(default="", max_length=200)
    date: date

    @field_validator("amount")
    @classmethod
    def amount_rounds_to_a_positive_cent(cls, value: Decimal) -> Decimal:
        """Reject amounts that do not round to at least one cent."""
        if to_cents(value) <= 0:
            raise ValueError("amount must be at least one cent")
        return value


class TransactionOut(BaseModel):
    """A stored transaction returned to the client."""

    id: int
    amount: Decimal
    category: Category
    description: str
    date: date


class CategoryTotal(BaseModel):
    """The summed amount for a single category within a period."""

    category: Category
    total: Decimal


class Summary(BaseModel):
    """A monthly summary: per-category totals plus the overall total."""

    month: str
    totals: list[CategoryTotal]
    total: Decimal


class RecurrenceFrequency(str, Enum):
    """How often a recurring transaction repeats."""

    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class RecurringRuleIn(BaseModel):
    """A new recurring transaction rule to define."""

    amount: Decimal = Field(..., description="Amount in the major currency unit, e.g. 12.50.")
    category: Category
    description: str = Field(default="", max_length=200)
    frequency: RecurrenceFrequency
    start_date: date
    end_date: date | None = None

    @field_validator("amount")
    @classmethod
    def amount_rounds_to_a_positive_cent(cls, value: Decimal) -> Decimal:
        """Reject amounts that do not round to at least one cent."""
        if to_cents(value) <= 0:
            raise ValueError("amount must be at least one cent")
        return value


class RecurringRuleOut(BaseModel):
    """A stored recurring transaction rule returned to the client."""

    id: int
    amount: Decimal
    category: Category
    description: str
    frequency: RecurrenceFrequency
    start_date: date
    end_date: date | None
