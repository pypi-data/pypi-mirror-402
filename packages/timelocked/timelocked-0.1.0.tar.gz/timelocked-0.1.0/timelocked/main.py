#!/usr/bin/env python3
"""Track screen lock/unlock times via dbus."""

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path.home() / ".timelocked.jsonl"


def get_log_file() -> Path:
    return LOG_FILE


def parse_log() -> list[dict]:
    """Read all events from log file."""
    log_file = get_log_file()
    if not log_file.exists():
        return []
    
    events = []
    for line in log_file.read_text().strip().split("\n"):
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def log_event(event_type: str):
    """Append an event to the log."""
    log_file = get_log_file()
    entry = {
        "time": datetime.now().isoformat(),
        "event": event_type,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"{entry['time']} {event_type}")


def calculate_unlocked_time(since: datetime | None = None) -> timedelta:
    """Calculate total unlocked time, optionally since a given datetime."""
    events = parse_log()
    
    if not events:
        return timedelta(0)
    
    total = timedelta(0)
    last_unlock = None
    
    for event in events:
        event_time = datetime.fromisoformat(event["time"])
        
        if since and event_time < since:
            # Track state but don't count time before 'since'
            if event["event"] == "UNLOCKED":
                last_unlock = since  # Start counting from 'since'
            else:
                last_unlock = None
            continue
        
        if event["event"] == "UNLOCKED":
            last_unlock = event_time
        elif event["event"] == "LOCKED" and last_unlock:
            total += event_time - last_unlock
            last_unlock = None
    
    # If currently unlocked, add time until now
    if last_unlock:
        total += datetime.now() - last_unlock
    
    return total


def format_duration(td: timedelta) -> str:
    """Format timedelta as human readable string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours:
        return f"{hours}h {minutes}m"
    elif minutes:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def daemon():
    """Run the dbus monitor daemon."""
    print(f"Logging to {get_log_file()}")
    
    proc = subprocess.Popen(
        ["dbus-monitor", "--session", "interface='org.freedesktop.ScreenSaver'"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    
    try:
        for line in proc.stdout:
            if "boolean true" in line:
                log_event("LOCKED")
            elif "boolean false" in line:
                log_event("UNLOCKED")
    except KeyboardInterrupt:
        proc.terminate()


def install_service():
    """Install systemd user service."""
    import shutil
    
    # Find timelocked executable
    timelocked_path = shutil.which("timelocked")
    if not timelocked_path:
        # Fallback to current script
        timelocked_path = Path(__file__).resolve()
    
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    
    service_file = service_dir / "timelocked.service"
    service_content = f"""[Unit]
Description=Track screen lock/unlock times
After=graphical-session.target

[Service]
ExecStart={timelocked_path} --daemon
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
"""
    
    service_file.write_text(service_content)
    print(f"Created {service_file}")
    
    # Reload and enable
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "timelocked.service"], check=True)
    subprocess.run(["systemctl", "--user", "start", "timelocked.service"], check=True)
    
    print("Service installed and started.")
    print("Check status: systemctl --user status timelocked")


def main():
    parser = argparse.ArgumentParser(description="Track screen lock/unlock times")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run the dbus monitor daemon")
    parser.add_argument("--unlocked", "--un", action="store_true", help="Show total unlocked time today")
    parser.add_argument("--since", "-s", type=str, help="Calculate unlocked time since (ISO datetime or 'today')")
    parser.add_argument("--log", "-l", action="store_true", help="Show recent log entries")
    parser.add_argument("--log-file", action="store_true", help="Print log file path")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--install", action="store_true", help="Install systemd user service")
    
    args = parser.parse_args()
    
    if args.install:
        install_service()
        return
    
    if args.log_file:
        print(get_log_file())
        return
    
    if args.daemon:
        daemon()
        return
    
    if args.log:
        events = parse_log()
        for event in events[-20:]:
            print(f"{event['time']} {event['event']}")
        return
    
    if args.unlocked:
        since = None
        if args.since:
            if args.since == "today":
                since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                since = datetime.fromisoformat(args.since)
        else:
            # Default to today
            since = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        unlocked = calculate_unlocked_time(since)
        if args.json:
            print(json.dumps({"unlocked_seconds": int(unlocked.total_seconds())}))
        else:
            print(format_duration(unlocked))
        return
    
    # Default: show status
    events = parse_log()
    if events:
        last = events[-1]
        state = "UNLOCKED" if last["event"] == "UNLOCKED" else "LOCKED"
        print(f"Currently: {state}")
        print(f"Last event: {last['time']}")
    
    # Show today's unlocked time
    since_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    unlocked = calculate_unlocked_time(since_today)
    print(f"Unlocked today: {format_duration(unlocked)}")


if __name__ == "__main__":
    main()