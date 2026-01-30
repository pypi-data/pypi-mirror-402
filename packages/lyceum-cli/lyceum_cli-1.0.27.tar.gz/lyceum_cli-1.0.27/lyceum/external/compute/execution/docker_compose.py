"""
Docker Compose execution commands
"""

import json
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console

from ....shared.config import config
from ....shared.streaming import StatusLine, stream_execution_output

console = Console()


compose_app = typer.Typer(name="compose", help="Docker Compose execution commands")


@compose_app.command("run")
def run_docker_compose(
    compose_file: Path = typer.Argument(
        ...,
        help="Path to docker-compose.yml file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True
    ),
    machine_type: str = typer.Option(
        "cpu", "--machine", "-m", help="Machine type (cpu, a100, h100, etc.)"
    ),
    timeout: int = typer.Option(
        300, "--timeout", "-t", help="Execution timeout in seconds"
    ),
    file_name: Optional[str] = typer.Option(
        None, "--file-name", "-f", help="Name for the execution"
    ),
    detach: bool = typer.Option(
        False, "--detach", "-d", help="Run in background and print execution ID"
    ),
    callback_url: Optional[str] = typer.Option(
        None, "--callback", help="Webhook URL for completion notification"
    ),
    registry_creds: Optional[str] = typer.Option(
        None, "--registry-creds", help="Docker registry credentials as JSON string"
    ),
    registry_type: Optional[str] = typer.Option(
        None, "--registry-type", help="Registry credential type: basic, aws, etc."
    ),
):
    """Execute a Docker Compose application on Lyceum Cloud.

    By default, streams container output in real-time.
    Use --detach to run in background and return immediately.

    Examples:
        lyceum compose run docker-compose.yml
        lyceum compose run ./app/docker-compose.yml -m a100
        lyceum compose run compose.yml --registry-type basic --registry-creds '{"username":"user","password":"pass"}'
    """
    status = StatusLine()

    try:
        config.get_client()

        status.start()
        status.update("Validating configuration...")

        # Read the compose file
        try:
            compose_file_content = compose_file.read_text()
        except Exception as e:
            status.stop()
            console.print(f"[red]Error reading compose file: {e}[/red]")
            raise typer.Exit(1)

        # Parse registry credentials
        registry_credentials = None
        if registry_creds:
            try:
                registry_credentials = json.loads(registry_creds)
            except json.JSONDecodeError:
                status.stop()
                console.print(
                    "[red]Error: Invalid JSON format for registry credentials[/red]"
                )
                raise typer.Exit(1)

        # Validate registry credentials and type
        if (registry_creds and not registry_type) or (
            registry_type and not registry_creds
        ):
            status.stop()
            console.print(
                "[red]Error: Both --registry-creds and --registry-type must be provided together[/red]"
            )
            raise typer.Exit(1)

        status.update(f"Starting Docker Compose from {compose_file.name}...")

        # Build request for v2 compose API
        compose_request = {
            "compose_file_code": compose_file_content,
            "timeout": timeout,
            "execution_type": machine_type,
        }

        if file_name:
            compose_request["file_name"] = file_name
        else:
            compose_request["file_name"] = compose_file.name

        # Handle registry credentials
        if registry_type and registry_credentials:
            compose_request["docker_registry_credential_type"] = registry_type

            if registry_type == "aws":
                creds = registry_credentials
                compose_request.update(
                    {
                        "aws_access_key_id": creds.get("aws_access_key_id"),
                        "aws_secret_access_key": creds.get("aws_secret_access_key"),
                        "aws_session_token": creds.get("aws_session_token"),
                        "aws_region": creds.get("region", "us-east-1"),
                    }
                )
            elif registry_type == "basic":
                creds = registry_credentials
                compose_request.update(
                    {
                        "docker_username": creds.get("username"),
                        "docker_password": creds.get("password"),
                    }
                )

        # Call the v2 compose endpoint
        status.update("Submitting execution...")

        response = httpx.post(
            f"{config.base_url}/api/v2/external/execution/compose/start",
            json=compose_request,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=30.0,
        )

        if response.status_code != 200:
            status.stop()
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            if response.status_code == 401:
                console.print(
                    "[red]Authentication failed. Your session may have expired.[/red]"
                )
                console.print("[yellow]Run 'lyceum auth login' to re-authenticate.[/yellow]")
            elif response.content:
                console.print(f"[red]{response.content.decode()}[/red]")
            raise typer.Exit(1)

        result = response.json()
        execution_id = result.get("execution_id")
        streaming_url = result.get("streaming_url")

        if detach:
            # Detached mode - just return the execution info
            status.stop()
            console.print(f"[dim]Compose file: {compose_file.name}[/dim]")
            console.print(f"[dim]Machine: {machine_type}[/dim]")
            console.print(f"[dim]Execution ID: {execution_id}[/dim]")
            console.print("")
            console.print(f"[dim]To stream logs:[/dim] lyceum compose logs {execution_id}")
        else:
            # Default: stream output in real-time
            status.stop()
            success = stream_execution_output(execution_id, streaming_url)

            # Show execution ID at the end
            console.print(f"[dim]Execution ID: {execution_id}[/dim]")

            if not success:
                raise typer.Exit(1)

    except typer.Exit:
        status.stop()
        raise
    except Exception as e:
        status.stop()
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@compose_app.command("logs")
def compose_logs(
    execution_id: str = typer.Argument(..., help="Execution ID to stream logs from"),
):
    """Stream logs from a running or completed Docker Compose execution.

    Examples:
        lyceum compose logs 9d73319c-6f1c-4b4c-90e4-044244353ce4
    """
    status = StatusLine()

    try:
        config.get_client()

        status.start()
        status.update("Connecting to execution...")
        status.stop()

        # Pass None for streaming_url to use the default v2 endpoint
        success = stream_execution_output(execution_id, None)

        console.print(f"[dim]Execution ID: {execution_id}[/dim]")

        if not success:
            raise typer.Exit(1)

    except typer.Exit:
        status.stop()
        raise
    except Exception as e:
        status.stop()
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@compose_app.command("registry-examples")
def show_registry_examples():
    """Show examples of Docker registry credential formats"""
    console.print("[bold cyan]Docker Registry Credential Examples[/bold cyan]\n")

    console.print("[bold]1. Docker Hub (basic)[/bold]")
    console.print("Type: [green]basic[/green]")
    console.print(
        'Credentials: [yellow]\'{"username": "myuser", "password": "mypassword"}\'[/yellow]\n'
    )

    console.print("[bold]2. AWS ECR (aws)[/bold]")
    console.print("Type: [green]aws[/green]")
    console.print(
        'Credentials: [yellow]\'{"region": "us-west-2", "aws_access_key_id": "AKIAI...", "aws_secret_access_key": "wJalrX...", "session_token": "optional..."}\'[/yellow]\n'
    )

    console.print("[bold]3. Private Registry (basic)[/bold]")
    console.print("Type: [green]basic[/green]")
    console.print(
        'Credentials: [yellow]\'{"username": "admin", "password": "secret"}\'[/yellow]\n'
    )

    console.print("[bold]Example Commands:[/bold]")
    console.print("# Docker Hub:")
    console.print(
        "[dim]lyceum compose run docker-compose.yml --registry-type basic --registry-creds '{\"username\": \"myuser\", \"password\": \"mytoken\"}'[/dim]"
    )
    console.print("\n# AWS ECR:")
    console.print(
        "[dim]lyceum compose run docker-compose.yml --registry-type aws --registry-creds '{\"region\": \"us-west-2\", \"aws_access_key_id\": \"AKIAI...\", \"aws_secret_access_key\": \"wJalrX...\"}'[/dim]"
    )
    console.print("\n# Private Registry:")
    console.print(
        "[dim]lyceum compose run docker-compose.yml --registry-type basic --registry-creds '{\"username\": \"admin\", \"password\": \"secret\"}'[/dim]"
    )
