"""Command-line interface: argument parsing and output formatting."""

import argparse
import datetime
import sys
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError

from .errors import TrackerError
from .models import Expense
from .store import ExpenseStore


def parse_amount(text: str) -> Decimal:
    """Turn the AMOUNT argument into a Decimal. Range checks are left to the Expense model."""
    try:
        return Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"invalid amount: {text!r}") from None


def parse_month(text: str) -> str:
    """Accept 'YYYY-MM' and return it normalised (e.g. '2026-1' -> '2026-01')."""
    try:
        return datetime.datetime.strptime(text.strip(), "%Y-%m").strftime("%Y-%m")
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid month (use YYYY-MM): {text!r}") from None


def parse_date(text: str) -> datetime.date:
    """Accept 'YYYY-MM-DD' and return a date."""
    try:
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date (use YYYY-MM-DD): {text!r}") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense-tracker", description="Track expenses in a JSON file."
    )
    parser.add_argument("--file", default="expenses.json", help="where expenses are stored")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add an expense")
    add.add_argument("amount", type=parse_amount, help="the amount, e.g. 12.50")
    add.add_argument("category", help="the category, e.g. food")
    add.add_argument("description", nargs="?", default="", help="optional description")
    add.add_argument(
        "--date",
        type=parse_date,
        metavar="YYYY-MM-DD",
        help="the date of the expense (default: today)",
    )

    lst = sub.add_parser("list", help="list expenses")
    lst.add_argument("--category", help="only show this category")
    lst.add_argument("--month", type=parse_month, metavar="YYYY-MM", help="only show this month")

    summary = sub.add_parser("summary", help="show totals per category")
    summary.add_argument(
        "--month", type=parse_month, metavar="YYYY-MM", help="only summarise this month"
    )

    delete = sub.add_parser("delete", help="delete an expense")
    delete.add_argument("id", type=int, help="the id of the expense to delete")

    return parser


def format_validation_error(exc: ValidationError) -> str:
    """Return the first validation error as 'field: message'."""
    first = exc.errors()[0]
    field = ".".join(str(part) for part in first["loc"])
    return f"{field}: {first['msg']}" if field else first["msg"]


def print_added(expense: Expense) -> None:
    line = f"Added #{expense.id}: {expense.amount:.2f} {expense.category} on {expense.date}"
    if expense.description:
        line += f" ({expense.description})"
    print(line)


def print_list(expenses: list[Expense]) -> None:
    if not expenses:
        print("No expenses found")
        return
    print(f"{'ID':>3}  {'Date':<10}  {'Category':<12}{'Amount':>9}  Description")
    for e in expenses:
        row = f"{e.id:>3}  {e.date}  {e.category:<12}{e.amount:>9.2f}  {e.description}"
        print(row.rstrip())


def print_summary(totals: dict[str, Decimal], total: Decimal) -> None:
    if not totals:
        print("No expenses found")
        return
    for category, amount in totals.items():
        print(f"{category:<12}{amount:>10.2f}")
    print("-" * 22)
    print(f"{'Total':<12}{total:>10.2f}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        store = ExpenseStore(args.file)
        match args.command:
            case "add":
                print_added(store.add(args.amount, args.category, args.description, args.date))
            case "list":
                print_list(store.list(category=args.category, month=args.month))
            case "summary":
                print_summary(store.summary(month=args.month), store.total(month=args.month))
            case "delete":
                print(f"Deleted #{store.delete(args.id).id}")
    except ValidationError as exc:
        print(f"Error: {format_validation_error(exc)}", file=sys.stderr)
        return 1
    except TrackerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
