"""Пока заглушка."""
import argparse


def cli(argv: list[str] | None = None) -> None:
    """Пока заглушка."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default="World")
    args = parser.parse_args(argv)
    print(f"Hello, {args.name}!")
