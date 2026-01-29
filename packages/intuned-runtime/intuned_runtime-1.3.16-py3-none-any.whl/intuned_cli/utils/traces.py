from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from _intuned_runtime_internal.types.run_types import TracingDisabled
from _intuned_runtime_internal.types.run_types import TracingEnabled
from intuned_cli.utils.console import console

_trace_dir_name = datetime.now().isoformat()

_count = 0


def get_trace_path(id: str):
    global _count
    _count += 1
    return Path() / "traces" / _trace_dir_name / f"{_count}-{id}.zip"


@contextmanager
def cli_trace(id: str | None):
    if not id:
        yield TracingDisabled()
        return

    trace_path = get_trace_path(id)
    try:
        yield TracingEnabled(file_path=str(trace_path))
    finally:
        if trace_path.exists():
            console.print(f"[bold]Trace saved to [/bold][underline]{str(trace_path)}[/underline]")
