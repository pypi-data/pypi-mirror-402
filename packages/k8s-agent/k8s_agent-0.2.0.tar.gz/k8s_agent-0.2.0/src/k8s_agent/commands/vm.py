"""VM management commands: list, delete."""

import json as json_module
import os

import click

from ..config import AgentConfig
from ..http import K8sVMgrAPI, APIError


def _default_api_url():
    return os.environ.get("K8SVMGR_API_URL", "").strip()


def _normalize_api_url(api_url: str) -> str:
    api_url = (api_url or "").strip().rstrip("/")
    if api_url.lower().endswith("/api"):
        api_url = api_url[:-4]
    return api_url


def _extract_data(resp: dict):
    """Extract data from API response, handling both dict and list responses."""
    data = resp.get("data")
    # Return the data regardless of type (dict, list, etc.)
    # Return empty dict only if data is None
    return data if data is not None else {}


def _get_authenticated_api(api_url: str = ""):
    """Get authenticated API client or raise error."""
    cfg = AgentConfig.load()
    api_url = _normalize_api_url(api_url or cfg.api_url or _default_api_url())
    if not api_url or not cfg.access_token:
        raise click.ClickException("Not logged in. Run: k8s-agent login")
    return K8sVMgrAPI(api_url, access_token=cfg.access_token), api_url


@click.group()
def vm_commands():
    """VM management commands."""
    pass


@vm_commands.command(name="list")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "simple"]), default="table", help="Output format")
def list_vms(api_url: str, output_format: str):
    """List all VMs (requires login)."""
    api, _ = _get_authenticated_api(api_url)

    try:
        resp = api.request("GET", "/api/vm")
    except APIError as e:
        raise click.ClickException(str(e))

    data = _extract_data(resp)
    vms = data.get("vms", [])

    if not vms:
        click.echo("No VMs found.")
        return

    if output_format == "json":
        click.echo(json_module.dumps(vms, indent=2, ensure_ascii=False))
    elif output_format == "simple":
        for vm in vms:
            click.echo(f"{vm.get('id', 'N/A')}\t{vm.get('status', 'N/A')}\t{vm.get('machine_type', 'N/A')}")
    else:  # table format
        _print_vm_table(vms)


def _print_vm_table(vms):
    """Print VMs in a condensed table format."""
    from datetime import datetime

    col_widths = {
        "id": 18,
        "status": 12,
        "gpu_model": 14,
        "gpu_num": 5,
        "cpu_num": 5,
        "duration": 12,
        "ip": 16,
        "port": 8,
        "credit": 10,
    }

    # Header: ID, Status, GPU Model, GPU, CPU, Duration, IP, Port, Credit
    header = (
        f"{'ID':<{col_widths['id']}} "
        f"{'Status':<{col_widths['status']}} "
        f"{'GPU Model':<{col_widths['gpu_model']}} "
        f"{'GPU':<{col_widths['gpu_num']}} "
        f"{'CPU':<{col_widths['cpu_num']}} "
        f"{'Duration':<{col_widths['duration']}} "
        f"{'IP Address':<{col_widths['ip']}} "
        f"{'Port':<{col_widths['port']}} "
        f"{'Credit':<{col_widths['credit']}}"
    )
    click.echo(header)
    click.echo("-" * sum(col_widths.values()) + "-" * (len(col_widths) - 1))

    # Rows
    for vm in vms:
        # ID
        vm_id = (vm.get("id") or "N/A")[:col_widths["id"]]

        # Status (second column)
        status = (vm.get("status") or "N/A")[:col_widths["status"]]

        # GPU Model
        gpu_model = (vm.get("gpu_model") or "-")[:col_widths["gpu_model"]]

        # GPU Number
        gpu_num = str(vm.get("gpu_num", 0))[:col_widths["gpu_num"]]

        # CPU Number
        cpu_num = str(vm.get("cpu_num", 0))[:col_widths["cpu_num"]]

        # Duration (calculate from create_time to now)
        create_ts = vm.get("create_time")
        if create_ts:
            duration_sec = int(datetime.now().timestamp() - create_ts)
            # Handle negative durations (e.g., clock skew or future timestamps)
            if duration_sec < 0:
                duration = "0h 0m"
            else:
                hours = duration_sec // 3600
                minutes = (duration_sec % 3600) // 60
                duration = f"{hours}h {minutes}m"
        else:
            duration = "-"
        duration = duration[:col_widths["duration"]]

        # Host IP
        host_ip = (vm.get("host_ip") or "-")[:col_widths["ip"]]

        # Port
        svc_port = (vm.get("svc_port") or "-")[:col_widths["port"]]

        # Used credit
        used_credit = vm.get("used_credit")
        credit_str = f"{used_credit:.1f}" if used_credit is not None else "-"
        credit_str = credit_str[:col_widths["credit"]]

        row = (
            f"{vm_id:<{col_widths['id']}} "
            f"{status:<{col_widths['status']}} "
            f"{gpu_model:<{col_widths['gpu_model']}} "
            f"{gpu_num:<{col_widths['gpu_num']}} "
            f"{cpu_num:<{col_widths['cpu_num']}} "
            f"{duration:<{col_widths['duration']}} "
            f"{host_ip:<{col_widths['ip']}} "
            f"{svc_port:<{col_widths['port']}} "
            f"{credit_str:<{col_widths['credit']}}"
        )
        click.echo(row)

    click.echo(f"\nTotal: {len(vms)} VM(s)")


