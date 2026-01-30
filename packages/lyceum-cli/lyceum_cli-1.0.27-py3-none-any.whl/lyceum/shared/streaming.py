"""Streaming utilities for execution output"""

import json
import re
import sys

import httpx
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from .config import config

console = Console()


class StatusLine:
    """A single-line status display that updates in place with a spinner."""

    def __init__(self):
        self._live = None
        self._current_status = ""

    def start(self):
        """Start the live display."""
        self._live = Live(console=console, refresh_per_second=10, transient=True)
        self._live.start()

    def update(self, message: str):
        """Update the status message."""
        self._current_status = message
        if self._live:
            spinner = Spinner("dots", text=Text(f" {message}", style="dim"))
            self._live.update(spinner)

    def stop(self):
        """Stop the live display and clear the line."""
        if self._live:
            self._live.stop()
            self._live = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


def normalize_newlines(text: str) -> str:
    """Collapse multiple consecutive newlines into single newlines"""
    # Replace 2+ consecutive newlines with a single newline. For some reason the format that is being sent from the execlet still has too many newlines.
    return re.sub(r'\n{2,}', '\n', text)


def stream_execution_output(execution_id: str, streaming_url: str = None) -> bool:
    """Stream execution output in real-time. Returns True if successful, False if failed."""
    if not streaming_url:
        # Fallback to stream endpoint if no streaming URL provided
        stream_url = f"{config.base_url}/api/v1/stream/{execution_id}"
    else:
        stream_url = streaming_url

    try:
        console.print("[dim]Connecting to execution stream...[/dim]")

        headers = {"Authorization": f"Bearer {config.api_key}"}
        with httpx.stream("GET", stream_url, headers=headers, timeout=600.0) as response:
            if response.status_code != 200:
                console.print(f"[red]Stream failed: HTTP {response.status_code}[/red]")
                return False

            console.print("[dim]Streaming output...[/dim]")

            first_output = True
            for line in response.iter_lines():
                if line.strip():
                    # Parse Server-Sent Events format
                    if line.startswith("data: "):
                        data_json = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(data_json)

                            # Handle output event
                            if "output" in data:
                                output_data = data["output"]
                                content = output_data.get("content", "")
                                if content:
                                    clean_output = strip_ansi_codes(content)
                                    # Normalize newlines to avoid excessive blank lines
                                    clean_output = normalize_newlines(clean_output)
                                    print(clean_output, end="", flush=True)

                            # Handle job finished event
                            elif "jobFinished" in data:
                                job_data = data["jobFinished"]
                                job = job_data.get("job", {})
                                result = job.get("result", {})
                                return_code = result.get("returnCode")
                                error = result.get("error")

                                # Print final newline if we had output
                                if not first_output:
                                    print()

                                if error:
                                    console.print(f"[red]{error}[/red]")
                                    return False
                                elif return_code is not None and str(return_code) != "0":
                                    console.print(f"[red]Failed (exit code {return_code})[/red]")
                                    return False
                                else:
                                    return True

                            # Handle old-style events (for backward compatibility)
                            elif "type" in data:
                                event_type = data.get("type")

                                if event_type == "output":
                                    output = data.get("content", "")
                                    if output:
                                        clean_output = strip_ansi_codes(output)
                                        clean_output = normalize_newlines(clean_output)
                                        print(clean_output, end="", flush=True)

                                elif event_type == "completed":
                                    status = data.get("status", "unknown")
                                    if status == "completed":
                                        console.print("\n[green]Execution completed successfully[/green]")
                                        return True
                                    else:
                                        console.print(f"\n[red]Execution failed: {status}[/red]")
                                        return False

                                elif event_type == "error":
                                    error_msg = data.get("message", "Unknown error")
                                    console.print(f"\n[red]Error: {error_msg}[/red]")
                                    return False

                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue

            console.print("\n[yellow]Stream ended without completion signal[/yellow]")
            # Fallback: poll execution status
            return check_execution_status(execution_id)

    except Exception as e:
        console.print(f"\n[red]Streaming error: {e}[/red]")
        # Fallback: poll execution status
        return check_execution_status(execution_id)


def check_execution_status(execution_id: str) -> bool:
    """Check execution status as fallback when streaming fails."""
    import time

    console.print("[dim]Checking execution status...[/dim]")

    for _ in range(30):  # Poll for up to 30 seconds
        try:
            response = httpx.get(
                f"{config.base_url}/api/v2/external/execution/streaming/{execution_id}/status",
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')

                if status == 'completed':
                    console.print("[green]Execution completed successfully[/green]")
                    return True
                elif status in ['failed_user', 'failed_system', 'failed']:
                    console.print(f"[red]Execution failed: {status}[/red]")
                    errors = data.get('errors')
                    if errors:
                        console.print(f"[red]Error: {errors}[/red]")
                    return False
                elif status in ['timeout', 'cancelled']:
                    console.print(f"[yellow]Execution {status}[/yellow]")
                    return False
                elif status in ['running', 'pending', 'queued']:
                    # Still running, continue polling
                    time.sleep(1)
                    continue

        except Exception as e:
            console.print(f"[red]Error checking status: {e}[/red]")
            break

    console.print("[yellow]Status check timed out[/yellow]")
    return False
