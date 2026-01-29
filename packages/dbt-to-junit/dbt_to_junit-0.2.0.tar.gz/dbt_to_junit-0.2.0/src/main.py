import argparse
import json
import logging
from pathlib import Path
from typing import Any

from junit_xml import TestCase, TestSuite, to_xml_report_string

logger = logging.getLogger(__name__)


def _configure_logging(log_level: str) -> None:
    """Configure logging for this command-line tool.

    This function configures Python's standard library logging (the root logger)
    with a simple, pipeline-friendly format so messages show up in the terminal
    output of local runs and CI systems (e.g., Azure DevOps).

    Notes:
        - This uses `logging.basicConfig(...)`, which only has an effect the first
          time it is called (unless the logging system is reset elsewhere).
        - Any unknown `log_level` value falls back to `INFO`.

    Args:
        log_level: Logging level name (case-insensitive), for example:
            - "DEBUG" to see verbose troubleshooting output
            - "INFO" for normal operation
            - "WARNING" / "ERROR" for quieter runs

    Returns:
        None.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )


def _read_run_results(path: Path) -> dict[str, Any]:
    """Read and parse a dbt `run_results.json` file from disk.

    dbt writes `run_results.json` to the `target/` directory when `--write-json`
    is enabled (it is enabled by default for most dbt invocations). This tool
    treats that file as the source of truth for building a JUnit XML report that
    Azure DevOps can render in the "Tests" tab.

    Args:
        path: Path to the `run_results.json` file. This can be an absolute path
            or a path relative to the current working directory.

    Returns:
        A dictionary representing the parsed JSON document.

        The expected top-level shape (simplified) is:
        - `metadata`: dict (optional but common)
        - `results`: list of per-node result dictionaries (required for report)
        - `args`: dict with invocation details such as `which` (optional)

    Raises:
        FileNotFoundError: If `path` does not exist or cannot be opened.
        ValueError: If the file exists but is not valid JSON.
    """
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"run_results.json not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def _to_junit_xml(
    run_results: dict[str, Any], *, include_models: bool
) -> tuple[str, int]:
    """Convert parsed dbt run results into a JUnit XML report.

    This function transforms dbt's `run_results.json` structure into a single
    JUnit `<testsuite>` containing `<testcase>` entries. The resulting XML can
    be published to Azure DevOps using the `PublishTestResults@2` task with
    `testResultsFormat: JUnit`.

    What gets included:
        - By default (`include_models=False`), only dbt tests are included.
          These can be identified by `unique_id` starting with `"test."`.
        - If `include_models=True`, non-test nodes (e.g., models) are also
          included as testcases.

    How dbt statuses are mapped:
        - "pass": testcase has no failure/error child elements (success)
        - "skipped": testcase gets a `<skipped>` element
        - "fail": testcase gets a `<failure>` element
        - "error": testcase gets an `<error>` element
        - anything else: if it's a dbt test, it's treated as an `<error>`

    Naming and grouping:
        - `classname` is derived from the first two `unique_id` segments so ADO
          groups results nicely (e.g., `test.jaffle_shop`).
        - `name` is the remaining portion of `unique_id`.
        - If `metadata.invocation_id` is present, it is included in the suite name.

    Args:
        run_results: Parsed contents of dbt `run_results.json` (output of
            `_read_run_results`).
        include_models: Whether to include non-test nodes as JUnit testcases.
            Keep this False if you only want dbt tests to appear in ADO.

    Returns:
        A tuple of:
        - xml_report: A UTF-8 JUnit XML string (includes XML declaration).
        - failing_test_count: Number of dbt *tests* (not models) that failed or
          errored. This is useful for deciding process exit code in CI.

    Raises:
        ValueError: If:
            - `args.which` is present and not `"build"` (this tool expects dbt
              build artifacts), or
            - the JSON does not contain a top-level `results` list.
    """
    which = run_results.get("args", {}).get("which")
    if which and which != "build":
        raise ValueError(f"Expected a dbt build artifact, got: {which}")

    results = run_results.get("results")
    if not isinstance(results, list):
        raise ValueError("run_results.json missing a top-level 'results' list")

    test_cases: list[TestCase] = []
    failing_tests = 0

    for result in results:
        if not isinstance(result, dict):
            continue

        unique_id = str(result.get("unique_id", "unknown"))
        status = str(result.get("status", "unknown"))
        execution_time = result.get("execution_time")
        elapsed_sec = (
            float(execution_time) if isinstance(execution_time, (int, float)) else None
        )

        is_test = unique_id.startswith("test.")
        if not include_models and not is_test:
            continue

        parts = unique_id.split(".")
        classname = ".".join(parts[:2]) if len(parts) >= 2 else parts[0]
        name = ".".join(parts[2:]) if len(parts) >= 3 else unique_id

        test_case = TestCase(name=name, classname=classname, elapsed_sec=elapsed_sec)

        message = result.get("message")
        if message is None and isinstance(result.get("adapter_response"), dict):
            message = result["adapter_response"].get("_message")
        message_str = "" if message is None else str(message)

        if status == "pass":
            pass

        if status == "skipped":
            test_case.add_skipped_info(message=message_str or "skipped")

        if status == "fail":
            test_case.add_failure_info(
                message=message_str or "dbt test failed", output=unique_id
            )
            if is_test:
                failing_tests += 1

        if status == "error":
            test_case.add_error_info(
                message=message_str or "dbt error", output=unique_id
            )
            if is_test:
                failing_tests += 1

        if status not in ["pass", "skipped", "fail", "error"]:
            if is_test:
                test_case.add_error_info(
                    message=f"Unknown dbt status: {status}", output=unique_id
                )
                failing_tests += 1

        test_cases.append(test_case)

    suite_name = "dbt"
    if "metadata" in run_results and isinstance(run_results["metadata"], dict):
        invocation_id = run_results["metadata"].get("invocation_id")
        if invocation_id:
            suite_name = f"dbt ({invocation_id})"

    suite = TestSuite(suite_name, test_cases=test_cases)

    xml = to_xml_report_string([suite], encoding="utf-8")
    return xml, failing_tests


def main(argv: list[str] | None = None) -> int:
    """Run the CLI to convert dbt `run_results.json` into JUnit XML.

    This is the entrypoint used by the `dbt-junit-xml` console script declared
    in `pyproject.toml`. It reads a dbt `run_results.json` file, converts dbt
    test results into a JUnit report, and writes the report to disk.

    Typical usage (local):
        - `dbt-junit-xml --input target/run_results.json --output dbt-junit.xml`

    Typical usage (Azure DevOps):
        1) Run `dbt build` (which produces `target/run_results.json`).
        2) Run this tool to produce an XML file in the working directory.
        3) Publish with `PublishTestResults@2` and `testResultsFormat: JUnit`.

    Exit codes are designed for CI:
        - 0 means the report was generated and there were no failing dbt tests.
        - 1 means the report was generated but at least one dbt test failed.
        - 2 means the report could not be generated (bad input, missing file, etc.).

    Args:
        argv: Optional list of CLI arguments (primarily for tests). If omitted,
            arguments are read from `sys.argv` by `argparse`.

    Returns:
        The process exit code (0/1/2 as described above).
    """
    parser = argparse.ArgumentParser(
        description="Convert dbt run_results.json to JUnit XML."
    )
    parser.add_argument(
        "--input",
        default=str(Path("target") / "run_results.json"),
        help="Path to dbt run_results.json (default: target/run_results.json)",
    )
    parser.add_argument(
        "--output",
        default="dbt-junit.xml",
        help="Path to write JUnit XML (default: dbt-junit.xml)",
    )
    parser.add_argument(
        "--include-models",
        action="store_true",
        help="Include model results as testcases (default: only dbt tests).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO",
    )
    args = parser.parse_args(argv)
    _configure_logging(args.log_level)

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        run_results = _read_run_results(input_path)
        xml, failing_tests = _to_junit_xml(
            run_results, include_models=args.include_models
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(xml, encoding="utf-8")
    except Exception as e:
        logger.error(str(e))
        return 2

    logger.info("Wrote JUnit XML to %s", output_path)
    return 1 if failing_tests > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