@vm_commands.command(name="create")
@click.option("--vm-id", "vm_id", help="VM ID (auto-generated if not specified)")
@click.option("--cpu", type=int, help="Number of CPUs")
@click.option("--gpu", type=int, default=0, help="Number of GPUs (default: 0)")
@click.option("--gpu-model", "gpu_model", help="GPU model (e.g., A800-80G-R)")
@click.option("--shm", type=int, help="Shared memory in GB")
@click.option("--driver-version", "driver_version", help="GPU driver version (default: 535)")
@click.option("--image", help="Docker image URL")
@click.option("--command", help="Custom command to run")
@click.option("--args", help="Arguments for the command")
@click.option("--key", help="SSH public key content (or use --key-name for lookup)")
@click.option("--key-name", "key_name", help="SSH public key name/description to use")
@click.option("--home-save", "home_save", help="Home backup to restore (e.g., fuchenxu_zero.tar)")
@click.option("--env-save", "env_save", help="Environment backup to restore (e.g., fuchenxu_env.tar)")
@click.option("--zero", is_flag=True, help="Mark as zero machine (primary backup machine)")
@click.option("--experimental", is_flag=True, help="Mark as experimental machine")
@click.option("--purpose", help="Purpose/description of the VM")
@click.option("--max-idle-hrs", "max_idle_hrs", type=int, help="Max idle hours before auto-shutdown")
@click.option("--node-name", "node_name", help="Specific node to schedule on (Constraints apply)")
@click.option("--check", "-c", is_flag=True, help="Check availability only (don't create VM)")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def create_vm(vm_id, cpu, gpu, gpu_model, shm, driver_version, image, command, args, key, key_name,
              home_save, env_save, zero, experimental, purpose, max_idle_hrs, node_name, check, api_url):
    """Create a new VM (requires login).

    Examples:
        # Check availability for CPU machine
        k8s-agent create --cpu 16 --check

        # Check availability for GPU machine
        k8s-agent create --gpu 2 --gpu-model A800-80G-R --check

        # CPU machine
        k8s-agent create --cpu 16

        # GPU machine with SSH key
        k8s-agent create --gpu 2 --gpu-model A800-80G-R --key-name "my-laptop"

        # Restore from backups
        k8s-agent create --gpu 2 --gpu-model A800-80G-R --home-save fuchenxu_zero.tar --env-save fuchenxu_env.tar

        # Schedule on specific node
        k8s-agent create --gpu 2 --gpu-model A800-80G-R --node-name node-gpu-01

        # Full specification
        k8s-agent create --gpu 4 --gpu-model A800-80G-R --shm 32 --image harbor.example.com/ml/pytorch:latest --purpose "Training model" --key-name "workstation"
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        # Validate GPU requirements
        if gpu and gpu > 0:
            if not gpu_model:
                raise click.ClickException("--gpu-model is required when creating GPU machines")

        # Check availability mode
        if check:
            click.echo("Checking availability...")

            # Build query parameters
            params = []
            if cpu:
                params.append(f"cpu={cpu}")
            if gpu and gpu > 0:
                params.append(f"gpu={gpu}")
                params.append(f"gpu_model={gpu_model}")
                if driver_version:
                    params.append(f"driver_version={driver_version}")

            # Build URL with query string
            query_string = "&".join(params)
            endpoint = f"/api/vm/availability?{query_string}" if query_string else "/api/vm/availability"

            # Query availability endpoint
            resp = api.request("GET", endpoint)
            data = resp.get("data", {})

            total = data.get("total", 0)
            available_nodes = data.get("items", [])

            if total > 0:
                click.echo(f"✓ {total} node(s) available")
                if available_nodes:
                    click.echo(f"\nAvailable nodes:")
                    for node in available_nodes:
                        click.echo(f"  - {node}")
            else:
                click.echo("✗ No nodes available for the specified configuration")

            return  # Exit without creating VM

        # Resolve SSH key if key_name is provided
        public_key_value = None
        if key_name:
            click.echo(f"Looking up SSH key '{key_name}'...")
            keys_resp = api.request("GET", "/api/keys")
            keys_data = _extract_data(keys_resp)

            if isinstance(keys_data, list):
                # Search for key by description
                matching_keys = [k for k in keys_data if k.get("description") == key_name]
                if not matching_keys:
                    raise click.ClickException(f"SSH key '{key_name}' not found. Use 'k8s-agent keys' to list available keys.")
                if len(matching_keys) > 1:
                    raise click.ClickException(f"Multiple keys found with name '{key_name}'. Please use a unique key name.")

                public_key_value = matching_keys[0].get("key")
                click.echo(f"✓ Found SSH key: {key_name}")
        elif key is not None:
            # Legacy: key ID provided
            public_key_value = key

        # Build request body matching frontend formData structure
        limit = {
            "gpu": gpu or 0,
            "storage": 0,
            "local_storage": 200,
        }

        if cpu is not None:
            limit["cpu"] = cpu
        if gpu_model:
            limit["gpu_model"] = gpu_model
        if shm is not None:
            limit["shm"] = shm

        body = {
            "limit": limit,
            "machines": [],
            "zero": zero,
            "preemptive": False,
        }

        # Optional parameters
        if vm_id:
            body["vm_id"] = vm_id
        if public_key_value is not None:
            body["public_key"] = public_key_value
        if home_save or env_save:
            # saves is a tuple: (home_save, env_save)
            body["saves"] = (home_save or "", env_save or "")
        if image:
            body["image"] = image
        if command:
            body["command"] = command
        if args:
            body["args"] = args
        if purpose:
            body["purpose"] = purpose
        if driver_version:
            body["driver_version"] = driver_version
        if experimental:
            body["experimental"] = experimental
        if max_idle_hrs is not None:
            body["max_idle_hrs"] = max_idle_hrs
        if node_name:
            body["node_name"] = node_name

        # Create VM
        click.echo("Creating VM...")
        resp = api.request("POST", "/api/vm", json_body=body)

        data = resp.get("data", {})
        if data.get("pending"):
            click.echo("⚠ VM is pending - waiting for cluster resources.")
        else:
            click.echo("✓ VM creation request submitted successfully.")

        # Show summary
        machine_type_str = f"{gpu_model} x{gpu}" if gpu and gpu > 0 else f"CPU x{cpu or 8}"
        click.echo(f"\nVM Configuration:")
        click.echo(f"  Type: {machine_type_str}")
        if shm:
            click.echo(f"  Shared Memory: {shm}GB")
        if image:
            click.echo(f"  Image: {image}")
        if purpose:
            click.echo(f"  Purpose: {purpose}")

        flags = []
        if zero:
            flags.append("Zero machine")
        if experimental:
            flags.append("Experimental")
        if flags:
            click.echo(f"  Flags: {', '.join(flags)}")

        click.echo("\nUse 'k8s-agent list' to check VM status.")

    except APIError as e:
        error_msg = str(e)
        raise click.ClickException(f"Failed to create VM: {error_msg}")


@vm_commands.command(name="events")
@click.argument("vm_id")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def vm_events(vm_id: str, api_url: str):
    """Get VM events (requires login).

    Examples:
        k8s-agent events my-vm-001
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        endpoint = f"/api/vm/events?vmid={vm_id}"
        resp = api.request("GET", endpoint)

        data = resp.get("data", {})
        events = data if isinstance(data, list) else data.get("events", [])

        if not events:
            click.echo("No events found for this VM.")
            return

        click.echo(f"Events for VM '{vm_id}':\n")
        for event in events:
            # Handle both dict and object formats
            if isinstance(event, dict):
                event_type = event.get("type", "N/A")
                reason = event.get("reason", "N/A")
                message = event.get("message", "N/A")
                timestamp = event.get("last_timestamp", event.get("timestamp", "N/A"))
            else:
                event_type = getattr(event, "type", "N/A")
                reason = getattr(event, "reason", "N/A")
                message = getattr(event, "message", "N/A")
                timestamp = getattr(event, "last_timestamp", getattr(event, "timestamp", "N/A"))

            click.echo(f"[{timestamp}] {event_type}: {reason}")
            click.echo(f"  {message}\n")

    except APIError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise click.ClickException(f"VM '{vm_id}' not found.")
        raise click.ClickException(f"Failed to get events: {error_msg}")


