from pathlib import Path

import pytest

from expense_tracker.cli import main


@pytest.fixture
def file(tmp_path: Path) -> str:
    return str(tmp_path / "expenses.json")


def add_sample_expenses(file: str) -> None:
    main(["--file", file, "add", "12.50", "food", "Lunch", "--date", "2026-11-02"])
    main(["--file", file, "add", "45", "transport", "Fuel", "--date", "2026-11-03"])
    main(["--file", file, "add", "8.75", "food", "Coffee beans", "--date", "2026-11-05"])
    main(["--file", file, "add", "120", "bills", "Internet", "--date", "2026-10-28"])


def test_add_prints_confirmation(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--file", file, "add", "12.50", "food", "Lunch", "--date", "2026-11-02"])
    assert code == 0
    assert capsys.readouterr().out == "Added #1: 12.50 food on 2026-11-02 (Lunch)\n"


def test_add_zero_amount_is_an_error(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--file", file, "add", "0", "food"])
    assert code == 1
    assert capsys.readouterr().err == "Error: amount: Input should be greater than 0\n"


def test_list_by_month(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    add_sample_expenses(file)
    capsys.readouterr()
    assert main(["--file", file, "list", "--month", "2026-11"]) == 0
    assert capsys.readouterr().out == (
        " ID  Date        Category       Amount  Description\n"
        "  1  2026-11-02  food            12.50  Lunch\n"
        "  2  2026-11-03  transport       45.00  Fuel\n"
        "  3  2026-11-05  food             8.75  Coffee beans\n"
    )


def test_list_empty(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--file", file, "list"]) == 0
    assert capsys.readouterr().out == "No expenses found\n"


def test_summary_prints_total(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    add_sample_expenses(file)
    capsys.readouterr()
    assert main(["--file", file, "summary"]) == 0
    assert capsys.readouterr().out == (
        "bills           120.00\n"
        "transport        45.00\n"
        "food             21.25\n"
        "----------------------\n"
        "Total           186.25\n"
    )


def test_summary_by_month(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    add_sample_expenses(file)
    capsys.readouterr()
    main(["--file", file, "summary", "--month", "2026-11"])
    assert capsys.readouterr().out.splitlines()[-1] == "Total            66.25"


def test_delete(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    add_sample_expenses(file)
    capsys.readouterr()
    assert main(["--file", file, "delete", "2"]) == 0
    assert capsys.readouterr().out == "Deleted #2\n"


def test_delete_unknown_id(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--file", file, "delete", "99"])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert captured.err == "Error: expense #99 not found\n"


def test_corrupt_file_is_an_error(file: str, capsys: pytest.CaptureFixture[str]) -> None:
    Path(file).write_text("oops", encoding="utf-8")
    assert main(["--file", file, "list"]) == 1
    assert capsys.readouterr().err.startswith("Error: invalid JSON")


def test_invalid_amount_exits_with_usage_error(file: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--file", file, "add", "abc", "food"])
    assert exc_info.value.code == 2
