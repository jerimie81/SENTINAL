"""SENTINAL command-line interface.

Commands
--------
  init    — Initialise the data directory and config stub.
  ingest  — Ingest a document file into the knowledge base.
  search  — Search the knowledge base by query string.
  ask     — Ask a natural-language question over ingested documents.
  stats   — Show storage and index statistics.
  doctor  — Run environment and index health checks.

All commands support --json for machine-readable output and
--profile to select a config profile.

Usage examples::

    sentinal init
    sentinal ingest ./docs/spec.md
    sentinal search "offline first architecture"
    sentinal ask "What chunking strategies are supported?"
    sentinal stats
    sentinal doctor
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from sentinal.config import SentinalConfig, load_config
from sentinal.doctor import run_doctor
from sentinal.errors import SentinalError
from sentinal.logging_utils import configure_logging, get_logger
from sentinal.pipeline import Pipeline

log = get_logger("cli")


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.option(
    "--profile",
    default=None,
    help="Config profile: dev | prod | airgap | edge_lowmem",
)
@click.option(
    "--config-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Path to a TOML config file (default: .sentinal/config.toml).",
)
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def cli(
    ctx: click.Context,
    profile: Optional[str],
    config_file: Optional[Path],
    output_json: bool,
) -> None:
    """SENTINAL — offline-first local AI knowledge system."""
    ctx.ensure_object(dict)
    try:
        cfg = load_config(config_file=config_file, profile=profile)
    except SentinalError as exc:
        click.echo(f"Config error: {exc}", err=True)
        sys.exit(1)

    configure_logging(cfg.log_level, cfg.log_format)
    ctx.obj["config"] = cfg
    ctx.obj["json"] = output_json


def _cfg(ctx: click.Context) -> SentinalConfig:
    return ctx.obj["config"]


def _json_mode(ctx: click.Context) -> bool:
    return ctx.obj.get("json", False)


def _out(ctx: click.Context, data: dict) -> None:
    if _json_mode(ctx):
        click.echo(json.dumps(data, indent=2))
    else:
        for k, v in data.items():
            click.echo(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialise the SENTINAL data directory and config stub.

    Example::

        sentinal init
        sentinal --profile prod init
    """
    cfg = _cfg(ctx)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.index_path.mkdir(parents=True, exist_ok=True)

    config_stub = cfg.data_dir / "config.toml"
    if not config_stub.exists():
        config_stub.write_text(
            f'# SENTINAL config — edit and uncomment to override defaults\n'
            f'# profile = "{cfg.profile}"\n'
            f'# log_level = "{cfg.log_level}"\n'
            f'# log_format = "{cfg.log_format}"\n'
            f'# chunk_size = {cfg.chunk_size}\n'
            f'# chunk_overlap = {cfg.chunk_overlap}\n'
            f'# max_results = {cfg.max_results}\n'
        )

    result = {
        "data_dir": str(cfg.data_dir),
        "config_stub": str(config_stub),
        "status": "initialised",
    }
    if _json_mode(ctx):
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"✓ Initialised SENTINAL at: {cfg.data_dir}")
        click.echo(f"  Config stub: {config_stub}")


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--force",
    is_flag=True,
    help="Re-ingest even if the document checksum is unchanged.",
)
@click.option(
    "--strategy",
    type=click.Choice(["fixed_token", "sentence"]),
    default="fixed_token",
    show_default=True,
    help="Chunking strategy.",
)
@click.pass_context
def ingest(ctx: click.Context, path: Path, force: bool, strategy: str) -> None:
    """Ingest a document into the knowledge base.

    Supported formats: .txt, .md, .pdf

    Examples::

        sentinal ingest README.md
        sentinal ingest report.pdf --strategy sentence
        sentinal ingest notes.txt --force
    """
    try:
        pipeline = Pipeline(_cfg(ctx))
        result = pipeline.ingest(path, force=force, strategy=strategy)  # type: ignore[arg-type]
    except SentinalError as exc:
        click.echo(f"Ingest error: {exc}", err=True)
        sys.exit(1)

    if _json_mode(ctx):
        click.echo(json.dumps(result, indent=2))
    else:
        if result["skipped"]:
            click.echo(f"⏭  Skipped (unchanged): {result['source_uri']}")
        else:
            click.echo(
                f"✓ Ingested {result['source_uri']}\n"
                f"  doc_id:      {result['doc_id'][:12]}…\n"
                f"  chunks:      {result['chunk_count']}"
            )


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("query")
@click.option(
    "--top-k",
    default=None,
    type=int,
    help="Number of results (default: from config).",
)
@click.pass_context
def search(ctx: click.Context, query: str, top_k: Optional[int]) -> None:
    """Search the knowledge base by query string.

    Examples::

        sentinal search "chunking strategies"
        sentinal search "config validation" --top-k 3 --json
    """
    try:
        pipeline = Pipeline(_cfg(ctx))
        results = pipeline.search(query, top_k=top_k)
    except SentinalError as exc:
        click.echo(f"Search error: {exc}", err=True)
        sys.exit(1)

    if _json_mode(ctx):
        click.echo(json.dumps(results, indent=2))
    else:
        if not results:
            click.echo("No results found. Ingest documents first.")
            return
        click.echo(f"Results for: \"{query}\"\n")
        for i, r in enumerate(results, 1):
            src = r["meta"].get("source_uri", "?")
            click.echo(
                f"  [{i}] score={r['score']:.4f}  source={Path(src).name}\n"
                f"      {r['text'][:200].replace(chr(10), ' ')}\n"
            )