@vm_commands.command(name="logs")
@click.argument("vm_id")
@click.option("--tail", type=int, help="Number of lines to show from the end")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def vm_logs(vm_id: str, tail: int, api_url: str):
    """Get VM logs (requires login).

    Examples:
        k8s-agent logs my-vm-001
        k8s-agent logs my-vm-001 --tail 100
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        endpoint = f"/api/vm/logs?vmid={vm_id}"
        if tail:
            endpoint += f"&tail={tail}"

        resp = api.request("GET", endpoint)

        data = resp.get("data", {})
        logs = data if isinstance(data, str) else data.get("logs", "")

        if not logs:
            click.echo("No logs available for this VM.")
            return

        click.echo(logs)

    except APIError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise click.ClickException(f"VM '{vm_id}' not found.")
        raise click.ClickException(f"Failed to get logs: {error_msg}")


@vm_commands.command(name="dashboard")
@click.argument("vm_id")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def vm_dashboard(vm_id: str, api_url: str):
    """Get VM dashboard metrics with visual charts (requires login).

    Examples:
        k8s-agent dashboard my-vm-001
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        endpoint = f"/api/vm/dashboard?vmid={vm_id}"
        resp = api.request("GET", endpoint)

        data = resp.get("data", {})

        if not data:
            click.echo("No dashboard data available for this VM.")
            return

        click.echo(f"╔═══════════════════════════════════════════════════════════════╗")
        click.echo(f"║  Dashboard: {vm_id:<48}║")
        click.echo(f"╚═══════════════════════════════════════════════════════════════╝\n")

        # Display memory metrics
        memory_metrics = data.get("memory_metrics", {})
        if memory_metrics:
            _display_memory_section(memory_metrics)

        # Display GPU metrics
        gpu_metrics = data.get("gpu_metrics", {})
        if gpu_metrics:
            for gpu_idx, (uuid, metrics) in enumerate(gpu_metrics.items()):
                _display_gpu_section(uuid, metrics, gpu_idx)

    except APIError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise click.ClickException(f"VM '{vm_id}' not found.")
        raise click.ClickException(f"Failed to get dashboard: {error_msg}")


