import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notes", description="A tiny notes app")
    parser.add_argument("--file", default="notes.txt", help="where notes are stored")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a note")
    add.add_argument("text", help="the note text")  # positional, required
    add.add_argument("--tag", default="general")  # optional, named

    lst = sub.add_parser("list", help="list notes")
    lst.add_argument("--limit", type=int, default=10)  # converted to int

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    match args.command:
        case "add":
            print(f"adding {args.text!r} with tag {args.tag} to {args.file}")
        case "list":
            print(f"showing {args.limit} notes from {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
