# Expense Tracker

A small command-line app for tracking personal expenses. Expenses are validated with
Pydantic, stored as JSON with atomic writes, and handled with `Decimal` so money adds up
exactly (no `0.1 + 0.2` surprises).

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/umairsaeeddev/expense-tracker.git
cd expense-tracker
uv sync
```

## Usage

Expenses are saved to `expenses.json` in the current directory. Use the global `--file`
option (before the command) to pick a different file:
`uv run expense-tracker --file data/2026.json list`.

### Add an expense

```text
$ uv run expense-tracker add 12.50 food "Lunch" --date 2026-11-02
Added #1: 12.50 food on 2026-11-02 (Lunch)

$ uv run expense-tracker add 45 transport "Fuel" --date 2026-11-03
Added #2: 45.00 transport on 2026-11-03 (Fuel)
```

The description is optional and `--date` defaults to today. Categories are normalised
(`" Food "` becomes `food`).

### List expenses

```text
$ uv run expense-tracker list --month 2026-11
 ID  Date        Category       Amount  Description
  1  2026-11-02  food            12.50  Lunch
  2  2026-11-03  transport       45.00  Fuel
  3  2026-11-05  food             8.75  Coffee beans
```

Filter with `--month YYYY-MM` and/or `--category NAME`. The list is sorted by date.

### Summarise by category

```text
$ uv run expense-tracker summary
bills           120.00
transport        45.00
food             21.25
----------------------
Total           186.25
```

Add `--month YYYY-MM` to summarise a single month. Categories are listed highest first.

### Delete an expense

```text
$ uv run expense-tracker delete 2
Deleted #2

$ uv run expense-tracker delete 99
Error: expense #99 not found
```

### Errors

Invalid input gets a short, friendly message on stderr and exit code 1:

```text
$ uv run expense-tracker add 0 food
Error: amount: Input should be greater than 0
```

## Running the tests

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format --check .
```

## Project structure

```text
src/expense_tracker/
├── errors.py   # TrackerError, StoreError, ExpenseNotFoundError
├── models.py   # Expense Pydantic model
├── store.py    # ExpenseStore: load/save JSON, filtering, summaries
└── cli.py      # argparse interface and output formatting
tests/          # pytest tests for models, store and CLI
```

## What I learned

- **Separating layers**: the model validates, the store owns persistence and the CLI only
  parses arguments and prints. That made each part easy to test on its own.
- **`Decimal` for money**: floats can't represent `0.10` exactly, so `Decimal` with
  Pydantic's `decimal_places=2` keeps totals correct to the cent.
- **Atomic writes**: writing to a `.tmp` file and then calling `replace()` means a crash
  mid-write can never corrupt the real data file.
- **Custom exceptions with chaining**: a small exception hierarchy (`raise StoreError(...)
  from e`) lets the CLI catch one base class and show a clean message, without losing
  the original cause.
- **Testing a CLI**: making `main(argv)` return an exit code lets pytest call it directly,
  with `tmp_path` for isolated files and `capsys` to check stdout and stderr.