def _display_memory_section(metrics):
    """Display memory metrics with gauge chart."""
    mem_used_list = metrics.get("mem_used", [])
    mem_free_list = metrics.get("mem_free", [])

    if not mem_used_list or not mem_free_list:
        return

    # Get latest values
    mem_used = mem_used_list[-1] if mem_used_list else 0
    mem_free = mem_free_list[-1] if mem_free_list else 0
    mem_total = mem_used + mem_free

    if mem_total == 0:
        return

    mem_percent = (mem_used / mem_total) * 100

    click.echo("┌─────────────────────────────────────────────────────────────┐")
    click.echo("│ 💾 MEMORY                                                    │")
    click.echo("├─────────────────────────────────────────────────────────────┤")

    # Gauge chart
    _print_gauge(mem_percent, f"Memory Usage: {mem_used:.1f}GB / {mem_total:.1f}GB")

    # Simple sparkline for memory usage over time
    if len(mem_used_list) > 1:
        click.echo("│                                                             │")
        mem_percentages = [(u / (u + f) * 100) if (u + f) > 0 else 0
                          for u, f in zip(mem_used_list, mem_free_list)]
        _print_sparkline(mem_percentages, "Memory Trend", "%")

    click.echo("└─────────────────────────────────────────────────────────────┘\n")


