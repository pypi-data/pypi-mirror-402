""" Runs pytest, coverage, linters, and security checks. """

import os
import subprocess  # nosec


def get_modified_files_as_set():
    """Get a set of modified files in the current git branch."""
    # Run the git command
    result = subprocess.run(  # nosec
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,  # Redirect stdout/stderr
        text=True,  # Decode output to string
        check=False,
    )

    # Strip whitespace and split on newlines
    file_list = result.stdout.strip().split("\n")
    # Remove "pyproject.toml" from the list
    file_list = [f for f in file_list if f != "pyproject.toml"]

    # Convert to a set (filter out any empty strings that might occur)
    modified_files = {f for f in file_list if f}

    return modified_files


def run_coverage():
    """
    Run coverage against all files in the `src` directory
    and output an XML report to `reports/coverage.xml`.
    """
    # Set environment to skip integration tests by default
    env = os.environ.copy()
    if "INTEGRATION_TEST_ENABLE" not in env:
        env["INTEGRATION_TEST_ENABLE"] = "false"

    # 1. Run pytest with coverage, using `src` as the source
    subprocess.run(["coverage", "run", "--source=src", "-m", "pytest"], check=True, env=env)  # nosec

    # 2. Generate an XML coverage report in `reports/coverage.xml`
    subprocess.run(["coverage", "xml", "-o", "reports/coverage/coverage.xml"], check=True)  # nosec

    print("Coverage completed. XML report generated at reports/coverage.xml.")


def run_tests():
    """Runs pytests against tests in the `tests` directory."""
    # Set environment to skip integration tests by default
    env = os.environ.copy()
    if "INTEGRATION_TEST_ENABLE" not in env:
        env["INTEGRATION_TEST_ENABLE"] = "false"

    subprocess.run(["pytest", "tests"], check=True, env=env)  # nosec


def run_lint_all():
    """
    Run linters for black, pylint, flake8, and isort
    """
    subprocess.run(  # nosec
        ["black", "src", "tests"],
        check=False,
    )
    subprocess.run(  # nosec
        ["isort", "src", "tests"],
        check=False,
    )
    subprocess.run(  # nosec
        ["flake8", "src", "tests"],
        check=False,
    )
    subprocess.run(  # nosec
        ["pylint", "src", "tests"],
        check=False,
    )


def run_lint():
    """
    Run linters for black, pylint, flake8, and isort on modified git files
    """
    files = get_modified_files_as_set()
    files_list = list(files)

    if not files_list:
        print("No modified files detected.")
        return

    subprocess.run(["black", *files_list], check=False)  # black  # nosec
    subprocess.run(["isort", *files_list], check=False)  # isort  # nosec
    subprocess.run(["flake8", *files_list], check=False)  # flake8  # nosec
    subprocess.run(["pylint", *files_list], check=False)  # pylint  # nosec


def run_badge():
    """Generate a badge using genbadge."""
    # Set environment to skip integration tests by default
    env = os.environ.copy()
    if "INTEGRATION_TEST_ENABLE" not in env:
        env["INTEGRATION_TEST_ENABLE"] = "false"

    subprocess.run(  # nosec
        [
            "coverage",
            "run",
            "--source=src",
            "-m",
            "pytest",
            "--junit-xml=reports/junit/junit.xml",
        ],
        check=True,
        env=env,
    )

    # 2. Generate an XML coverage report in `reports/coverage.xml`
    subprocess.run(["coverage", "xml", "-o", "reports/coverage/coverage.xml"], check=True)  # nosec

    # 3. Generate an Flake8 report in `reports/flake8stats.xml`
    subprocess.run(  # nosec
        [
            "flake8",
            "--statistics",
            "--output-file=reports/flake8/flake8stats.txt",
            "--extend-exclude",
            ".github,reports,.venv,.vscode",
        ],
        check=False,
    )

    # 4. Generate badge for flake8
    subprocess.run(["genbadge", "flake8", "-o", "badge/flake8-badge.svg"], check=True)  # nosec

    # 5. Generate badge for coverage
    subprocess.run(["genbadge", "coverage", "-o", "badge/coverage-badge.svg"], check=True)  # nosec

    # 6. Generate badge for tests
    subprocess.run(  # nosec
        ["genbadge", "tests", "-t", "90", "-o", "badge/test-badge.svg"],
        check=True,
    )
