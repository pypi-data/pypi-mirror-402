# secureproximity/cli.py
import asyncio
import sys
import threading
import time
from secureproximity import __version__
from secureproximity.config import load_config, save_config, reset_config
from secureproximity.utils import sp_discover_nearby_devices
from secureproximity.core import SPMonitorThread

# ANSI color helpers
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"

BANNER = f"""
 {YELLOW} ███████╗███████╗ ██████╗██╗   ██╗██████╗ ███████╗██████╗ ██████╗ ██╗  ██╗██╗███╗   ███╗██╗████████╗██╗   ██╗
██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗██╔═══██╗╚██╗██╔╝██║████╗ ████║██║╚══██╔══╝╚██╗ ██╔╝
███████╗█████╗  ██║     ██║   ██║██████╔╝█████╗  ██████╔╝██║   ██║ ╚███╔╝ ██║██╔████╔██║██║   ██║    ╚████╔╝
╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║ ██╔██╗ ██║██║╚██╔╝██║██║   ██║     ╚██╔╝
███████║███████╗╚██████╗╚██████╔╝██║  ██║███████╗██║     ╚██████╔╝██╔╝ ██╗██║██║ ╚═╝ ██║██║   ██║      ██║
╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚═╝   ╚═╝      ╚═╝{RESET}

 {CYAN}SecureProximity — Advanced Security Tool v{__version__}{RESET}
Type 'help' for commands.
"""

PROMPT = f"{CYAN}secure-proximity> {RESET}"

# Global monitor reference for SecureProximity
_sp_monitor: SPMonitorThread = None
_sp_monitor_lock = threading.Lock()

def print_banner():
    print(BANNER)
    # Show last device connected (configured device)
    cfg = load_config()
    phone_mac = cfg.get("PHONE_MAC")
    device_name = cfg.get("DEVICE_NAME")
    
    if phone_mac:
        name_display = device_name if device_name else "Unknown Device"
        print(f"{CYAN}Last Device Connected: {name_display} ({phone_mac}){RESET}")
    else:
        print(f"{YELLOW}No device configured. Run 'scan' to find your phone.{RESET}")


def cmd_help():
    print(f"""
{CYAN}Available commands:{RESET}
  {GREEN}scan{RESET}                 - Discover nearby Bluetooth devices
  {GREEN}set-device <num>{RESET}    - Select device from last scan results
  {GREEN}start{RESET}                - Start background proximity monitoring
  {GREEN}stop{RESET}                 - Stop background monitoring
  {GREEN}status{RESET}               - Show monitor status and config
  {GREEN}reset{RESET}                - Reset saved configuration
  {GREEN}help{RESET}                 - Show this help
  {GREEN}exit{RESET} / {GREEN}quit{RESET} - Exit the tool
""")

# In-memory last scan results
_last_scan = []

def command_scan():
    global _last_scan
    cfg = load_config()
    duration = cfg.get("SCAN_DURATION", 5)
    print(f"{YELLOW}Scanning for nearby Bluetooth devices ({duration}s)...{RESET}")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        devices = loop.run_until_complete(sp_discover_nearby_devices(duration=duration))
        loop.close()
    except Exception as e:
        print(f"{RED}Error scanning: {e}{RESET}")
        devices = []
    _last_scan = devices
    if not devices:
        print(f"{RED}No devices found. Ensure Bluetooth is enabled and your phone is discoverable.{RESET}")
        return
    for i, (mac, name) in enumerate(devices):
        print(f"  [{i}] {name} ({mac})")

def command_set_device(tokens):
    global _last_scan
    if not _last_scan:
        print(f"{YELLOW}No previous scan results. Run 'scan' first.{RESET}")
        return
    if len(tokens) < 2:
        print(f"{YELLOW}Usage: set-device <number>{RESET}")
        return
    try:
        idx = int(tokens[1])
        mac, name = _last_scan[idx]
        cfg = load_config()
        cfg["PHONE_MAC"] = mac
        cfg["DEVICE_NAME"] = name
        save_config(cfg)
        print(f"{GREEN}Device saved: {name} ({mac}){RESET}")
    except (ValueError, IndexError):
        print(f"{RED}Invalid selection.{RESET}")