def _display_gpu_section(uuid, metrics, gpu_idx):
    """Display GPU metrics with gauges and sparklines."""
    gpu_util_list = metrics.get("gpu_utilization", [])
    mem_util_list = metrics.get("memory_utilization", [])
    gpu_mem_used_list = metrics.get("gpu_memory_used", [])
    gpu_mem_free_list = metrics.get("gpu_memory_free", [])
    power_list = metrics.get("power_usage", [])
    temp_list = metrics.get("gpu_temp", [])

    if not gpu_util_list:
        return

    # Get latest values
    gpu_util = gpu_util_list[-1] if gpu_util_list else 0
    mem_util = mem_util_list[-1] if mem_util_list else 0
    gpu_mem_used = gpu_mem_used_list[-1] if gpu_mem_used_list else 0
    gpu_mem_free = gpu_mem_free_list[-1] if gpu_mem_free_list else 0
    gpu_mem_total = gpu_mem_used + gpu_mem_free
    power = power_list[-1] if power_list else 0
    temp = temp_list[-1] if temp_list else 0

    # Truncate UUID for display
    uuid_short = uuid[:8] + "..." if len(uuid) > 8 else uuid

    click.echo("┌─────────────────────────────────────────────────────────────┐")
    click.echo(f"│ 🎮 GPU #{gpu_idx} ({uuid_short:<45}) │")
    click.echo("├─────────────────────────────────────────────────────────────┤")

    # GPU Utilization Gauge
    _print_gauge(gpu_util, f"GPU Utilization")

    click.echo("│                                                             │")

    # GPU Memory Gauge
    if gpu_mem_total > 0:
        mem_percent = (gpu_mem_used / gpu_mem_total) * 100
        _print_gauge(mem_percent, f"GPU Memory: {gpu_mem_used:.1f}GB / {gpu_mem_total:.1f}GB")
    else:
        _print_gauge(mem_util, f"GPU Memory Utilization")

    click.echo("│                                                             │")

    # Temperature and Power as text
    temp_bar = _get_bar(temp, 100, 20)
    power_bar = _get_bar(power, 400, 20)

    click.echo(f"│  🌡  Temperature: {temp:>5.1f}°C  {temp_bar}                │")
    click.echo(f"│  ⚡ Power Usage: {power:>6.1f}W  {power_bar}                │")

    # Sparklines for trends
    if len(gpu_util_list) > 1:
        click.echo("│                                                             │")
        _print_sparkline(gpu_util_list, "GPU Util Trend", "%")

    if len(power_list) > 1:
        _print_sparkline(power_list, "Power Trend", "W")

    if len(temp_list) > 1:
        _print_sparkline(temp_list, "Temp Trend", "°C")

    click.echo("└─────────────────────────────────────────────────────────────┘\n")


