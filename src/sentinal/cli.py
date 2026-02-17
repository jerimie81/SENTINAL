import argparse
import requests
import json
from . import core

def invoke_adk(message: str):
    """Sends a message to the local ADK server and prints the response."""
    url = "http://localhost:8000/invoke"
    payload = {"message": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to ADK server: {e}")
        print("Please ensure the local ADK server is running.")

def main():
    parser = argparse.ArgumentParser(
        description="Sentinal: A low-resource system administration CLI for Linux desktop workflows.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # health command
    health_parser = subparsers.add_parser("health", help="Display live system health stats.")
    health_parser.add_argument("--json", action="store_true", help="Output in JSON format.")
    health_parser.add_argument("--spark", action="store_true", help="Include a sparkline for metrics.")

    # clean command
    clean_parser = subparsers.add_parser("clean", help="Clean temporary files and logs.")
    clean_parser.add_argument("--force", action="store_true", help="Perform the cleanup (default is dry-run).")

    # lint command
    lint_parser = subparsers.add_parser("lint", help="Audit a Python file for common issues.")
    lint_parser.add_argument("file", help="The Python file to audit.")

    # kill-top command
    kill_parser = subparsers.add_parser("kill-top", help="Kill the top N memory-hogging processes.")
    kill_parser.add_argument("num", type=int, help="Number of processes to kill.")
    kill_parser.add_argument("--force", action="store_true", help="Perform the kill (default is dry-run).")

    # audit command
    audit_parser = subparsers.add_parser("audit", help="Check permissions of key files in a directory.")
    audit_parser.add_argument("dir", help="The directory to audit.")

    # gpu command
    gpu_parser = subparsers.add_parser("gpu", help="Show GPU utilization and memory.")

    # metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Export metrics in Prometheus format.")
    metrics_parser.add_argument("port", type=int, nargs="?", default=9101, help="The port to export metrics on.")

    # ask-local command
    ask_local_parser = subparsers.add_parser("ask-local", help="Ask a question to the local 3B LLM.")
    ask_local_parser.add_argument("question", help="The question to ask.")

    # trace-io command
    trace_io_parser = subparsers.add_parser("trace-io", help="Trace block I/O using eBPF.")
    trace_io_parser.add_argument("duration", type=int, help="The duration of the trace in seconds.")

    # index-tree command
    index_tree_parser = subparsers.add_parser("index-tree", help="Index a directory tree into the database.")
    index_tree_parser.add_argument("path", help="The path to the directory to index.")
    
    # ADK command (hidden from help)
    adk_parser = subparsers.add_parser("adk", help=argparse.SUPPRESS)
    adk_parser.add_argument("message", help="Message to send to the ADK agent.")

    args = parser.parse_args()

    if args.command == "health":
        core.health(json_output=args.json, spark=args.spark)
    elif args.command == "clean":
        core.clean(force=args.force)
    elif args.command == "lint":
        core.lint(file=args.file)
    elif args.command == "kill-top":
        core.kill_top(num=args.num, force=args.force)
    elif args.command == "audit":
        core.audit(directory=args.dir)
    elif args.command == "gpu":
        core.gpu()
    elif args.command == "metrics":
        core.metrics(port=args.port)
    elif args.command == "ask-local":
        core.ask_local(question=args.question)
    elif args.command == "trace-io":
        core.trace_io(duration=args.duration)
    elif args.command == "index-tree":
        core.index_tree(path=args.path)
    elif args.command == "adk":
        invoke_adk(args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
