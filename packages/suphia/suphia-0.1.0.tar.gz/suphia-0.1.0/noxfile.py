import nox

nox.options.sessions = ["format", "lint", "type_check", "test"]
nox.options.reuse_existing_virtualenvs = True


@nox.session  # type: ignore[untyped-decorator]
def format(session: nox.Session) -> None:
    """Run formatter."""
    session.install("ruff")
    session.run("ruff", "format", ".")


@nox.session  # type: ignore[untyped-decorator]
def lint(session: nox.Session) -> None:
    """Run linting."""
    session.install("ruff")
    session.run("ruff", "check", ".")


@nox.session  # type: ignore[untyped-decorator]
def type_check(session: nox.Session) -> None:
    """Run type checking."""
    session.install(".")
    session.install("mypy")
    session.run("mypy", ".")


@nox.session  # type: ignore[untyped-decorator]
def test(session: nox.Session) -> None:
    """Run tests."""
    session.install(".")
    session.install("pytest", "syrupy")
    session.run("pytest", *session.posargs)