def _print_gauge(percent, label):
    """Print a gauge chart for the given percentage."""
    # Ensure percent is in 0-100 range
    percent = max(0, min(100, percent))

    # Determine color/symbol based on percentage
    if percent >= 90:
        symbol = "█"
        status = "⚠"
    elif percent >= 70:
        symbol = "▓"
        status = "●"
    else:
        symbol = "▒"
        status = "●"

    # Create gauge (40 chars wide)
    gauge_width = 40
    filled = int((percent / 100) * gauge_width)
    gauge = symbol * filled + "░" * (gauge_width - filled)

    click.echo(f"│  {status} {label:<22}                              │")
    click.echo(f"│  [{gauge}] {percent:>5.1f}%  │")


def _get_bar(value, max_value, width=20):
    """Get a simple bar representation."""
    if max_value == 0:
        return "░" * width

    filled = int((value / max_value) * width)
    filled = max(0, min(width, filled))
    return "▓" * filled + "░" * (width - filled)


def _print_sparkline(values, label, unit):
    """Print a simple sparkline chart."""
    if not values or len(values) < 2:
        return

    # Use only recent values (last 30)
    values = values[-30:]

    # Create sparkline using unicode characters
    spark_chars = "▁▂▃▄▅▆▇█"

    if not values:
        return

    min_val = min(values)
    max_val = max(values)

    # Avoid division by zero
    if max_val == min_val:
        sparkline = spark_chars[0] * len(values)
    else:
        sparkline = "".join([
            spark_chars[min(int((v - min_val) / (max_val - min_val) * (len(spark_chars) - 1)), len(spark_chars) - 1)]
            for v in values
        ])

    # Truncate sparkline to fit
    sparkline = sparkline[:45]
    current_val = values[-1]

    click.echo(f"│  {label:<15} {sparkline} {current_val:>6.1f}{unit:<3}  │")


