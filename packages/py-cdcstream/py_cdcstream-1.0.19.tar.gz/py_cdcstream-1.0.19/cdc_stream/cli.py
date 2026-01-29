"""
CDC Stream - Command Line Interface
Simple, Docker-free CDC solution.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import socket
import os
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="CDC Stream - Real-time database change notifications")
console = Console()

# Global flag to track worker status
_worker_thread = None
_worker_running = False


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


@app.command()
def version() -> None:
    """Show version."""
    from cdc_stream import __version__
    rprint(f"[bold green]cdc-stream[/] v{__version__}")


@app.command()
def start(
    port: int = typer.Option(5858, "--port", "-p", help="Web server port"),
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run in background (detached mode)"),
) -> None:
    """
    🚀 Start CDC Stream - Everything with a single command!

    No Docker required! This command will:
    1. Setup database (SQLite for metadata)
    2. Start CDC Worker (listens for database changes)
    3. Start Web Server (UI + API)

    Examples:
        cdcstream start                    # Default port 5858
        cdcstream start --port 8080        # Custom port
        cdcstream start -p 8080 -d         # Background mode on port 8080
    """
    global _worker_thread, _worker_running

    # Daemon mode: restart self in background
    if daemon:
        import platform

        args = [sys.executable, "-m", "cdc_stream", "start", "--port", str(port)]

        if platform.system() == "Windows":
            # Windows: use DETACHED_PROCESS
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                args,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        else:
            # Linux/Mac: use nohup-like behavior
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )

        rprint(f"[green]✅ CDC Stream started in background on port {port}[/]")
        rprint(f"[dim]   Web UI: http://localhost:{port}[/]")
        rprint(f"[dim]   API:    http://localhost:{port}/api/[/]")
        rprint()
        rprint("[dim]To stop: cdcstream stop[/]")
        return

    # Banner
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔄 CDC Stream[/bold cyan]\n"
        "[dim]Real-time database change notifications[/dim]\n"
        "[dim green]No Docker • No Kafka • Just Python[/dim green]",
        border_style="cyan"
    ))
    console.print()

    # Step tracking
    total_steps = 3

    def step(num: int, text: str, status: str = "running"):
        symbols = {
            "running": "[yellow]⏳[/yellow]",
            "success": "[green]✅[/green]",
            "error": "[red]❌[/red]",
            "skip": "[dim]⏭️[/dim]"
        }
        console.print(f"{symbols[status]} [bold]Step {num}/{total_steps}:[/bold] {text}")

    step_num = 1

    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Setup Django & Migrations
    # ═══════════════════════════════════════════════════════════════
    step(step_num, "Setting up database...")

    from cdc_stream.django_setup import setup_django_if_needed
    setup_django_if_needed()
    from django.core.management import call_command

    # Run migrations silently
    call_command("migrate", interactive=False, verbosity=0)
    step(step_num, "Database ready (SQLite)", "success")
    step_num += 1

    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Start CDC Worker
    # ═══════════════════════════════════════════════════════════════
    step(step_num, "Starting CDC Worker...")
    _worker_running = True
    _worker_thread = threading.Thread(target=_run_worker_loop, daemon=True)
    _worker_thread.start()
    step(step_num, "CDC Worker running", "success")
    step_num += 1

    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Start Web Server
    # ═══════════════════════════════════════════════════════════════
    step(step_num, "Starting Web Server...")

    # Show final status
    console.print()

    table = Table(title="🎉 CDC Stream Ready!", border_style="green")
    table.add_column("Service", style="cyan")
    table.add_column("URL / Status", style="green")

    table.add_row("🌐 Web UI", f"http://localhost:{port}")
    table.add_row("📡 API", f"http://localhost:{port}/api/")
    table.add_row("⚙️ CDC Worker", "Listening for changes")

    console.print(table)
    console.print()

    # Instructions
    console.print(Panel(
        "[bold]Quick Start:[/bold]\n"
        "1. Open [cyan]http://localhost:{port}[/cyan] in your browser\n"
        "2. Add a database connection\n"
        "3. Create an alert (triggers auto-installed!)\n"
        "4. Watch for notifications! 🎉".format(port=port),
        title="📋 Next Steps",
        border_style="blue"
    ))
    console.print()

    console.print("[bold green]✨ All systems running![/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print()

    try:
        call_command("runserver", f"0.0.0.0:{port}", use_reloader=False)
    except KeyboardInterrupt:
        _worker_running = False
        console.print()
        console.print("[yellow]👋 CDC Stream stopped. Goodbye![/yellow]")


def _run_worker_loop():
    """Worker loop that auto-restarts and watches for datasources"""
    global _worker_running
    from cdc_stream.worker import run_worker

    while _worker_running:
        try:
            run_worker()
        except KeyboardInterrupt:
            break
        except Exception as e:
            if _worker_running:
                console.print(f"[yellow]⚠️ Worker: {e}. Restarting in 10s...[/yellow]")
                time.sleep(10)


@app.command()
def webserver(
    port: int = typer.Option(5858, help="Web server port"),
) -> None:
    """
    🌐 Start only the web server (no worker).
    """
    from cdc_stream.django_setup import setup_django_if_needed
    setup_django_if_needed()
    from django.core.management import call_command
    rprint(f"[cyan]Starting server on http://localhost:{port}[/]")
    call_command("migrate", interactive=False, verbosity=0)
    call_command("runserver", f"0.0.0.0:{port}", use_reloader=False)


@app.command()
def worker() -> None:
    """
    ⚙️ Start only the CDC Worker.
    """
    from cdc_stream.worker import run_worker
    run_worker()


@app.command()
def stop(
    port: int = typer.Option(5858, "--port", "-p", help="Port to stop"),
) -> None:
    """
    🛑 Stop CDC Stream running in background.
    """
    import platform

    if platform.system() == "Windows":
        # Windows: find and kill process using the port
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                shell=True
            )

            pid = None
            for line in result.stdout.split('\n'):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if parts:
                        pid = parts[-1]
                        break

            if pid:
                subprocess.run(["taskkill", "/F", "/PID", pid], shell=True, capture_output=True)
                rprint(f"[green]✅ CDC Stream stopped (PID: {pid})[/]")
            else:
                rprint(f"[yellow]⚠️ No CDC Stream found on port {port}[/]")
        except Exception as e:
            rprint(f"[red]❌ Error stopping: {e}[/]")
    else:
        # Linux/Mac: use lsof or fuser
        try:
            result = subprocess.run(
                ["lsof", "-t", f"-i:{port}"],
                capture_output=True,
                text=True
            )

            pids = result.stdout.strip().split('\n')
            if pids and pids[0]:
                for pid in pids:
                    subprocess.run(["kill", "-9", pid], capture_output=True)
                rprint(f"[green]✅ CDC Stream stopped[/]")
            else:
                rprint(f"[yellow]⚠️ No CDC Stream found on port {port}[/]")
        except Exception as e:
            rprint(f"[red]❌ Error stopping: {e}[/]")


@app.command()
def reset() -> None:
    """
    🗑️ Reset CDC Stream - Delete all data and start fresh.

    This will:
    - Stop any running CDC Stream instance
    - Delete the SQLite database (all connections, alerts, history)
    - Next start will be a fresh install

    Examples:
        cdcstream reset
    """
    from pathlib import Path
    import sys

    # Find database location WITHOUT importing Django (to avoid locking the db)
    db_path = None

    # Check common locations where Django might put the database
    possible_paths = [
        # Django default: BASE_DIR.parent / "db.sqlite3" where BASE_DIR is cdcserver package
        Path(sys.prefix) / "Lib" / "db.sqlite3",  # Windows pip install
        Path(sys.prefix) / "lib" / "db.sqlite3",  # Linux pip install
        Path.cwd() / "db.sqlite3",  # Current directory (dev mode)
        Path.home() / "db.sqlite3",  # Home directory
    ]

    # Also check site-packages locations
    for site_pkg in sys.path:
        if "site-packages" in site_pkg:
            pkg_path = Path(site_pkg)
            possible_paths.extend([
                pkg_path / "db.sqlite3",
                pkg_path.parent / "db.sqlite3",  # Lib/db.sqlite3
            ])

    for p in possible_paths:
        if p.exists():
            db_path = p
            break

    if not db_path or not db_path.exists():
        rprint("[yellow]⚠️ No database found. Nothing to reset.[/]")
        return

    # Stop any running CDCStream instances first
    rprint("[dim]Stopping any running CDCStream instances...[/dim]")
    import subprocess
    import platform
    import time

    stopped_any = False
    for port in [5858, 8000, 8080, 3000]:  # Common ports
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.strip().split()
                        if parts:
                            pid = parts[-1]
                            subprocess.run(["taskkill", "/F", "/PID", pid], shell=True, capture_output=True)
                            stopped_any = True
            else:
                result = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(["kill", "-9", pid], capture_output=True)
                        stopped_any = True
        except:
            pass

    # Wait for processes to fully terminate
    if stopped_any:
        rprint("[dim]Waiting for processes to terminate...[/dim]")
        time.sleep(3)

    # Delete the database with retry
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db_path.unlink()
            rprint("[green]✅ Database deleted successfully![/]")
            rprint("[dim]Run 'cdcstream start' for a fresh start.[/dim]")
            return
        except PermissionError:
            if attempt < max_retries - 1:
                rprint(f"[dim]Database still locked, retrying ({attempt + 2}/{max_retries})...[/dim]")
                time.sleep(2)
            else:
                rprint(f"[red]❌ Database is still in use. Please close any running CDCStream instances.[/]")
                rprint(f"[dim]Database location: {db_path}[/dim]")
                rprint(f"[dim]Try manually: Remove-Item \"{db_path}\"[/dim]")
        except Exception as e:
            rprint(f"[red]❌ Failed to delete database: {e}[/]")
            rprint(f"[dim]Try manually: Remove-Item \"{db_path}\"[/dim]")
            return


@app.command()
def status(
    port: int = typer.Option(5858, "--port", "-p", help="Port to check"),
) -> None:
    """
    📊 Show status of CDC Stream services.
    """
    console.print()
    console.print("[bold]CDC Stream Status[/bold]")
    console.print()

    # Check web server
    web_running = _is_port_open("localhost", port)

    table = Table()
    table.add_column("Service", style="cyan")
    table.add_column("Port")
    table.add_column("Status")

    table.add_row(
        "CDC Stream Web",
        str(port),
        "[green]● Running[/green]" if web_running else "[red]● Stopped[/red]"
    )

    console.print(table)
    console.print()

    # Database info
    from cdc_stream.django_setup import setup_django_if_needed
    setup_django_if_needed()

    try:
        from api.models import DataSource, Rule
        ds_count = DataSource.objects.count()
        rule_count = Rule.objects.filter(is_active=True).count()

        console.print(f"[dim]Datasources: {ds_count}[/dim]")
        console.print(f"[dim]Active Alerts: {rule_count}[/dim]")
    except Exception:
        pass

    console.print()


@app.command()
def build() -> None:
    """
    🔨 Build frontend for production.
    """
    web_dir = _project_root() / "web"

    if not web_dir.exists():
        rprint("[red]❌ web/ directory not found![/]")
        raise typer.Exit(1)

    rprint("[cyan]📦 Installing dependencies...[/]")
    result = subprocess.run(["npm", "install"], cwd=web_dir, shell=True)
    if result.returncode != 0:
        rprint("[red]❌ npm install failed![/]")
        raise typer.Exit(1)

    rprint("[cyan]🔨 Building frontend...[/]")
    result = subprocess.run(["npm", "run", "build"], cwd=web_dir, shell=True)
    if result.returncode != 0:
        rprint("[red]❌ npm run build failed![/]")
        raise typer.Exit(1)

    out_dir = web_dir / "out"
    if out_dir.exists():
        rprint(f"[green]✅ Frontend built successfully![/]")
        rprint(f"[dim]Output: {out_dir}[/]")
    else:
        rprint("[yellow]⚠️ Build completed but output directory not found[/]")


@app.command()
def triggers(
    datasource_id: int = typer.Argument(..., help="Datasource ID to manage triggers for"),
    action: str = typer.Argument("list", help="Action: list, sync, or remove"),
) -> None:
    """
    🔧 Manage CDC triggers on database tables.

    Actions:
    - list: Show all CDC triggers
    - sync: Sync triggers with active alerts
    - remove: Remove all CDC triggers
    """
    from cdc_stream.django_setup import setup_django_if_needed
    setup_django_if_needed()

    from api.models import DataSource
    from cdc_stream.trigger_manager import TriggerManager, get_connection

    try:
        ds = DataSource.objects.get(id=datasource_id)
    except DataSource.DoesNotExist:
        rprint(f"[red]❌ Datasource #{datasource_id} not found[/]")
        raise typer.Exit(1)

    config = ds.connector_config or {}
    if not config.get('host'):
        rprint("[red]❌ Datasource has no connection config[/]")
        raise typer.Exit(1)

    try:
        conn = get_connection(config)
        manager = TriggerManager(conn)

        if action == "list":
            triggers = manager.list_triggers()
            if triggers:
                table = Table(title=f"CDC Triggers on {ds.name}")
                table.add_column("Schema")
                table.add_column("Table")
                table.add_column("Trigger")
                for t in triggers:
                    table.add_row(t['schema'], t['table'], t['trigger_name'])
                console.print(table)
            else:
                rprint("[dim]No CDC triggers found[/dim]")

        elif action == "sync":
            from api.models import Rule
            rules = Rule.objects.filter(datasource=ds, is_active=True)
            alerts = [{'schema': r.schema_name or 'public', 'table': r.table_name, 'is_active': True} for r in rules]
            result = manager.sync_triggers_with_alerts(alerts)
            if result['created']:
                rprint(f"[green]✅ Created: {', '.join(result['created'])}[/]")
            if result['removed']:
                rprint(f"[yellow]Removed: {', '.join(result['removed'])}[/]")
            if not result['created'] and not result['removed']:
                rprint("[dim]No changes needed[/dim]")

        elif action == "remove":
            triggers = manager.list_triggers()
            for t in triggers:
                manager.drop_trigger(t['schema'], t['table'])
            rprint(f"[green]✅ Removed {len(triggers)} trigger(s)[/]")

        else:
            rprint(f"[red]Unknown action: {action}[/]")

        conn.close()

    except Exception as e:
        rprint(f"[red]❌ Error: {e}[/]")
        raise typer.Exit(1)


@app.command()
def test_listener(
    datasource_id: int = typer.Argument(..., help="Datasource ID to listen to"),
) -> None:
    """
    🎧 Test the CDC listener for a datasource.

    This will listen for NOTIFY events and print them to the console.
    Press Ctrl+C to stop.
    """
    from cdc_stream.django_setup import setup_django_if_needed
    setup_django_if_needed()

    from api.models import DataSource
    from cdc_stream.listener import run_standalone_listener

    try:
        ds = DataSource.objects.get(id=datasource_id)
    except DataSource.DoesNotExist:
        rprint(f"[red]❌ Datasource #{datasource_id} not found[/]")
        raise typer.Exit(1)

    config = ds.connector_config or {}
    if not config.get('host'):
        rprint("[red]❌ Datasource has no connection config[/]")
        raise typer.Exit(1)

    rprint(f"[cyan]🎧 Listening for CDC events on {ds.name}...[/]")
    rprint("[dim]Press Ctrl+C to stop[/dim]")
    rprint()

    run_standalone_listener(config)


if __name__ == "__main__":
    app()
