"""
CDC Stream - Daily Log Cleanup Worker
Runs daily at midnight to delete old trigger logs based on each alert's retention settings.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from rich import print as rprint

from .django_setup import setup_django_if_needed

# Global state
_cleanup_worker_running = False
_cleanup_thread: Optional[threading.Thread] = None
_last_run_time: Optional[datetime] = None
_next_run_time: Optional[datetime] = None
_logs_deleted_count: int = 0
_last_run_status: str = "not_started"


def get_daily_cleanup_stats() -> dict:
    """Get daily cleanup worker statistics."""
    return {
        "name": "daily_log_cleanup",
        "running": _cleanup_worker_running,
        "last_run_time": _last_run_time.isoformat() if _last_run_time else None,
        "next_run_time": _next_run_time.isoformat() if _next_run_time else None,
        "logs_deleted_last_run": _logs_deleted_count,
        "last_run_status": _last_run_status,
    }


def cleanup_old_logs() -> int:
    """
    Delete old trigger logs based on each alert's log_retention_days setting.
    Returns the number of logs deleted.
    """
    global _logs_deleted_count, _last_run_status, _last_run_time

    setup_django_if_needed()

    from django.utils import timezone
    from api.models import Rule, TriggerLog

    total_deleted = 0
    now = timezone.now()

    try:
        # Get all rules with their retention settings
        rules = Rule.objects.all()

        for rule in rules:
            retention_days = rule.log_retention_days or 30
            cutoff_date = now - timedelta(days=retention_days)

            # Delete logs older than the cutoff date for this rule
            deleted_count, _ = TriggerLog.objects.filter(
                rule=rule,
                created_at__lt=cutoff_date
            ).delete()

            if deleted_count > 0:
                rprint(f"[cyan]🗑️ Deleted {deleted_count} old logs for alert '{rule.name}' (retention: {retention_days} days)[/]")
                total_deleted += deleted_count

        _logs_deleted_count = total_deleted
        _last_run_status = "success"
        _last_run_time = now

        if total_deleted > 0:
            rprint(f"[green]✅ Daily cleanup completed: {total_deleted} logs deleted[/]")
        else:
            rprint(f"[green]✅ Daily cleanup completed: No old logs to delete[/]")

    except Exception as e:
        _last_run_status = f"error: {str(e)}"
        _last_run_time = now
        rprint(f"[red]❌ Daily cleanup failed: {e}[/]")

    return total_deleted


def _calculate_next_midnight() -> datetime:
    """Calculate the next midnight time."""
    from django.utils import timezone

    now = timezone.now()
    # Next midnight
    tomorrow = now.date() + timedelta(days=1)
    midnight = datetime.combine(tomorrow, datetime.min.time())

    # Make it timezone aware
    if timezone.is_naive(midnight):
        midnight = timezone.make_aware(midnight)

    return midnight


def _cleanup_worker_loop():
    """Main loop for the daily cleanup worker."""
    global _cleanup_worker_running, _next_run_time

    setup_django_if_needed()
    from django.utils import timezone

    rprint("[cyan]🕐 Daily log cleanup worker started[/]")

    # Run initial cleanup on startup
    rprint("[cyan]🔄 Running initial log cleanup...[/]")
    cleanup_old_logs()

    while _cleanup_worker_running:
        try:
            # Calculate next midnight
            _next_run_time = _calculate_next_midnight()
            now = timezone.now()

            # Calculate seconds until midnight
            seconds_until_midnight = (_next_run_time - now).total_seconds()

            if seconds_until_midnight > 0:
                rprint(f"[cyan]⏰ Next cleanup scheduled at {_next_run_time.strftime('%Y-%m-%d %H:%M:%S')} ({int(seconds_until_midnight/3600)} hours)[/]")

                # Sleep in small intervals to allow for graceful shutdown
                sleep_interval = 60  # Check every minute
                while seconds_until_midnight > 0 and _cleanup_worker_running:
                    time.sleep(min(sleep_interval, seconds_until_midnight))
                    now = timezone.now()
                    seconds_until_midnight = (_next_run_time - now).total_seconds()

            if _cleanup_worker_running:
                rprint("[cyan]🕛 Midnight reached - running daily cleanup...[/]")
                cleanup_old_logs()

        except Exception as e:
            rprint(f"[red]❌ Cleanup worker error: {e}[/]")
            time.sleep(60)  # Wait a minute before retrying

    rprint("[yellow]⏹️ Daily log cleanup worker stopped[/]")


def start_daily_cleanup_worker():
    """Start the daily cleanup worker thread."""
    global _cleanup_worker_running, _cleanup_thread

    if _cleanup_worker_running:
        rprint("[yellow]⚠️ Daily cleanup worker already running[/]")
        return

    _cleanup_worker_running = True
    _cleanup_thread = threading.Thread(target=_cleanup_worker_loop, daemon=True)
    _cleanup_thread.start()

    rprint("[green]✅ Daily log cleanup worker started (daily_log_delete)[/]")


def stop_daily_cleanup_worker():
    """Stop the daily cleanup worker."""
    global _cleanup_worker_running, _cleanup_thread

    _cleanup_worker_running = False

    if _cleanup_thread and _cleanup_thread.is_alive():
        _cleanup_thread.join(timeout=5)

    _cleanup_thread = None
    rprint("[yellow]⏹️ Daily log cleanup worker stopped[/]")


def is_cleanup_worker_running() -> bool:
    """Check if the cleanup worker is running."""
    return _cleanup_worker_running

