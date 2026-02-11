from .db import create_tables


def main() -> None:
    create_tables()
    print("Tables created (if not exist).")


if __name__ == "__main__":
    main()

