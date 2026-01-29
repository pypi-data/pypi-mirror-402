"""Command-line interface for running workflows."""

import argparse
import json
import sys
from pathlib import Path

from .executor import execute_workflow
from .logger import save_log
from .parser import WorkflowParseError, parse_workflow


def main():
    """Entry point for the narrative-flow CLI."""
    parser = argparse.ArgumentParser(
        description="Execute LLM conversation workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Run a workflow with inputs from command line
  narrative-flow run workflow.md --input short_transcript="Hello world"

  # Run with inputs from a JSON file
  narrative-flow run workflow.md --inputs-file inputs.json

  # Validate a workflow file without running
  narrative-flow validate workflow.md
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Execute a workflow")
    run_parser.add_argument("workflow", type=Path, help="Path to .workflow.md file")
    run_parser.add_argument(
        "--input",
        "-i",
        action="append",
        dest="inputs",
        metavar="NAME=VALUE",
        help="Input variable (can be repeated)",
    )
    run_parser.add_argument(
        "--inputs-file",
        "-f",
        type=Path,
        help="JSON file containing input variables",
    )
    run_parser.add_argument(
        "--log-dir",
        "-l",
        type=Path,
        default=Path("."),
        help="Directory for log files (default: current directory)",
    )
    run_parser.add_argument(
        "--no-log",
        action="store_true",
        help="Don't save execution log",
    )
    run_parser.add_argument(
        "--output-json",
        "-o",
        action="store_true",
        help="Output results as JSON",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a workflow file")
    validate_parser.add_argument("workflow", type=Path, help="Path to .workflow.md file")

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "run":
        return cmd_run(args)


def cmd_validate(args) -> int:
    """Validate a workflow file."""
    try:
        workflow = parse_workflow(args.workflow)
        print(f"✅ Valid workflow: {workflow.name}")
        print(f"   Description: {workflow.description or '(none)'}")
        print(f"   Conversation model: {workflow.models.conversation}")
        print(f"   Extraction model: {workflow.models.extraction}")
        print(f"   Inputs: {', '.join(i.name for i in workflow.inputs) or '(none)'}")
        outputs_display = ", ".join(f"{o.name} ({o.type.value})" for o in workflow.outputs)
        print(f"   Outputs: {outputs_display or '(none)'}")
        print(f"   Steps: {len(workflow.steps)}")
        return 0
    except WorkflowParseError as e:
        print(f"❌ Invalid workflow: {e}", file=sys.stderr)
        return 1


def cmd_run(args) -> int:
    """Execute a workflow."""
    # Parse workflow
    try:
        workflow = parse_workflow(args.workflow)
    except WorkflowParseError as e:
        print(f"❌ Failed to parse workflow: {e}", file=sys.stderr)
        return 1

    # Collect inputs
    inputs = {}

    # From JSON file
    if args.inputs_file:
        try:
            inputs.update(json.loads(args.inputs_file.read_text()))
        except Exception as e:
            print(f"❌ Failed to read inputs file: {e}", file=sys.stderr)
            return 1

    # From command line (override file inputs)
    if args.inputs:
        for inp in args.inputs:
            if "=" not in inp:
                print(f"❌ Invalid input format: {inp} (expected NAME=VALUE)", file=sys.stderr)
                return 1
            name, value = inp.split("=", 1)
            inputs[name] = value

    # Execute
    print(f"🚀 Running workflow: {workflow.name}")
    result = execute_workflow(workflow, inputs)

    # Save log
    if not args.no_log:
        log_path = save_log(result, output_dir=args.log_dir)
        print(f"📝 Log saved: {log_path}")

    # Output results
    if args.output_json:
        output = {
            "success": result.success,
            "error": result.error,
            "outputs": result.outputs,
        }
        print(json.dumps(output, indent=2))
    else:
        if result.success:
            print("✅ Workflow completed successfully")
            print("\nOutputs:")
            for name, value in result.outputs.items():
                display_value = _format_output_value(value)
                # Truncate long values for display
                display_value = display_value if len(display_value) <= 100 else display_value[:100] + "..."
                print(f"  {name}: {display_value}")
        else:
            print(f"❌ Workflow failed: {result.error}", file=sys.stderr)
            return 1

    return 0


def _format_output_value(value: object) -> str:
    """Format output values for CLI display."""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


if __name__ == "__main__":
    sys.exit(main())
