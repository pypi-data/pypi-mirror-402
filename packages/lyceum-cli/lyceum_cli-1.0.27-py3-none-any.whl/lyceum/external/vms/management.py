"""VM instance management commands"""

import time

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from ...shared.config import config

console = Console()

vms_app = typer.Typer(name="vms", help="VM instance management commands")


@vms_app.command("start")
def start_instance(
    hardware_profile: str = typer.Option(
        "a100", "--hardware-profile", "-h", help="Hardware profile (cpu, a100, h100, etc.)"
    ),
    public_key: str = typer.Option(..., "--key", "-k", help="SSH public key for VM access"),
    name: str | None = typer.Option(None, "--name", "-n", help="Friendly name for the instance"),
    cpu: int | None = typer.Option(None, "--cpu", help="Number of CPU cores (uses hardware profile default if not specified)"),
    memory: int | None = typer.Option(None, "--memory", help="Memory in GB (uses hardware profile default if not specified)"),
    disk: int | None = typer.Option(None, "--disk", help="Disk size in GB (uses hardware profile default if not specified)"),
    gpu_count: int | None = typer.Option(None, "--gpu-count", help="Number of GPUs (uses hardware profile default if not specified)"),
):
    """Start a new VM instance"""
    try:
        # Ensure we have a valid token
        config.get_client()

        # Create instance specs - only include values that were explicitly provided
        instance_specs = {}
        if cpu is not None:
            instance_specs["cpu"] = cpu
        if memory is not None:
            instance_specs["memory"] = memory
        if disk is not None:
            instance_specs["disk"] = disk
        if gpu_count is not None:
            instance_specs["gpu_count"] = gpu_count

        # Create request payload
        payload = {
            "instance_specs": instance_specs,
            "user_public_key": public_key,
            "hardware_profile": hardware_profile,
        }

        if name:
            payload["name"] = name

        # Make API request
        console.print("[dim]Creating VM instance...[/dim]")
        response = httpx.post(
            f"{config.base_url}/api/v2/external/vms/create",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
            timeout=60.0,
        )

        if response.status_code != 200:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            try:
                error_data = response.json()
                console.print(f"[red]{error_data.get('detail', response.text)}[/red]")
            except Exception:
                console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()

        console.print("[green]✅ VM instance created successfully![/green]")
        console.print(f"[bold]VM ID:[/bold] {data['vm_id']}")
        console.print(f"[bold]Status:[/bold] {data['status']}")
        if data.get("name"):
            console.print(f"[bold]Name:[/bold] {data['name']}")
        console.print(f"[dim]Created at: {data['created_at']}[/dim]")

        # If instance is pending, poll for readiness
        if data['status'] == 'pending':
            console.print("\n[yellow]Instance is provisioning...[/yellow]")

            vm_id = data['vm_id']
            poll_interval = 30  # seconds
            max_attempts = 20  # 10 minutes max
            attempt = 0

            with Live(Spinner("dots", text="Provisioning instance..."), console=console, refresh_per_second=4) as live:
                while attempt < max_attempts:
                    time.sleep(poll_interval)
                    attempt += 1

                    try:
                        status_response = httpx.get(
                            f"{config.base_url}/api/v2/external/vms/{vm_id}/status",
                            headers={"Authorization": f"Bearer {config.api_key}"},
                            timeout=30.0,
                        )

                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            current_status = status_data.get('status')

                            if current_status == 'ready' or current_status == 'running':
                                live.stop()
                                console.print(f"\n[green]✅ Instance is now {current_status}![/green]")

                                if status_data.get("ip_address"):
                                    ip_addr = status_data['ip_address']
                                    console.print(f"[bold]IP Address:[/bold] {ip_addr}")

                                    # Handle IP:PORT format
                                    if ':' in ip_addr:
                                        ip, port = ip_addr.split(':', 1)
                                        console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> -p {port} ubuntu@{ip}")
                                    else:
                                        console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> ubuntu@{ip_addr}")
                                break
                            elif current_status in ['failed', 'terminated', 'error']:
                                live.stop()
                                console.print(f"\n[red]❌ Instance provisioning failed with status: {current_status}[/red]")
                                break
                            else:
                                live.update(Spinner("dots", text=f"Provisioning instance... (status: {current_status}, attempt {attempt}/{max_attempts})"))
                    except Exception as e:
                        # Continue polling even if status check fails
                        live.update(Spinner("dots", text=f"Provisioning instance... (attempt {attempt}/{max_attempts})"))

                if attempt >= max_attempts:
                    live.stop()
                    console.print(f"\n[yellow]⚠️  Polling timed out. Instance may still be provisioning.[/yellow]")
                    console.print(f"[dim]Check status with: lyceum vms instance-status {vm_id}[/dim]")

        elif data.get("ip_address"):
            ip_addr = data['ip_address']
            console.print(f"[bold]IP Address:[/bold] {ip_addr}")

            # Handle IP:PORT format
            if ':' in ip_addr:
                ip, port = ip_addr.split(':', 1)
                console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> -p {port} ubuntu@{ip}")
            else:
                console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> ubuntu@{ip_addr}")

    except httpx.TimeoutException:
        console.print("[red]Error: Request timed out[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@vms_app.command("list")
def list_instances():
    """List all your VM instances (both active and inactive)"""
    try:
        # Ensure we have a valid token
        config.get_client()

        # Make API request
        response = httpx.get(
            f"{config.base_url}/api/v2/external/vms/list",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=30.0,
        )

        if response.status_code != 200:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()
        vms = data.get("vms", [])

        if not vms:
            console.print("[yellow]No VM instances found.[/yellow]")
            return

        # Create table
        table = Table(title="VM Instances")
        table.add_column("VM ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("IP Address", style="blue")
        table.add_column("Hardware", style="magenta")
        table.add_column("Billed ($)", style="red")
        table.add_column("Created At", style="dim")

        for vm in vms:
            table.add_row(
                vm["vm_id"],
                vm.get("name", "-"),
                vm["status"],
                vm.get("ip_address", "-"),
                vm.get("hardware_profile", "-"),
                f"{vm.get('billed', 0):.4f}" if vm.get("billed") is not None else "-",
                vm["created_at"],
            )

        console.print(table)

    except httpx.TimeoutException:
        console.print("[red]Error: Request timed out[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@vms_app.command("availability")
def list_availability():
    """List available VM hardware profiles"""
    try:
        # Ensure we have a valid token
        config.get_client()

        # Make API request
        response = httpx.get(
            f"{config.base_url}/api/v2/external/vms/availability",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=30.0,
        )

        if response.status_code != 200:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()
        hardware_profiles = data.get("available_hardware_profiles", [])
        pool_name = data.get("pool_name", "")

        if not hardware_profiles:
            console.print("[yellow]No hardware profiles available.[/yellow]")
            return

        console.print(f"\n[bold cyan]Available Hardware Profiles[/bold cyan] (Pool: {pool_name})\n")

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Hardware Profile", style="cyan")
        table.add_column("Available", style="green", justify="right")
        table.add_column("Total", style="yellow", justify="right")
        table.add_column("GPU Type", style="blue")
        table.add_column("vCPU", style="white", justify="right")
        table.add_column("Memory (GB)", style="white", justify="right")

        for profile in hardware_profiles:
            table.add_row(
                profile.get("hardware_profile", "-"),
                str(profile.get("available", 0)),
                str(profile.get("total", 0)),
                profile.get("gpu_type", "-"),
                str(profile.get("vcpu", "-")),
                str(profile.get("memory_gb", "-")),
            )

        console.print(table)
        console.print(f"\n[dim]Use these hardware profile names with: lyceum vms start-instance --hardware-profile <name>[/dim]")

    except httpx.TimeoutException:
        console.print("[red]Error: Request timed out[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@vms_app.command("status")
def instance_status(
    vm_id: str = typer.Argument(..., help="VM instance ID"),
):
    """Get detailed status of a VM instance"""
    try:
        # Ensure we have a valid token
        config.get_client()

        # Make API request
        response = httpx.get(
            f"{config.base_url}/api/v2/external/vms/{vm_id}/status",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=30.0,
        )

        if response.status_code != 200:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            try:
                error_data = response.json()
                console.print(f"[red]{error_data.get('detail', response.text)}[/red]")
            except Exception:
                console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()

        console.print(f"[bold cyan]VM Instance: {vm_id}[/bold cyan]\n")
        console.print(f"[bold]Status:[/bold] {data['status']}")
        if data.get("name"):
            console.print(f"[bold]Name:[/bold] {data['name']}")
        if data.get("ip_address"):
            console.print(f"[bold]IP Address:[/bold] {data['ip_address']}")
        console.print(f"[bold]Hardware Profile:[/bold] {data.get('hardware_profile', '-')}")
        if data.get("billed") is not None:
            console.print(f"[bold]Total Billed:[/bold] ${data['billed']:.4f}")
        if data.get("uptime_seconds") is not None:
            hours = data["uptime_seconds"] / 3600
            console.print(f"[bold]Uptime:[/bold] {hours:.2f} hours")
        console.print(f"[dim]Created at: {data['created_at']}[/dim]")

        if data.get("instance_specs"):
            console.print("\n[bold]Instance Specs:[/bold]")
            specs = data["instance_specs"]
            console.print(f"  CPU: {specs.get('cpu', '-')} cores")
            console.print(f"  Memory: {specs.get('memory', '-')} GB")
            console.print(f"  Disk: {specs.get('disk', '-')} GB")
            console.print(f"  GPU Count: {specs.get('gpu_count', '-')}")

        if data.get("ip_address"):
            ip_addr = data['ip_address']
            # Handle IP:PORT format
            if ':' in ip_addr:
                ip, port = ip_addr.split(':', 1)
                console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> -p {port} ubuntu@{ip}")
            else:
                console.print(f"\n[cyan]SSH command:[/cyan] ssh -i <your-key> ubuntu@{ip_addr}")

    except httpx.TimeoutException:
        console.print("[red]Error: Request timed out[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@vms_app.command("terminate")
def terminate_instance(
    vm_id: str = typer.Argument(..., help="VM instance ID to terminate"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Terminate (delete) a VM instance"""
    try:
        # Ensure we have a valid token
        config.get_client()

        # Confirm termination unless --force is used
        if not force:
            confirm = typer.confirm(f"Are you sure you want to terminate VM {vm_id}?")
            if not confirm:
                console.print("[yellow]Termination cancelled.[/yellow]")
                return

        # Make API request
        console.print("[dim]Terminating VM instance...[/dim]")
        response = httpx.delete(
            f"{config.base_url}/api/v2/external/vms/{vm_id}",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=30.0,
        )

        if response.status_code != 200:
            console.print(f"[red]Error: HTTP {response.status_code}[/red]")
            try:
                error_data = response.json()
                console.print(f"[red]{error_data.get('detail', response.text)}[/red]")
            except Exception:
                console.print(f"[red]{response.text}[/red]")
            raise typer.Exit(1)

        data = response.json()

        console.print(f"[green]✅ {data.get('message', 'VM instance terminated successfully')}[/green]")

    except httpx.TimeoutException:
        console.print("[red]Error: Request timed out[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
