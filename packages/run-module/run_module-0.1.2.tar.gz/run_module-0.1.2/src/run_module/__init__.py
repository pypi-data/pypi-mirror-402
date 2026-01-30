import runpy
import sys

USAGE = "Usage: run-module <module_name> [args...]"

def main() -> None:
    if len(sys.argv) < 2:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    if not all(part.isidentifier() for part in sys.argv[1].split(".")):
        print(f"Invalid module name: {sys.argv[1]}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    module_name = sys.argv[1]
    sys.argv = sys.argv[1:]  # Shift so module sees itself as argv[0]
    runpy.run_module(module_name, run_name="__main__", alter_sys=True)
