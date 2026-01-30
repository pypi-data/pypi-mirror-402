import nox


@nox.session(python=["3.9", "3.11"])
def tests(session: nox.Session) -> None:
    """Runs pytest"""
    session.install("-e", ".[ssh]")
    session.install("pytest", "pytest-cov")
    session.run(
        "pytest",
        "--cov=libsan",
        "--cov-config",
        "pyproject.toml",
        "--cov-report=",
        *session.posargs,
        env={"COVERAGE_FILE": f".coverage.{session.python}"},
    )
    session.notify("coverage")


@nox.session
def coverage(session) -> None:
    """Coverage analysis"""
    session.install("coverage[toml]")
    session.run("coverage", "combine")
    session.run("coverage", "report")
    session.run("coverage", "erase")