def start_monitor():
    global _sp_monitor
    with _sp_monitor_lock:
        if _sp_monitor and not _sp_monitor.stopped():
            print(f"{YELLOW}Monitor already running.{RESET}")
            return
        cfg = load_config()
        sp_phone_mac = cfg.get("PHONE_MAC")
        if not sp_phone_mac:
            print(f"{YELLOW}No device configured. Run 'scan' then 'set-device'.{RESET}")
            return
        poll = cfg.get("POLL_INTERVAL", 10)
        pause = cfg.get("UNLOCK_PAUSE", 180)
        threshold = cfg.get("SAFETY_THRESHOLD", 2)
        scan_dur = cfg.get("SCAN_DURATION", 5)
        _sp_monitor = SPMonitorThread(sp_phone_mac=sp_phone_mac,
                                  poll_interval=poll,
                                  pause_after_unlock=pause,
                                  safety_threshold=threshold,
                                  scan_duration=scan_dur)
        _sp_monitor.start()
        print(f"{GREEN}Monitor started for {sp_phone_mac} (interval={poll}s, pause={pause}s).{RESET}")

def stop_monitor():
    global _sp_monitor
    with _sp_monitor_lock:
        if not _sp_monitor or _sp_monitor.stopped():
            print(f"{YELLOW}Monitor is not running.{RESET}")
            return
        _sp_monitor.stop()
        # wait a short time for thread to exit
        for _ in range(10):
            if _sp_monitor.stopped():
                break
            time.sleep(0.2)
        print(f"{GREEN}Monitor stopped.{RESET}")
        _sp_monitor = None

def show_status():
    cfg = load_config()
    sp_phone = cfg.get("PHONE_MAC") or "<not set>"
    name = cfg.get("DEVICE_NAME") or "<unknown>"
    poll = cfg.get("POLL_INTERVAL", 10)
    pause = cfg.get("UNLOCK_PAUSE", 180)
    threshold = cfg.get("SAFETY_THRESHOLD", 2)
    running = _sp_monitor is not None and not _sp_monitor.stopped()
    print(f"{CYAN}Status:{RESET}")
    print(f"  Device: {name} ({sp_phone})")
    print(f"  Monitoring: {GREEN if running else YELLOW}{running}{RESET}")
    
    if running and _sp_monitor.last_seen > 0:
        elapsed = time.time() - _sp_monitor.last_seen
        last_seen_str = time.strftime('%H:%M:%S', time.localtime(_sp_monitor.last_seen))
        print(f"  Last Seen: {GREEN}{last_seen_str} ({int(elapsed)}s ago){RESET}")
    elif running:
        print(f"  Last Seen: {YELLOW}Never (since start){RESET}")

    print(f"  Interval: {poll}s  Pause after lock: {pause}s  Safety threshold: {threshold}")


def reset_config_command():
    confirm = input("Are you sure you want to reset configuration? (y/n): ").strip().lower()
    if confirm == "y":
        reset_config()
        print(f"{GREEN}Configuration reset.{RESET}")
    else:
        print("Cancelled.")

def repl():
    print_banner()
    while True:
        try:
            cmdline = input(PROMPT).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting SecureProximity...")
            stop_monitor()
            sys.exit(0)

        if not cmdline:
            continue

        tokens = cmdline.split()
        cmd = tokens[0].lower()

        if cmd == "help":
            cmd_help()
        elif cmd == "scan":
            command_scan()
        elif cmd == "set-device":
            command_set_device(tokens)
        elif cmd == "start":
            start_monitor()
        elif cmd == "stop":
            stop_monitor()
        elif cmd == "status":
            show_status()
        elif cmd == "reset":
            reset_config_command()
        elif cmd in ("exit", "quit"):
            stop_monitor()
            print("Goodbye.")
            sys.exit(0)
        else:
            print(f"{YELLOW}Unknown command: {cmd}. Type 'help' for commands.{RESET}")

def main():
    try:
        repl()
    except Exception as e:
        print(f"{RED}SecureProximity fatal error: {e}{RESET}")
        stop_monitor()
        raise

if __name__ == "__main__":
    main()
