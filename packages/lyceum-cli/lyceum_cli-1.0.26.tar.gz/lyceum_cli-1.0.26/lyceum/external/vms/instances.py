"""
VM instance management CLI commands.

Provides commands for:
- Starting VM instances with specified hardware profiles
- Listing user's VM instances
- Getting instance status
- Terminating instances
"""

import sys
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

from lyceum.shared.config import config

app = typer.Typer(help="Manage VM instances")
console = Console()


def get_headers() -> dict[str, str]:
    """Get authorization headers for API requests."""
    # Ensure we have a valid token
    config.get_client()
    return {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}


@app.command("start")
def start_instance(
    hardware_profile: str = typer.Option(
        ..., "--profile", "-p", help="Hardware profile (e.g., 'a100', 'h100', 'cpu')"
    ),
    ssh_key: str = typer.Option(
        ..., "--key", "-k", help="SSH public key for accessing the instance"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Optional friendly name for the instance"
    ),
    vcpu_min: int = typer.Option(1, "--vcpu", help="Minimum vCPU count"),
    memory_min: int = typer.Option(8, "--memory", "-m", help="Minimum memory in GB"),
    disk_min: int = typer.Option(20, "--disk", "-d", help="Minimum disk in GB"),
    gpu_type: Optional[str] = typer.Option(None, "--gpu-type", help="GPU type (e.g., 'A100', 'H100')"),
    gpu_count: Optional[int] = typer.Option(None, "--gpu-count", help="Number of GPUs"),
    gpu_memory: Optional[int] = typer.Option(None, "--gpu-memory", help="GPU memory in GB"),
):
    """
    Start a new VM instance with specified hardware profile.

    Example:
        lyceum vms start -p a100 -k "ssh-rsa AAAAB3..." -n "training-vm"
    """
    console.print(f"[cyan]Starting VM instance with profile: {hardware_profile}...[/cyan]")

    # Construct instance specs
    instance_specs = {
        "vcpu": {"min": vcpu_min},
        "memory": {"min": memory_min},
        "disk": {"min": disk_min},
    }

    if gpu_type:
        instance_specs["gpu_type"] = gpu_type
    if gpu_count:
        instance_specs["gpu_count"] = gpu_count
    if gpu_memory:
        instance_specs["gpu_memory"] = {"value": gpu_memory}

    payload = {
        "instance_specs": instance_specs,
        "user_public_key": ssh_key,
        "hardware_profile": hardware_profile,
    }

    if name:
        payload["name"] = name

    try:
        base_url = config.base_url
        url = f"{base_url}/api/v2/external/vms/create"

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=get_headers())
            response.raise_for_status()
            data = response.json()

        console.print("[green]✓[/green] VM instance created successfully!")
        console.print(f"\n[bold]Instance ID:[/bold] {data['vm_id']}")
        console.print(f"[bold]Status:[/bold] {data['status']}")
        if data.get("ip_address"):
            console.print(f"[bold]IP Address:[/bold] {data['ip_address']}")
            console.print(f"\n[cyan]Connect via:[/cyan] ssh root@{data['ip_address']}")
        if data.get("name"):
            console.print(f"[bold]Name:[/bold] {data['name']}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            console.print("[red]Error:[/red] Insufficient credits")
            try:
                detail = e.response.json().get("detail", "")
                console.print(f"[yellow]{detail}[/yellow]")
            except Exception:
                pass
        else:
            console.print(f"[red]Error:[/red] HTTP {e.response.status_code}")
            try:
                console.print(f"[yellow]{e.response.json().get('detail', e.response.text)}[/yellow]")
            except Exception:
                console.print(f"[yellow]{e.response.text}[/yellow]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Failed to connect to API: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("list")
def list_instances():
    """
    List all VM instances for the current user.

    Example:
        lyceum vms list
    """
    try:
        base_url = config.base_url
        url = f"{base_url}/api/v2/external/vms/list"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers())
            response.raise_for_status()
            data = response.json()

        vms = data.get("vms", [])

        if not vms:
            console.print("[yellow]No VM instances found.[/yellow]")
            return

        table = Table(title="Your VM Instances", show_header=True, header_style="bold magenta")
        table.add_column("VM ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("IP Address", style="blue")
        table.add_column("Billed ($)", style="red", justify="right")
        table.add_column("Created At", style="white")

        for vm in vms:
            table.add_row(
                vm.get("vm_id", ""),
                vm.get("name", "-"),
                vm.get("status", ""),
                vm.get("ip_address", "-"),
                f"{vm.get('billed', 0):.4f}",
                vm.get("created_at", "")[:19] if vm.get("created_at") else "-",
            )

        console.print(table)
        console.print(f"\n[cyan]Total instances: {data.get('total', 0)}[/cyan]")

    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error:[/red] HTTP {e.response.status_code}")
        try:
            console.print(f"[yellow]{e.response.json().get('detail', e.response.text)}[/yellow]")
        except Exception:
            console.print(f"[yellow]{e.response.text}[/yellow]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Failed to connect to API: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("status")
def instance_status(
    vm_id: str = typer.Argument(..., help="VM instance ID"),
):
    """
    Get detailed status of a specific VM instance.

    Example:
        lyceum vms status vm-abc123
    """
    try:
        base_url = config.base_url
        url = f"{base_url}/api/v2/external/vms/{vm_id}/status"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=get_headers())
            response.raise_for_status()
            data = response.json()

        console.print(f"\n[bold cyan]VM Instance Details[/bold cyan]")
        console.print(f"[bold]VM ID:[/bold] {data['vm_id']}")
        if data.get("name"):
            console.print(f"[bold]Name:[/bold] {data['name']}")
        console.print(f"[bold]Status:[/bold] {data['status']}")
        if data.get("ip_address"):
            console.print(f"[bold]IP Address:[/bold] {data['ip_address']}")
        if data.get("uptime_seconds"):
            hours = data["uptime_seconds"] // 3600
            minutes = (data["uptime_seconds"] % 3600) // 60
            seconds = data["uptime_seconds"] % 60
            console.print(f"[bold]Uptime:[/bold] {hours}h {minutes}m {seconds}s")
        if data.get("billed") is not None:
            console.print(f"[bold]Total Billed:[/bold] ${data['billed']:.4f}")
        console.print(f"[bold]Created At:[/bold] {data.get('created_at', '-')}")

        if data.get("instance_specs"):
            console.print(f"\n[bold cyan]Hardware Specs:[/bold cyan]")
            specs = data["instance_specs"]
            if "vcpu" in specs:
                console.print(f"  vCPU: {specs['vcpu']}")
            if "memory" in specs:
                console.print(f"  Memory: {specs['memory']}")
            if "disk" in specs:
                console.print(f"  Disk: {specs['disk']}")
            if "gpu_type" in specs:
                console.print(f"  GPU Type: {specs['gpu_type']}")
            if "gpu_count" in specs:
                console.print(f"  GPU Count: {specs['gpu_count']}")
            if "gpu_memory" in specs:
                console.print(f"  GPU Memory: {specs['gpu_memory']}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error:[/red] VM instance '{vm_id}' not found")
        else:
            console.print(f"[red]Error:[/red] HTTP {e.response.status_code}")
            try:
                console.print(f"[yellow]{e.response.json().get('detail', e.response.text)}[/yellow]")
            except Exception:
                console.print(f"[yellow]{e.response.text}[/yellow]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Failed to connect to API: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("terminate")
def terminate_instance(
    vm_id: str = typer.Argument(..., help="VM instance ID to terminate"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    Terminate and delete a VM instance permanently.

    Example:
        lyceum vms terminate vm-abc123
    """
    if not force:
        confirm = typer.confirm(
            f"Are you sure you want to terminate VM instance '{vm_id}'? This action cannot be undone."
        )
        if not confirm:
            console.print("[yellow]Termination cancelled.[/yellow]")
            raise typer.Exit(0)

    console.print(f"[cyan]Terminating VM instance {vm_id}...[/cyan]")

    try:
        base_url = config.base_url
        url = f"{base_url}/api/v2/external/vms/{vm_id}"

        with httpx.Client(timeout=30.0) as client:
            response = client.delete(url, headers=get_headers())
            response.raise_for_status()
            data = response.json()

        console.print(f"[green]✓[/green] {data.get('message', 'VM instance terminated successfully')}")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Error:[/red] VM instance '{vm_id}' not found")
        else:
            console.print(f"[red]Error:[/red] HTTP {e.response.status_code}")
            try:
                console.print(f"[yellow]{e.response.json().get('detail', e.response.text)}[/yellow]")
            except Exception:
                console.print(f"[yellow]{e.response.text}[/yellow]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Error:[/red] Failed to connect to API: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
