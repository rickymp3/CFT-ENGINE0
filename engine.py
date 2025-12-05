"""Minimal engine entry point for CFT-ENGINE0."""


def run() -> str:
    """Return a status message describing the engine state."""
    return "CFT-ENGINE0 engine is running."


def main() -> None:
    """Print the engine status to stdout."""
    print(run())


if __name__ == "__main__":
    main()
