import json
from pathlib import Path

from click.testing import CliRunner

from sentinal.cli_py import cli
from sentinal.config import SentinalConfig
from sentinal.pipeline import Pipeline


def test_pipeline_ingest_search_ask_is_deterministic(tmp_path: Path) -> None:
    data_dir = tmp_path / ".sentinal"
    cfg = SentinalConfig(data_dir=data_dir)
    source = tmp_path / "baseline.txt"
    source.write_text(
        "SENTINAL works offline first. It ingests local files and retrieves relevant chunks for answers.",
        encoding="utf-8",
    )

    first = Pipeline(cfg)
    ingest_result = first.ingest(source)
    first_answer = first.ask("How does SENTINAL work?")

    second = Pipeline(cfg)
    second_answer = second.ask("How does SENTINAL work?")

    assert ingest_result["skipped"] is False
    assert ingest_result["chunk_count"] >= 1
    assert first_answer["grounded"] is True
    assert first_answer["answer"] == second_answer["answer"]
    assert first_answer["sources"] == second_answer["sources"]


def test_cli_init_ingest_search_and_ask_json_output(tmp_path: Path) -> None:
    """
    Run the CLI end-to-end in JSON mode to validate init, ingest, search, and ask workflows.
    
    Executes the CLI with a temporary data directory and a sample source file, then:
    - Initializes the profile and asserts the returned status is "initialised".
    - Ingests the sample file and asserts the payload indicates it was not skipped.
    - Performs a search for "ingestion" and asserts the search payload is non-empty.
    - Asks "What does SENTINAL include?" and asserts the response is grounded and includes sources.
    """
    runner = CliRunner()
    data_dir = tmp_path / "state"
    source = tmp_path / "notes.md"
    source.write_text("SENTINAL includes ingestion, indexing, and ask commands.", encoding="utf-8")

    init_result = runner.invoke(cli, ["--json", "--profile", "dev", "init"], env={"SENTINAL_DATA_DIR": str(data_dir), "SENTINAL_LOG_LEVEL": "CRITICAL"})
    assert init_result.exit_code == 0
    init_payload = json.loads(init_result.output)
    assert init_payload["status"] == "initialised"

    ingest_result = runner.invoke(
        cli,
        ["--json", "ingest", str(source)],
        env={"SENTINAL_DATA_DIR": str(data_dir), "SENTINAL_LOG_LEVEL": "CRITICAL"},
    )
    assert ingest_result.exit_code == 0
    ingest_payload = json.loads(ingest_result.output)
    assert ingest_payload["skipped"] is False

    search_result = runner.invoke(
        cli,
        ["--json", "search", "ingestion"],
        env={"SENTINAL_DATA_DIR": str(data_dir), "SENTINAL_LOG_LEVEL": "CRITICAL"},
    )
    assert search_result.exit_code == 0
    search_payload = json.loads(search_result.output)
    assert search_payload

    ask_result = runner.invoke(
        cli,
        ["--json", "ask", "What does SENTINAL include?"],
        env={"SENTINAL_DATA_DIR": str(data_dir), "SENTINAL_LOG_LEVEL": "CRITICAL"},
    )
    assert ask_result.exit_code == 0
    ask_payload = json.loads(ask_result.output)
    assert ask_payload["grounded"] is True
    assert ask_payload["sources"]
