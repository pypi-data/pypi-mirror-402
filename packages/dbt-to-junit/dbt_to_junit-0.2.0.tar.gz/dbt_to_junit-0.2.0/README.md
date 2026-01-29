# dbt to JUnit XML

Convert dbt's `target/run_results.json` into a JUnit XML report so Azure DevOps (ADO) can display dbt test results in the Tests tab.

This tool is designed for CI: it reads the run results produced by `dbt build`, generates a single JUnit report, and writes it to a file that can be published by ADO.

## What it reads

- **Input**: dbt `run_results.json` (typically `target/run_results.json`)
- **Source of truth**: the `results` list inside that file
- **Filtering**: by default, only dbt tests are included (`unique_id` starts with `test.`)

## What it writes

- **Output**: a JUnit XML file (default: `dbt-junit.xml`)
- **Structure**: one `<testsuite>` containing one `<testcase>` per dbt test

## Install / run (local)

If you're using this repo with `uv`:

```bash
uv sync
uv run dbt-junit-xml --input target/run_results.json --output dbt-junit.xml
```

You can also run it directly with Python:

```bash
python -m src.main --input target/run_results.json --output dbt-junit.xml
```

## CLI options

- `--input`: path to `run_results.json` (default: `target/run_results.json`)
- `--output`: output XML path (default: `dbt-junit.xml`)
- `--log-level`: `DEBUG|INFO|WARNING|ERROR` (default: `INFO`)
- `--include-models`: include non-test nodes as testcases (default: off)

## Help

You can also run the following command to get some help in the terminal:

```bash
uv run dbt-junit-xml --help
```

or

```bash
python -m src.main --help
```

Response:

```bash
usage: dbt-junit-xml [-h] [--input INPUT] [--output OUTPUT] [--include-models] [--log-level LOG_LEVEL]

Convert dbt run_results.json to JUnit XML.

options:
  -h, --help            show this help message and exit
  --input INPUT         Path to dbt run_results.json (default: target/run_results.json)
  --output OUTPUT       Path to write JUnit XML (default: dbt-junit.xml)
  --include-models      Include model results as testcases (default: only dbt tests).
  --log-level LOG_LEVEL
                        Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
```

## Exit codes

- **0**: report generated and no failing dbt tests
- **1**: report generated and at least one dbt test failed/errored
- **2**: could not generate report (missing file, invalid JSON, unexpected format, etc.)

## Azure DevOps pipeline example

Run dbt (which produces `target/run_results.json`), generate the JUnit XML, then publish it:

```yaml
- script: |
    dbt build
    dbt-junit-xml --input target/run_results.json --output dbt-junit.xml
  displayName: "Run dbt and generate JUnit report"

- task: PublishTestResults@2
  displayName: "Publish dbt test results"
  inputs:
    testResultsFormat: "JUnit"
    testResultsFiles: "dbt-junit.xml"
    failTaskOnFailedTests: true
```

## Notes / tips

- If your pipeline working directory is not the dbt project root, pass an explicit `--input` path.
- If you only want dbt tests in ADO, do not pass `--include-models` (default behavior already filters to tests).
