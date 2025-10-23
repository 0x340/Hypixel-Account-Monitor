"""
monitor_hypixel.py

Polls the Hypixel API every N seconds and notifies when a monitored JSON value changes.
Configuration can be provided via --config or CLI arguments.

Requires: requests, jmespath
Optional: win10toast (for Windows notifications)
"""

import time
import argparse
import requests
import json
import sys
import os

try:
    import jmespath
except Exception:
    print("Missing dependency: jmespath. Install with: pip install jmespath")
    sys.exit(1)

# Optional Windows toast
try:
    from win10toast import ToastNotifier
    TOASTER = ToastNotifier()
except Exception:
    TOASTER = None

HYPEX_BASE = "https://api.hypixel.net"
MOJANG_API = "https://api.mojang.com/users/profiles/minecraft/{}"


def get_uuid_for_username(username: str) -> str | None:
    """Resolve a Minecraft username to a UUID using Mojang API."""
    try:
        r = requests.get(MOJANG_API.format(username), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("id")
        return None
    except Exception:
        return None


def fetch_hypixel(endpoint: str, api_key: str, params: dict) -> dict | None:
    url = f"{HYPEX_BASE}/{endpoint}"
    params = params.copy() if params else {}
    params["key"] = api_key
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None


def notify_windows(title: str, msg: str) -> None:
    if TOASTER:
        try:
            TOASTER.show_toast(title, msg, duration=6, threaded=True)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Monitor a value from Hypixel API and notify on change")
    parser.add_argument("--api-key", "-k", help="Hypixel API key", required=False)
    parser.add_argument("--username", "-u", help="Minecraft username to monitor (optional, will be resolved to UUID)")
    parser.add_argument("--uuid", help="Minecraft UUID to monitor (if you already have it)")
    parser.add_argument("--endpoint", "-e", default="player", help="Hypixel endpoint to call (default: player). Examples: player, skyblock/profiles, skyblock/profile")
    parser.add_argument("--jmespath", "-j", required=False, help="JMESPath expression to extract the value to monitor from the JSON response. Example: player.networkExp or profiles[0].members.'<uuid>'.experience_skill_farming")
    parser.add_argument("--interval", "-i", type=int, default=300, help="Poll interval in seconds (default 300 = 5min)")
    parser.add_argument("--config", "-c", help="Path to JSON config file (optional). CLI args override config file)")
    parser.add_argument("--notify", action="store_true", help="Show Windows toast notifications if possible")
    args = parser.parse_args()

    config = {}
    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Failed to read config file: {e}")
            sys.exit(1)

    api_key = args.api_key or config.get("api_key")
    username = args.username or config.get("username")
    uuid = args.uuid or config.get("uuid")
    endpoint = args.endpoint or config.get("endpoint", "player")
    jmespath_expr = args.jmespath or config.get("jmespath")
    interval = args.interval or config.get("interval", 300)
    do_notify = args.notify or config.get("notify", False)

    if not api_key:
        print("Hypixel API key is required. Get one from https://api.hypixel.net/")
        sys.exit(1)

    if username and not uuid:
        print(f"Resolving username '{username}' to UUID...")
        uuid = get_uuid_for_username(username)
        if not uuid:
            print("Failed to resolve username to UUID. Provide a UUID instead or check the username.")
            sys.exit(1)
        else:
            print(f"Resolved UUID: {uuid}")

    # Prepare params depending on endpoint commonly used
    params = {}
    if endpoint in ("player",):
        if username:
            params["name"] = username
        elif uuid:
            params["uuid"] = uuid
    elif endpoint in ("skyblock/profiles",):
        if uuid:
            params["uuid"] = uuid
        else:
            print("When monitoring skyblock/profiles you should provide --uuid (profile owner UUID)")
            sys.exit(1)
    elif endpoint in ("skyblock/profile",):
        prof = config.get("profile")
        if prof:
            params["profile"] = prof
        else:
            print("For endpoint skyblock/profile you must provide a profile id in the config (profile)")
            sys.exit(1)
    else:

        params.update(config.get("params", {}))

    if not jmespath_expr:
        print("You must supply a JMESPath expression to extract the value to monitor. Example expressions are in README.md")
        sys.exit(1)

    last_value = None
    print("Starting monitor: endpoint=", endpoint, "interval=", interval, "seconds")

    while True:
        data = fetch_hypixel(endpoint, api_key, params)
        if data is None:
            print("Failed to fetch data this round; will retry after interval.")
        else:
            try:
                value = jmespath.search(jmespath_expr, data)
            except Exception as e:
                print(f"Failed to evaluate JMESPath expression: {e}")
                print("Expression:", jmespath_expr)
                sys.exit(1)

            if value != last_value:
                # On first run last_value will be None and we'll treat as change — print state
                if last_value is None:
                    print(f"[INIT] Monitored value: {value}")
                else:
                    print(f"[CHANGE] Value changed: {last_value} -> {value}")
                    msg = f"Value changed: {last_value} -> {value}"
                    if do_notify and TOASTER:
                        notify_windows("Hypixel Monitor", msg)
                last_value = value
            else:
                print(f"No change. Current value: {value}")

        time.sleep(max(5, interval))


if __name__ == "__main__":
    main()