@vm_commands.command(name="interconnect")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def vm_interconnect(api_url: str):
    """Interconnect all running VMs for the current user (requires login).

    Sets up SSH key-based authentication between all running VMs.

    Examples:
        k8s-agent interconnect
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        click.echo("Setting up VM interconnection...")
        resp = api.request("PUT", "/api/vm/interconnect")

        data = resp.get("data", "")

        click.echo("✓ VMs interconnected successfully.\n")

        if data:
            click.echo("Deepspeed Hostfile:")
            click.echo(data)
            click.echo("\nYou can now SSH between VMs using: ssh <vm-id>")

    except APIError as e:
        error_msg = str(e)
        if "no running vms" in error_msg.lower():
            raise click.ClickException("No running VMs to interconnect.")
        raise click.ClickException(f"Failed to interconnect VMs: {error_msg}")


@vm_commands.command(name="ssh")
@click.argument("vm_id")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
def ssh_vm(vm_id: str, api_url: str):
    """Open SSH connection to VM using temporary SSH keys (requires login).

    This command generates a temporary SSH key pair, injects the public key into the VM,
    and connects using your system's SSH client. This ensures full terminal compatibility
    with vim, nano, tmux, and all other terminal applications.

    Examples:
        k8s-agent ssh my-vm-001
        k8s-agent ssh username1-0
    """
    import subprocess
    import tempfile
    import os

    api, _ = _get_authenticated_api(api_url)

    try:
        # Get VM info to verify it exists
        resp = api.request("GET", "/api/vm")
        vms = resp.get("data", {}).get("vms", []) if isinstance(resp.get("data"), dict) else resp.get("data", [])

        # Find the VM
        vm = next((v for v in vms if v.get("id") == vm_id), None)

        if not vm:
            raise click.ClickException(f"VM '{vm_id}' not found. Use 'k8s-agent list' to see available VMs.")

        # Check if VM is running
        status = vm.get("status")
        if status != "running":
            raise click.ClickException(f"VM '{vm_id}' is not running (status: {status}).")

        # Get SSH connection info from VM
        ssh_host = vm.get("host_ip")
        ssh_port = vm.get("svc_port")
        ssh_user = "root"  # Default user for VMs

        if not ssh_host or not ssh_port:
            raise click.ClickException(f"VM '{vm_id}' does not have SSH connection information (host_ip or svc_port missing).")

        # Use persistent SSH key stored in user's config directory
        config_dir = os.path.expanduser("~/.k8s-agent")
        os.makedirs(config_dir, exist_ok=True)
        private_key_path = os.path.join(config_dir, "id_ed25519")
        public_key_path = os.path.join(config_dir, "id_ed25519.pub")

        # Check if key already exists, if not generate it
        if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
            click.echo(f"Generating SSH key pair (first time only)...")
            keygen_result = subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-f", private_key_path, "-N", "", "-C", "k8s-agent-cli"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'  # Handle encoding issues on Windows
            )
            if keygen_result.returncode != 0:
                raise click.ClickException(f"Failed to generate SSH key: {keygen_result.stderr}")

        # Read the public key
        with open(public_key_path, 'r') as f:
            public_key = f.read().strip()

        # Try SSH connection first to see if key is already setup
        ssh_command = [
            "ssh",
            f"-p{ssh_port}",
            f"{ssh_user}@{ssh_host}",
            "-i", private_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR",
            "-o", "ConnectTimeout=2",
            "-o", "BatchMode=yes",  # Non-interactive
            "exit"  # Just test connection
        ]

        # Test if SSH key already works
        test_result = subprocess.run(ssh_command, capture_output=True)

        if test_result.returncode != 0:
            # Key not setup, inject it
            click.echo(f"Setting up SSH access to {vm_id}...")

            try:
                response = api.request('POST', '/api/vm/ssh-key', json_body={
                    'vmid': vm_id,
                    'public_key': public_key
                })
                if not response:
                    raise click.ClickException("Failed to setup SSH key in VM")
            except APIError as e:
                raise click.ClickException(f"Failed to inject SSH key: {e}")

        # Connect using SSH (remove test options)
        ssh_command = [
            "ssh",
            f"-p{ssh_port}",
            f"{ssh_user}@{ssh_host}",
            "-i", private_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR"
        ]

        # Execute SSH connection - this hands over control to the SSH client
        result = subprocess.run(ssh_command)

        # Exit with the same code as SSH (non-zero if connection failed)
        if result.returncode != 0 and result.returncode != 130:  # 130 is Ctrl+C
            raise click.ClickException(f"SSH connection exited with code {result.returncode}")

    except APIError as e:
        error_msg = str(e)
        raise click.ClickException(f"Failed to connect: {error_msg}")


@vm_commands.command(name="delete")
@click.argument("vm_id")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
@click.option("--force", is_flag=True, default=False, help="Force delete without confirmation")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip confirmation prompt")
def delete_vm(vm_id: str, api_url: str, force: bool, yes: bool):
    """Delete a VM by ID (requires login).

    Examples:
        k8s-agent delete my-vm-001
        k8s-agent delete my-vm-001 --yes
        k8s-agent delete my-vm-001 --force
    """
    api, _ = _get_authenticated_api(api_url)

    # Confirm deletion
    if not yes and not force:
        if not click.confirm(f"Are you sure you want to delete VM '{vm_id}'?"):
            click.echo("Cancelled.")
            return

    # Delete VM
    try:
        if force:
            # Force delete endpoint expects {"id": vm_id}
            endpoint = "/api/vm/force"
            json_body = {"id": vm_id}
        else:
            # Normal delete endpoint expects {"ids": [vm_id]}
            endpoint = "/api/vm"
            json_body = {"ids": [vm_id]}

        resp = api.request("DELETE", endpoint, json_body=json_body)
        click.echo(f"✓ VM '{vm_id}' deletion initiated successfully.")

        if force:
            click.echo("  (Force deleted - VM removed immediately)")
        else:
            click.echo("  (VM will be deleted)")
    except APIError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise click.ClickException(f"VM '{vm_id}' not found. Use 'k8s-agent list' to see available VMs.")
        raise click.ClickException(f"Failed to delete VM: {error_msg}")


@vm_commands.command(name="saves")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
@click.option("--json", "output_json", is_flag=True, default=False, help="Output in JSON format")
def list_saves(api_url: str, output_json: bool):
    """List available backup saves (requires login).

    Examples:
        k8s-agent saves
        k8s-agent saves --json
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        resp = api.request("GET", "/api/backup-saves")
        data = _extract_data(resp)

        if output_json:
            click.echo(json_module.dumps(data, indent=2))
            return

        home_saves = data.get("home_saves", [])
        env_saves = data.get("env_saves", [])

        if not home_saves and not env_saves:
            click.echo("No backup saves found.")
            return

        if home_saves:
            click.echo("\n📁 Home Backups:")
            for save in home_saves:
                name = save.get("name", "unknown") if isinstance(save, dict) else str(save)
                size = save.get("size_gb", 0) if isinstance(save, dict) else 0
                modified = save.get("modified", "") if isinstance(save, dict) else ""
                click.echo(f"  - {name:50s} {size:>8.2f} GB  {modified}")

        if env_saves:
            click.echo("\n🐍 Environment Backups:")
            for save in env_saves:
                name = save.get("name", "unknown") if isinstance(save, dict) else str(save)
                size = save.get("size_gb", 0) if isinstance(save, dict) else 0
                modified = save.get("modified", "") if isinstance(save, dict) else ""
                click.echo(f"  - {name:50s} {size:>8.2f} GB  {modified}")

        click.echo()

    except APIError as e:
        error_msg = str(e)
        raise click.ClickException(f"Failed to list saves: {error_msg}")