# ---------------------------------------------------------------------------
# ask
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("question")
@click.option("--top-k", default=None, type=int, help="Context chunks to retrieve.")
@click.pass_context
def ask(ctx: click.Context, question: str, top_k: Optional[int]) -> None:
    """Ask a natural-language question over ingested documents.

    Examples::

        sentinal ask "What is SENTINAL?"
        sentinal ask "How does chunking work?" --json
    """
    try:
        pipeline = Pipeline(_cfg(ctx))
        result = pipeline.ask(question, top_k=top_k)
    except SentinalError as exc:
        click.echo(f"QA error: {exc}", err=True)
        sys.exit(1)

    if _json_mode(ctx):
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"\n{result['answer']}\n")
        if result.get("sources"):
            click.echo("Sources:")
            for s in result["sources"]:
                click.echo(
                    f"  • {Path(s['source_uri']).name}  "
                    f"chunk={s['chunk_index']}  score={s['score']:.4f}"
                )


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show storage and index statistics.

    Example::

        sentinal stats --json
    """
    try:
        pipeline = Pipeline(_cfg(ctx))
        data = pipeline.stats()
    except SentinalError as exc:
        click.echo(f"Stats error: {exc}", err=True)
        sys.exit(1)

    if _json_mode(ctx):
        click.echo(json.dumps(data, indent=2))
    else:
        s = data["storage"]
        idx = data["index"]
        click.echo(
            f"Documents : {s['documents']}\n"
            f"Chunks    : {s['chunks']}\n"
            f"Index dir : {idx['index_dir']}\n"
            f"Embedder  : {idx['embedder']}"
        )


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Run environment and index health checks.

    Example::

        sentinal doctor
        sentinal doctor --json
    """
    cfg = _cfg(ctx)
    report = run_doctor(cfg)

    if _json_mode(ctx):
        click.echo(json.dumps(
            {
                "healthy": report.healthy,
                "checks": [
                    {
                        "name": c.name,
                        "passed": c.passed,
                        "message": c.message,
                        "remediation": c.remediation,
                    }
                    for c in report.checks
                ],
            },
            indent=2,
        ))
    else:
        click.echo(report.summary())

    if not report.healthy:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