@vm_commands.command(name="keys")
@click.option("--api-url", "api_url", default="", help="Override API base URL")
@click.option("--json", "output_json", is_flag=True, default=False, help="Output in JSON format")
def list_keys(api_url: str, output_json: bool):
    """List SSH keys (requires login).

    Examples:
        k8s-agent keys
        k8s-agent keys --json
    """
    api, _ = _get_authenticated_api(api_url)

    try:
        resp = api.request("GET", "/api/keys")
        data = _extract_data(resp)

        if output_json:
            click.echo(json_module.dumps(data, indent=2))
            return

        if not data or (isinstance(data, list) and len(data) == 0):
            click.echo("No SSH keys found.")
            return

        keys = data if isinstance(data, list) else [data]

        click.echo("\n🔑 SSH Keys:")
        click.echo(f"{'ID':<8} {'Description':<30} {'Key (truncated)':<50} {'Created'}")
        click.echo("─" * 120)

        for key_info in keys:
            key_id = key_info.get("id", "N/A")
            description = key_info.get("description", "")[:28]
            key_value = key_info.get("key", "")
            # Truncate key to show first 40 chars
            key_truncated = key_value[:40] + "..." if len(key_value) > 40 else key_value
            create_time = key_info.get("create_time", "")

            click.echo(f"{key_id:<8} {description:<30} {key_truncated:<50} {create_time}")

        click.echo()

    except APIError as e:
        error_msg = str(e)
        raise click.ClickException(f"Failed to list keys: {error_msg}")
